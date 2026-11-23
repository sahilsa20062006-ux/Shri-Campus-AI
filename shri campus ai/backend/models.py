"""
Shri Campus AI - Pydantic Models
Request/response schemas for the API.
"""

from pydantic import BaseModel, Field
from typing import Optional


class ChatRequest(BaseModel):
    """Chat request from frontend."""
    message: str = Field(..., min_length=1, max_length=1000, description="User's question")
    session_id: Optional[str] = Field(None, description="Conversation session ID")
    starting_location: Optional[str] = Field(None, max_length=200, description="User's starting location on campus")
    language: Optional[str] = Field(None, description="Preferred language (auto-detected if not set)")


class ChatResponse(BaseModel):
    """Chat response to frontend."""
    response: str
    session_id: str
    source: str = "ai_assisted"


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    service: str = "Shri Campus AI"
    knowledge_base: bool
    ollama: dict


class KnowledgeBaseStatus(BaseModel):
    """Knowledge base status response."""
    loaded: bool
    path: Optional[str] = None
    sections: Optional[list[str]] = None
    faculty_count: Optional[int] = None
    rooms_count: Optional[int] = None
    classrooms_count: Optional[int] = None
    labs_count: Optional[int] = None
    faq_count: Optional[int] = None
    search_index_size: Optional[int] = None
    error: Optional[str] = None
