"""
Shri Campus AI - Live Qwen Refinement Test
Tests that Qwen actually generates intelligent, natural, polite, and refined answers
across English, Hindi, follow-up context, navigation, and unverified data.
"""

import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.knowledge import KnowledgeBase
from backend.ollama_service import OllamaService
from backend.chat import ChatService
from backend.config import KNOWLEDGE_BASE_PATH


async def run_live_test():
    print("=" * 65)
    print("TESTING LIVE QWEN REFINEMENT PIPELINE")
    print("=" * 65)

    kb = KnowledgeBase(KNOWLEDGE_BASE_PATH)
    kb.load()
    ollama = OllamaService()
    chat = ChatService(kb, ollama)

    session = "test-live-session"

    queries = [
        ("Query 1 (Faculty - English)", "Who is the AIML HOD?", None),
        ("Query 2 (Follow-up Context)", "Where is his office?", None),
        ("Query 3 (Hindi / Hinglish)", "Library kaha hai?", None),
        ("Query 4 (Campus Directions)", "How can I reach Room 103 from the main entrance gate?", "Main Entrance Gate"),
        ("Query 5 (Unverified Information)", "What is the principal's name?", None),
    ]

    for label, q, loc in queries:
        print(f"\n--- {label} ---")
        print(f"Student: \"{q}\"" + (f" (From: {loc})" if loc else ""))
        res = await chat.process_message(q, session_id=session, starting_location=loc)
        print(f"AI ({res.get('source')}):\n{res.get('response')}")

    await ollama.close()
    print("\n" + "=" * 65)
    print("COMPLETED LIVE QWEN REFINEMENT TEST")
    print("=" * 65)


if __name__ == "__main__":
    asyncio.run(run_live_test())
