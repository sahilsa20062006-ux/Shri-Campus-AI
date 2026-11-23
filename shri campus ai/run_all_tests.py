"""
Shri Campus AI - Unified Test Suite Runner
Runs all unit, integration, and question verification test suites.
"""

import sys
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

TESTS = [
    ("Knowledge Base Tests", BASE_DIR / "tests" / "test_knowledge.py"),
    ("Chat Pipeline Tests", BASE_DIR / "tests" / "test_chat.py"),
    ("API Integration Tests", BASE_DIR / "tests" / "test_api.py"),
    ("Campus Q&A Verification Tests", BASE_DIR / "tests" / "test_questions.py"),
]

def main():
    print("=" * 65)
    print("      SHRI CAMPUS AI — COMPREHENSIVE TEST SUITE")
    print("=" * 65)

    all_passed = True
    results = []

    for name, path in TESTS:
        print(f"\n[RUNNING] {name} ({path.name})...")
        res = subprocess.run([sys.executable, str(path)], capture_output=False)
        success = res.returncode == 0
        results.append((name, success))
        if not success:
            all_passed = False

    print("\n" + "=" * 65)
    print("                      OVERALL SUMMARY")
    print("=" * 65)
    for name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"  {status:12} : {name}")

    print("=" * 65)
    if all_passed:
        print("🎉 ALL TEST SUITES PASSED PERFECTLY!")
    else:
        print("⚠️ Some test suites reported errors.")
    print("=" * 65)

    sys.exit(0 if all_passed else 1)

if __name__ == "__main__":
    main()
