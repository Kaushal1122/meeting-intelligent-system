"""
Unit and Integration Tests for Member 4 Normalizer (Phase 2).

Verifies the 14 requirements:
1. Valid Member 3 action item.
2. Missing responsible person.
3. Missing deadline.
4. Ambiguous deadline.
5. Missing topic_reference.
6. Invalid topic_reference.
7. Valid topic_reference with Member 2 enrichment.
8. Empty/invalid task text.
9. Duplicate action items.
10. Invalid source priority/confidence values.
11. Deterministic output.
12. Real ES2002a Member 3 artifact.
13. Real ES2002a Member 2 topic enrichment where supported.
14. Verify no Member 1/2/3/pipeline imports.
"""

import json
import sys
import unittest
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.member4 import (
    Member4Input,
    Member4NormalizedOutput,
    TopicContextStatus,
    normalize_member3_input,
)


class TestMember4Normalizer(unittest.TestCase):
    """Test suite for Member 4 Validation and Normalization Layer."""

    def test_01_valid_action_item(self):
        """1. Valid Member 3 action item normalization."""
        raw_m3 = {
            "meeting_id": "TEST_001",
            "action_items": [
                {
                    "task": "Draft the user manual specification",
                    "responsible_person": "SPEAKER_01",
                    "deadline": "by next Monday",
                    "topic_reference": 5,
                    "priority": "High",
                    "confidence_score": 0.92,
                }
            ],
            "key_decisions": [],
        }
        res = normalize_member3_input(raw_m3)
        self.assertEqual(res.meeting_id, "TEST_001")
        self.assertEqual(res.total_action_items, 1)

        item = res.action_items[0]
        self.assertEqual(item.item_id, "norm_act_001")
        self.assertEqual(item.task, "Draft the user manual specification")
        self.assertEqual(item.responsible_person, "SPEAKER_01")
        self.assertFalse(item.is_unassigned)
        self.assertEqual(item.deadline, "by next Monday")
        self.assertFalse(item.is_ambiguous_deadline)
        self.assertEqual(item.topic_reference, 5)
        self.assertEqual(item.source_priority, "High")
        self.assertEqual(item.source_confidence_score, 0.92)

    def test_02_missing_responsible_person(self):
        """2. Missing/unknown responsible person handled safely (not invented)."""
        test_cases = [None, "", "   ", "None", "unknown", "unassigned", "N/A"]
        for val in test_cases:
            raw_m3 = {
                "meeting_id": "TEST_002",
                "action_items": [
                    {
                        "task": "Follow up with design agency",
                        "responsible_person": val,
                    }
                ],
            }
            res = normalize_member3_input(raw_m3)
            item = res.action_items[0]
            self.assertIsNone(item.responsible_person, f"Failed for raw value: {val!r}")
            self.assertTrue(item.is_unassigned)
            self.assertIn("Unassigned responsible person", item.validation_diagnostics)

    def test_03_missing_deadline(self):
        """3. Missing deadline handled safely (not invented)."""
        test_cases = [None, "", "None mentioned", "null", "none", "N/A", "no deadline"]
        for val in test_cases:
            raw_m3 = {
                "meeting_id": "TEST_003",
                "action_items": [
                    {
                        "task": "Test battery longevity",
                        "deadline": val,
                    }
                ],
            }
            res = normalize_member3_input(raw_m3)
            item = res.action_items[0]
            self.assertIsNone(item.deadline, f"Failed for raw deadline: {val!r}")
            self.assertFalse(item.is_ambiguous_deadline)

    def test_04_ambiguous_deadline(self):
        """4. Ambiguous deadline detected and flagged without destroying original text."""
        ambiguous_cases = ["as soon as possible", "asap", "soon", "later", "at some point"]
        for val in ambiguous_cases:
            raw_m3 = {
                "meeting_id": "TEST_004",
                "action_items": [
                    {
                        "task": "Test signal reception",
                        "deadline": val,
                    }
                ],
            }
            res = normalize_member3_input(raw_m3)
            item = res.action_items[0]
            self.assertEqual(item.deadline, val)
            self.assertTrue(item.is_ambiguous_deadline, f"Failed to flag: {val}")
            self.assertTrue(
                any("Ambiguous deadline" in diag for diag in item.validation_diagnostics)
            )

    def test_05_missing_topic_reference(self):
        """5. Missing topic_reference marks context as MISSING_REFERENCE."""
        raw_m3 = {
            "meeting_id": "TEST_005",
            "action_items": [
                {
                    "task": "Verify volume buttons",
                    "topic_reference": None,
                }
            ],
        }
        res = normalize_member3_input(raw_m3)
        item = res.action_items[0]
        self.assertIsNone(item.topic_reference)
        self.assertEqual(item.context_status, TopicContextStatus.MISSING_REFERENCE)
        self.assertIsNone(item.topic_context)

    def test_06_invalid_topic_reference(self):
        """6. Invalid topic_reference (e.g. absent from Member 2) marks UNRESOLVED."""
        raw_m3 = {
            "meeting_id": "TEST_006",
            "action_items": [
                {
                    "task": "Order plastic prototypes",
                    "topic_reference": 999,  # Non-existent topic
                }
            ],
        }
        m2_data = {
            "topics": [
                {"topic_id": 1, "summary": "Intro"},
                {"topic_id": 2, "summary": "Design review"},
            ]
        }
        res = normalize_member3_input(raw_m3, member2_data=m2_data)
        item = res.action_items[0]
        self.assertEqual(item.topic_reference, 999)
        self.assertEqual(item.context_status, TopicContextStatus.UNRESOLVED)
        self.assertIsNone(item.topic_context)
        self.assertTrue(any("not found in Member 2" in d for d in item.validation_diagnostics))

    def test_07_valid_topic_reference_with_member2_enrichment(self):
        """7. Valid topic_reference correctly enriches with Member 2 topic context."""
        raw_m3 = {
            "meeting_id": "TEST_007",
            "action_items": [
                {
                    "task": "Finalize remote control casing dimensions",
                    "responsible_person": "David",
                    "topic_reference": 2,
                }
            ],
            "key_decisions": [
                {
                    "decision": "Use curved ergonomic corners",
                    "topic_reference": 2,
                }
            ],
        }
        m2_data = {
            "topics": [
                {
                    "topic_id": 2,
                    "segment_count": 8,
                    "speakers": ["SPEAKER_00", "SPEAKER_03"],
                    "start": 120.5,
                    "end": 245.0,
                    "summary": "Detailed physical casing dimension review.",
                    "source_segment_ids": [10, 11, 12],
                }
            ]
        }
        res = normalize_member3_input(raw_m3, member2_data=m2_data)
        self.assertTrue(res.member2_context_enriched)

        # Check action item enrichment
        item = res.action_items[0]
        self.assertEqual(item.context_status, TopicContextStatus.RESOLVED)
        self.assertIsNotNone(item.topic_context)
        self.assertEqual(item.topic_context.topic_id, 2)
        self.assertEqual(item.topic_context.summary, "Detailed physical casing dimension review.")
        self.assertEqual(item.topic_context.speakers, ["SPEAKER_00", "SPEAKER_03"])

        # Check decision enrichment
        dec = res.key_decisions[0]
        self.assertEqual(dec.context_status, TopicContextStatus.RESOLVED)
        self.assertIsNotNone(dec.topic_context)
        self.assertEqual(dec.topic_context.summary, "Detailed physical casing dimension review.")

    def test_08_empty_invalid_task_text(self):
        """8. Empty/whitespace task text rejected deterministically."""
        # Non-strict mode: records rejected item without crashing
        raw_m3 = {
            "meeting_id": "TEST_008",
            "action_items": [
                {"task": ""},
                {"task": "   "},
                {"task": "Valid task text"},
            ],
        }
        res = normalize_member3_input(raw_m3, strict=False)
        self.assertEqual(res.total_action_items, 1)
        self.assertEqual(len(res.rejected_items), 2)
        self.assertEqual(res.action_items[0].task, "Valid task text")

        # Strict mode: raises ValueError
        with self.assertRaises(ValueError):
            normalize_member3_input(raw_m3, strict=True)

    def test_09_duplicate_action_items(self):
        """9. Duplicate action items detected deterministically without record destruction."""
        raw_m3 = {
            "meeting_id": "TEST_009",
            "action_items": [
                {
                    "task": "Order sample batteries",
                    "responsible_person": "SPEAKER_02",
                    "topic_reference": 4,
                },
                {
                    "task": "Order sample batteries",
                    "responsible_person": "SPEAKER_02",
                    "topic_reference": 4,
                },
                {
                    "task": "order sample batteries.",  # Punctuation/case variant
                    "responsible_person": "SPEAKER_02",
                    "topic_reference": 4,
                },
                {
                    "task": "Different distinct task",
                    "responsible_person": "SPEAKER_02",
                    "topic_reference": 4,
                },
            ],
        }
        res = normalize_member3_input(raw_m3)
        self.assertEqual(res.total_action_items, 4)
        self.assertEqual(res.duplicates_detected, 2)

        first_item = res.action_items[0]
        self.assertFalse(first_item.is_duplicate)
        self.assertIsNone(first_item.duplicate_of)

        second_item = res.action_items[1]
        self.assertTrue(second_item.is_duplicate)
        self.assertEqual(second_item.duplicate_of, "norm_act_001")

        third_item = res.action_items[2]
        self.assertTrue(third_item.is_duplicate)
        self.assertEqual(third_item.duplicate_of, "norm_act_001")

        fourth_item = res.action_items[3]
        self.assertFalse(fourth_item.is_duplicate)

    def test_10_invalid_source_priority_confidence(self):
        """10. Out-of-bounds or non-float confidence handled gracefully."""
        raw_m3 = {
            "meeting_id": "TEST_010",
            "action_items": [
                {
                    "task": "Task with out-of-range confidence",
                    "priority": "Extreme",
                    "confidence_score": 95.0,  # Out of range [0, 1]
                },
                {
                    "task": "Task with string confidence",
                    "confidence_score": "not_a_float",
                },
            ],
        }
        res = normalize_member3_input(raw_m3)
        item1 = res.action_items[0]
        self.assertEqual(item1.source_priority, "Extreme")
        self.assertEqual(item1.source_confidence_score, 95.0)
        self.assertTrue(any("out of bounds" in d for d in item1.validation_diagnostics))

        item2 = res.action_items[1]
        self.assertIsNone(item2.source_confidence_score)
        self.assertTrue(any("Invalid source confidence" in d for d in item2.validation_diagnostics))

    def test_11_deterministic_output(self):
        """11. Normalizer output is 100% deterministic given identical input."""
        raw_m3 = {
            "meeting_id": "DETERMINISTIC_TEST",
            "action_items": [
                {"task": "Task A", "responsible_person": "SPEAKER_00", "topic_reference": 1},
                {"task": "Task B", "responsible_person": "SPEAKER_01", "topic_reference": 2},
            ],
            "key_decisions": [
                {"decision": "Decision A", "topic_reference": 1}
            ],
        }
        run1 = normalize_member3_input(raw_m3)
        run2 = normalize_member3_input(raw_m3)

        self.assertEqual(run1.model_dump(), run2.model_dump())

    def test_12_real_es2002a_member3_artifact(self):
        """12. Validate against real data/processed/ES2002a_member3_results.json."""
        m3_path = PROJECT_ROOT / "data" / "processed" / "ES2002a_member3_results.json"
        self.assertTrue(m3_path.exists(), f"Missing real artifact: {m3_path}")

        res = normalize_member3_input(m3_path)
        self.assertEqual(res.meeting_id, "ES2002a")
        self.assertEqual(res.total_action_items, 32)
        self.assertEqual(res.total_decisions, 9)
        self.assertEqual(len(res.rejected_items), 0)

        # Inspect specific known item
        item40 = [a for a in res.action_items if a.topic_reference == 40][0]
        self.assertEqual(item40.task, "Work on the actual working design of the remote control")
        self.assertEqual(item40.responsible_person, "SPEAKER_00")
        self.assertEqual(item40.deadline, "30 minutes")
        self.assertFalse(item40.is_ambiguous_deadline)
        self.assertEqual(item40.source_priority, "High")
        self.assertEqual(item40.source_confidence_score, 0.95)

    def test_13_real_es2002a_with_member2_enrichment(self):
        """13. Real ES2002a Member 3 normalized with Member 2 topic enrichment."""
        m3_path = PROJECT_ROOT / "data" / "processed" / "ES2002a_member3_results.json"
        m2_path = PROJECT_ROOT / "data" / "processed" / "ES2002a_member2_results.json"
        self.assertTrue(m3_path.exists())
        self.assertTrue(m2_path.exists())

        res = normalize_member3_input(m3_path, member2_data=m2_path)
        self.assertTrue(res.member2_context_enriched)
        self.assertEqual(res.total_action_items, 32)
        self.assertEqual(res.total_decisions, 9)

        # Topic 40 item should be resolved
        item40 = [a for a in res.action_items if a.topic_reference == 40][0]
        self.assertEqual(item40.context_status, TopicContextStatus.RESOLVED)
        self.assertIsNotNone(item40.topic_context)
        self.assertEqual(item40.topic_context.topic_id, 40)
        self.assertIn("SPEAKER_03", item40.topic_context.speakers)
        self.assertTrue(len(item40.topic_context.summary) > 0)

        # Count resolved vs unresolved
        resolved_count = sum(
            1 for a in res.action_items if a.context_status == TopicContextStatus.RESOLVED
        )
        self.assertEqual(resolved_count, 32, "All 32 items should map to existing topics.")

    def test_14_verify_no_upstream_imports(self):
        """14. Verify normalizer does not import Member 1/2/3 pipeline modules or models."""
        from backend.member4 import normalizer

        normalizer_text = Path(normalizer.__file__).read_text(encoding="utf-8")
        forbidden = [
            "whisperx",
            "pyannote",
            "transformers",
            "ollama",
            "backend.pipeline",
            "backend.speaker_aware_transcription",
            "backend.summarization",
            "backend.extraction",
            "streamlit",
        ]
        for term in forbidden:
            self.assertNotIn(
                f"import {term}",
                normalizer_text,
                f"Forbidden import found in normalizer.py: {term}",
            )


if __name__ == "__main__":
    unittest.main()
