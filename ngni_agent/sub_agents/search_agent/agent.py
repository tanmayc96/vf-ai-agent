import os 
from google.adk.agents import Agent
from google.genai import types
from .prompts import return_instructions_search
from google.adk.tools import google_search

os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"

search_agent = Agent(
    name="search_agent",
    model="gemini-2.5-flash",
    instruction=return_instructions_search(),
    description="Retrieves insights from Google Search. Retrieves all the possible information to help with the analysis.",
    tools=[google_search],
    generate_content_config=types.GenerateContentConfig(temperature=0.01),
)