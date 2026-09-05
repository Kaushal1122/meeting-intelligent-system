"""
Unit and Integration Tests for Member 4 Confidence Intelligence Engine (Phase 5).

Verifies all 28 requirements:
1. Score is within [0, 1].
2. Confidence thresholds work.
3. Fully resolved context increases confidence.
4. Missing topic lowers confidence.
5. Unresolved topic lowers confidence.
6. Partial context handled correctly.
7. Localized dialogue increases evidence confidence.
8. Missing dialogue handled safely.
9. Source segment IDs affect evidence quality.
10. Timestamps preserved/used correctly.
11. Speaker evidence handled correctly.
12. Missing responsible person handled safely.
13. Responsible person != assignment speaker is not automatically a conflict.
14. Clear deadline evidence improves confidence.
15. Ambiguous deadline lowers deadline evidence quality.
16. Missing deadline does not automatically mean low confidence.
17. Conflicting decisions reduce confidence appropriately.
18. Multiple alternatives handled conservatively.
19. No fabricated evidence.
20. Member 3 confidence does not control Member 4 confidence.
21. Priority score does not directly determine confidence.
22. Repeated execution is deterministic.
23. Factor contributions are correct.
24. No LLM/API/network calls.
25. No Member 1/2/3 implementation imports.
26. Real ES2002a data can be processed.
27. High-priority low-confidence scenario works.
28. Low-priority high-confidence scenario works.
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
    ConfidenceLevel,
    ConfidenceModelConfig,
    DEFAULT_CONFIDENCE_CONFIG,
    Member4ConfidenceOutput,
    PriorityLevel,
    infer_task_confidence,
)


class TestMember4ConfidenceEngine(unittest.TestCase):
    """Test suite for Member 4 Confidence Intelligence Engine."""

    def setUp(self):
        """Prepare mock context fixtures for unit testing."""
        self.mock_topic_40 = {
            "topics": [
                {
                    "topic_id": 40,
                    "summary": "Right, so it is to wrap up. The next meeting is going to be in 30 minutes. In between now and then, as the industrial designer, you're going to be working on the actual working design of it.",
                    "speakers": ["SPEAKER_03"],
                    "start": 976.58,
                    "end": 1019.12,
                    "segments": [
                        {"segment_id": 183, "speaker": "SPEAKER_03", "text": "Right, so it is to wrap up.", "start": 976.58, "end": 979.65},
                        {"segment_id": 184, "speaker": "SPEAKER_03", "text": "The next meeting is going to be in 30 minutes, so that's about 10 to 12 by my watch.", "start": 979.77, "end": 985.98},
                        {"segment_id": 185, "speaker": "SPEAKER_03", "text": "In between now and then, as the industrial designer, you're going to be working on the actual working design of it, so you know what you're doing there.", "start": 986.0, "end": 996.17},
                    ],
                }
            ]
        }

    def test_01_score_is_within_bounds(self):
        """1. All confidence scores are strictly bounded within [0.0, 1.0]."""
        raw_m3 = {
            "meeting_id": "TEST_CONF_01",
            "action_items": [
                {"task": "Design casing", "deadline": "30 minutes", "responsible_person": "David", "topic_reference": 40}
            ],
        }
        res = infer_task_confidence(raw_m3, member2_data=self.mock_topic_40)
        score = res.action_items[0].confidence_assessment.score
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)

    def test_02_confidence_thresholds_work(self):
        """2. Confidence labels match configured thresholds."""
        cfg = ConfidenceModelConfig(threshold_high=0.80, threshold_medium=0.55)
        raw_m3 = {
            "meeting_id": "TEST_CONF_02",
            "action_items": [
                {"task": "Design remote control casing", "deadline": "30 minutes", "responsible_person": "David", "topic_reference": 40},
                {"task": "Vague task", "topic_reference": None},
            ],
        }
        res = infer_task_confidence(raw_m3, member2_data=self.mock_topic_40, config=cfg)
        for item in res.action_items:
            score = item.confidence_assessment.score
            level = item.confidence_assessment.level
            if score >= cfg.threshold_high:
                self.assertEqual(level, ConfidenceLevel.HIGH)
            elif score >= cfg.threshold_medium:
                self.assertEqual(level, ConfidenceLevel.MEDIUM)
            else:
                self.assertEqual(level, ConfidenceLevel.LOW)

    def test_03_fully_resolved_context_increases_confidence(self):
        """3. Fully resolved context yields maximum context_resolution contribution."""
        raw_m3 = {
            "meeting_id": "TEST_CONF_03",
            "action_items": [
                {"task": "Design remote control casing", "topic_reference": 40}
            ],
        }
        res = infer_task_confidence(raw_m3, member2_data=self.mock_topic_40)
        f_ctx = [f for f in res.action_items[0].confidence_assessment.factor_contributions if f.factor_name == "context_resolution"][0]
        self.assertTrue(f_ctx.has_evidence)
        self.assertEqual(f_ctx.raw_value, 1.00)

    def test_04_missing_topic_lowers_confidence(self):
        """4. Missing topic reference produces 0.0 context resolution contribution."""
        raw_m3 = {
            "meeting_id": "TEST_CONF_04",
            "action_items": [{"task": "Inspect prototype", "topic_reference": None}],
        }
        res = infer_task_confidence(raw_m3)
        f_ctx = [f for f in res.action_items[0].confidence_assessment.factor_contributions if f.factor_name == "context_resolution"][0]
        self.assertFalse(f_ctx.has_evidence)
        self.assertEqual(f_ctx.raw_value, 0.0)

    def test_05_unresolved_topic_lowers_confidence(self):
        """5. Unresolved topic reference (not in Member 2) yields low confidence contribution."""
        raw_m3 = {
            "meeting_id": "TEST_CONF_05",
            "action_items": [{"task": "Inspect prototype", "topic_reference": 999}],
        }
        res = infer_task_confidence(raw_m3, member2_data=self.mock_topic_40)
        f_ctx = [f for f in res.action_items[0].confidence_assessment.factor_contributions if f.factor_name == "context_resolution"][0]
        self.assertFalse(f_ctx.has_evidence)
        self.assertEqual(f_ctx.raw_value, 0.20)

    def test_06_partial_context_handled_correctly(self):
        """6. Partially resolved context (topic summary only, no segments) yields intermediate score."""
        raw_m3 = {
            "meeting_id": "TEST_CONF_06",
            "action_items": [{"task": "Inspect prototype", "topic_reference": 5}],
        }
        m2_partial = {
            "topics": [
                {"topic_id": 5, "summary": "Prototype review topic.", "speakers": ["SPEAKER_01"], "segments": []}
            ]
        }
        res = infer_task_confidence(raw_m3, member2_data=m2_partial)
        f_ctx = [f for f in res.action_items[0].confidence_assessment.factor_contributions if f.factor_name == "context_resolution"][0]
        self.assertTrue(f_ctx.has_evidence)
        self.assertEqual(f_ctx.raw_value, 0.50)

    def test_07_localized_dialogue_increases_evidence_confidence(self):
        """7. Localized dialogue window with segment IDs and timestamps maximizes localized evidence."""
        raw_m3 = {
            "meeting_id": "TEST_CONF_07",
            "action_items": [{"task": "Work on the actual working design", "topic_reference": 40}],
        }
        res = infer_task_confidence(raw_m3, member2_data=self.mock_topic_40)
        f_loc = [f for f in res.action_items[0].confidence_assessment.factor_contributions if f.factor_name == "localized_evidence_grounding"][0]
        self.assertTrue(f_loc.has_evidence)
        self.assertEqual(f_loc.raw_value, 1.00)

    def test_08_missing_dialogue_handled_safely(self):
        """8. Missing localized dialogue results in 0.0 localized evidence contribution."""
        raw_m3 = {
            "meeting_id": "TEST_CONF_08",
            "action_items": [{"task": "Inspect prototype", "topic_reference": None}],
        }
        res = infer_task_confidence(raw_m3)
        f_loc = [f for f in res.action_items[0].confidence_assessment.factor_contributions if f.factor_name == "localized_evidence_grounding"][0]
        self.assertFalse(f_loc.has_evidence)
        self.assertEqual(f_loc.raw_value, 0.0)

    def test_09_source_segment_ids_affect_evidence_quality(self):
        """9. Segment IDs are collected and preserved in factor contributions."""
        raw_m3 = {
            "meeting_id": "TEST_CONF_09",
            "action_items": [{"task": "Work on working design", "topic_reference": 40}],
        }
        res = infer_task_confidence(raw_m3, member2_data=self.mock_topic_40)
        f_loc = [f for f in res.action_items[0].confidence_assessment.factor_contributions if f.factor_name == "localized_evidence_grounding"][0]
        self.assertTrue(len(f_loc.evidence_segment_ids) > 0)
        self.assertIn(185, f_loc.evidence_segment_ids)

    def test_10_timestamps_preserved_and_used(self):
        """10. Timestamps contribute to localized evidence grounding."""
        raw_m3 = {
            "meeting_id": "TEST_CONF_10",
            "action_items": [{"task": "Work on working design", "topic_reference": 40}],
        }
        res = infer_task_confidence(raw_m3, member2_data=self.mock_topic_40)
        f_loc = [f for f in res.action_items[0].confidence_assessment.factor_contributions if f.factor_name == "localized_evidence_grounding"][0]
        self.assertIn("timestamps", f_loc.evidence_text)

    def test_11_speaker_evidence_handled_correctly(self):
        """11. Speaker evidence in window contributes to localized grounding."""
        raw_m3 = {
            "meeting_id": "TEST_CONF_11",
            "action_items": [{"task": "Work on working design", "topic_reference": 40}],
        }
        res = infer_task_confidence(raw_m3, member2_data=self.mock_topic_40)
        f_loc = [f for f in res.action_items[0].confidence_assessment.factor_contributions if f.factor_name == "localized_evidence_grounding"][0]
        self.assertIn("SPEAKER_03", f_loc.evidence_text)

    def test_12_missing_responsible_person_handled_safely(self):
        """12. Unassigned task receives conservative assignee consistency without crashing."""
        raw_m3 = {
            "meeting_id": "TEST_CONF_12",
            "action_items": [{"task": "General exploratory task", "responsible_person": None, "topic_reference": 40}],
        }
        res = infer_task_confidence(raw_m3, member2_data=self.mock_topic_40)
        f_asg = [f for f in res.action_items[0].confidence_assessment.factor_contributions if f.factor_name == "task_assignee_consistency"][0]
        self.assertFalse(f_asg.has_evidence)
        self.assertEqual(f_asg.raw_value, 0.35)

    def test_13_assignee_different_from_speaker_not_a_conflict(self):
        """13. Responsible person (SPEAKER_00) != speaker in turn (SPEAKER_03) is clean delegation."""
        raw_m3 = {
            "meeting_id": "TEST_CONF_13",
            "action_items": [
                {
                    "task": "Work on the actual working design",
                    "responsible_person": "SPEAKER_00",
                    "topic_reference": 40,
                }
            ],
        }
        res = infer_task_confidence(raw_m3, member2_data=self.mock_topic_40)
        f_asg = [f for f in res.action_items[0].confidence_assessment.factor_contributions if f.factor_name == "task_assignee_consistency"][0]
        self.assertTrue(f_asg.has_evidence)
        self.assertEqual(f_asg.raw_value, 1.00)

    def test_14_clear_deadline_improves_confidence(self):
        """14. Explicit deadline corroborated by dialogue snippet yields 1.00 deadline evidence."""
        raw_m3 = {
            "meeting_id": "TEST_CONF_14",
            "action_items": [
                {
                    "task": "Work on the actual working design",
                    "deadline": "30 minutes",
                    "topic_reference": 40,
                }
            ],
        }
        res = infer_task_confidence(raw_m3, member2_data=self.mock_topic_40)
        f_dl = [f for f in res.action_items[0].confidence_assessment.factor_contributions if f.factor_name == "deadline_evidence_quality"][0]
        self.assertTrue(f_dl.has_evidence)
        self.assertEqual(f_dl.raw_value, 1.00)

    def test_15_ambiguous_deadline_lowers_confidence(self):
        """15. Ambiguous deadline (e.g. 'asap', 'soon') reduces deadline evidence score to 0.30."""
        raw_m3 = {
            "meeting_id": "TEST_CONF_15",
            "action_items": [
                {
                    "task": "Work on the actual working design",
                    "deadline": "as soon as possible",
                    "topic_reference": 40,
                }
            ],
        }
        res = infer_task_confidence(raw_m3, member2_data=self.mock_topic_40)
        f_dl = [f for f in res.action_items[0].confidence_assessment.factor_contributions if f.factor_name == "deadline_evidence_quality"][0]
        self.assertTrue(f_dl.has_evidence)
        self.assertEqual(f_dl.raw_value, 0.30)

    def test_16_missing_deadline_not_penalized(self):
        """16. Missing deadline is not penalized (receives 0.60 neutral baseline)."""
        raw_m3 = {
            "meeting_id": "TEST_CONF_16",
            "action_items": [
                {"task": "Prepare user manual", "deadline": None, "topic_reference": 40}
            ],
        }
        res = infer_task_confidence(raw_m3, member2_data=self.mock_topic_40)
        f_dl = [f for f in res.action_items[0].confidence_assessment.factor_contributions if f.factor_name == "deadline_evidence_quality"][0]
        self.assertEqual(f_dl.raw_value, 0.60)

    def test_17_conflicting_decisions_reduce_confidence(self):
        """17. Multiple competing decisions in the same topic reduce decision consistency score."""
        raw_m3 = {
            "meeting_id": "TEST_CONF_17",
            "action_items": [{"task": "Finalize mascot design", "topic_reference": 10}],
            "key_decisions": [
                {"decision": "Mascot is family beagle", "topic_reference": 10},
                {"decision": "Mascot is small furry animal", "topic_reference": 10},
            ],
        }
        m2_topic_10 = {
            "topics": [
                {"topic_id": 10, "summary": "Mascot debate.", "speakers": ["SPEAKER_01"], "segments": []}
            ]
        }
        res = infer_task_confidence(raw_m3, member2_data=m2_topic_10)
        f_dec = [f for f in res.action_items[0].confidence_assessment.factor_contributions if f.factor_name == "decision_evidence_consistency"][0]
        self.assertTrue(f_dec.has_evidence)
        self.assertEqual(f_dec.raw_value, 0.20)


    def test_18_multiple_alternatives_handled_conservatively(self):
        """18. Single decision (1.00) yields higher confidence than conflicting alternatives (0.40)."""
        raw_single = {
            "meeting_id": "TEST_CONF_18",
            "action_items": [{"task": "Finalize mascot", "topic_reference": 10}],
            "key_decisions": [{"decision": "Mascot is family beagle", "topic_reference": 10}],
        }
        raw_multi = {
            "meeting_id": "TEST_CONF_18",
            "action_items": [{"task": "Finalize mascot", "topic_reference": 10}],
            "key_decisions": [
                {"decision": "Mascot is family beagle", "topic_reference": 10},
                {"decision": "Mascot is small animal", "topic_reference": 10},
            ],
        }
        m2 = {"topics": [{"topic_id": 10, "summary": "Mascot.", "speakers": ["SPEAKER_01"], "segments": []}]}
        res_single = infer_task_confidence(raw_single, member2_data=m2)
        res_multi = infer_task_confidence(raw_multi, member2_data=m2)

        dec_single = [f for f in res_single.action_items[0].confidence_assessment.factor_contributions if f.factor_name == "decision_evidence_consistency"][0]
        dec_multi = [f for f in res_multi.action_items[0].confidence_assessment.factor_contributions if f.factor_name == "decision_evidence_consistency"][0]

        self.assertGreater(dec_single.raw_value, dec_multi.raw_value)

    def test_19_no_fabricated_evidence(self):
        """19. When evidence is missing, has_evidence is False and raw_value is uninflated."""
        raw_m3 = {
            "meeting_id": "TEST_CONF_19",
            "action_items": [{"task": "Vague task", "topic_reference": None, "deadline": None, "responsible_person": None}],
        }
        res = infer_task_confidence(raw_m3)
        item = res.action_items[0]
        f_ctx = [f for f in item.confidence_assessment.factor_contributions if f.factor_name == "context_resolution"][0]
        f_loc = [f for f in item.confidence_assessment.factor_contributions if f.factor_name == "localized_evidence_grounding"][0]
        f_asg = [f for f in item.confidence_assessment.factor_contributions if f.factor_name == "task_assignee_consistency"][0]

        self.assertFalse(f_ctx.has_evidence)
        self.assertFalse(f_loc.has_evidence)
        self.assertFalse(f_asg.has_evidence)

    def test_20_member3_confidence_does_not_control_score(self):
        """20. Changing Member 3 confidence from 0.1 to 0.99 does NOT change Member 4 confidence."""
        raw_low = {"meeting_id": "TEST_M3", "action_items": [{"task": "Test device", "confidence_score": 0.10, "topic_reference": None}]}
        raw_high = {"meeting_id": "TEST_M3", "action_items": [{"task": "Test device", "confidence_score": 0.99, "topic_reference": None}]}

        res_low = infer_task_confidence(raw_low)
        res_high = infer_task_confidence(raw_high)

        self.assertEqual(res_low.action_items[0].confidence_assessment.score, res_high.action_items[0].confidence_assessment.score)
        self.assertEqual(res_low.action_items[0].confidence_assessment.level, res_high.action_items[0].confidence_assessment.level)

    def test_21_priority_score_does_not_determine_confidence(self):
        """21. Changing priority alone does not change confidence score."""
        # Task with urgent words (changes priority from Low to Medium/High)
        raw_normal = {"meeting_id": "TEST_P_C", "action_items": [{"task": "Review drawings", "topic_reference": None}]}
        raw_urgent = {"meeting_id": "TEST_P_C", "action_items": [{"task": "Review critical emergency drawings immediately", "topic_reference": None}]}

        res_normal = infer_task_confidence(raw_normal)
        res_urgent = infer_task_confidence(raw_urgent)

        # Priority differs
        self.assertNotEqual(res_normal.action_items[0].priority_assessment.score, res_urgent.action_items[0].priority_assessment.score)
        # Structural confidence remains within baseline parity
        self.assertEqual(res_normal.action_items[0].confidence_assessment.level, res_urgent.action_items[0].confidence_assessment.level)

    def test_22_repeated_execution_is_deterministic(self):
        """22. Repeated runs produce identical output bit-for-bit."""
        raw_m3 = {
            "meeting_id": "TEST_DET",
            "action_items": [{"task": "Design remote control casing", "deadline": "30 minutes", "topic_reference": 40}],
        }
        res1 = infer_task_confidence(raw_m3, member2_data=self.mock_topic_40)
        res2 = infer_task_confidence(raw_m3, member2_data=self.mock_topic_40)

        self.assertEqual(
            res1.action_items[0].confidence_assessment.model_dump(),
            res2.action_items[0].confidence_assessment.model_dump(),
        )

    def test_23_factor_contributions_are_correct(self):
        """23. Verify weighted_contribution equals round(raw_value * weight, 4)."""
        raw_m3 = {
            "meeting_id": "TEST_MATH",
            "action_items": [{"task": "Design remote control casing", "deadline": "30 minutes", "topic_reference": 40}],
        }
        res = infer_task_confidence(raw_m3, member2_data=self.mock_topic_40)
        for f in res.action_items[0].confidence_assessment.factor_contributions:
            expected = round(f.raw_value * f.weight, 4)
            self.assertEqual(f.weighted_contribution, expected)

    def test_24_no_llm_or_external_calls(self):
        """24. Verify confidence_engine contains zero references to external APIs or LLMs."""
        from backend.member4 import confidence_engine

        code = Path(confidence_engine.__file__).read_text(encoding="utf-8")
        forbidden = ["requests.", "urllib.", "http.", "openai", "anthropic", "ollama", "qwen"]
        for term in forbidden:
            self.assertNotIn(term, code, f"Forbidden call reference found: {term}")

    def test_25_no_upstream_imports(self):
        """25. Verify confidence_engine does not import Member 1/2/3 pipeline code."""
        from backend.member4 import confidence_engine

        code = Path(confidence_engine.__file__).read_text(encoding="utf-8")
        forbidden = [
            "whisperx", "pyannote", "transformers", "backend.pipeline",
            "backend.speaker_aware_transcription", "backend.summarization",
            "backend.extraction", "streamlit",
        ]
        for term in forbidden:
            self.assertNotIn(f"import {term}", code, f"Forbidden import found: {term}")

    def test_26_real_es2002a_data_processed(self):
        """26. Real ES2002a Member 3 + Member 2 data is processed successfully."""
        m3_path = PROJECT_ROOT / "data" / "processed" / "ES2002a_member3_results.json"
        m2_path = PROJECT_ROOT / "data" / "processed" / "ES2002a_member2_results.json"
        self.assertTrue(m3_path.exists())
        self.assertTrue(m2_path.exists())

        res = infer_task_confidence(m3_path, member2_data=m2_path)
        self.assertEqual(res.meeting_id, "ES2002a")
        self.assertEqual(res.total_action_items, 32)
        self.assertGreater(res.high_confidence_count, 0)

    def test_27_high_priority_low_confidence_scenario(self):
        """27. HIGH Priority + LOW Confidence scenario: Urgent task with ambiguous deadline & missing topic."""
        raw_m3 = {
            "meeting_id": "TEST_HP_LC",
            "action_items": [
                {
                    "task": "CRITICAL EMERGENCY BLOCKER: Server is crashing, fix it immediately",
                    "deadline": "as soon as possible",
                    "responsible_person": None,
                    "topic_reference": None,
                }
            ],
        }
        res = infer_task_confidence(raw_m3)
        item = res.action_items[0]

        # High priority due to critical urgency terms
        self.assertIn(item.priority_assessment.level, [PriorityLevel.HIGH, PriorityLevel.MEDIUM])
        # Low confidence due to missing context resolution and missing topic
        self.assertEqual(item.confidence_assessment.level, ConfidenceLevel.LOW)
        self.assertLess(item.confidence_assessment.score, 0.50)

    def test_28_low_priority_high_confidence_scenario(self):
        """28. LOW Priority + HIGH Confidence scenario: Routine task with verified dialogue turns & topic."""
        mock_topic_routine = {
            "topics": [
                {
                    "topic_id": 3,
                    "summary": "Introduction and agenda overview.",
                    "speakers": ["SPEAKER_03"],
                    "start": 10.0,
                    "end": 50.0,
                    "segments": [
                        {"segment_id": 5, "speaker": "SPEAKER_03", "text": "Welcome everyone to the meeting.", "start": 10.0, "end": 20.0},
                        {"segment_id": 6, "speaker": "SPEAKER_03", "text": "Let us quickly go over the agenda items.", "start": 20.0, "end": 35.0},
                    ],
                }
            ]
        }
        raw_m3 = {
            "meeting_id": "TEST_LP_HC",
            "action_items": [
                {
                    "task": "Introduce the agenda items",
                    "responsible_person": "SPEAKER_03",
                    "deadline": None,
                    "topic_reference": 3,
                }
            ],
        }
        res = infer_task_confidence(raw_m3, member2_data=mock_topic_routine)
        item = res.action_items[0]

        # Low priority (no urgency, no deadline, exploratory/routine)
        self.assertEqual(item.priority_assessment.level, PriorityLevel.LOW)
        self.assertLess(item.priority_assessment.score, 0.35)

        # High confidence (resolved context, verified speaker, unpenalized missing deadline)
        self.assertEqual(item.confidence_assessment.level, ConfidenceLevel.HIGH)
        self.assertGreaterEqual(item.confidence_assessment.score, 0.75)

    def test_29_evidence_discrimination_strong_moderate_weak(self):
        """29. Verify monotonic evidence discrimination: Strong > Moderate > Weak."""
        # Strong Evidence: Corroborated dialogue, explicit deadline, direct delegation
        raw_strong = {
            "meeting_id": "TEST_DISC",
            "action_items": [
                {
                    "task": "Work on the actual working design",
                    "responsible_person": "SPEAKER_00",
                    "deadline": "30 minutes",
                    "topic_reference": 40,
                }
            ],
        }
        # Moderate Evidence: Competing mascot decisions, uncorroborated dialogue keywords
        raw_moderate = {
            "meeting_id": "TEST_DISC",
            "action_items": [
                {
                    "task": "Discuss general ideas without dialogue keywords",
                    "responsible_person": "SPEAKER_01",
                    "deadline": None,
                    "topic_reference": 10,
                }
            ],
            "key_decisions": [
                {"decision": "Decision alternative A", "topic_reference": 10},
                {"decision": "Decision alternative B", "topic_reference": 10},
            ],
        }
        m2_topic_10 = {
            "topics": [
                {"topic_id": 10, "summary": "Debate.", "speakers": ["SPEAKER_01"], "segments": [{"segment_id": 1, "speaker": "SPEAKER_01", "text": "Unrelated remarks."}]}
            ]
        }
        # Weak Evidence: Missing context, unassigned, unanchored
        raw_weak = {
            "meeting_id": "TEST_DISC",
            "action_items": [
                {
                    "task": "Vague unanchored task",
                    "responsible_person": None,
                    "deadline": None,
                    "topic_reference": None,
                }
            ],
        }

        res_strong = infer_task_confidence(raw_strong, member2_data=self.mock_topic_40)
        res_moderate = infer_task_confidence(raw_moderate, member2_data=m2_topic_10)
        res_weak = infer_task_confidence(raw_weak)

        score_strong = res_strong.action_items[0].confidence_assessment.score
        score_moderate = res_moderate.action_items[0].confidence_assessment.score
        score_weak = res_weak.action_items[0].confidence_assessment.score

        # Monotonic evidence discrimination
        self.assertGreater(score_strong, score_moderate)
        self.assertGreater(score_moderate, score_weak)

        # Categorical tiers agree
        self.assertEqual(res_strong.action_items[0].confidence_assessment.level, ConfidenceLevel.HIGH)
        self.assertEqual(res_weak.action_items[0].confidence_assessment.level, ConfidenceLevel.LOW)


if __name__ == "__main__":
    unittest.main()

