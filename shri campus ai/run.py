"""
Shri Campus AI - Server Runner
Launches the FastAPI backend and serves the frontend.
"""

import uvicorn
from backend.config import HOST, PORT, LOG_LEVEL

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 Starting Shri Campus AI Server")
    print(f"📍 Local URL: http://localhost:{PORT}")
    print(f"📖 API Docs: http://localhost:{PORT}/docs")
    print("=" * 60)
    uvicorn.run("backend.main:app", host=HOST, port=PORT, log_level=LOG_LEVEL, reload=True)
