"""
Shri Campus AI - Chat Orchestration Service
Manages conversation context, retrieval, and response generation.
"""

import logging
import uuid
from typing import Optional

from backend.knowledge import KnowledgeBase
from backend.ollama_service import OllamaService
from backend.config import MAX_CONVERSATION_HISTORY

logger = logging.getLogger("shri_campus_ai.chat")


class ConversationManager:
    """Manages conversation sessions with context memory."""

    def __init__(self):
        self._sessions: dict[str, list[dict]] = {}

    def get_or_create_session(self, session_id: str) -> list[dict]:
        """Get existing session history or create a new one."""
        if session_id not in self._sessions:
            self._sessions[session_id] = []
        return self._sessions[session_id]

    def add_message(self, session_id: str, role: str, content: str):
        """Add a message to conversation history."""
        history = self.get_or_create_session(session_id)
        history.append({"role": role, "content": content})
        # Trim to max history
        if len(history) > MAX_CONVERSATION_HISTORY * 2:
            self._sessions[session_id] = history[-(MAX_CONVERSATION_HISTORY * 2):]

    def get_history(self, session_id: str) -> list[dict]:
        """Get conversation history for a session."""
        return self._sessions.get(session_id, [])

    def clear_session(self, session_id: str):
        """Clear a conversation session."""
        self._sessions.pop(session_id, None)


class ChatService:
    """Orchestrates the full chat pipeline: retrieve -> augment -> generate."""

    def __init__(self, knowledge_base: KnowledgeBase, ollama_service: OllamaService):
        self.kb = knowledge_base
        self.ollama = ollama_service
        self.conversations = ConversationManager()

    async def process_message(self, message: str, session_id: Optional[str] = None,
                               starting_location: Optional[str] = None) -> dict:
        """Process a user message through the full RAG pipeline."""
        # Create session if needed
        if not session_id:
            session_id = str(uuid.uuid4())

        # Get conversation history
        history = self.conversations.get_history(session_id)

        # Build enriched query using context
        enriched_query = self._enrich_query(message, history)

        # Retrieve relevant knowledge
        retrieved_entries = self.kb.search(enriched_query, top_k=5)

        # Also search the original message in case enrichment changed meaning
        if enriched_query != message:
            original_results = self.kb.search(message, top_k=3)
            # Merge unique results
            seen_contents = {e["content"] for e in retrieved_entries}
            for entry in original_results:
                if entry["content"] not in seen_contents:
                    retrieved_entries.append(entry)
                    seen_contents.add(entry["content"])

        # Format retrieved context
        context_parts = []
        for entry in retrieved_entries[:7]:  # Limit to 7 entries max
            context_parts.append(f"[{entry['type'].upper()}] {entry['content']}")

        retrieved_context = "\n".join(context_parts)

        # Add starting location context if provided
        if starting_location:
            retrieved_context = f"[USER LOCATION] Student is currently at: {starting_location}\n" + retrieved_context

        # Store user message in history
        self.conversations.add_message(session_id, "user", message)

        # Primary flow: Always use Qwen LLM to refine and generate the answer
        response = await self.ollama.generate(
            user_message=message,
            retrieved_context=retrieved_context,
            conversation_history=history
        )

        source = "qwen_ai"

        # Graceful fallback if Ollama is temporarily unavailable or timed out
        if not response:
            logger.warning("Ollama did not return a response. Using knowledge base fallback.")
            direct_answer = self._try_direct_answer(message, retrieved_entries)
            if direct_answer:
                response = direct_answer
                source = "knowledge_base_fallback"
            elif retrieved_entries:
                top_entry = retrieved_entries[0]
                response = top_entry["content"]
                source = "knowledge_base_fallback"
            else:
                response = "I don't have verified information about this in my college records. Please check with the administration office."
                source = "unverified_fallback"

        # Store assistant response
        self.conversations.add_message(session_id, "assistant", response)

        return {
            "response": response,
            "session_id": session_id,
            "source": source
        }

    def _enrich_query(self, message: str, history: list[dict]) -> str:
        """Enrich the query with context from conversation history for follow-up questions."""
        if not history:
            return message

        msg_lower = message.lower().strip("?.! ")

        # Known campus keywords that indicate an independent topic
        independent_entities = [
            "library", "principal", "accounts", "exam cell", "record room", "strong room",
            "tpo", "pro", "seminar hall", "girls room", "staff room", "smart classroom",
            "physics", "chemistry", "electrical", "bce", "language", "cse", "aiml", "iot",
            "mba", "b.tech", "btech", "first-year", "second-year", "third-year", "fourth-year",
            "1st year", "2nd year", "3rd year", "4th year", "sudeep", "ruchi", "khan",
            "sameer", "vaidya", "ankit", "kachhi", "vikas", "dhanwani", "incharge"
        ]

        # If user explicitly asks about a known entity, do NOT overwrite with previous context
        has_independent_entity = any(ent in msg_lower for ent in independent_entities)
        if has_independent_entity:
            return message

        # Detect pronoun references
        pronouns = ["his", "her", "their", "its", "that", "this", "the same", "he", "she", "him", "uska", "unka", "unki", "uski", "woh", "wo"]
        words = msg_lower.split()
        has_pronoun = any(p in words for p in pronouns)

        # Detect short follow-up patterns (e.g. "Which floor?", "Office?", "Kahan hai?")
        follow_up_patterns = ["office", "room", "floor", "where", "which", "kahan", "kaha", "kis", "konsa", "kab", "kisko", "location"]
        is_short_followup = len(words) <= 4 and any(p in msg_lower for p in follow_up_patterns)

        if (has_pronoun or is_short_followup) and history:
            # Find the last entity mentioned in history
            for msg in reversed(history):
                content = msg.get("content", "").lower()
                for fac in self.kb.data.get("faculty", []):
                    if fac["name"].lower() in content or fac.get("designation", "").lower() in content:
                        return f"{fac['name']} {fac.get('designation', '')} {message}"
                for office in self.kb.data.get("administrative_offices", []):
                    if office["name"].lower() in content:
                        return f"{office['name']} {message}"
                for lab in self.kb.data.get("labs", []):
                    if lab["name"].lower() in content:
                        return f"{lab['name']} {message}"
                for fac_item in self.kb.data.get("facilities", []):
                    if fac_item["name"].lower() in content:
                        return f"{fac_item['name']} {message}"

        return message

    def _try_direct_answer(self, message: str, retrieved: list[dict]) -> Optional[str]:
        """Try to find a direct FAQ answer for the question."""
        for entry in retrieved:
            if entry["type"] == "faq":
                return entry["data"].get("answer")
        return None

    def _needs_llm(self, message: str) -> bool:
        """Determine if the message is complex enough to need LLM processing."""
        msg_lower = message.lower()
        # Simple factual questions can use direct FAQ answers
        # Complex questions need the LLM
        complex_indicators = [
            "how", "explain", "tell me about", "describe", "help",
            "kaise", "batao", "samjhao",
            "reach", "navigate", "direction", "find",
            "difference", "compare"
        ]
        return any(ind in msg_lower for ind in complex_indicators)
