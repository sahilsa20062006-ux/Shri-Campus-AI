"""
Shri Campus AI - API and Chat Integration Tests
Tests the FastAPI endpoints and chat functionality.
"""

import sys
import asyncio
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.knowledge import KnowledgeBase
from backend.ollama_service import OllamaService
from backend.chat import ChatService, ConversationManager
from backend.config import KNOWLEDGE_BASE_PATH


async def test_chat_service():
    """Test the chat orchestration service."""
    print("=" * 60)
    print("SHRI CAMPUS AI - CHAT SERVICE TESTS")
    print("=" * 60)

    kb = KnowledgeBase(KNOWLEDGE_BASE_PATH)
    kb.load()

    ollama = OllamaService()
    chat = ChatService(kb, ollama)

    passed = 0
    failed = 0
    total = 0

    def assert_test(name, condition, detail=""):
        nonlocal passed, failed, total
        total += 1
        if condition:
            passed += 1
            print(f"  ✅ PASS: {name}")
        else:
            failed += 1
            print(f"  ❌ FAIL: {name} {detail}")

    # Test conversation manager
    print("\n💬 Test Group: Conversation Manager")
    cm = ConversationManager()

    session = cm.get_or_create_session("test-1")
    assert_test("New session creates empty list", len(session) == 0)

    cm.add_message("test-1", "user", "Hello")
    cm.add_message("test-1", "assistant", "Hi there!")
    history = cm.get_history("test-1")
    assert_test("History has 2 messages after 2 adds", len(history) == 2)
    assert_test("First message is user role", history[0]["role"] == "user")
    assert_test("Second message is assistant role", history[1]["role"] == "assistant")

    cm.clear_session("test-1")
    assert_test("Session cleared", len(cm.get_history("test-1")) == 0)

    # Test query enrichment
    print("\n🔗 Test Group: Query Enrichment (Follow-ups)")

    # Simulate a conversation about AIML HOD
    cm.add_message("test-2", "user", "Who is the AIML HOD?")
    cm.add_message("test-2", "assistant", "The AIML HOD is Sudeep Sharma. His office is in Room 103, First Floor.")

    history_2 = cm.get_history("test-2")
    enriched = chat._enrich_query("Where is his office?", history_2)
    assert_test(
        "Follow-up 'his office' enriched with Sudeep Sharma context",
        "sudeep sharma" in enriched.lower() or "aiml hod" in enriched.lower(),
        f"- Got: {enriched}"
    )

    # Test retrieval pipeline
    print("\n🔎 Test Group: Retrieval Pipeline")

    # Test that search retrieves correct info for chat questions
    chat_questions = [
        ("Who is the AIML HOD?", ["sudeep sharma"]),
        ("Where is the AIML HOD office?", ["room 103", "first floor"]),
        ("Who is the CSE HOD?", ["ruchi kshatri patel"]),
        ("Where is the CSE HOD office?", ["room 113"]),
        ("Where is the library?", ["room 10", "ground floor"]),
        ("Where is the Principal's office?", ["room 01", "ground floor"]),
        ("Who is the principal?", ["sameer vaidya"]),
        ("Who is the third year AIML incharge?", ["ankit kachhi"]),
        ("Where is the First-Year HOD?", ["room 19", "m.s. khan"]),
        ("Where is the MBA department?", ["third floor"]),
        ("Where is Third-Year AIML?", ["room 117"]),
        ("Where is Third-Year CSE-A?", ["room 215", "second floor"]),
        ("Where is the seminar hall?", ["room 218"]),
    ]

    for question, expected_tokens in chat_questions:
        results = kb.search(question, top_k=5)
        all_content = " ".join(r["content"].lower() for r in results)
        all_found = all(token.lower() in all_content for token in expected_tokens)
        assert_test(
            f"Retrieval for '{question}' finds {expected_tokens}",
            all_found,
            f"- Missing from results"
        )

    # Test Ollama health check
    print("\n🏥 Test Group: Ollama Health")
    health = await ollama.check_health()
    ollama_running = health.get("ollama_running", False)
    if ollama_running:
        assert_test("Ollama is running", True)
        assert_test("Model available", health.get("model_available", False),
                     f"- Available models: {health.get('available_models', [])}")
    else:
        print(f"  ⚠️  SKIP: Ollama not running ({health.get('message', 'unknown')})")
        print("       Chat tests with LLM will be skipped.")

    # Test live chat (only if Ollama is running)
    if ollama_running and health.get("model_available", False):
        print("\n🤖 Test Group: Live Chat (Ollama)")

        live_tests = [
            ("Who is the AIML HOD?", ["sudeep sharma"]),
            ("Where is the library?", ["room 10", "ground floor"]),
            ("Where is the CSE HOD office?", ["room 113"]),
        ]

        for question, expected_in_answer in live_tests:
            try:
                result = await chat.process_message(question)
                response = result["response"].lower()
                found = all(exp.lower() in response for exp in expected_in_answer)
                assert_test(
                    f"Live chat '{question}' → contains {expected_in_answer}",
                    found,
                    f"- Got: {result['response'][:120]}..."
                )
            except Exception as e:
                assert_test(f"Live chat '{question}'", False, f"- Error: {e}")

    await ollama.close()

    # Summary
    print("\n" + "=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed, {total} total")
    if failed == 0:
        print("🎉 ALL TESTS PASSED!")
    else:
        print(f"⚠️  {failed} test(s) failed")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(test_chat_service())
    sys.exit(0 if success else 1)
