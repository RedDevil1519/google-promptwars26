import os
import logging
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, constr

from app_build.services.vertex_llm import generate_response
from app_build.services.bq_analytics import log_event
from app_build.services.db_client import save_chat_history

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Assistant API", description="Smart assistant powered by Google Cloud")

# Mount static files for the frontend
app.mount("/static", StaticFiles(directory="app_build/static"), name="static")

class ChatRequest(BaseModel):
    # Security Guardrail: strict length limits to prevent DoS via massive context
    message: constr(min_length=1, max_length=500)

class ChatResponse(BaseModel):
    reply: str

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    user_message = request.message.strip()
    
    # Security Guardrail: Explicit validation
    if not user_message:
        raise HTTPException(status_code=400, detail="Empty message is not allowed.")
        
    try:
        # Interact with Google Cloud Vertex AI
        bot_reply = await generate_response(user_message)
        
        # In a complete implementation, we sink this to Cloud SQL and BigQuery
        # await save_chat_history(user_message, bot_reply)
        # await log_event("chat_interaction", {"message_length": len(user_message)})
        
        return ChatResponse(reply=bot_reply)
        
    except Exception as e:
        logger.error(f"Error processing chat: {e}")
        # Security Guardrail: Never leak internal error details to the client
        raise HTTPException(status_code=500, detail="Internal server error while processing the request.")

@app.get("/")
async def root():
    return RedirectResponse(url="/static/index.html")
