import os
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from dotenv import load_dotenv

load_dotenv()


from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, constr

from app_build.services.vertex_llm import generate_response
from app_build.services.bq_analytics import log_event
from app_build.services.db_client import save_chat_history, init_db

# Configure production-grade logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Handles startup and shutdown events for the FastAPI application.
    Initializes database connections cleanly.
    """
    logger.info("Initializing application resources...")
    # Trigger DB initialization synchronously before serving traffic (or async if driver supports it)
    init_db()
    yield
    logger.info("Tearing down application resources...")

app = FastAPI(
    title="AI Assistant API", 
    description="Smart fullstack assistant powered by Google Cloud Vertex AI",
    version="1.0.0",
    lifespan=lifespan
)

# Security Enhancements: Add CORS Middleware (allowing frontend domain in prod)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In strict prod, replace with exact domains
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Security Enhancements: Add custom Security Headers Middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next) -> Response:
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response

# Mount static files for the frontend
app.mount("/static", StaticFiles(directory="app_build/static"), name="static")

class ChatRequest(BaseModel):
    """Pydantic Model for incoming chat requests."""
    # Security Guardrail: strict length limits to prevent DoS via massive context
    message: constr(min_length=1, max_length=500) # type: ignore

class ChatResponse(BaseModel):
    """Pydantic Model for outgoing chat responses."""
    reply: str

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest) -> ChatResponse:
    """
    Handles user chat interactions, queries the LLM, and persists telemetry.
    
    Args:
        request (ChatRequest): The validated incoming message payload.
        
    Returns:
        ChatResponse: The validated AI text response.
        
    Raises:
        HTTPException: If an internal failure or service outage occurs.
    """
    user_message = request.message.strip()
    
    # Security Guardrail: Explicit validation against pure whitespace
    if not user_message:
        raise HTTPException(status_code=400, detail="Empty message is not allowed.")
        
    try:
        # Interact with Google Cloud Vertex AI
        bot_reply = await generate_response(user_message)
        
        # Parallel database and analytics sink (for higher performance)
        # We wait for both using a simple approach or await sequentially. 
        # Since we use asyncio.to_thread under the hood, this will not block.
        await save_chat_history(user_message, bot_reply)
        await log_event("chat_interaction", {"message_length": len(user_message)})
        
        return ChatResponse(reply=bot_reply)
        
    except Exception as e:
        logger.error(f"Error processing chat endpoint: {e}", exc_info=True)
        # Security Guardrail: Never leak internal error details to the client
        raise HTTPException(status_code=500, detail="Internal server error while processing the request.")

@app.get("/")
async def root() -> RedirectResponse:
    """Redirects the root path to the static frontend application."""
    return RedirectResponse(url="/static/index.html")
