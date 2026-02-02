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
        response = None
        if hasattr(root_agent, "query"):
            response = root_agent.query(request.query)
        elif hasattr(root_agent, "invoke"):
            response = root_agent.invoke(request.query)
        elif callable(root_agent):
            response = root_agent(request.query)
        else:
            # Fallback: try to find a method that looks like a query method
            attrs = dir(root_agent)
            print(f"DEBUG: Agent attributes: {attrs}")
            raise HTTPException(status_code=500, detail=f"Agent interface unknown. Available attributes: {attrs}")
        
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
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    print("main",AGENT_DIR)
    uvicorn.run(app, host="0.0.0.0", port=8080)