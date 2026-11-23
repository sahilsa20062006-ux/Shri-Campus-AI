"""
Shri Campus AI - FastAPI Application
Main entry point for the backend server.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

from backend.config import KNOWLEDGE_BASE_PATH, CORS_ORIGINS, HOST, PORT, LOG_LEVEL, BASE_DIR
from backend.knowledge import KnowledgeBase
from backend.ollama_service import OllamaService
from backend.chat import ChatService
from backend.models import ChatRequest, ChatResponse, HealthResponse, KnowledgeBaseStatus

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("shri_campus_ai")

# Global service instances
knowledge_base = KnowledgeBase(KNOWLEDGE_BASE_PATH)
ollama_service = OllamaService()
chat_service: ChatService = None


def ensure_initialized():
    """Ensure knowledge base and chat service are initialized."""
    global chat_service
    if not knowledge_base.is_loaded:
        if not knowledge_base.load():
            logger.error("Failed to load knowledge base! Check the JSON file path.")
    if chat_service is None:
        chat_service = ChatService(knowledge_base, ollama_service)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown."""
    # Startup
    logger.info("Starting Shri Campus AI...")
    ensure_initialized()
    kb_status = knowledge_base.get_status()
    logger.info(f"Knowledge base loaded: {kb_status.get('search_index_size', 0)} searchable entries")

    # Check Ollama health
    health = await ollama_service.check_health()
    logger.info(f"Ollama status: {health.get('status', 'unknown')}")
    if not health.get("ollama_running", False):
        logger.warning("Ollama is not running. AI responses will not be available.")

    yield

    # Shutdown
    logger.info("Shutting down Shri Campus AI...")
    await ollama_service.close()
    logger.info("Shutting down Shri Campus AI...")
    await ollama_service.close()


# Create FastAPI app
app = FastAPI(
    title="Shri Campus AI",
    description="Intelligent college assistant for SRIST, Jabalpur",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- API Routes ---

@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Check the health of all services."""
    ensure_initialized()
    ollama_health = await ollama_service.check_health()
    return HealthResponse(
        status="healthy" if knowledge_base.is_loaded else "degraded",
        knowledge_base=knowledge_base.is_loaded,
        ollama=ollama_health
    )


@app.get("/api/ollama/health")
async def ollama_health():
    """Check Ollama service health."""
    return await ollama_service.check_health()


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Process a chat message."""
    ensure_initialized()
    if chat_service is None:
        raise HTTPException(status_code=503, detail="Chat service not initialized")

    if not knowledge_base.is_loaded:
        raise HTTPException(status_code=503, detail="Knowledge base not loaded")

    try:
        result = await chat_service.process_message(
            message=request.message,
            session_id=request.session_id,
            starting_location=request.starting_location
        )
        return ChatResponse(**result)
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail="An error occurred processing your message. Please try again.")


@app.get("/api/knowledge/status", response_model=KnowledgeBaseStatus)
async def knowledge_status():
    """Get knowledge base status."""
    ensure_initialized()
    status = knowledge_base.get_status()
    return KnowledgeBaseStatus(**status)


@app.get("/api/knowledge/search")
async def search_knowledge(q: str, limit: int = 5):
    """Search the knowledge base directly."""
    ensure_initialized()
    if not knowledge_base.is_loaded:
        raise HTTPException(status_code=503, detail="Knowledge base not loaded")

    if not q or len(q.strip()) < 2:
        raise HTTPException(status_code=400, detail="Query too short")

    results = knowledge_base.search(q.strip(), top_k=min(limit, 10))
    return {
        "query": q,
        "results": [{"type": r["type"], "content": r["content"]} for r in results]
    }


# --- Serve Frontend ---

FRONTEND_DIR = BASE_DIR / "frontend"

# Mount static assets if frontend/assets exists
assets_dir = FRONTEND_DIR / "assets"
if assets_dir.exists():
    app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

# Serve logo
logo_path = FRONTEND_DIR / "logo.png"


@app.get("/logo.png")
async def serve_logo():
    if logo_path.exists():
        return FileResponse(str(logo_path), media_type="image/png")
    raise HTTPException(status_code=404, detail="Logo not found")


# Serve frontend index.html as fallback for all non-API routes
@app.get("/{full_path:path}")
async def serve_frontend(full_path: str):
    """Serve the frontend SPA."""
    # Try to serve exact file first
    file_path = FRONTEND_DIR / full_path
    if full_path and file_path.exists() and file_path.is_file():
        return FileResponse(str(file_path))

    # Fallback to index.html for SPA routing
    index_path = FRONTEND_DIR / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))

    raise HTTPException(status_code=404, detail="Frontend not found. Please build the frontend first.")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host=HOST, port=PORT, log_level=LOG_LEVEL, reload=True)
