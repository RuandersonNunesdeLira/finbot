"""
FastAPI main application.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
import sys

from backend.config import get_settings
from backend.models.schemas import (
    ChatRequest, ChatResponse, ToolCall,
    FeedbackRequest, FeedbackEntry,
    PromptStatus, PromptVersion,
    WAHAStatus,
)
from backend.services.ai_service import get_ai_service
from backend.services.feedback_service import get_feedback_service
from backend.services.waha_service import get_waha_service
from backend.services.vector_service import get_vector_service


logger.remove()
logger.add(sys.stderr, level="INFO", format="<green>{time:HH:mm:ss}</green> | <level>{level:<7}</level> | <cyan>{name}</cyan> - {message}")
logger.add("logs/backend.log", rotation="5 MB", retention="7 days", level="DEBUG")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle: startup and shutdown."""
    logger.info("Starting FinBot backend")

    # Initialize services eagerly
    get_vector_service()
    get_feedback_service()
    get_ai_service()

    # Try to start WAHA session
    waha = get_waha_service()
    await waha.create_and_start_session()

    logger.info("All services initialized")
    yield
    logger.info("Shutting down FinBot backend")


app = FastAPI(
    title="FinBot API",
    description="AI Financial Assistant Backend with dynamic prompt feedback",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -- Chat --

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Send a message to the AI agent and get a response."""
    try:
        ai = get_ai_service()
        result = await ai.chat(request.message, request.session_id)
        return ChatResponse(
            response=result["response"],
            tools_used=[ToolCall(**t) for t in result["tools_used"]],
            session_id=result["session_id"],
        )
    except Exception as e:
        logger.error(f"Chat endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# -- Feedback --

async def _bg_optimize_prompt():
    """Background task to analyze feedback and update the prompt."""
    try:
        ai = get_ai_service()
        await ai.analyze_and_update_prompt()
        logger.info("Background prompt optimization finished.")
    except Exception as e:
        logger.error(f"Background optimization error: {e}")


@app.post("/api/feedback", response_model=FeedbackEntry)
async def submit_feedback(request: FeedbackRequest, background_tasks: BackgroundTasks):
    """Submit feedback on the agent's response."""
    try:
        svc = get_feedback_service()
        entry = svc.add_feedback(
            rating=request.rating,
            comment=request.comment,
            suggestion=request.suggestion,
            message_id=request.message_id,
        )
        
        background_tasks.add_task(_bg_optimize_prompt)
        
        return entry
    except Exception as e:
        logger.error(f"Feedback endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/feedbacks", response_model=list[FeedbackEntry])
async def get_feedbacks():
    """Get all recorded feedbacks."""
    svc = get_feedback_service()
    return svc.get_feedbacks()


@app.post("/api/feedback/process")
async def process_feedback():
    """Trigger AI-powered prompt optimization based on collected feedback."""
    try:
        ai = get_ai_service()
        result = await ai.analyze_and_update_prompt()
        if result:
            return {"status": "updated", **result}
        return {"status": "no_update_needed"}
    except Exception as e:
        logger.error(f"Feedback process error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# -- Prompt --

@app.get("/api/prompt", response_model=PromptStatus)
async def get_prompt_status():
    """Get the current prompt and its version history."""
    svc = get_feedback_service()
    return PromptStatus(
        current_prompt=svc.get_current_prompt(),
        current_version=svc.get_current_version(),
        history=svc.get_prompt_history(),
    )


@app.put("/api/prompt")
async def update_prompt_manually(new_prompt: str, reason: str = "Manual update"):
    """Manually update the system prompt."""
    svc = get_feedback_service()
    version = svc.update_prompt(new_prompt, reason)
    return {"status": "updated", "version": version.version}


# -- WAHA --

@app.get("/api/waha/status")
async def waha_status():
    """Get WAHA WhatsApp connection status."""
    waha = get_waha_service()
    return await waha.get_status()


@app.get("/api/waha/qr")
async def waha_qr():
    """Get QR code for WhatsApp authentication."""
    waha = get_waha_service()
    return await waha.get_qr_code()

import time
from cachetools import TTLCache

processed_message_ids = TTLCache(maxsize=1000, ttl=3600)

@app.post("/api/waha/webhook")
async def waha_webhook(payload: dict):
    """
    Webhook endpoint for WAHA to send incoming WhatsApp messages.
    Processes the message through the AI agent and sends the response back.
    """
    try:
        event = payload.get("event")
        if event != "message":
            return {"status": "ignored", "event": event}

        message_data = payload.get("payload", {})
        body = message_data.get("body", "")
        chat_id = message_data.get("from", "")
        is_from_me = message_data.get("fromMe", False)
        msg_id = message_data.get("id", "")
        
        if not body or not chat_id or not msg_id:
            return {"status": "skipped"}
            
        if msg_id in processed_message_ids:
            logger.info(f"Skipping duplicate message {msg_id}")
            return {"status": "duplicate"}
            
        processed_message_ids[msg_id] = True

        if is_from_me:
            return {"status": "skipped", "reason": "bot_outgoing_message"}

        logger.info(f"WhatsApp message from {chat_id}: {body[:50]}...")


        ai = get_ai_service()
        result = await ai.chat(body, session_id=f"whatsapp_{chat_id}")


        waha = get_waha_service()
        await waha.send_message(chat_id, result["response"])

        return {"status": "processed"}

    except Exception as e:
        logger.error(f"WAHA webhook error: {e}")
        return {"status": "error", "detail": str(e)}


# -- Health --

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "service": "finbot-backend"}
