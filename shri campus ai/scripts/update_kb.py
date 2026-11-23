"""
Update SRIST Knowledge Base with Principal (Dr. Sameer Vaidya)
and Third-Year AIML Incharges (Prof. Ankit Kachhi & Prof. Vikas Dhanwani).
"""

import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
KB_PATH = BASE_DIR / "data" / "srist_knowledge_base.json"

def update():
    with open(KB_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 1. Update institute
    data["institute"]["principal"] = "Dr. Sameer Vaidya"

    # 2. Update faculty
    new_faculty = [
        {
            "id": "FAC004",
            "name": "Dr. Sameer Vaidya",
            "designation": "Principal",
            "department": "Administration",
            "branch": None,
            "room": "01",
            "floor": "Ground Floor",
            "notes": "Principal of Shri Ram Institute of Science & Technology (SRIST)."
        },
        {
            "id": "FAC005",
            "name": "Prof. Ankit Kachhi",
            "designation": "Third-Year AIML Incharge",
            "department": "B.Tech",
            "branch": "AIML",
            "room": None,
            "floor": "First Floor",
            "notes": "Incharge faculty for AIML Third Year."
        },
        {
            "id": "FAC006",
            "name": "Prof. Vikas Dhanwani",
            "designation": "Third-Year AIML Incharge",
            "department": "B.Tech",
            "branch": "AIML",
            "room": None,
            "floor": "First Floor",
            "notes": "Incharge faculty for AIML Third Year."
        }
    ]

    for nf in new_faculty:
        if not any(f["id"] == nf["id"] or f["name"] == nf["name"] for f in data["faculty"]):
            data["faculty"].append(nf)

    # 3. Update administrative offices
    for off in data.get("administrative_offices", []):
        if off["id"] == "ADM001":
            off["person"] = "Dr. Sameer Vaidya"
            off["notes"] = "Principal of SRIST is Dr. Sameer Vaidya."

    # 4. Update rooms ground_floor
    for r in data.get("rooms", {}).get("ground_floor", []):
        if r["room"] == "01":
            r["use"] = "Principal's Office — Dr. Sameer Vaidya (Principal)"

    # 5. Update classrooms
    for c in data.get("classrooms", []):
        if c["id"] == "CLS007":
            c["incharge"] = ["Prof. Ankit Kachhi", "Prof. Vikas Dhanwani"]
            c["notes"] = "Incharge faculty: Prof. Ankit Kachhi and Prof. Vikas Dhanwani."

    # 6. Update data_quality_notes
    notes = data.get("data_quality_notes", [])
    new_notes = []
    for n in notes:
        if "principal's name has not been supplied" in n:
            new_notes.append("The principal's name is Dr. Sameer Vaidya, located in Room 01, Ground Floor.")
        else:
            new_notes.append(n)
    if not any("Ankit Kachhi" in n for n in new_notes):
        new_notes.append("The incharges for AIML Third Year are Prof. Ankit Kachhi and Prof. Vikas Dhanwani.")
    data["data_quality_notes"] = new_notes

    # 7. Update FAQ
    faq = data.get("faq", [])
    for item in faq:
        if item["id"] == "Q12":
            item["answer"] = "Dr. Sameer Vaidya is the Principal of Shri Ram Institute of Science & Technology (SRIST). His office is located in Room 01 on the Ground Floor."
        elif item["id"] == "Q61":
            item["answer"] = "Yes, the Principal of SRIST is Dr. Sameer Vaidya, whose office is located in Room 01 on the Ground Floor."

    # Add new FAQ items if not present
    existing_q_ids = {item["id"] for item in faq}
    new_faqs = [
        {
            "id": "Q62",
            "question": "What is the principal's name?",
            "answer": "The Principal of Shri Ram Institute of Science & Technology (SRIST) is Dr. Sameer Vaidya. His office is located in Room 01 on the Ground Floor."
        },
        {
            "id": "Q63",
            "question": "Who is the AIML Third-Year Incharge?",
            "answer": "The incharges for AIML Third Year are Prof. Ankit Kachhi and Prof. Vikas Dhanwani."
        },
        {
            "id": "Q64",
            "question": "Who is the incharge of Third-Year AIML?",
            "answer": "Prof. Ankit Kachhi and Prof. Vikas Dhanwani are the incharges of Third-Year AIML."
        }
    ]

    for nq in new_faqs:
        if nq["id"] not in existing_q_ids:
            faq.append(nq)

    with open(KB_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print("Successfully updated srist_knowledge_base.json!")
    print(f"Total faculty count: {len(data['faculty'])}")
    print(f"Total FAQ count: {len(data['faq'])}")
    print(f"Principal: {data['institute'].get('principal')}")

if __name__ == "__main__":
    update()
