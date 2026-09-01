from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import verifier
import storage

app = FastAPI(
    title="AI Hallucination Detector Enterprise API",
    description="Backend REST API for Hallucination Verification Engine, Chrome Extension & Analytics Dashboard",
    version="2.5.0"
)

# Enable CORS for Chrome Extension and external callers
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PromptRequest(BaseModel):
    prompt: str
    search_engine: Optional[str] = "hybrid"
    model_name: Optional[str] = "Llama 3.3 (Groq)"

class TextRequest(BaseModel):
    text: str
    search_engine: Optional[str] = "hybrid"
    model_name: Optional[str] = "Llama 3.3 (Groq)"

class CorrectionRequest(BaseModel):
    text: str
    results: list[dict]

class AgentRequest(BaseModel):
    input: str
    type: Optional[str] = "prompt"
    search_engine: Optional[str] = "hybrid"
    model_name: Optional[str] = "Llama 3.3 (Groq)"

@app.get("/api/health")
def health_check():
    return {
        "status": "ok",
        "service": "AI Autonomous Agent & Hallucination Detector Engine",
        "version": "3.0.0",
        "db_connected": True
    }

@app.post("/api/agent-verify")
def run_agent_verification(request: AgentRequest):
    """
    Execute full Autonomous Agent workflow for any prompt or response.
    """
    if not request.input.strip():
        raise HTTPException(status_code=400, detail="Input cannot be empty.")
    try:
        report = verifier.run_autonomous_agent(
            prompt_or_text=request.input, 
            input_type=request.type, 
            search_engine=request.search_engine, 
            model_name=request.model_name
        )
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generate-and-verify")
def generate_and_verify(request: PromptRequest):
    """
    Generate an LLM response for a prompt, audit factual claims, and log audit to SQLite DB.
    """
    if not request.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt cannot be empty.")
    try:
        report = verifier.process_prompt(request.prompt, search_engine=request.search_engine, model_name=request.model_name)
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/verify")
def verify_existing_text(request: TextRequest):
    """
    Audit an existing text string for hallucinations and store audit metrics.
    """
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty.")
    try:
        report = verifier.verify_text(request.text, search_engine=request.search_engine, model_name=request.model_name, source_type="text")
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/correct")
def correct_text(request: CorrectionRequest):
    """
    Generate fact-corrected version of text based on claim results.
    """
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty.")
    try:
        corrected = verifier.correct_hallucinations(request.text, request.results)
        return {"original_text": request.text, "corrected_text": corrected}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/history")
def get_audit_history(limit: int = 50):
    """
    Retrieve audit history log from SQLite database.
    """
    try:
        history = storage.get_history(limit=limit)
        return {"count": len(history), "history": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stats")
def get_analytics_statistics():
    """
    Retrieve aggregate stats and timeline for dashboard reporting.
    """
    try:
        return storage.get_analytics_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/history/{run_id}")
def delete_audit_run(run_id: int):
    """
    Delete a specific audit run from SQLite DB.
    """
    try:
        storage.delete_run(run_id)
        return {"status": "success", "deleted_run_id": run_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)

