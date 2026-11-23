"""
Shri Campus AI - Ollama LLM Service
Handles communication with the local Ollama Qwen model.
"""

import httpx
import json
import logging
from typing import Optional

from backend.config import OLLAMA_BASE_URL, OLLAMA_MODEL, REQUEST_TIMEOUT

logger = logging.getLogger("shri_campus_ai.ollama")

SYSTEM_PROMPT = """You are Shri Campus AI, the official intelligent AI campus assistant for Shri Ram Institute of Science & Technology (SRIST), Jabalpur, Madhya Pradesh, India.

YOUR PERSONA & COMMUNICATION STYLE:
- You are an articulate, polite, highly knowledgeable, and welcoming academic assistant.
- NEVER give blunt, robotic one-word answers or raw database lookups. Instead, provide complete, natural, and helpful sentences that explain the answer clearly and warmly.
- Always include relevant context such as both Room Number AND Floor whenever discussing locations, faculty offices, classrooms, or labs.

LANGUAGE MATCHING (CRITICAL):
- Strictly match the language used by the student:
  * When the student's question is in English -> You MUST respond in English.
  * When the student's question is in Hindi (Devanagari) -> Respond in polite Hindi.
  * When the student's question is in Hinglish (Roman Hindi) -> Respond in natural Hinglish.
  * NEVER reply in Hindi if the question was asked in English.

STRICT ACCURACY & CAMPUS KNOWLEDGE RULES:
1. The provided VERIFIED CAMPUS RECORDS are your single source of truth for all campus facts.
2. NEVER invent, guess, or hallucinate room numbers, names, departments, facilities, or walking routes.
3. If a detail is missing or unverified in the records (such as Fourth-Year classroom allocations or a specific MBA room number):
   - Clearly and politely explain that this specific detail is not recorded in the verified college directory.
   - Guide the student on who to contact or where to visit (e.g., department notice board, HOD office, or administration).
4. Preserve exact faculty names, titles, and room numbers from the records.
5. When a starting location is provided or walking directions are asked:
   - Provide sensible text-based guidance (e.g. guide them to take the stairs or elevator to the target floor).
   - Clarify that detailed corridor turn-by-turn indoor GPS navigation is not recorded.
6. Support follow-up questions smoothly by using the conversation history to understand pronouns and context (e.g. "his office", "which floor", "that room")."""


class OllamaService:
    """Service for interacting with the local Ollama Qwen model."""

    def __init__(self):
        self.base_url = OLLAMA_BASE_URL
        self.model = OLLAMA_MODEL
        self.timeout = REQUEST_TIMEOUT
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=httpx.Timeout(self.timeout))
        return self._client

    async def check_health(self) -> dict:
        """Check if Ollama is running and the model is available."""
        try:
            client = await self._get_client()
            # Check Ollama server
            response = await client.get(f"{self.base_url}/api/tags")
            if response.status_code != 200:
                return {"status": "error", "message": "Ollama server not responding"}

            models_data = response.json()
            available_models = [m.get("name", "") for m in models_data.get("models", [])]

            model_found = any(self.model in m for m in available_models)

            return {
                "status": "healthy" if model_found else "model_not_found",
                "ollama_running": True,
                "model": self.model,
                "model_available": model_found,
                "available_models": available_models
            }
        except httpx.ConnectError:
            return {
                "status": "error",
                "ollama_running": False,
                "message": "Cannot connect to Ollama. Please ensure Ollama is running."
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Unexpected error: {str(e)}"
            }

    async def generate(self, user_message: str, retrieved_context: str,
                       conversation_history: list[dict] = None) -> str:
        """Generate a response using Qwen via Ollama."""
        try:
            client = await self._get_client()

            # Build the messages array
            messages = [{"role": "system", "content": SYSTEM_PROMPT}]

            # Add conversation history (last few turns)
            if conversation_history:
                for msg in conversation_history[-6:]:  # Keep last 6 messages (3 turns)
                    messages.append({
                        "role": msg.get("role", "user"),
                        "content": msg.get("content", "")
                    })

            # Build the user message with retrieved context
            augmented_message = f"""VERIFIED SRIST CAMPUS RECORDS:
{retrieved_context if retrieved_context else "No specific records found in campus directory for this query."}

STUDENT QUERY:
{user_message}

Please provide an intelligent, accurate, and articulate response for the student based strictly on the verified campus records above.
CRITICAL LANGUAGE INSTRUCTION: If the student query is in English, you MUST respond in English. If the student query is in Hindi or Hinglish, respond in Hindi or Hinglish."""

            messages.append({"role": "user", "content": augmented_message})

            # Call Ollama API
            response = await client.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": messages,
                    "stream": False,
                    "think": False,
                    "options": {
                        "temperature": 0.3,
                        "top_p": 0.9,
                        "num_predict": 1000
                    }
                }
            )

            if response.status_code != 200:
                logger.error(f"Ollama API error: {response.status_code} - {response.text}")
                return None

            result = response.json()
            message_obj = result.get("message", {})
            answer = message_obj.get("content", "").strip()

            # Clean up thinking tags if present in content
            if "<think>" in answer:
                import re
                answer = re.sub(r'<think>.*?</think>', '', answer, flags=re.DOTALL).strip()

            # Robust fallback: If content is empty but thinking was generated, extract the drafted conclusion
            if not answer and message_obj.get("thinking"):
                thinking_text = message_obj.get("thinking", "").strip()
                logger.info(f"Qwen content was empty; extracting drafted response from thinking ({len(thinking_text)} chars)")
                # Look for drafted response or final paragraphs
                import re
                draft_match = re.search(r'(?:Output Generation|Construct Final Response|Final Response|Draft Response)[:\s*]+["\']?([^\n"\']{20,})', thinking_text, re.IGNORECASE)
                if draft_match:
                    answer = draft_match.group(1).strip().strip('"\'')
                else:
                    # Take the last meaningful non-empty paragraph of thinking
                    paragraphs = [p.strip() for p in thinking_text.split('\n\n') if p.strip()]
                    if paragraphs:
                        last_p = paragraphs[-1]
                        # Remove markdown bullet prefixes like "* " or "7. "
                        last_p = re.sub(r'^(?:\d+\.|\*|-)\s*', '', last_p)
                        if len(last_p) > 20 and not last_p.lower().startswith('thinking'):
                            answer = last_p

            return answer if answer else None

        except httpx.ConnectError:
            logger.error("Cannot connect to Ollama")
            return None
        except httpx.ReadTimeout:
            logger.error("Ollama request timed out")
            return None
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return None

    async def close(self):
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
