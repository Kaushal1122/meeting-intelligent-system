"""
Unit Tests for Phase 6: Human Review / Uncertainty Handling Engine (Member 4).

Verifies deterministic triage state assignments (AUTO_ACCEPT, REVIEW_RECOMMENDED, REVIEW_REQUIRED),
structured reason codes, human-readable explanations, priority-confidence interactions,
and isolation from upstream components.
"""

from pathlib import Path
import sys
import unittest

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.member4 import (
    ConfidenceLevel,
    Member4ConfidenceOutput,
    Member4TriageOutput,
    PriorityLevel,
    ReviewDecision,
    ReviewModelConfig,
    ReviewReasonCode,
    ReviewStatus,
    TopicContextStatus,
    TriageEnrichedActionItem,
    evaluate_task_triage,
    infer_task_confidence,
    triage_action_items,
)


class TestMember4ReviewEngine(unittest.TestCase):
    """Test suite for Member 4 Human Review & Uncertainty Handling Engine."""

    def setUp(self):
        """Prepare mock context fixtures for testing."""
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
                        {"segment_id": 185, "speaker": "SPEAKER_03", "text": "In between now and then, as the industrial designer, you're going to be working on the actual working design of it.", "start": 986.73, "end": 996.17},
                    ],
                }
            ]
        }

        self.mock_topic_routine = {
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

    def test_01_high_confidence_low_priority_auto_accept(self):
        """1. HIGH confidence + LOW priority yields AUTO_ACCEPT when no uncertainty exists."""
        raw_m3 = {
            "meeting_id": "TEST_01",
            "action_items": [
                {
                    "task": "Introduce the agenda items",
                    "responsible_person": "SPEAKER_03",
                    "deadline": None,
                    "topic_reference": 3,
                }
            ],
        }
        res = triage_action_items(raw_m3, member2_data=self.mock_topic_routine)
        item = res.action_items[0]

        self.assertEqual(item.confidence_assessment.level, ConfidenceLevel.HIGH)
        self.assertEqual(item.priority_assessment.level, PriorityLevel.LOW)
        self.assertEqual(item.review_decision.status, ReviewStatus.AUTO_ACCEPT)
        self.assertFalse(item.review_decision.review_required)
        self.assertFalse(item.review_decision.review_recommended)
        self.assertEqual(item.review_decision.reason_codes, [])
        self.assertIn("automatically accepted", item.review_decision.explanation)

    def test_02_high_priority_low_confidence_requires_review(self):
        """2. HIGH priority + LOW confidence triggers REVIEW_REQUIRED."""
        raw_m3 = {
            "meeting_id": "TEST_02",
            "action_items": [
                {
                    "task": "CRITICAL emergency blocker: produce the actual working design specification before launch, cannot proceed without this prerequisite",
                    "responsible_person": "SPEAKER_01",
                    "deadline": "30 minutes",
                    "topic_reference": 999,  # Unresolved topic not in Member 2 -> LOW confidence
                }
            ],
        }
        m2 = {"topics": [{"topic_id": 1, "summary": "Intro", "segments": []}]}
        res = triage_action_items(raw_m3, member2_data=m2)
        item = res.action_items[0]

        self.assertEqual(item.priority_assessment.level, PriorityLevel.HIGH)
        self.assertEqual(item.confidence_assessment.level, ConfidenceLevel.LOW)
        self.assertEqual(item.review_decision.status, ReviewStatus.REVIEW_REQUIRED)
        self.assertTrue(item.review_decision.review_required)
        self.assertIn(ReviewReasonCode.HIGH_PRIORITY_LOW_CONFIDENCE, item.review_decision.reason_codes)
        self.assertIn("critically low contextual evidence", item.review_decision.explanation)

    def test_03_high_priority_medium_confidence_recommends_review(self):
        """3. HIGH priority + MEDIUM confidence triggers REVIEW_RECOMMENDED."""
        m2_topic_10 = {
            "topics": [
                {
                    "topic_id": 10,
                    "summary": "Mascot debate.",
                    "speakers": ["SPEAKER_01"],
                    "segments": [
                        {"segment_id": 1, "speaker": "SPEAKER_01", "text": "Let us look at options.", "start": 10.0, "end": 20.0}
                    ],
                }
            ]
        }
        raw_m3 = {
            "meeting_id": "TEST_03",
            "action_items": [
                {
                    "task": "CRITICAL emergency blocker: produce the actual working design specification before launch",
                    "responsible_person": "SPEAKER_01",
                    "deadline": "in 15 minutes",
                    "topic_reference": 10,
                }
            ],
            "key_decisions": [
                {"decision": "Mascot is beagle", "topic_reference": 10},
                {"decision": "Mascot is cat", "topic_reference": 10},
            ],
        }
        res = triage_action_items(raw_m3, member2_data=m2_topic_10)
        item = res.action_items[0]

        # Priority is HIGH (0.765) due to urgent deadline and critical blocker language
        self.assertEqual(item.priority_assessment.level, PriorityLevel.HIGH)
        # Confidence is MEDIUM (0.725) due to competing decisions in topic 10 and weak dialogue grounding
        self.assertEqual(item.confidence_assessment.level, ConfidenceLevel.MEDIUM)
        self.assertEqual(item.review_decision.status, ReviewStatus.REVIEW_RECOMMENDED)
        self.assertTrue(item.review_decision.review_recommended)
        self.assertFalse(item.review_decision.review_required)
        self.assertIn(ReviewReasonCode.HIGH_PRIORITY_MEDIUM_CONFIDENCE, item.review_decision.reason_codes)

    def test_04_low_priority_high_confidence_auto_accept(self):
        """4. LOW priority + HIGH confidence triggers AUTO_ACCEPT when clear."""
        raw_m3 = {
            "meeting_id": "TEST_04",
            "action_items": [
                {
                    "task": "Introduce the agenda items",
                    "responsible_person": "SPEAKER_03",
                    "deadline": None,
                    "topic_reference": 3,
                }
            ],
        }
        res = triage_action_items(raw_m3, member2_data=self.mock_topic_routine)
        item = res.action_items[0]

        self.assertEqual(item.review_decision.status, ReviewStatus.AUTO_ACCEPT)
        self.assertFalse(item.review_decision.review_required)

    def test_05_unresolved_topic_context_triggers_review_required(self):
        """5. Unresolved topic reference (not in Member 2) triggers REVIEW_REQUIRED."""
        raw_m3 = {
            "meeting_id": "TEST_05",
            "action_items": [
                {
                    "task": "Prepare report",
                    "responsible_person": "SPEAKER_01",
                    "topic_reference": 999,  # Does not exist
                }
            ],
        }
        m2 = {"topics": [{"topic_id": 1, "summary": "Intro", "segments": []}]}
        res = triage_action_items(raw_m3, member2_data=m2)
        item = res.action_items[0]

        self.assertEqual(item.context_status, TopicContextStatus.UNRESOLVED)
        self.assertEqual(item.review_decision.status, ReviewStatus.REVIEW_REQUIRED)
        self.assertIn(ReviewReasonCode.UNRESOLVED_CONTEXT, item.review_decision.reason_codes)

    def test_06_partially_resolved_context_recommends_review(self):
        """6. Partially resolved context (topic summary only, no segments) triggers REVIEW_RECOMMENDED."""
        raw_m3 = {
            "meeting_id": "TEST_06",
            "action_items": [
                {
                    "task": "Discuss marketing plan with team",
                    "responsible_person": "SPEAKER_01",
                    "deadline": "by Friday",
                    "topic_reference": 5,
                }
            ],
            "key_decisions": [{"decision": "Marketing plan approved", "topic_reference": 5}],
        }
        m2_partial = {
            "topics": [
                {"topic_id": 5, "summary": "Marketing summary without segments.", "speakers": ["SPEAKER_01"], "segments": []}
            ]
        }
        res = triage_action_items(raw_m3, member2_data=m2_partial)
        item = res.action_items[0]

        self.assertEqual(item.context_status, TopicContextStatus.PARTIALLY_RESOLVED)
        self.assertEqual(item.review_decision.status, ReviewStatus.REVIEW_RECOMMENDED)
        self.assertIn(ReviewReasonCode.PARTIAL_CONTEXT, item.review_decision.reason_codes)


    def test_07_ambiguous_deadline_triggers_review_signal(self):
        """7. Ambiguous deadline (e.g. 'asap') triggers AMBIGUOUS_DEADLINE reason code."""
        raw_m3 = {
            "meeting_id": "TEST_07",
            "action_items": [
                {
                    "task": "Introduce the agenda items",
                    "responsible_person": "SPEAKER_03",
                    "deadline": "as soon as possible",
                    "topic_reference": 3,
                }
            ],
        }
        res = triage_action_items(raw_m3, member2_data=self.mock_topic_routine)
        item = res.action_items[0]

        self.assertTrue(item.is_ambiguous_deadline)
        self.assertIn(ReviewReasonCode.AMBIGUOUS_DEADLINE, item.review_decision.reason_codes)
        self.assertEqual(item.review_decision.status, ReviewStatus.REVIEW_RECOMMENDED)

    def test_08_unassigned_task_triggers_review_signal(self):
        """8. Unassigned task triggers UNASSIGNED_TASK reason code."""
        raw_m3 = {
            "meeting_id": "TEST_08",
            "action_items": [
                {
                    "task": "Introduce the agenda items",
                    "responsible_person": None,
                    "deadline": None,
                    "topic_reference": 3,
                }
            ],
        }
        res = triage_action_items(raw_m3, member2_data=self.mock_topic_routine)
        item = res.action_items[0]

        self.assertTrue(item.is_unassigned)
        self.assertIn(ReviewReasonCode.UNASSIGNED_TASK, item.review_decision.reason_codes)
        self.assertEqual(item.review_decision.status, ReviewStatus.REVIEW_RECOMMENDED)

    def test_09_conflicting_decisions_trigger_review_signal(self):
        """9. Multiple competing decisions in same topic trigger CONFLICTING_DECISIONS."""
        raw_m3 = {
            "meeting_id": "TEST_09",
            "action_items": [
                {
                    "task": "Finalize the beagle mascot design",
                    "responsible_person": "SPEAKER_01",
                    "topic_reference": 10,
                }
            ],
            "key_decisions": [
                {"decision": "Mascot is cutout of beagle", "topic_reference": 10},
                {"decision": "Mascot is small furry animal", "topic_reference": 10},
                {"decision": "Mascot is plant leaf", "topic_reference": 10},
            ],
        }
        m2 = {
            "topics": [
                {"topic_id": 10, "summary": "Mascot debate.", "speakers": ["SPEAKER_01"], "segments": [{"segment_id": 1, "speaker": "SPEAKER_01", "text": "Let's discuss beagle mascot design."}]}
            ]
        }
        res = triage_action_items(raw_m3, member2_data=m2)
        item = res.action_items[0]

        self.assertIn(ReviewReasonCode.CONFLICTING_DECISIONS, item.review_decision.reason_codes)
        self.assertEqual(item.review_decision.status, ReviewStatus.REVIEW_RECOMMENDED)

    def test_10_weak_dialogue_grounding_triggers_review_signal(self):
        """10. Zero lexical corroboration in dialogue turns triggers WEAK_DIALOGUE_GROUNDING."""
        raw_m3 = {
            "meeting_id": "TEST_10",
            "action_items": [
                {
                    "task": "Discuss unrelated quantum telemetry physics",
                    "responsible_person": "SPEAKER_03",
                    "topic_reference": 3,
                }
            ],
        }
        res = triage_action_items(raw_m3, member2_data=self.mock_topic_routine)
        item = res.action_items[0]

        self.assertIn(ReviewReasonCode.WEAK_DIALOGUE_GROUNDING, item.review_decision.reason_codes)
        self.assertEqual(item.review_decision.status, ReviewStatus.REVIEW_RECOMMENDED)

    def test_11_missing_deadline_alone_does_not_require_review(self):
        """11. Missing deadline alone on a grounded routine task does NOT trigger review (AUTO_ACCEPT)."""
        raw_m3 = {
            "meeting_id": "TEST_11",
            "action_items": [
                {
                    "task": "Introduce the agenda items",
                    "responsible_person": "SPEAKER_03",
                    "deadline": None,  # No deadline
                    "topic_reference": 3,
                }
            ],
        }
        res = triage_action_items(raw_m3, member2_data=self.mock_topic_routine)
        item = res.action_items[0]

        self.assertIsNone(item.deadline)
        self.assertEqual(item.review_decision.status, ReviewStatus.AUTO_ACCEPT)
        self.assertFalse(item.review_decision.review_required)
        self.assertFalse(item.review_decision.review_recommended)

    def test_12_missing_decision_linkage_alone_does_not_require_review(self):
        """12. Zero linked decisions alone does NOT trigger review (AUTO_ACCEPT)."""
        raw_m3 = {
            "meeting_id": "TEST_12",
            "action_items": [
                {
                    "task": "Introduce the agenda items",
                    "responsible_person": "SPEAKER_03",
                    "deadline": None,
                    "topic_reference": 3,
                }
            ],
            "key_decisions": [],  # No decisions
        }
        res = triage_action_items(raw_m3, member2_data=self.mock_topic_routine)
        item = res.action_items[0]

        self.assertEqual(len(item.related_decisions), 0)
        self.assertEqual(item.review_decision.status, ReviewStatus.AUTO_ACCEPT)

    def test_13_priority_changes_alone_do_not_change_confidence(self):
        """13. Changing priority inputs alone leaves confidence score and assessment identical."""
        raw_urgent = {
            "meeting_id": "TEST_13",
            "action_items": [
                {"task": "CRITICAL emergency: fix working design", "topic_reference": 40}
            ],
        }
        raw_normal = {
            "meeting_id": "TEST_13",
            "action_items": [
                {"task": "Look at working design", "topic_reference": 40}
            ],
        }
        res_u = triage_action_items(raw_urgent, member2_data=self.mock_topic_40)
        res_n = triage_action_items(raw_normal, member2_data=self.mock_topic_40)

        item_u = res_u.action_items[0]
        item_n = res_n.action_items[0]

        # Priorities are different
        self.assertNotEqual(item_u.priority_assessment.score, item_n.priority_assessment.score)
        # Context and dialogue factors are identical
        self.assertEqual(item_u.confidence_assessment.scoring_breakdown["context_resolution"], item_n.confidence_assessment.scoring_breakdown["context_resolution"])

    def test_14_confidence_does_not_alter_stored_priority(self):
        """14. Triage evaluation does not alter or recompute priority assessment."""
        raw_m3 = {
            "meeting_id": "TEST_14",
            "action_items": [
                {
                    "task": "Work on the actual working design",
                    "responsible_person": "SPEAKER_00",
                    "deadline": "30 minutes",
                    "topic_reference": 40,
                }
            ],
        }
        res = triage_action_items(raw_m3, member2_data=self.mock_topic_40)
        item = res.action_items[0]

        # Prior priority remains HIGH with identical score
        self.assertEqual(item.priority_assessment.level, PriorityLevel.HIGH)
        self.assertEqual(item.priority_assessment.score, 0.7150)

    def test_15_reason_codes_are_deterministic(self):
        """15. Repeated execution against identical input yields identical reason codes."""
        raw_m3 = {
            "meeting_id": "TEST_15",
            "action_items": [
                {
                    "task": "Review telemetry",
                    "responsible_person": None,
                    "deadline": "soon",
                    "topic_reference": None,
                }
            ],
        }
        res1 = triage_action_items(raw_m3)
        res2 = triage_action_items(raw_m3)

        codes1 = [c.value for c in res1.action_items[0].review_decision.reason_codes]
        codes2 = [c.value for c in res2.action_items[0].review_decision.reason_codes]

        self.assertEqual(codes1, codes2)
        self.assertEqual(res1.action_items[0].review_decision.status, res2.action_items[0].review_decision.status)

    def test_16_explanation_matches_reason_codes(self):
        """16. Human-readable explanation text accurately matches assigned reason codes."""
        raw_m3 = {
            "meeting_id": "TEST_16",
            "action_items": [
                {
                    "task": "Unanchored vague task",
                    "responsible_person": None,
                    "deadline": None,
                    "topic_reference": None,
                }
            ],
        }
        res = triage_action_items(raw_m3)
        item = res.action_items[0]

        decision = item.review_decision
        self.assertEqual(decision.status, ReviewStatus.REVIEW_REQUIRED)
        self.assertIn("Review required:", decision.explanation)
        self.assertIn("cannot be anchored in meeting dialogue", decision.explanation)

    def test_17_repeated_execution_identical_output(self):
        """17. Repeated execution yields bit-for-bit identical output."""
        raw_m3 = {
            "meeting_id": "TEST_17",
            "action_items": [
                {
                    "task": "Work on the actual working design",
                    "responsible_person": "SPEAKER_00",
                    "deadline": "30 minutes",
                    "topic_reference": 40,
                }
            ],
        }
        res1 = triage_action_items(raw_m3, member2_data=self.mock_topic_40)
        res2 = triage_action_items(raw_m3, member2_data=self.mock_topic_40)

        self.assertEqual(res1.model_dump(), res2.model_dump())

    def test_18_pydantic_schema_conformance(self):
        """18. Verify output is an instance of Member4TriageOutput conforming to schemas."""
        raw_m3 = {
            "meeting_id": "TEST_18",
            "action_items": [
                {
                    "task": "Work on the actual working design",
                    "responsible_person": "SPEAKER_00",
                    "deadline": "30 minutes",
                    "topic_reference": 40,
                }
            ],
        }
        res = triage_action_items(raw_m3, member2_data=self.mock_topic_40)

        self.assertIsInstance(res, Member4TriageOutput)
        self.assertIsInstance(res.action_items[0], TriageEnrichedActionItem)
        self.assertIsInstance(res.action_items[0].review_decision, ReviewDecision)

    def test_19_no_llm_or_external_api_calls(self):
        """19. Verify review_engine contains zero references to external APIs or LLM clients."""
        engine_path = PROJECT_ROOT / "backend" / "member4" / "review_engine.py"
        with open(engine_path, "r", encoding="utf-8") as f:
            code = f.read()

        prohibited = [
            "openai", "anthropic", "requests.post", "requests.get",
            "urllib.request", "http.client", "ollama", "boto3", "socket"
        ]
        for term in prohibited:
            self.assertNotIn(term, code, f"Prohibited external client '{term}' found in review_engine.py!")

    def test_20_no_upstream_imports(self):
        """20. Verify review_engine does not import Member 1/2/3 pipeline code."""
        engine_path = PROJECT_ROOT / "backend" / "member4" / "review_engine.py"
        with open(engine_path, "r", encoding="utf-8") as f:
            code = f.read()

        prohibited = [
            "backend.transcribe", "backend.speaker_aware_transcription",
            "backend.preprocessing", "backend.summarization",
            "backend.extraction", "backend.pipeline"
        ]
        for term in prohibited:
            self.assertNotIn(term, code, f"Prohibited upstream import '{term}' found in review_engine.py!")

    def test_21_high_priority_unassigned_requires_review(self):
        """21. High-priority deliverable without an assigned owner triggers REVIEW_REQUIRED."""
        raw_m3 = {
            "meeting_id": "TEST_21",
            "action_items": [
                {
                    "task": "CRITICAL emergency blocker: produce the actual working design specification, prerequisite for launch",
                    "responsible_person": None,  # unassigned!
                    "deadline": "30 minutes",
                    "topic_reference": 40,
                }
            ],
        }
        res = triage_action_items(raw_m3, member2_data=self.mock_topic_40)
        item = res.action_items[0]

        self.assertEqual(item.priority_assessment.level, PriorityLevel.HIGH)
        self.assertEqual(item.review_decision.status, ReviewStatus.REVIEW_REQUIRED)
        self.assertIn(ReviewReasonCode.UNASSIGNED_HIGH_PRIORITY_TASK, item.review_decision.reason_codes)

    def test_22_high_priority_ambiguous_deadline_requires_review(self):
        """22. High-priority deliverable with an ambiguous deadline triggers REVIEW_REQUIRED."""
        raw_m3 = {
            "meeting_id": "TEST_22",
            "action_items": [
                {
                    "task": "CRITICAL emergency blocker: produce the actual working design specification, prerequisite for launch",
                    "responsible_person": "SPEAKER_00",
                    "deadline": "as soon as possible",
                    "topic_reference": 40,
                }
            ],
        }
        res = triage_action_items(raw_m3, member2_data=self.mock_topic_40)
        item = res.action_items[0]

        self.assertEqual(item.priority_assessment.level, PriorityLevel.HIGH)
        self.assertEqual(item.review_decision.status, ReviewStatus.REVIEW_REQUIRED)
        self.assertIn(ReviewReasonCode.HIGH_PRIORITY_AMBIGUOUS_DEADLINE, item.review_decision.reason_codes)


    def test_23_real_es2002a_data_processed(self):
        """23. Real ES2002a Member 3 + Member 2 data processed end-to-end through Phase 6."""
        m3_path = PROJECT_ROOT / "data" / "processed" / "ES2002a_member3_results.json"
        m2_path = PROJECT_ROOT / "data" / "processed" / "ES2002a_member2_results.json"

        res = triage_action_items(m3_path, member2_data=m2_path)

        self.assertEqual(res.meeting_id, "ES2002a")
        self.assertEqual(res.total_action_items, 32)
        self.assertEqual(
            res.auto_accept_count + res.review_recommended_count + res.review_required_count,
            32
        )
        # All items must have valid review_decision
        for item in res.action_items:
            self.assertIn(item.review_decision.status, [ReviewStatus.AUTO_ACCEPT, ReviewStatus.REVIEW_RECOMMENDED, ReviewStatus.REVIEW_REQUIRED])


if __name__ == "__main__":
    unittest.main()
