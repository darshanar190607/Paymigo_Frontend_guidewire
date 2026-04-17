from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import List, Optional
from paymigo_assistant.backend.core.agent import MigoAgent
import uvicorn
import os
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"

load_dotenv(BASE_DIR / ".env")
ASSISTANT_PORT = int(os.getenv("ASSISTANT_PORT", 8001))

app = FastAPI(title="Migo Assistant API - v2")

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

# Initialize Agent
agent = MigoAgent()

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[ChatMessage]] = []

@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    return (FRONTEND_DIR / "index.html").read_text(encoding="utf-8")

@app.get("/health")
async def health_check():
    return {
        "status": "healthy", 
        "service": "migo-assistant",
        "port": ASSISTANT_PORT,
        "mode": "production_upgrade"
    }

@app.post("/chat")
async def chat(request: ChatRequest):
    try:
        # Convert Pydantic models to dict for the agent
        history_dicts = [{"role": m.role, "content": m.content} for m in request.history]
        
        # The agent now returns {answer: str, actions: list, system_meta: dict}
        response = agent.generate_response(request.message, history=history_dicts)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    print(f"Starting Migo Assistant on port {ASSISTANT_PORT}...")
    uvicorn.run(app, host="0.0.0.0", port=ASSISTANT_PORT)
