"""
Unit and Integration Tests for Member 4 Priority Intelligence Engine (Phase 4).

Verifies all 26 requirements:
1. Imminent deadline increases priority.
2. Distant deadline contributes less than imminent deadline.
3. Missing deadline does not create a fake deadline.
4. Ambiguous deadline is handled conservatively.
5. Explicit urgency evidence increases priority.
6. Ordinary non-urgent language does not falsely create urgency.
7. Explicit assignment evidence is recognized.
8. Responsible person is not confused with assignment speaker.
9. Dependency/blocker evidence affects priority.
10. No dependency is invented when evidence is absent.
11. Related decision linkage is handled conservatively.
12. Same-topic decisions are not automatically assumed to be supporting.
13. Task specificity is deterministic.
14. Missing context is handled safely.
15. Score stays within defined bounds.
16. Labels match configured thresholds.
17. Factor contributions are deterministic.
18. Contribution calculation is correct.
19. Changing context can change priority for the same task.
20. Member 3 source priority does not control Member 4 score.
21. Repeated execution produces identical results.
22. No LLM/external API calls are made.
23. No imports from Member 1/2/3 implementation modules.
24. Real ES2002a data can be processed.
25. Topic 40 receives a priority consistent with evidence (HIGH).
26. No hardcoded Topic 40/task-specific rule exists in code.
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
    DEFAULT_CONFIG,
    Member4PriorityOutput,
    PriorityLevel,
    PriorityModelConfig,
    build_task_context,
    infer_task_priorities,
)


class TestMember4PriorityEngine(unittest.TestCase):
    """Comprehensive test suite for Member 4 Priority Intelligence Engine."""

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

    def test_01_imminent_deadline_increases_priority(self):
        """1. Imminent deadline (e.g. 30 minutes) increases deadline_urgency factor."""
        raw_m3 = {
            "meeting_id": "TEST_PRIO_01",
            "action_items": [
                {"task": "Prepare working drawings", "deadline": "30 minutes", "topic_reference": 40}
            ],
            "key_decisions": [],
        }
        res = infer_task_priorities(raw_m3, member2_data=self.mock_topic_40)
        item = res.action_items[0]
        dl_contrib = [f for f in item.priority_assessment.factor_contributions if f.factor_name == "deadline_urgency"][0]
        self.assertTrue(dl_contrib.has_evidence)
        self.assertGreaterEqual(dl_contrib.raw_value, 0.90)

    def test_02_distant_deadline_contributes_less(self):
        """2. Distant deadline (e.g. next month) contributes less than imminent deadline."""
        raw_imminent = {
            "meeting_id": "TEST_PRIO_02",
            "action_items": [{"task": "Review drawings", "deadline": "30 minutes", "topic_reference": 40}],
        }
        raw_distant = {
            "meeting_id": "TEST_PRIO_02",
            "action_items": [{"task": "Review drawings", "deadline": "next month", "topic_reference": 40}],
        }
        res_imm = infer_task_priorities(raw_imminent, member2_data=self.mock_topic_40)
        res_dist = infer_task_priorities(raw_distant, member2_data=self.mock_topic_40)

        imm_dl = [f for f in res_imm.action_items[0].priority_assessment.factor_contributions if f.factor_name == "deadline_urgency"][0]
        dist_dl = [f for f in res_dist.action_items[0].priority_assessment.factor_contributions if f.factor_name == "deadline_urgency"][0]

        self.assertGreater(imm_dl.raw_value, dist_dl.raw_value)
        self.assertGreater(res_imm.action_items[0].priority_assessment.score, res_dist.action_items[0].priority_assessment.score)

    def test_03_missing_deadline_does_not_create_fake_deadline(self):
        """3. Missing deadline does not create fake deadline and has 0.0 contribution."""
        raw_m3 = {
            "meeting_id": "TEST_PRIO_03",
            "action_items": [{"task": "Review drawings", "deadline": None, "topic_reference": 40}],
        }
        res = infer_task_priorities(raw_m3, member2_data=self.mock_topic_40)
        dl_contrib = [f for f in res.action_items[0].priority_assessment.factor_contributions if f.factor_name == "deadline_urgency"][0]
        self.assertFalse(dl_contrib.has_evidence)
        self.assertEqual(dl_contrib.raw_value, 0.0)
        self.assertEqual(dl_contrib.weighted_contribution, 0.0)

    def test_04_ambiguous_deadline_handled_conservatively(self):
        """4. Ambiguous deadline (e.g. 'asap' or 'soon') is handled conservatively (<= 0.40)."""
        raw_m3 = {
            "meeting_id": "TEST_PRIO_04",
            "action_items": [{"task": "Review drawings", "deadline": "as soon as possible", "topic_reference": 40}],
        }
        res = infer_task_priorities(raw_m3, member2_data=self.mock_topic_40)
        dl_contrib = [f for f in res.action_items[0].priority_assessment.factor_contributions if f.factor_name == "deadline_urgency"][0]
        self.assertTrue(dl_contrib.has_evidence)
        self.assertLessEqual(dl_contrib.raw_value, 0.40)

    def test_05_explicit_urgency_evidence_increases_priority(self):
        """5. Explicit critical urgency terminology (e.g. 'critical', 'emergency') increases score."""
        raw_urgent = {
            "meeting_id": "TEST_PRIO_05",
            "action_items": [{"task": "Fix critical emergency battery failure", "topic_reference": 40}],
        }
        raw_normal = {
            "meeting_id": "TEST_PRIO_05",
            "action_items": [{"task": "Inspect battery options", "topic_reference": 40}],
        }
        res_urg = infer_task_priorities(raw_urgent, member2_data=self.mock_topic_40)
        res_norm = infer_task_priorities(raw_normal, member2_data=self.mock_topic_40)

        urg_f = [f for f in res_urg.action_items[0].priority_assessment.factor_contributions if f.factor_name == "explicit_urgency_language"][0]
        norm_f = [f for f in res_norm.action_items[0].priority_assessment.factor_contributions if f.factor_name == "explicit_urgency_language"][0]

        self.assertTrue(urg_f.has_evidence)
        self.assertGreater(urg_f.raw_value, norm_f.raw_value)

    def test_06_ordinary_language_does_not_falsely_create_urgency(self):
        """6. Ordinary verbs (discuss, work, look, design) do not trigger explicit urgency."""
        raw_m3 = {
            "meeting_id": "TEST_PRIO_06",
            "action_items": [{"task": "Discuss the look and feel of the device", "topic_reference": None}],
        }
        res = infer_task_priorities(raw_m3)
        urg_f = [f for f in res.action_items[0].priority_assessment.factor_contributions if f.factor_name == "explicit_urgency_language"][0]
        self.assertFalse(urg_f.has_evidence)
        self.assertEqual(urg_f.raw_value, 0.0)

    def test_07_explicit_assignment_evidence_recognized(self):
        """7. Direct second-person assignment in dialogue turns is recognized."""
        raw_m3 = {
            "meeting_id": "TEST_PRIO_07",
            "action_items": [
                {
                    "task": "Work on the actual working design",
                    "responsible_person": "David",
                    "topic_reference": 40,
                }
            ],
        }
        res = infer_task_priorities(raw_m3, member2_data=self.mock_topic_40)
        item = res.action_items[0]
        assign_f = [f for f in item.priority_assessment.factor_contributions if f.factor_name == "assignment_explicitness"][0]
        self.assertTrue(assign_f.has_evidence)
        self.assertGreaterEqual(assign_f.raw_value, 0.80)

    def test_08_responsible_person_not_confused_with_assignment_speaker(self):
        """8. Responsible person (David) and assigning speaker (SPEAKER_03) are kept distinct."""
        raw_m3 = {
            "meeting_id": "TEST_PRIO_08",
            "action_items": [
                {
                    "task": "Work on the actual working design",
                    "responsible_person": "SPEAKER_00",
                    "topic_reference": 40,
                }
            ],
        }
        res = infer_task_priorities(raw_m3, member2_data=self.mock_topic_40)
        item = res.action_items[0]
        # In topic 40, dialogue window has SPEAKER_03 speaking, while responsible_person is SPEAKER_00
        self.assertEqual(item.responsible_person, "SPEAKER_00")
        self.assertIn("SPEAKER_03", item.localized_context.speakers)

    def test_09_dependency_blocker_evidence_affects_priority(self):
        """9. Sequential milestone or blocker phrasing increases dependency_blocker factor."""
        raw_blocker = {
            "meeting_id": "TEST_PRIO_09",
            "action_items": [
                {"task": "Prepare circuit board prerequisite before we can start assembly", "topic_reference": 40}
            ],
        }
        res = infer_task_priorities(raw_blocker, member2_data=self.mock_topic_40)
        dep_f = [f for f in res.action_items[0].priority_assessment.factor_contributions if f.factor_name == "dependency_blocker"][0]
        self.assertTrue(dep_f.has_evidence)
        self.assertGreater(dep_f.raw_value, 0.50)

    def test_10_no_dependency_invented_when_absent(self):
        """10. No dependency is inferred merely because task shares a topic."""
        raw_independent = {
            "meeting_id": "TEST_PRIO_10",
            "action_items": [
                {"task": "Browse color palette options", "topic_reference": None}
            ],
        }
        res = infer_task_priorities(raw_independent)
        dep_f = [f for f in res.action_items[0].priority_assessment.factor_contributions if f.factor_name == "dependency_blocker"][0]
        self.assertFalse(dep_f.has_evidence)
        self.assertEqual(dep_f.raw_value, 0.0)

    def test_11_related_decision_linkage_handled_conservatively(self):
        """11. Single related decision provides modest positive contribution."""
        raw_m3 = {
            "meeting_id": "TEST_PRIO_11",
            "action_items": [{"task": "Implement chosen casing", "topic_reference": 40}],
            "key_decisions": [{"decision": "Agreed to use curved plastic casing", "topic_reference": 40}],
        }
        res = infer_task_priorities(raw_m3, member2_data=self.mock_topic_40)
        dec_f = [f for f in res.action_items[0].priority_assessment.factor_contributions if f.factor_name == "decision_linkage"][0]
        self.assertTrue(dec_f.has_evidence)
        self.assertEqual(dec_f.raw_value, 0.40)

    def test_12_contradictory_same_topic_decisions_not_blindly_supportive(self):
        """12. Multiple decisions (e.g. 3 competing alternatives) are treated conservatively."""
        raw_m3 = {
            "meeting_id": "TEST_PRIO_12",
            "action_items": [{"task": "Finalize mascot", "topic_reference": 10}],
            "key_decisions": [
                {"decision": "Mascot should be family beagle cutout", "topic_reference": 10},
                {"decision": "Mascot should be small furry animal", "topic_reference": 10},
                {"decision": "Mascot should be plant leaf", "topic_reference": 10},
            ],
        }
        m2_topic_10 = {
            "topics": [
                {
                    "topic_id": 10,
                    "summary": "Discussion of mascot alternatives.",
                    "speakers": ["SPEAKER_01"],
                    "segments": [{"segment_id": 1, "speaker": "SPEAKER_01", "text": "What about a beagle or a leaf?"}],
                }
            ]
        }
        res = infer_task_priorities(raw_m3, member2_data=m2_topic_10)
        dec_f = [f for f in res.action_items[0].priority_assessment.factor_contributions if f.factor_name == "decision_linkage"][0]
        # Multiple alternatives must NOT inflate score above single clear decision
        self.assertLessEqual(dec_f.raw_value, 0.20)
        self.assertIn("Multiple same-topic decisions", dec_f.evidence_text)

    def test_13_task_specificity_is_deterministic(self):
        """13. Concrete deliverable yields higher specificity than vague task."""
        raw_spec = {"meeting_id": "TEST_SPEC", "action_items": [{"task": "Create circuit board CAD specification"}]}
        raw_vague = {"meeting_id": "TEST_SPEC", "action_items": [{"task": "Discuss general ideas"}]}

        res_spec = infer_task_priorities(raw_spec)
        res_vague = infer_task_priorities(raw_vague)

        spec_f = [f for f in res_spec.action_items[0].priority_assessment.factor_contributions if f.factor_name == "deliverable_specificity"][0]
        vague_f = [f for f in res_vague.action_items[0].priority_assessment.factor_contributions if f.factor_name == "deliverable_specificity"][0]

        self.assertGreater(spec_f.raw_value, vague_f.raw_value)

    def test_14_missing_context_handled_safely(self):
        """14. Tasks with missing context receive low score without crashing."""
        raw_m3 = {
            "meeting_id": "TEST_MISSING",
            "action_items": [{"task": "Vague unanchored task", "topic_reference": None, "deadline": None, "responsible_person": None}],
        }
        res = infer_task_priorities(raw_m3)
        item = res.action_items[0]
        self.assertEqual(item.priority_assessment.level, PriorityLevel.LOW)
        self.assertLess(item.priority_assessment.score, 0.35)

    def test_15_score_stays_within_defined_bounds(self):
        """15. All continuous priority scores are strictly bounded within [0.0, 1.0]."""
        raw_max = {
            "meeting_id": "TEST_BOUNDS",
            "action_items": [
                {"task": "URGENT critical emergency blocker wiring design specification", "deadline": "immediately in 10 minutes", "responsible_person": "David", "topic_reference": 40}
            ],
        }
        res = infer_task_priorities(raw_max, member2_data=self.mock_topic_40)
        score = res.action_items[0].priority_assessment.score
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)

    def test_16_labels_match_configured_thresholds(self):
        """16. Priority labels strictly match configured thresholds."""
        cfg = PriorityModelConfig(threshold_high=0.70, threshold_medium=0.40)
        raw_m3 = {
            "meeting_id": "TEST_THRESH",
            "action_items": [
                {"task": "Work on the actual working design", "deadline": "30 minutes", "topic_reference": 40},
                {"task": "Discuss general ideas", "topic_reference": None},
            ],
        }
        res = infer_task_priorities(raw_m3, member2_data=self.mock_topic_40, config=cfg)
        for item in res.action_items:
            score = item.priority_assessment.score
            level = item.priority_assessment.level
            if score >= cfg.threshold_high:
                self.assertEqual(level, PriorityLevel.HIGH)
            elif score >= cfg.threshold_medium:
                self.assertEqual(level, PriorityLevel.MEDIUM)
            else:
                self.assertEqual(level, PriorityLevel.LOW)

    def test_17_factor_contributions_are_deterministic(self):
        """17. Factor contributions are identical across two independent runs."""
        raw_m3 = {
            "meeting_id": "TEST_DET",
            "action_items": [{"task": "Work on the actual working design", "deadline": "30 minutes", "topic_reference": 40}],
        }
        res1 = infer_task_priorities(raw_m3, member2_data=self.mock_topic_40)
        res2 = infer_task_priorities(raw_m3, member2_data=self.mock_topic_40)
        self.assertEqual(
            res1.action_items[0].priority_assessment.model_dump(),
            res2.action_items[0].priority_assessment.model_dump(),
        )

    def test_18_contribution_calculation_is_correct(self):
        """18. Verify weighted_contribution equals round(raw_value * weight, 4)."""
        raw_m3 = {
            "meeting_id": "TEST_MATH",
            "action_items": [{"task": "Work on working design", "deadline": "30 minutes", "topic_reference": 40}],
        }
        res = infer_task_priorities(raw_m3, member2_data=self.mock_topic_40)
        for f in res.action_items[0].priority_assessment.factor_contributions:
            expected = round(f.raw_value * f.weight, 4)
            self.assertEqual(f.weighted_contribution, expected)

    def test_19_changing_context_changes_priority_for_same_task(self):
        """19. Same task text receives different priority when surrounding context changes."""
        same_task = "Finalize the design specification"

        # Context A: Imminent deadline, direct assignment, resolved topic
        raw_a = {"meeting_id": "CTX_A", "action_items": [{"task": same_task, "deadline": "30 minutes", "responsible_person": "David", "topic_reference": 40}]}
        res_a = infer_task_priorities(raw_a, member2_data=self.mock_topic_40)

        # Context B: Missing context, no deadline, unassigned
        raw_b = {"meeting_id": "CTX_B", "action_items": [{"task": same_task, "deadline": None, "responsible_person": None, "topic_reference": None}]}
        res_b = infer_task_priorities(raw_b)

        self.assertGreater(res_a.action_items[0].priority_assessment.score, res_b.action_items[0].priority_assessment.score)
        self.assertEqual(res_a.action_items[0].priority_assessment.level, PriorityLevel.HIGH)
        self.assertEqual(res_b.action_items[0].priority_assessment.level, PriorityLevel.LOW)

    def test_20_member3_priority_does_not_control_score(self):
        """20. Changing Member 3's source priority from Low to High does NOT change Member 4's score."""
        raw_low = {"meeting_id": "TEST_M3", "action_items": [{"task": "Test device", "priority": "Low", "topic_reference": None}]}
        raw_high = {"meeting_id": "TEST_M3", "action_items": [{"task": "Test device", "priority": "High", "topic_reference": None}]}

        res_low = infer_task_priorities(raw_low)
        res_high = infer_task_priorities(raw_high)

        self.assertEqual(res_low.action_items[0].priority_assessment.score, res_high.action_items[0].priority_assessment.score)
        self.assertEqual(res_low.action_items[0].priority_assessment.level, res_high.action_items[0].priority_assessment.level)

    def test_21_repeated_execution_identical_results(self):
        """21. Repeated executions against production artifacts produce bit-for-bit identical output."""
        m3_path = PROJECT_ROOT / "data" / "processed" / "ES2002a_member3_results.json"
        m2_path = PROJECT_ROOT / "data" / "processed" / "ES2002a_member2_results.json"

        run1 = infer_task_priorities(m3_path, member2_data=m2_path)
        run2 = infer_task_priorities(m3_path, member2_data=m2_path)

        self.assertEqual(run1.model_dump(), run2.model_dump())

    def test_22_no_llm_or_external_api_calls(self):
        """22. Verify priority_engine contains zero references to external APIs or LLM clients."""
        from backend.member4 import priority_engine

        code = Path(priority_engine.__file__).read_text(encoding="utf-8")
        forbidden = ["requests.", "urllib.", "http.", "openai", "anthropic", "ollama", "qwen"]
        for term in forbidden:
            self.assertNotIn(term, code, f"Forbidden call reference found: {term}")

    def test_23_no_imports_from_upstream_modules(self):
        """23. Verify priority_engine does not import Member 1/2/3 pipeline code."""
        from backend.member4 import priority_engine

        code = Path(priority_engine.__file__).read_text(encoding="utf-8")
        forbidden = [
            "whisperx", "pyannote", "transformers", "backend.pipeline",
            "backend.speaker_aware_transcription", "backend.summarization",
            "backend.extraction", "streamlit",
        ]
        for term in forbidden:
            self.assertNotIn(f"import {term}", code, f"Forbidden import found: {term}")

    def test_24_real_es2002a_data_processed(self):
        """24. Real ES2002a Member 3 + Member 2 data is processed successfully."""
        m3_path = PROJECT_ROOT / "data" / "processed" / "ES2002a_member3_results.json"
        m2_path = PROJECT_ROOT / "data" / "processed" / "ES2002a_member2_results.json"
        self.assertTrue(m3_path.exists())
        self.assertTrue(m2_path.exists())

        res = infer_task_priorities(m3_path, member2_data=m2_path)
        self.assertEqual(res.meeting_id, "ES2002a")
        self.assertEqual(res.total_action_items, 32)
        self.assertGreater(res.high_priority_count, 0)
        self.assertGreater(res.medium_priority_count, 0)
        self.assertGreater(res.low_priority_count, 0)

    def test_25_topic_40_receives_high_priority_from_evidence(self):
        """25. Topic 40 working design task receives HIGH priority based on evidence."""
        m3_path = PROJECT_ROOT / "data" / "processed" / "ES2002a_member3_results.json"
        m2_path = PROJECT_ROOT / "data" / "processed" / "ES2002a_member2_results.json"

        res = infer_task_priorities(m3_path, member2_data=m2_path)
        item40 = [a for a in res.action_items if a.topic_reference == 40][0]

        self.assertEqual(item40.priority_assessment.level, PriorityLevel.HIGH)
        self.assertGreaterEqual(item40.priority_assessment.score, 0.65)

    def test_26_no_hardcoded_topic_40_rule(self):
        """26. Verify no hardcoded 'topic_id == 40' or 'actual working design' rule exists in priority_engine."""
        from backend.member4 import priority_engine

        code = Path(priority_engine.__file__).read_text(encoding="utf-8")
        self.assertNotIn("== 40", code, "Hardcoded topic ID 40 equality check found in priority_engine.py!")
        self.assertNotIn("topic_id == 40", code, "Hardcoded topic ID 40 found in priority_engine.py!")
        self.assertNotIn("topic_reference == 40", code, "Hardcoded topic_reference == 40 found in priority_engine.py!")
        self.assertNotIn("actual working design of the remote control", code, "Hardcoded task string found in priority_engine.py!")



if __name__ == "__main__":
    unittest.main()
