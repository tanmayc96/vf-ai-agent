import os

from google.adk.agents import Agent, LlmAgent, SequentialAgent
from vertexai.preview import rag

from dotenv import load_dotenv
from google.genai import types
from google.adk.tools.agent_tool import AgentTool
from google.adk.agents.callback_context import CallbackContext
from datetime import date
from google.adk.tools import load_artifacts

from .sub_agents.rag_agent.agent import rag_agent
from .sub_agents.bigquery.agent import db_agent
from .sub_agents.search_agent.agent import search_agent
from .prompts import return_instructions_root

from .sub_agents.bigquery.tools import (
    get_database_settings as get_bq_database_settings,
)

os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"
os.environ["GOOGLE_CLOUD_PROJECT"] = "vf-grp-aib-dev-ngi-sbx-alpha"
os.environ["GOOGLE_CLOUD_LOCATION"] = "europe-west1"

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

# coordinator = LlmAgent(
#     name="ngni_agent",
#     model="gemini-2.5-flash",
#     instruction= return_instructions_root(),
#     description="Assists network engineer based on network data and places insights data. Also can provide analysis of financial and quarterly reports of Vodafone",
#     sub_agents=[rag_agent,db_agent,search_agent],
#     before_agent_callback=setup_before_agent_call,
#     generate_content_config=types.GenerateContentConfig(temperature=0.0,top_p=0.1),
# )

# root_agent = coordinator