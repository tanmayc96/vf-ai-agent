import os 
import uvicorn 
from fastapi import FastAPI
from pydantic import BaseModel
from google.genai import types
from ngni_agent.agent import root_agent
from google.adk.cli.fast_api import get_fast_api_app
from google.adk.runners import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService

AGENT_DIR = os.path.abspath(os.path.dirname(__file__))

app: FastAPI = get_fast_api_app(
    agents_dir=AGENT_DIR, 
    web=True,
)

app.title = "root_agent"
app.description = "API for interacting with NGNI agent"

# Initialize services for custom endpoint
session_service = InMemorySessionService()
runner = Runner(
    agent=root_agent,
    session_service=session_service,
    app_name="ngni_agent"
)

class QueryRequest(BaseModel):
    query: str

@app.post("/query")
async def query_agent(request: QueryRequest):
    """
    Process a user query using the root_agent via ADK Runner.
    """
    # Use a fixed session for simplicity, or generate one per request if needed.
    # For a simple query endpoint, a new session or fixed one is fine.
    # We will use a fixed one to allow context retention if desired, 
    # or uuid for new session. Let's use a static one for now as per simple req.
    session_id = "default_session"
    
    response_text = ""
    async for event in runner.run_async(
        user_id="user",
        session_id=session_id,
        new_message=types.Content(role="user", parts=[types.Part(text=request.query)])
    ):
        # Accumulate text content from events
        if event.content:
            for part in event.content.parts:
                if part.text:
                    response_text += part.text
                    
    return {"response": response_text}

if __name__ == "__main__":
    print("main",AGENT_DIR)
    uvicorn.run(app, host="0.0.0.0", port=8000)