"""
Shri Campus AI - Knowledge Base Tests
Verifies all data from the PDF is correctly loaded and searchable.
"""

import sys
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.knowledge import KnowledgeBase
from backend.config import KNOWLEDGE_BASE_PATH


def test_knowledge_base():
    """Run all knowledge base tests."""
    print("=" * 60)
    print("SHRI CAMPUS AI - KNOWLEDGE BASE TESTS")
    print("=" * 60)

    kb = KnowledgeBase(KNOWLEDGE_BASE_PATH)
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

    # Test 1: Load knowledge base
    print("\n📂 Test Group: Knowledge Base Loading")
    result = kb.load()
    assert_test("KB loads successfully", result)
    assert_test("KB is marked as loaded", kb.is_loaded)

    # Test 2: JSON validation
    print("\n📋 Test Group: JSON Structure Validation")
    with open(KNOWLEDGE_BASE_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)

    expected_sections = ["institute", "faculty", "administrative_offices", "rooms", "classrooms", "labs", "facilities", "faq"]
    for section in expected_sections:
        assert_test(f"Section '{section}' exists", section in data)

    # Test 3: Faculty data accuracy
    print("\n👨‍🏫 Test Group: Faculty Data Accuracy")

    # AIML HOD
    aiml_hod = kb.get_faculty_by_name("Sudeep Sharma")
    assert_test("AIML HOD found: Sudeep Sharma", aiml_hod is not None)
    if aiml_hod:
        assert_test("AIML HOD designation", aiml_hod["designation"] == "AIML HOD")
        assert_test("AIML HOD room is 103", aiml_hod["room"] == "103")
        assert_test("AIML HOD floor is First Floor", aiml_hod["floor"] == "First Floor")

    # CSE HOD
    cse_hod = kb.get_faculty_by_name("Ruchi Kshatri Patel")
    assert_test("CSE HOD found: Dr. Ruchi Kshatri Patel", cse_hod is not None)
    if cse_hod:
        assert_test("CSE HOD designation", cse_hod["designation"] == "CSE HOD")
        assert_test("CSE HOD room is 113", cse_hod["room"] == "113")
        assert_test("CSE HOD floor is First Floor", cse_hod["floor"] == "First Floor")

    # Principal
    principal = kb.get_faculty_by_name("Sameer Vaidya")
    assert_test("Principal found: Dr. Sameer Vaidya", principal is not None)
    if principal:
        assert_test("Principal designation", principal["designation"] == "Principal")
        assert_test("Principal room is 01", principal["room"] == "01")
        assert_test("Principal floor is Ground Floor", principal["floor"] == "Ground Floor")

    # AIML 3rd Year Incharges
    incharge1 = kb.get_faculty_by_name("Ankit Kachhi")
    assert_test("Incharge found: Prof. Ankit Kachhi", incharge1 is not None)
    incharge2 = kb.get_faculty_by_name("Vikas Dhanwani")
    assert_test("Incharge found: Prof. Vikas Dhanwani", incharge2 is not None)

    # Test 4: Room data accuracy
    print("\n🚪 Test Group: Room Data Accuracy")

    room_tests = [
        ("01", "Principal's Office"),
        ("03", "Accounts Office"),
        ("10", "Library"),
        ("12", "TPO / PRO"),
        ("103", "AIML HOD Office"),
        ("113", "CSE HOD Office"),
        ("116", "Smart Classroom"),
        ("117", "AIML Third-Year"),
        ("118", "CSE-B Third-Year"),
        ("215", "CSE-A Third-Year"),
        ("218", "Seminar Hall"),
        ("121", "Exam Cell"),
        ("122", "Strong Room"),
    ]

    for room_num, expected_use in room_tests:
        rooms = kb.get_room_info(room_num)
        assert_test(
            f"Room {room_num} contains '{expected_use}'",
            any(expected_use.lower() in r.get("use", "").lower() for r in rooms),
            f"- Got: {[r.get('use', '') for r in rooms]}" if rooms else "- Room not found"
        )

    # Test 5: Search functionality
    print("\n🔍 Test Group: Search Accuracy")

    search_tests = [
        ("AIML HOD", "Sudeep Sharma"),
        ("CSE HOD", "Ruchi Kshatri Patel"),
        ("library", "Room 10"),
        ("Principal office", "Room 01"),
        ("First-Year HOD", "M.S. Khan"),
        ("MBA department", "Third Floor"),
        ("seminar hall", "Room 218"),
        ("engineering physics lab", "Room 19"),
        ("first year CSE classroom", "04"),
        ("AIML third year", "Room 117"),
        ("CSE-A third year", "Room 215"),
        ("staff room", "Room 21"),
        ("smart classroom", "Room 116"),
        ("exam cell", "Room 121"),
        ("girls room", "Room 11"),
    ]

    for query, expected_in_result in search_tests:
        results = kb.search(query, top_k=5)
        all_content = " ".join(r["content"] for r in results)
        assert_test(
            f"Search '{query}' finds '{expected_in_result}'",
            expected_in_result.lower() in all_content.lower(),
            f"- Results: {all_content[:100]}..."
        )

    # Missing information not invented
    print("\n🚫 Test Group: Missing Information Not Invented")

    # Fourth-year classroom should have no rooms
    for cls in kb.data.get("classrooms", []):
        if "Fourth" in cls.get("year", ""):
            assert_test("Fourth-year classroom has no verified rooms", len(cls.get("rooms", [])) == 0)

    # Test 7: FAQ accuracy
    print("\n❓ Test Group: FAQ Data")
    faq_data = kb.data.get("faq", [])
    assert_test(f"FAQ contains 64 entries", len(faq_data) == 64)

    # Spot check FAQ answers
    faq_checks = {
        "Q6": "Sudeep Sharma",
        "Q7": "Room 103",
        "Q8": "Dr. Ruchi Kshatri Patel",
        "Q9": "Room 113",
        "Q12": "Dr. Sameer Vaidya",
        "Q15": "Room 10",
        "Q62": "Dr. Sameer Vaidya",
        "Q63": "Prof. Ankit Kachhi",
    }

    for qid, expected in faq_checks.items():
        faq_item = next((f for f in faq_data if f["id"] == qid), None)
        if faq_item:
            assert_test(
                f"FAQ {qid} answer contains '{expected}'",
                expected in faq_item["answer"]
            )

    # Test 8: Knowledge base status
    print("\n📊 Test Group: KB Status")
    status = kb.get_status()
    assert_test("Status reports loaded=True", status["loaded"])
    assert_test("Faculty count is 6", status["faculty_count"] == 6)
    assert_test("FAQ count is 64", status["faq_count"] == 64)
    assert_test("Search index has entries", status["search_index_size"] > 0)

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
    success = test_knowledge_base()
    sys.exit(0 if success else 1)
