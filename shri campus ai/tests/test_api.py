"""
Shri Campus AI - API Integration Tests
Tests the FastAPI endpoints with the TestClient.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient
from backend.main import app


def test_api():
    """Test all API endpoints."""
    print("=" * 60)
    print("SHRI CAMPUS AI - API INTEGRATION TESTS")
    print("=" * 60)

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

    with TestClient(app) as client:
        # Test health endpoint
        print("\n🏥 Test Group: Health Endpoint")
        res = client.get("/api/health")
        assert_test("GET /api/health returns 200", res.status_code == 200)
        health_data = res.json()
        assert_test("Health reports service name", health_data.get("service") == "Shri Campus AI")
        assert_test("Health reports KB status", "knowledge_base" in health_data)
        assert_test("Health reports ollama status", "ollama" in health_data)

        # Test knowledge status
        print("\n📊 Test Group: Knowledge Status Endpoint")
        res = client.get("/api/knowledge/status")
        assert_test("GET /api/knowledge/status returns 200", res.status_code == 200)
        kb_status = res.json()
        assert_test("KB status loaded=true", kb_status.get("loaded") == True)
        assert_test("KB has 64 FAQs", kb_status.get("faq_count") == 64)
        assert_test("KB has 6 faculty", kb_status.get("faculty_count") == 6)

        # Test knowledge search
        print("\n🔍 Test Group: Knowledge Search Endpoint")
        res = client.get("/api/knowledge/search?q=AIML HOD")
        assert_test("GET /api/knowledge/search returns 200", res.status_code == 200)
        search_data = res.json()
        assert_test("Search returns results", len(search_data.get("results", [])) > 0)
        all_content = " ".join(r["content"] for r in search_data.get("results", []))
        assert_test("Search finds Sudeep Sharma", "sudeep sharma" in all_content.lower())

        # Test search validation
        res = client.get("/api/knowledge/search?q=a")
        assert_test("Short query rejected (400)", res.status_code == 400)

        # Test chat endpoint
        print("\n💬 Test Group: Chat Endpoint")

        # Valid request
        res = client.post("/api/chat", json={"message": "Who is the AIML HOD?"})
        assert_test("POST /api/chat returns 200", res.status_code == 200)
        chat_data = res.json()
        assert_test("Chat returns response", "response" in chat_data)
        assert_test("Chat returns session_id", "session_id" in chat_data)
        assert_test("Chat response not empty", len(chat_data.get("response", "")) > 0)

        # Test with starting location
        res = client.post("/api/chat", json={
            "message": "Where is Room 103?",
            "starting_location": "Main Entrance Gate"
        })
        assert_test("Chat with starting_location returns 200", res.status_code == 200)

        # Test conversation continuity
        if chat_data.get("session_id"):
            res2 = client.post("/api/chat", json={
                "message": "Where is his office?",
                "session_id": chat_data["session_id"]
            })
            assert_test("Follow-up with session_id returns 200", res2.status_code == 200)

        # Validation tests
        res = client.post("/api/chat", json={"message": ""})
        assert_test("Empty message rejected (422)", res.status_code == 422)

        # Test frontend serving
        print("\n🌐 Test Group: Frontend Serving")
        res = client.get("/")
        assert_test("GET / returns 200 (frontend)", res.status_code == 200)
        assert_test("Frontend contains Shri Campus AI", "Shri Campus AI" in res.text)

        res = client.get("/logo.png")
        assert_test("GET /logo.png returns 200", res.status_code == 200)

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
    success = test_api()
    sys.exit(0 if success else 1)
