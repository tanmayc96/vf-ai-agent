import os

from google.adk.agents import Agent, LlmAgent, SequentialAgent
from vertexai.preview import rag

from dotenv import load_dotenv
import json

from google.genai import types
from google.adk.tools.agent_tool import AgentTool
from google.adk.agents.callback_context import CallbackContext
from datetime import date
from google.adk.tools import load_artifacts

from .sub_agents.rag_agent.agent import rag_agent
from .sub_agents.bigquery.agent import db_agent
from .sub_agents.search_agent.agent import search_agent
from .prompts import return_instructions_root

from google.adk.runners import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from .sub_agents.bigquery import tools as bq_tools

from .sub_agents.bigquery.tools import (
    get_database_settings as get_bq_database_settings,
)

os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"
os.environ["GOOGLE_CLOUD_PROJECT"] = "vf-grp-aib-dev-ngi-sbx-alpha"
os.environ["GOOGLE_CLOUD_LOCATION"] = "europe-west1"

def classify_query(query: str) -> dict:
    """Classifies the query to determine if it relates to strategy or performance."""
    lower_query = query.lower()
    strategy_keywords = [
        "strategy documents", "strategy document", "strategic reports", 
        "strategic report", "strategic document", "strategy"
    ]
    performance_keywords = [
        "vodafone performance data", "performance data", "network performance", 
        "commercial performance", "vodafone data"
    ]
    
    return {
        "has_strategy": any(k in lower_query for k in strategy_keywords),
        "has_performance": any(k in lower_query for k in performance_keywords),
    }

async def run_adk_agent(agent: Agent, query: str, state_updates: dict = None, session_id: str = "default_user", user_id: str = "user") -> str:
    """Runs a standard ADK agent for a single turn."""
    session_service = InMemorySessionService()
    runner = Runner(agent=agent, session_service=session_service, app_name="temp_runner")
    
    # Pre-populate state if needed (hacky way to inject state before run)
    session = session_service.get_session(session_id, user_id)
    if not session:
        session = session_service.create_session(session_id, user_id)
    
    if state_updates:
        session.state.update(state_updates)
        session_service.update_session(session) # Ensure persistence if needed (InMemory handles ref)

    response_text = ""
    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=types.Content(role="user", parts=[types.Part(text=query)])
    ):
        if event.content:
            for part in event.content.parts:
                if part.text:
                    response_text += part.text
    return response_text

async def run_rag_agent(query: str, session_id: str, user_id: str) -> str:
    return await run_adk_agent(rag_agent, query, None, session_id, user_id)

async def run_search_agent(query: str, session_id: str, user_id: str) -> str:
    return await run_adk_agent(search_agent, query, None, session_id, user_id)

async def run_db_agent(query: str, data_type: str, session_id: str = "default", user_id: str = "user") -> str:
    """Runs the DB agent with a restricted schema based on data_type."""
    allowed_tables = []
    if data_type == "foundation":
        allowed_tables = ["berlin_external_foundation"]
    elif data_type == "all":
        # From tools.py
        allowed_tables = [
            "berlin_external_foundation",
            "vodafone_performance"
        ]
    else:
        # Default fallback
        allowed_tables = ["berlin_external_foundation"]
        
    # Generate schema for these tables
    # explicit project/dataset ids from tools.py
    ddl_schema = bq_tools.get_bigquery_schema(
        dataset_id="h3_consumption",
        project_id="vf-grp-aib-dev-ngi-sbx-alpha",
        allowed_tables=allowed_tables
    )
    
    state_updates = {
        "database_settings": {
            "bq_project_id": "vf-grp-aib-dev-ngi-sbx-alpha",
            "bq_dataset_id": "h3_consumption",
            "bq_ddl_schema": ddl_schema,
        }
    }
    
    return await run_adk_agent(db_agent, query, state_updates, session_id, user_id)

async def custom_agent_orchestrator(query: str, session_id: str = "default_session", user_id: str = "user") -> dict:
    """Orchestrates sub-agent calls based on query analysis and formats the output."""
    analysis = classify_query(query)
    
    results = {}
    
    # Deterministic Routing Logic
    if analysis["has_strategy"] and analysis["has_performance"]:
        print(f"Routing Application: Strategy + Performance Mode")
        # Strategy + External Foundation + Network & Commercial Performance + Search
        results["rag"] = await run_rag_agent(query, session_id, user_id)
        results["db"] = await run_db_agent(query, "all", session_id, user_id)
        results["search"] = await run_search_agent(query, session_id, user_id)

    elif analysis["has_strategy"]:
        print(f"Routing Application: Strategy Mode")
        # Strategy + External Foundation + Search
        results["rag"] = await run_rag_agent(query, session_id, user_id)
        results["db"] = await run_db_agent(query, "foundation", session_id, user_id)
        results["search"] = await run_search_agent(query, session_id, user_id)
        
    else:
        print(f"Routing Application: Default/External Mode")
        # External Foundation + Search (No Strategy)
        results["db"] = await run_db_agent(query, "foundation", session_id, user_id)
        results["search"] = await run_search_agent(query, session_id, user_id)
        
    # Consolidate information
    consolidated_info = ""
    for source, content in results.items():
        consolidated_info += f"\n--- Source: {source.upper()} ---\n{content}\n"
    
    # Generate final JSON output using an LLM
    prompt = f"""
    You are the Lead Strategic Coordinator for the NGNI Agent.
    Based on the following information from various sub-agents, provide a FINAL ANSWER to the user's query: '{query}'.
    
    STRICT REQUIREMENT: The output MUST be a valid JSON object. Do not include markdown formatting (like ```json ... ```) outside of the raw string if possible, but the parser handles it.
    
    The JSON structure MUST be:
    {{
        "ranked_areas": [
            {{
                "rank": <Integer 1-N>,
                "municipality": "<Municipality Name>",
                "score": <Integer 0-100>,
                "details": {{
                    "strategy": "<Strategy insights>",
                    "data": "<Data metrics or 'Not Available'>",
                    "context": "<Market context used for ranking>"
                }}
            }}
        ]
    }}
    
    CRITICAL INSTRUCTIONS:
    1.  **NEVER RETURN AN EMPTY LIST.** You MUST return a ranked list of municipalities found in the 'DB' source.
    2.  **PARTIAL DATA IS OK.** If 'Vodafone Data' or 'Strategy Data' is missing, rank based on available 'External Data' (population, density) or 'Search' context.
    3.  **Use Foundation Data.** The DB source provides a list of municipalities. Use ALL of them. Do not filter them out just because other columns are NULL.
    4.  **Ranking Fallback.** If no specific metrics exist to differentiate, rank by Population or Density, or simply list them.
    
    Use the following information sources:
    {consolidated_info}
    
    Verify that the 'ranking' is strictly an integer between 0 and 100.
    """
    
    try:
        response = model.generate_content(prompt)
        # Attempt to parse the first valid JSON object from the response text
        raw_text = response.text
        # Basic cleanup for common markdown and non-JSON parts
        if raw_text.strip().startswith("```json"):
            raw_text = raw_text.strip().replace("```json", "", 1)
            raw_text = raw_text.rsplit("```", 1)[0]
        elif raw_text.strip().startswith("```"): # Handle generic code block
             raw_text = raw_text.strip().replace("```", "", 1)
             raw_text = raw_text.rsplit("```", 1)[0]

        return json.loads(raw_text.strip())
    except json.JSONDecodeError as e:
        print(f"JSON Decode Error: {e}")
        print(f"Raw LLM output: {raw_text}")
        return {
            "error": "Failed to generate valid JSON", 
            "ranking": 0, 
            "raw_output": raw_text
        }
    except Exception as e:
        print(f"Error during LLM call: {e}")
        return {"error": str(e), "ranking": 0}

def setup_before_agent_call(callback_context: CallbackContext):
    """Setup the agent."""

    # setting up database settings in session.state
    if "database_settings" not in callback_context.state:
        db_settings = dict()
        db_settings["use_database"] = "BigQuery"
        callback_context.state["all_db_settings"] = db_settings

    # setting up schema in instruction
    if callback_context.state["all_db_settings"]["use_database"] == "BigQuery":
        callback_context.state["database_settings"] = get_bq_database_settings()
        schema = callback_context.state["database_settings"]["bq_ddl_schema"]

        callback_context._invocation_context.agent.instruction = (
            return_instructions_root()
            + f"""

    --------- The BigQuery schema of the relevant data with a few sample rows. ---------
    {schema}

    """
        )

# ROOT AGENT DEFINITION
root_agent = Agent(
    name="ngni_agent",
    model="gemini-2.5-flash",
    instruction=return_instructions_root(),
    description="Assists network engineer based on network data and places insights data. Also can provide analysis of strategy reports of Vodafone",
    tools=[AgentTool(rag_agent), AgentTool(db_agent), AgentTool(search_agent)], 
    before_agent_callback=setup_before_agent_call,
    generate_content_config=types.GenerateContentConfig(temperature=0.0,top_p=0.1)
)