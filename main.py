from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from config.ollama_config import (
    DEFAULT_OLLAMA_BASE_URL,
    DEFAULT_OLLAMA_MODEL,
    get_ollama_settings,
)
from agents.subagent import invoke_supervisor

app = FastAPI(title="HelloSubAgents")


class AssistantRequest(BaseModel):
    message: str = Field(..., min_length=1)


class AssistantResponse(BaseModel):
    response: str


@app.get("/")
async def root():
    model_name, base_url = get_ollama_settings()
    return {
        "message": "HelloSubAgents is configured to use Ollama",
        "ollama_model": model_name,
        "ollama_base_url": base_url,
    }


@app.get("/health")
async def health():
    model_name, base_url = get_ollama_settings()
    return {
        "status": "ok",
        "provider": "ollama",
        "ollama_model": model_name or DEFAULT_OLLAMA_MODEL,
        "ollama_base_url": base_url or DEFAULT_OLLAMA_BASE_URL,
    }


@app.post("/assistant", response_model=AssistantResponse)
def assistant(request: AssistantRequest):
    try:
        return AssistantResponse(response=invoke_supervisor(request.message))
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
