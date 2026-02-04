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
            "bq_dataset_id": "h3_c