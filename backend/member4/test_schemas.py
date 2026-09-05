"""
Unit and Integration Tests for Member 4 Data Contract Schemas.

Validates:
1. Parsing of valid Member 3 extraction payloads.
2. Graceful acceptance of missing optional fields (assignee, deadline, topic_reference).
3. Rejection of invalid types or empty required fields.
4. Correct representation of Action Items and Decisions.
5. Correct handling of topic_reference mappings.
6. Successful validation against real production artifact: data/processed/ES2002a_member3_results.json.
7. Verification that Member 4 schemas do NOT import Member 1/2/3 modules or UI libraries.
"""

import json
import sys
import unittest
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.member4.schemas import (
    Member4Input,
    Member4ActionItemInput,
    Member4DecisionInput,
    Member2TopicContextInput,
    Member4Output,
    PriorityLevel,
    ReviewPriority,
)


class TestMember4Schemas(unittest.TestCase):
    """Test suite for Member 4 boundary schemas."""

    def test_01_valid_action_item_parsing(self):
        """Verify parsing of fully specified and minimal action items."""
        data = {
            "task": "Review the product architecture diagram",
            "responsible_person": "SPEAKER_01",
            "deadline": "by Friday",
            "topic_reference": 12,
            "priority": "High",
            "confidence_score": 0.95,
        }
        item = Member4ActionItemInput.model_validate(data)
        self.assertEqual(item.task, "Review the product architecture diagram")
        self.assertEqual(item.responsible_person, "SPEAKER_01")
        self.assertEqual(item.deadline, "by Friday")
        self.assertEqual(item.topic_reference, 12)
        self.assertEqual(item.source_priority, "High")
        self.assertEqual(item.source_confidence_score, 0.95)

    def test_02_minimal_action_item_optional_fields(self):
        """Verify action item with only required 'task' field."""
        data = {"task": "Minimal task with no assignee or deadline"}
        item = Member4ActionItemInput.model_validate(data)
        self.assertEqual(item.task, "Minimal task with no assignee or deadline")
        self.assertIsNone(item.responsible_person)
        self.assertIsNone(item.deadline)
        self.assertIsNone(item.topic_reference)
        self.assertIsNone(item.source_priority)
        self.assertIsNone(item.source_confidence_score)

    def test_03_invalid_action_item_rejection(self):
        """Verify empty task or missing task is rejected."""
        with self.assertRaises(ValueError):
            Member4ActionItemInput.model_validate({"task": ""})

        with self.assertRaises(ValueError):
            Member4ActionItemInput.model_validate({"task": "   "})

        with self.assertRaises(ValueError):
            Member4ActionItemInput.model_validate({})

    def test_04_valid_decision_parsing(self):
        """Verify decision parsing with and without topic_reference."""
        dec1 = Member4DecisionInput.model_validate({
            "decision": "Use PostgreSQL for relational storage",
            "topic_reference": 5,
        })
        self.assertEqual(dec1.decision, "Use PostgreSQL for relational storage")
        self.assertEqual(dec1.topic_reference, 5)

        dec2 = Member4DecisionInput.model_validate({
            "decision": "Agree to meet weekly on Tuesdays"
        })
        self.assertEqual(dec2.decision, "Agree to meet weekly on Tuesdays")
        self.assertIsNone(dec2.topic_reference)

    def test_05_invalid_decision_rejection(self):
        """Verify empty decision string is rejected."""
        with self.assertRaises(ValueError):
            Member4DecisionInput.model_validate({"decision": ""})

    def test_06_top_level_member4_input_parsing(self):
        """Verify top-level Member 3 meeting payload parsing."""
        payload = {
            "meeting_id": "TEST_001",
            "processing_stage": "member_3_complete",
            "total_action_items": 1,
            "total_decisions": 1,
            "action_items": [
                {
                    "task": "Test action item",
                    "responsible_person": "SPEAKER_00",
                    "topic_reference": 2,
                }
            ],
            "key_decisions": [
                {
                    "decision": "Test key decision",
                    "topic_reference": 2,
                }
            ],
        }
        parsed = Member4Input.model_validate(payload)
        self.assertEqual(parsed.meeting_id, "TEST_001")
        self.assertEqual(len(parsed.action_items), 1)
        self.assertEqual(len(parsed.key_decisions), 1)

    def test_07_topic_reference_handling(self):
        """Verify topic_reference handles positive ints, null, and Member 2 bridge."""
        item = Member4ActionItemInput(
            task="Check the remote control",
            topic_reference=42
        )
        self.assertEqual(item.topic_reference, 42)

        # Member 2 Context Model
        m2_topic = Member2TopicContextInput(
            topic_id=42,
            segment_count=4,
            speakers=["SPEAKER_01", "SPEAKER_02"],
            summary="Discussion about remote control buttons.",
        )
        self.assertEqual(m2_topic.topic_id, item.topic_reference)

    def test_08_no_ui_and_no_upstream_imports(self):
        """Verify Member 4 schemas do not import UI or Member 1/2/3 implementation modules."""
        import backend.member4.schemas as m4_schemas

        module_text = Path(m4_schemas.__file__).read_text(encoding="utf-8")
        forbidden = [
            "streamlit",
            "gradio",
            "whisperx",
            "pyannote",
            "transformers",
            "ollama",
            "backend.pipeline",
            "backend.speaker_aware_transcription",
            "backend.summarization",
            "backend.extraction",
        ]
        for term in forbidden:
            self.assertNotIn(
                f"import {term}",
                module_text,
                f"Forbidden dependency found in schemas.py: {term}"
            )

    def test_09_real_production_json_validation(self):
        """Validate against the real ES2002a_member3_results.json file."""
        real_json_path = PROJECT_ROOT / "data" / "processed" / "ES2002a_member3_results.json"
        self.assertTrue(real_json_path.exists(), f"File not found: {real_json_path}")

        with open(real_json_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        parsed = Member4Input.model_validate(raw_data)

        # Assertions based on verified contents
        self.assertEqual(parsed.meeting_id, "ES2002a")
        self.assertEqual(len(parsed.action_items), 32)
        self.assertEqual(len(parsed.key_decisions), 9)

        # Check a specific known item
        first_item = parsed.action_items[0]
        self.assertEqual(first_item.task, "Introduce the team members")
        self.assertEqual(first_item.responsible_person, "SPEAKER_03")
        self.assertEqual(first_item.topic_reference, 3)
        self.assertEqual(first_item.source_priority, "Normal")
        self.assertEqual(first_item.source_confidence_score, 0.9)

        print("\n" + "=" * 60)
        print("REAL ARTIFACT VALIDATION SUMMARY:")
        print(f"- Meeting ID: {parsed.meeting_id}")
        print(f"- Action Items Ingested: {len(parsed.action_items)}")
        print(f"- Key Decisions Ingested: {len(parsed.key_decisions)}")
        print("=" * 60)


if __name__ == "__main__":
    unittest.main()
