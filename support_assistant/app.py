from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from graph import workflow, SupportResponseSchema

app = FastAPI(title="Zepto GenAI Support Assistant API")

class AskRequest(BaseModel):
    query: str

@app.post("/ask", response_model=SupportResponseSchema)
def ask_question(request: AskRequest):
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query string cannot be empty.")
        
    initial_state = {
        "query": request.query,
        "intent": None,
        "retrieved_chunks": [],
        "final_output": None
    }
    
    res = workflow.invoke(initial_state)
    return res["final_output"]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)