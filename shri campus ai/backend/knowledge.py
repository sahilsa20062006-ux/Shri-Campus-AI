"""
Shri Campus AI - Knowledge Base Service
Loads, indexes, and searches the SRIST college knowledge base.
"""

import json
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger("shri_campus_ai.knowledge")


class KnowledgeBase:
    """Loads and searches the SRIST college knowledge base JSON."""

    def __init__(self, json_path: Path):
        self.json_path = json_path
        self.data: dict = {}
        self._search_index: list[dict] = []
        self._loaded = False

    def load(self) -> bool:
        """Load and index the knowledge base JSON file."""
        try:
            with open(self.json_path, "r", encoding="utf-8") as f:
                self.data = json.load(f)
            self._build_search_index()
            self._loaded = True
            logger.info(f"Knowledge base loaded from {self.json_path}")
            logger.info(f"Search index built with {len(self._search_index)} entries")
            return True
        except FileNotFoundError:
            logger.error(f"Knowledge base file not found: {self.json_path}")
            return False
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in knowledge base: {e}")
            return False

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    def _build_search_index(self):
        """Build a flat searchable index from all knowledge base sections."""
        self._search_index = []

        # Index institute info
        inst = self.data.get("institute", {})
        if inst:
            self._search_index.append({
                "type": "institute",
                "keywords": ["institute", "college", "srist", "shri ram", "campus", "department", "departments", "floor", "floors"],
                "content": f"Institute: {inst.get('name', '')} ({inst.get('short_name', '')}), located in {inst.get('location', '')}. Departments: {', '.join(inst.get('departments', []))}. Floors: {', '.join(inst.get('floors', []))}.",
                "data": inst
            })

        # Index faculty
        for fac in self.data.get("faculty", []):
            name_lower = fac["name"].lower()
            name_parts = name_lower.split()
            keywords = ["faculty", "hod", "professor", "teacher", "sir", "madam", "ma'am",
                         fac.get("designation", "").lower(), fac.get("branch", "").lower() if fac.get("branch") else ""]
            keywords.extend(name_parts)
            keywords.append(name_lower)
            # Add room as keyword
            if fac.get("room"):
                keywords.append(f"room {fac['room']}")
                keywords.append(fac["room"])

            self._search_index.append({
                "type": "faculty",
                "keywords": [k for k in keywords if k],
                "content": f"{fac['name']} is the {fac['designation']}. Office: Room {fac.get('room', 'N/A')}, {fac.get('floor', 'N/A')}." +
                           (f" Note: {fac['notes']}" if fac.get("notes") else ""),
                "data": fac
            })

        # Index administrative offices
        for office in self.data.get("administrative_offices", []):
            name_lower = office["name"].lower()
            keywords = ["office", "admin", "administration", name_lower]
            keywords.extend(name_lower.split())
            if office.get("person"):
                keywords.append(office["person"].lower())
                keywords.extend(office["person"].lower().split())
            if office.get("room"):
                keywords.append(f"room {office['room']}")
                keywords.append(office["room"])

            person_str = f" Occupant/Principal: {office['person']}." if office.get("person") else ""
            self._search_index.append({
                "type": "office",
                "keywords": keywords,
                "content": f"{office['name']}: Room {office.get('room', 'N/A')}, {office.get('floor', 'N/A')}." +
                           person_str +
                           (f" Note: {office['notes']}" if office.get("notes") else ""),
                "data": office
            })

        # Index classrooms
        for cls in self.data.get("classrooms", []):
            rooms_str = ", ".join(cls.get("rooms", []))
            keywords = ["classroom", "class", "room", "section",
                         cls.get("branch", "").lower(), cls.get("year", "").lower()]
            keywords.extend(cls.get("branch", "").lower().split("-"))
            # Add year variants
            year = cls.get("year", "").lower()
            if "first" in year:
                keywords.extend(["1st", "first", "1st year", "first year"])
            elif "second" in year:
                keywords.extend(["2nd", "second", "2nd year", "second year"])
            elif "third" in year:
                keywords.extend(["3rd", "third", "3rd year", "third year"])
            elif "fourth" in year:
                keywords.extend(["4th", "fourth", "4th year", "fourth year"])

            if cls.get("incharge"):
                incharge_val = cls["incharge"]
                if isinstance(incharge_val, list):
                    keywords.extend([p.lower() for p in incharge_val])
                    for p in incharge_val:
                        keywords.extend(p.lower().split())
                else:
                    keywords.append(str(incharge_val).lower())
                    keywords.extend(str(incharge_val).lower().split())
                keywords.append("incharge")

            for r in cls.get("rooms", []):
                keywords.append(r)
                keywords.append(f"room {r}")

            incharge_str = ""
            if cls.get("incharge"):
                inc = cls["incharge"]
                inc_text = ", ".join(inc) if isinstance(inc, list) else str(inc)
                incharge_str = f" Incharge faculty: {inc_text}."

            content = f"{cls.get('year', '')} {cls.get('branch', '')} classroom(s): Room(s) {rooms_str if rooms_str else 'Not available'}, {cls.get('floor', 'N/A')}." + incharge_str
            if cls.get("notes"):
                content += f" Note: {cls['notes']}"

            self._search_index.append({
                "type": "classroom",
                "keywords": [k for k in keywords if k],
                "content": content,
                "data": cls
            })

        # Index labs
        for lab in self.data.get("labs", []):
            name_lower = lab["name"].lower()
            keywords = ["lab", "laboratory", name_lower]
            keywords.extend(name_lower.split())
            if lab.get("room"):
                keywords.append(f"room {lab['room']}")
                keywords.append(lab["room"])

            self._search_index.append({
                "type": "lab",
                "keywords": keywords,
                "content": f"{lab['name']}: Room {lab.get('room', 'N/A')}, {lab.get('floor', 'N/A')}." +
                           (f" Note: {lab['notes']}" if lab.get("notes") else ""),
                "data": lab
            })

        # Index facilities
        for fac in self.data.get("facilities", []):
            name_lower = fac["name"].lower()
            keywords = [name_lower, "facility"]
            keywords.extend(name_lower.split())
            if fac.get("room"):
                keywords.append(f"room {fac['room']}")
                keywords.append(fac["room"])

            self._search_index.append({
                "type": "facility",
                "keywords": keywords,
                "content": f"{fac['name']}: Room {fac.get('room', 'N/A')}, {fac.get('floor', 'N/A')}.",
                "data": fac
            })

        # Index departments detail
        for dept in self.data.get("departments_detail", []):
            keywords = ["department", dept["name"].lower()]
            keywords.extend(dept["name"].lower().split())
            if dept.get("branches"):
                keywords.extend([b.lower() for b in dept["branches"]])

            branches_str = ", ".join(dept.get("branches", [])) if dept.get("branches") else "N/A"
            content = f"Department: {dept['name']}. Branches: {branches_str}."
            if dept.get("floor"):
                content += f" Located on {dept['floor']}."
            if dept.get("notes"):
                content += f" Note: {dept['notes']}"

            self._search_index.append({
                "type": "department",
                "keywords": keywords,
                "content": content,
                "data": dept
            })

        # Index rooms by floor
        for floor_key, rooms in self.data.get("rooms", {}).items():
            for room in rooms:
                if room.get("room"):
                    keywords = [f"room {room['room']}", room["room"], room.get("floor", "").lower(),
                                room.get("use", "").lower()]
                    keywords.extend(room.get("use", "").lower().split())

                    self._search_index.append({
                        "type": "room",
                        "keywords": [k for k in keywords if k],
                        "content": f"Room {room['room']}, {room.get('floor', 'N/A')}: {room.get('use', 'Unknown')}.",
                        "data": room
                    })

        # Index FAQ
        for faq in self.data.get("faq", []):
            q_lower = faq["question"].lower()
            keywords = q_lower.split()
            # Remove common words
            stop_words = {"what", "is", "the", "where", "who", "how", "do", "i", "are", "a", "an", "in", "on", "can", "of", "has", "have"}
            keywords = [w.strip("?.,!") for w in keywords if w.strip("?.,!") not in stop_words and len(w.strip("?.,!")) > 1]

            self._search_index.append({
                "type": "faq",
                "keywords": keywords,
                "content": f"Q: {faq['question']}\nA: {faq['answer']}",
                "data": faq
            })

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        """Search the knowledge base using keyword matching."""
        if not self._loaded:
            return []

        query_lower = query.lower()
        query_tokens = set()
        for word in query_lower.split():
            cleaned = word.strip("?.,!;:'\"")
            if cleaned and len(cleaned) > 1:
                query_tokens.add(cleaned)

        # Add common Hindi/Hinglish mappings
        hindi_map = {
            "kaha": ["where"], "kahan": ["where"], "kaun": ["who"], "kon": ["who"],
            "hai": [], "hain": [], "ka": ["of"], "ki": ["of"], "ke": ["of"],
            "kis": ["which"], "kya": ["what"], "floor": ["floor"], "par": ["on"],
            "office": ["office"], "room": ["room"], "library": ["library"],
            "principal": ["principal"], "pracharya": ["principal"], "classroom": ["classroom"], "class": ["class"],
            "lab": ["lab"], "department": ["department"], "hod": ["hod"],
            "incharge": ["incharge"], "in-charge": ["incharge"],
            "sir": ["sir", "hod", "faculty", "incharge"], "mam": ["madam", "hod", "faculty", "incharge"],
            "madam": ["madam", "hod", "faculty", "incharge"],
        }

        expanded_tokens = set(query_tokens)
        for token in query_tokens:
            if token in hindi_map:
                expanded_tokens.update(hindi_map[token])

        # Score each index entry
        scored_results = []
        for entry in self._search_index:
            score = 0
            entry_keywords = set(entry["keywords"])
            entry_content_lower = entry["content"].lower()

            # Exact token matches with keywords
            for token in expanded_tokens:
                for kw in entry_keywords:
                    if token == kw:
                        score += 10
                    elif token in kw:
                        score += 5
                    elif kw in token:
                        score += 3

            # Check if query tokens appear in content
            for token in expanded_tokens:
                if token in entry_content_lower:
                    score += 4

            # Boost for exact phrase matches
            if query_lower in entry_content_lower:
                score += 20

            # Boost FAQ type for direct question matches
            if entry["type"] == "faq":
                q_lower = entry["data"].get("question", "").lower()
                matching_words = sum(1 for t in expanded_tokens if t in q_lower)
                if matching_words >= 2:
                    score += matching_words * 3

            if score > 0:
                scored_results.append({"score": score, "entry": entry})

        # Sort by score descending
        scored_results.sort(key=lambda x: x["score"], reverse=True)

        # Return top-k unique content entries
        seen_content = set()
        results = []
        for item in scored_results:
            content = item["entry"]["content"]
            if content not in seen_content:
                seen_content.add(content)
                results.append(item["entry"])
                if len(results) >= top_k:
                    break

        return results

    def get_faculty_by_name(self, name: str) -> Optional[dict]:
        """Find a faculty member by name (partial match)."""
        name_lower = name.lower()
        for fac in self.data.get("faculty", []):
            if name_lower in fac["name"].lower():
                return fac
        return None

    def get_room_info(self, room_number: str) -> list[dict]:
        """Get information about a specific room number."""
        results = []
        for floor_rooms in self.data.get("rooms", {}).values():
            for room in floor_rooms:
                if room.get("room") == room_number:
                    results.append(room)
        return results

    def get_all_faculty(self) -> list[dict]:
        """Return all faculty records."""
        return self.data.get("faculty", [])

    def get_status(self) -> dict:
        """Return knowledge base status info."""
        if not self._loaded:
            return {"loaded": False, "error": "Knowledge base not loaded"}
        return {
            "loaded": True,
            "path": str(self.json_path),
            "sections": list(self.data.keys()),
            "faculty_count": len(self.data.get("faculty", [])),
            "rooms_count": sum(len(rooms) for rooms in self.data.get("rooms", {}).values()),
            "classrooms_count": len(self.data.get("classrooms", [])),
            "labs_count": len(self.data.get("labs", [])),
            "faq_count": len(self.data.get("faq", [])),
            "search_index_size": len(self._search_index)
        }
