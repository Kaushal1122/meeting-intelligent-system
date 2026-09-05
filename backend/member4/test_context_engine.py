"""
Unit and Integration Tests for Member 4 Contextual Task Intelligence Engine (Phase 3).

Verifies the 17 requirements:
1. Task with resolved topic context.
2. Task with missing topic reference.
3. Task with unresolved topic reference.
4. Topic resolved but source segments unavailable (partially resolved).
5. Localized context extraction.
6. Deterministic +/-2 segment context window.
7. Context speaker preservation.
8. Context timestamp preservation where available.
9. Related decision by same topic.
10. Task with no related decision.
11. Missing/ambiguous deadline context.
12. Multiple tasks referring to the same topic.
13. Real ES2002a Member 3 + Member 2 artifacts.
14. Deterministic repeated execution.
15. Verify Member 3 priority/confidence remain source metadata.
16. Verify no upstream imports.
17. Verify no LLM/external API calls.
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
    ContextRichActionItem,
    Member4ContextOutput,
    TopicContextStatus,
    build_task_context,
    normalize_member3_input,
)


class TestMember4ContextEngine(unittest.TestCase):
    """Test suite for Member 4 Context Engine."""

    def setUp(self):
        """Prepare reusable test fixtures."""
        self.sample_topic_segments = [
            {"segment_id": 10, "speaker": "SPEAKER_03", "text": "Let's review the schedule.", "start": 100.0, "end": 105.0},
            {"segment_id": 11, "speaker": "SPEAKER_00", "text": "I will prepare the casing drawings.", "start": 105.5, "end": 112.0},
            {"segment_id": 12, "speaker": "SPEAKER_03", "text": "David, work on the actual working design of the remote control.", "start": 112.5, "end": 120.0},
            {"segment_id": 13, "speaker": "SPEAKER_01", "text": "I'll do the user interface layout.", "start": 120.5, "end": 125.0},
            {"segment_id": 14, "speaker": "SPEAKER_02", "text": "We need this in 30 minutes.", "start": 125.5, "end": 130.0},
            {"segment_id": 15, "speaker": "SPEAKER_03", "text": "Great, let's reconvene then.", "start": 130.5, "end": 135.0},
        ]
        self.sample_m2 = {
            "topics": [
                {
                    "topic_id": 40,
                    "segment_count": 6,
                    "speakers": ["SPEAKER_03", "SPEAKER_00", "SPEAKER_01", "SPEAKER_02"],
                    "start": 100.0,
                    "end": 135.0,
                    "summary": "Breakout wrap-up. The team prepares for the design sprint before the next meeting.",
                    "source_segment_ids": [10, 11, 12, 13, 14, 15],
                    "segments": self.sample_topic_segments,
                }
            ]
        }

    def test_01_task_with_resolved_topic_context(self):
        """1. Task with resolved topic context maps correctly."""
        raw_m3 = {
            "meeting_id": "TEST_CTX_01",
            "action_items": [
                {
                    "task": "Work on the actual working design of the remote control",
                    "responsible_person": "SPEAKER_00",
                    "deadline": "30 minutes",
                    "topic_reference": 40,
                    "priority": "High",
                    "confidence_score": 0.95,
                }
            ],
            "key_decisions": [],
        }
        res = build_task_context(raw_m3, member2_data=self.sample_m2)
        self.assertEqual(res.meeting_id, "TEST_CTX_01")
        self.assertEqual(res.total_action_items, 1)

        item = res.action_items[0]
        self.assertEqual(item.context_status, TopicContextStatus.RESOLVED)
        self.assertEqual(item.topic_summary, "Breakout wrap-up. The team prepares for the design sprint before the next meeting.")
        self.assertEqual(len(item.topic_speakers), 4)
        self.assertIsNotNone(item.localized_context)

    def test_02_task_with_missing_topic_reference(self):
        """2. Task with missing topic reference gets MISSING_REFERENCE status."""
        raw_m3 = {
            "meeting_id": "TEST_CTX_02",
            "action_items": [
                {"task": "Prepare general presentation", "topic_reference": None}
            ],
            "key_decisions": [],
        }
        res = build_task_context(raw_m3, member2_data=self.sample_m2)
        item = res.action_items[0]
        self.assertEqual(item.context_status, TopicContextStatus.MISSING_REFERENCE)
        self.assertIsNone(item.topic_summary)
        self.assertIsNone(item.localized_context)
        self.assertEqual(res.missing_topics_count, 1)

    def test_03_task_with_unresolved_topic_reference(self):
        """3. Task with topic reference not in Member 2 gets UNRESOLVED status."""
        raw_m3 = {
            "meeting_id": "TEST_CTX_03",
            "action_items": [
                {"task": "Fix remote control battery", "topic_reference": 999}
            ],
            "key_decisions": [],
        }
        res = build_task_context(raw_m3, member2_data=self.sample_m2)
        item = res.action_items[0]
        self.assertEqual(item.context_status, TopicContextStatus.UNRESOLVED)
        self.assertIsNone(item.topic_summary)
        self.assertIsNone(item.localized_context)
        self.assertEqual(res.unresolved_topics_count, 1)

    def test_04_topic_resolved_but_segments_unavailable(self):
        """4. Topic resolved but without segments list gets PARTIALLY_RESOLVED status."""
        raw_m3 = {
            "meeting_id": "TEST_CTX_04",
            "action_items": [
                {"task": "Discuss ergonomics", "topic_reference": 5}
            ],
            "key_decisions": [],
        }
        m2_no_segments = {
            "topics": [
                {
                    "topic_id": 5,
                    "summary": "Ergonomics discussion without segment details.",
                    "speakers": ["SPEAKER_01"],
                    "start": 50.0,
                    "end": 80.0,
                    "segments": [],  # Empty segments
                }
            ]
        }
        res = build_task_context(raw_m3, member2_data=m2_no_segments)
        item = res.action_items[0]
        self.assertEqual(item.context_status, TopicContextStatus.PARTIALLY_RESOLVED)
        self.assertEqual(item.topic_summary, "Ergonomics discussion without segment details.")
        self.assertIsNone(item.localized_context)
        self.assertEqual(res.partially_resolved_count, 1)

    def test_05_localized_context_extraction(self):
        """5. Localized context extracts verbatim dialogue and segment IDs."""
        raw_m3 = {
            "meeting_id": "TEST_CTX_05",
            "action_items": [
                {
                    "task": "Work on the actual working design of the remote control",
                    "responsible_person": "SPEAKER_00",
                    "topic_reference": 40,
                }
            ],
            "key_decisions": [],
        }
        res = build_task_context(raw_m3, member2_data=self.sample_m2)
        item = res.action_items[0]
        ctx = item.localized_context
        self.assertIsNotNone(ctx)
        self.assertIn("SPEAKER_03: David, work on the actual working design of the remote control.", ctx.window_text)
        self.assertEqual(ctx.trigger_segment_id, 12)

    def test_06_deterministic_plus_minus_2_window(self):
        """6. Context window deterministically selects triggering turn +/- 2 turns."""
        raw_m3 = {
            "meeting_id": "TEST_CTX_06",
            "action_items": [
                {
                    "task": "Work on the actual working design of the remote control",
                    "topic_reference": 40,
                }
            ],
            "key_decisions": [],
        }
        res = build_task_context(raw_m3, member2_data=self.sample_m2)
        ctx = res.action_items[0].localized_context
        # Trigger segment is index 2 (seg 12).
        # Expected window: indices [0, 1, 2, 3, 4] -> segment IDs [10, 11, 12, 13, 14]
        expected_ids = [10, 11, 12, 13, 14]
        self.assertEqual(ctx.segment_ids, expected_ids)
        self.assertEqual(len(ctx.segment_ids), 5)

    def test_07_context_speaker_preservation(self):
        """7. Speakers present in the localized window are preserved."""
        raw_m3 = {
            "meeting_id": "TEST_CTX_07",
            "action_items": [
                {"task": "Work on the actual working design", "topic_reference": 40}
            ],
            "key_decisions": [],
        }
        res = build_task_context(raw_m3, member2_data=self.sample_m2)
        ctx = res.action_items[0].localized_context
        expected_speakers = ["SPEAKER_03", "SPEAKER_00", "SPEAKER_01", "SPEAKER_02"]
        for spk in expected_speakers:
            self.assertIn(spk, ctx.speakers)

    def test_08_context_timestamp_preservation(self):
        """8. Timestamps are preserved from the earliest and latest segment in the window."""
        raw_m3 = {
            "meeting_id": "TEST_CTX_08",
            "action_items": [
                {"task": "Work on the actual working design", "topic_reference": 40}
            ],
            "key_decisions": [],
        }
        res = build_task_context(raw_m3, member2_data=self.sample_m2)
        item = res.action_items[0]
        # First segment (10) starts at 100.0, segment 14 ends at 130.0
        self.assertEqual(item.context_start, 100.0)
        self.assertEqual(item.context_end, 130.0)

    def test_09_related_decision_by_same_topic(self):
        """9. Decision established in the same topic is attached as related decision."""
        raw_m3 = {
            "meeting_id": "TEST_CTX_09",
            "action_items": [
                {"task": "Implement casing", "topic_reference": 40}
            ],
            "key_decisions": [
                {"decision": "Use plastic double-molded remote shell", "topic_reference": 40}
            ],
        }
        res = build_task_context(raw_m3, member2_data=self.sample_m2)
        item = res.action_items[0]
        self.assertEqual(len(item.related_decisions), 1)
        rel_dec = item.related_decisions[0]
        self.assertEqual(rel_dec.decision, "Use plastic double-molded remote shell")
        self.assertEqual(rel_dec.topic_reference, 40)
        self.assertEqual(res.items_with_related_decisions, 1)

    def test_10_task_with_no_related_decision(self):
        """10. Task with no matching decision has empty related_decisions list."""
        raw_m3 = {
            "meeting_id": "TEST_CTX_10",
            "action_items": [
                {"task": "Prepare schedule", "topic_reference": 40}
            ],
            "key_decisions": [
                {"decision": "Decision in different topic", "topic_reference": 99}
            ],
        }
        res = build_task_context(raw_m3, member2_data=self.sample_m2)
        item = res.action_items[0]
        self.assertEqual(item.related_decisions, [])

    def test_11_missing_and_ambiguous_deadline_context(self):
        """11. Missing and ambiguous deadlines preserved with contextual snippet."""
        raw_m3 = {
            "meeting_id": "TEST_CTX_11",
            "action_items": [
                {
                    "task": "Work on the actual working design",
                    "deadline": "30 minutes",
                    "topic_reference": 40,
                },
                {
                    "task": "Review documentation",
                    "deadline": "as soon as possible",
                    "topic_reference": 40,
                },
                {
                    "task": "Clean up prototype board",
                    "deadline": None,
                    "topic_reference": 40,
                },
            ],
            "key_decisions": [],
        }
        res = build_task_context(raw_m3, member2_data=self.sample_m2)
        item1 = res.action_items[0]
        self.assertEqual(item1.deadline, "30 minutes")
        self.assertFalse(item1.is_ambiguous_deadline)
        self.assertIsNotNone(item1.deadline_context_snippet)
        self.assertIn("30 minutes", item1.deadline_context_snippet)

        item2 = res.action_items[1]
        self.assertEqual(item2.deadline, "as soon as possible")
        self.assertTrue(item2.is_ambiguous_deadline)

        item3 = res.action_items[2]
        self.assertIsNone(item3.deadline)
        self.assertIsNone(item3.deadline_context_snippet)

    def test_12_multiple_tasks_referring_to_same_topic(self):
        """12. Multiple tasks in the same topic are each contextualized independently."""
        raw_m3 = {
            "meeting_id": "TEST_CTX_12",
            "action_items": [
                {"task": "Work on working design of remote", "responsible_person": "SPEAKER_00", "topic_reference": 40},
                {"task": "Do the user interface layout", "responsible_person": "SPEAKER_01", "topic_reference": 40},
            ],
            "key_decisions": [],
        }
        res = build_task_context(raw_m3, member2_data=self.sample_m2)
        self.assertEqual(len(res.action_items), 2)

        item1 = res.action_items[0]
        item2 = res.action_items[1]
        self.assertEqual(item1.context_status, TopicContextStatus.RESOLVED)
        self.assertEqual(item2.context_status, TopicContextStatus.RESOLVED)

        # Task 1 triggers on seg 12 (working design)
        self.assertEqual(item1.localized_context.trigger_segment_id, 12)
        # Task 2 triggers on seg 13 (user interface layout)
        self.assertEqual(item2.localized_context.trigger_segment_id, 13)

    def test_13_real_es2002a_artifacts(self):
        """13. Validate against real ES2002a Member 3 and Member 2 processed artifacts."""
        m3_path = PROJECT_ROOT / "data" / "processed" / "ES2002a_member3_results.json"
        m2_path = PROJECT_ROOT / "data" / "processed" / "ES2002a_member2_results.json"
        self.assertTrue(m3_path.exists())
        self.assertTrue(m2_path.exists())

        res = build_task_context(m3_path, member2_data=m2_path)
        self.assertEqual(res.meeting_id, "ES2002a")
        self.assertEqual(res.total_action_items, 32)
        self.assertEqual(res.total_decisions, 9)
        self.assertEqual(res.resolved_topics_count, 32)
        self.assertEqual(res.items_with_localized_context, 32)

        # Inspect item 40 (working design)
        item40 = [a for a in res.action_items if a.topic_reference == 40][0]
        self.assertEqual(item40.context_status, TopicContextStatus.RESOLVED)
        self.assertIsNotNone(item40.localized_context)
        self.assertIn("SPEAKER_03", item40.localized_context.speakers)
        self.assertIn("working on the actual working design", item40.localized_context.window_text)
        self.assertIsNotNone(item40.deadline_context_snippet)
        self.assertIn("30 minutes", item40.deadline_context_snippet)

        # Inspect Topic 10 items (which should have related decisions!)
        items_topic_10 = [a for a in res.action_items if a.topic_reference == 10]
        self.assertTrue(len(items_topic_10) > 0)
        self.assertTrue(len(items_topic_10[0].related_decisions) > 0)

    def test_14_deterministic_repeated_execution(self):
        """14. Repeated executions yield identical output bit-for-bit."""
        m3_path = PROJECT_ROOT / "data" / "processed" / "ES2002a_member3_results.json"
        m2_path = PROJECT_ROOT / "data" / "processed" / "ES2002a_member2_results.json"

        run1 = build_task_context(m3_path, member2_data=m2_path)
        run2 = build_task_context(m3_path, member2_data=m2_path)

        self.assertEqual(run1.model_dump(), run2.model_dump())

    def test_15_source_priority_confidence_remain_metadata(self):
        """15. Member 3 priority and confidence are strictly preserved as source metadata."""
        m3_path = PROJECT_ROOT / "data" / "processed" / "ES2002a_member3_results.json"
        res = build_task_context(m3_path)
        item0 = res.action_items[0]
        self.assertEqual(item0.source_priority, "Normal")
        self.assertEqual(item0.source_confidence_score, 0.9)
        # Ensure no new priority score or confidence score fields were calculated on ContextRichActionItem
        self.assertFalse(hasattr(item0, "priority_score"))
        self.assertFalse(hasattr(item0, "overall_confidence"))

    def test_16_verify_no_upstream_imports(self):
        """16. Verify context_engine does not import Member 1/2/3 pipeline code."""
        from backend.member4 import context_engine

        engine_text = Path(context_engine.__file__).read_text(encoding="utf-8")
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
                engine_text,
                f"Forbidden import found in context_engine.py: {term}",
            )

    def test_17_verify_no_llm_or_external_calls(self):
        """17. Verify context_engine does not use network or LLM libraries."""
        from backend.member4 import context_engine

        engine_text = Path(context_engine.__file__).read_text(encoding="utf-8")
        forbidden_calls = ["requests.", "http.", "urllib.", "socket.", "openai", "anthropic", "qwen"]
        for term in forbidden_calls:
            self.assertNotIn(
                term,
                engine_text,
                f"Forbidden network/LLM call reference found: {term}",
            )


if __name__ == "__main__":
    unittest.main()
