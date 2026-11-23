"""
Shri Campus AI - Core Q&A Verification Tests
Verifies that all specific questions required by the prompt return strictly accurate answers
matching the verified PDF data without hallucination.
"""

import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.knowledge import KnowledgeBase
from backend.ollama_service import OllamaService
from backend.chat import ChatService
from backend.config import KNOWLEDGE_BASE_PATH


async def test_core_questions():
    print("=" * 65)
    print("SHRI CAMPUS AI - MANDATORY CAMPUS QUESTIONS VERIFICATION")
    print("=" * 65)

    kb = KnowledgeBase(KNOWLEDGE_BASE_PATH)
    kb.load()
    ollama = OllamaService()
    chat = ChatService(kb, ollama)

    test_cases = [
        {
            "query": "Who is the AIML HOD?",
            "must_contain": ["sudeep sharma"],
            "must_not_contain": []
        },
        {
            "query": "Where is the AIML HOD office?",
            "must_contain": ["103", "first floor"],
            "must_not_contain": []
        },
        {
            "query": "Who is the CSE HOD?",
            "must_contain": ["ruchi kshatri patel"],
            "must_not_contain": []
        },
        {
            "query": "Where is the CSE HOD office?",
            "must_contain": ["113", "first floor"],
            "must_not_contain": []
        },
        {
            "query": "Where is the library?",
            "must_contain": ["room 10", "ground floor"],
            "must_not_contain": []
        },
        {
            "query": "Where is the Principal's office?",
            "must_contain": ["room 01", "ground floor"],
            "must_not_contain": []
        },
        {
            "query": "What is the principal's name?",
            "must_contain": ["sameer", "vaidya"],
            "must_not_contain": []
        },
        {
            "query": "Who is the principal?",
            "must_contain": ["sameer vaidya"],
            "must_not_contain": []
        },
        {
            "query": "Who is the third year AIML incharge?",
            "must_contain": ["ankit kachhi", "vikas dhanwani"],
            "must_not_contain": []
        },
        {
            "query": "Where is the First-Year HOD's office?",
            "must_contain": ["room 19", "ground floor"],
            "must_not_contain": []
        },
        {
            "query": "Where is the MBA department?",
            "must_contain": ["third floor"],
            "must_not_contain": []
        },
        {
            "query": "Where is the Third-Year AIML classroom?",
            "must_contain": ["room 117", "first floor"],
            "must_not_contain": []
        },
        {
            "query": "Where is the Third-Year CSE-A classroom?",
            "must_contain": ["room 215", "second floor"],
            "must_not_contain": []
        },
        {
            "query": "Where is the Fourth-Year classroom?",
            "checker": lambda ans: any(w in ans.lower() for w in ["not", "no verified", "unverified", "not available", "not recorded", "not supplied"]),
        },
        {
            "query": "Library kaha hai?",
            "checker": lambda ans: ("10" in ans or "१०" in ans) and ("ground" in ans.lower() or "ज़मीन" in ans.lower() or "ग्राउंड" in ans.lower()),
        },
        {
            "query": "Principal office kis floor par hai?",
            "checker": lambda ans: "ground" in ans.lower() or "ज़मीन" in ans.lower() or "ग्राउंड" in ans.lower(),
        }
    ]

    passed = 0
    failed = 0

    for idx, tc in enumerate(test_cases, 1):
        q = tc["query"]
        res = await chat.process_message(q)
        answer = res["response"]
        ans_lower = answer.lower()

        # Check condition
        if "checker" in tc:
            is_pass = tc["checker"](answer)
            missing = [] if is_pass else ["condition check failed"]
            forbidden = []
        else:
            missing = [mc for mc in tc.get("must_contain", []) if mc not in ans_lower]
            forbidden = [mnc for mnc in tc.get("must_not_contain", []) if mnc in ans_lower]

        if not missing and not forbidden:
            passed += 1
            print(f"[{idx:02d}] ✅ PASS: \"{q}\"")
            print(f"     Answer: {answer[:110]}...")
        else:
            failed += 1
            print(f"[{idx:02d}] ❌ FAIL: \"{q}\"")
            print(f"     Answer: {answer}")
            if missing:
                print(f"     Missing expected tokens: {missing}")
            if forbidden:
                print(f"     Contained forbidden tokens: {forbidden}")

    # Test follow-up question
    print("\n--- Testing Follow-up Context ---")
    session_id = "test-context-flow"
    r1 = await chat.process_message("Who is the AIML HOD?", session_id=session_id)
    r2 = await chat.process_message("Where is his office?", session_id=session_id)
    r2_lower = r2["response"].lower()
    if "103" in r2_lower and "first floor" in r2_lower:
        passed += 1
        print("✅ PASS: Follow-up question 'Where is his office?' resolved to Room 103, First Floor")
        print(f"   Answer: {r2['response']}")
    else:
        failed += 1
        print("❌ FAIL: Follow-up question did not resolve correctly")
        print(f"   Answer: {r2['response']}")

    await ollama.close()

    print("\n" + "=" * 65)
    print(f"QUESTION TEST SUMMARY: {passed} PASSED, {failed} FAILED (TOTAL {passed + failed})")
    print("=" * 65)

    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(test_core_questions())
    sys.exit(0 if success else 1)
