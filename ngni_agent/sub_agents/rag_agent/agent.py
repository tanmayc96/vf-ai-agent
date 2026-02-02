import os 
from google.adk.agents import Agent
from google.genai import types
from .prompts import return_instructions_rag
from .tools import get_rag_tool 

os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"

rag_agent = Agent(
    name="rag_agent",
    model="gemini-2.5-flash",
    instruction=return_instructions_rag(),
    description="Retrieves insights from strategy reports.DO NOT use for structured data, Bigquery or network data assistance.",
    tools=[get_rag_tool()],
    generate_content_config=types.GenerateContentConfig(temperature=0.01),
)