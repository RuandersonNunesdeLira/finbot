"""
Pydantic schemas for API models.
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime



class ChatRequest(BaseModel):
    """Incoming chat message from the user."""
    message: str = Field(..., min_length=1, max_length=4096)
    session_id: str = Field(default="streamlit")


class ToolCall(BaseModel):
    """Represents a tool that was invoked during the response."""
    tool_name: str
    tool_input: dict
    tool_output: str


class ChatResponse(BaseModel):
    """Response from the AI agent."""
    response: str
    tools_used: list[ToolCall] = []
    session_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)



class FeedbackRequest(BaseModel):
    """User feedback on an agent response."""
    rating: int = Field(..., ge=1, le=5, description="1=terrible, 5=excellent")
    comment: str = Field(default="", max_length=2048)
    suggestion: str = Field(default="", max_length=2048, description="Suggestion for prompt improvement")
    message_id: Optional[str] = None


class FeedbackEntry(BaseModel):
    """Stored feedback entry with metadata."""
    id: str
    rating: int
    comment: str
    suggestion: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    applied: bool = False



class PromptVersion(BaseModel):
    """A version of the system prompt."""
    version: int
    prompt_text: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    reason: str = ""


class PromptStatus(BaseModel):
    """Current prompt status and history."""
    current_prompt: str
    current_version: int
    history: list[PromptVersion] = []



class WAHAStatus(BaseModel):
    """WAHA connection status."""
    connected: bool = False
    qr_code: Optional[str] = None
    session_name: str = "default"
    status: str = "disconnected"
