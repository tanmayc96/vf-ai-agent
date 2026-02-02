import os 
import uvicorn 
from fastapi import FastAPI
from ngni_agent.agent import root_agent
from google.adk.cli.fast_api import get_fast_api_app

AGENT_DIR = os.path.abspath(os.path.dirname(__file__))

app: FastAPI = get_fast_api_app(
    agents_dir=AGENT_DIR, 
    web=True,
)

app.title = "root_agent"
app.description = "API for interacting with NGNI agent"

from pydantic import BaseModel
from fastapi import HTTPException

class QueryRequest(BaseModel):
    query: str

@app.post("/query")
async def query_agent(request: QueryRequest):
    """
    Endpoint to query the agent.
    """
    try:
        if hasattr(root_agent, "query"):
            response = root_agent.query(request.query)
        elif hasattr(root_agent, "invoke"):
            response = root_agent.invoke(request.query)
        else:
            # Fallback: try to find a method that looks like a query method
            raise HTTPException(status_code=500, detail=f"Agent interface unknown. Available attributes: {dir(root_agent)}")
        
        # normalizing response
        if hasattr(response, "text"):
            return {"response": response.text}
        elif isinstance(response, str):
            return {"response": response}
        elif isinstance(response, dict):
            return response
        else:
            return {"response": str(response)}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    print("main",AGENT_DIR)
    uvicorn.run(app, host="0.0.0.0", port=8080)