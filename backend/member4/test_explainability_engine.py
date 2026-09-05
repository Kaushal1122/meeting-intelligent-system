"""
Unit Tests for Phase 7: Explainability Engine (Member 4).

Verifies deterministic, read-only multi-factor explainability trails,
mathematical contribution consistency, evidence traceability without fabrication,
factor ranking with tie-breaking, and zero decision drift.
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
    EvidenceReference,
    ExplainedActionItem,
    ExplanationFactor,
    Member4ExplainedOutput,
    PriorityLevel,
    ReviewReasonCode,
    ReviewStatus,
    explain_action_item,
    explain_confidence,
    explain_meeting_triage,
    explain_priority,
    explain_review,
    extract_evidence_traces,
    rank_explanation_factors,
    triage_action_items,
)


class TestMember4ExplainabilityEngine(unittest.TestCase):
    """Test suite for Member 4 Explainability Engine."""

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

    def test_01_strong_evidence_complete_explanation(self):
        """1. Strong evidence produces a complete, robust explainability trail."""
        raw_m3 = {
            "meeting_id": "TEST_01",
            "action_items": [
                {
                    "task": "Work on the actual working design of the remote control",
                    "responsible_person": "SPEAKER_00",
                    "deadline": "30 minutes",
                    "topic_reference": 40,
                }
            ],
        }
        res = explain_meeting_triage(raw_m3, member2_data=self.mock_topic_40)
        item = res.action_items[0]

        self.assertIsNotNone(item.explanation)
        exp = item.explanation
        self.assertEqual(exp.priority_explanation.level, PriorityLevel.HIGH)
        self.assertEqual(exp.confidence_explanation.level, ConfidenceLevel.HIGH)
        self.assertEqual(exp.review_explanation.status, ReviewStatus.AUTO_ACCEPT)
        self.assertGreater(len(exp.priority_explanation.top_contributors), 0)
        self.assertGreater(len(exp.confidence_explanation.supporting_evidence), 0)
        self.assertIn("Priority is HIGH", exp.unified_explanation)
        self.assertIn("Confidence is HIGH", exp.unified_explanation)

    def test_02_weak_evidence_produces_limiting_evidence(self):
        """2. Weak evidence produces explicit limiting-evidence entries."""
        raw_m3 = {
            "meeting_id": "TEST_02",
            "action_items": [
                {
                    "task": "Vague task without context",
                    "responsible_person": None,
                    "deadline": None,
                    "topic_reference": None,
                }
            ],
        }
        res = explain_meeting_triage(raw_m3)
        item = res.action_items[0]
        c_exp = item.explanation.confidence_explanation

        self.assertEqual(c_exp.level, ConfidenceLevel.LOW)
        self.assertGreater(len(c_exp.limiting_evidence), 0)
        self.assertTrue(
            any("No localized dialogue" in lim or "No topic reference" in lim for lim in c_exp.limiting_evidence)
        )

    def test_03_priority_explanation_uses_actual_phase4_values(self):
        """3. Priority explanation factors and contributions match Phase 4 exactly."""
        raw_m3 = {
            "meeting_id": "TEST_03",
            "action_items": [
                {
                    "task": "Work on the actual working design of the remote control",
                    "responsible_person": "SPEAKER_00",
                    "deadline": "30 minutes",
                    "topic_reference": 40,
                }
            ],
        }
        res = explain_meeting_triage(raw_m3, member2_data=self.mock_topic_40)
        item = res.action_items[0]

        p_orig = item.priority_assessment
        p_exp = item.explanation.priority_explanation

        self.assertEqual(p_exp.score, p_orig.score)
        self.assertEqual(p_exp.level, p_orig.level)
        orig_map = {f.factor_name: f.weighted_contribution for f in p_orig.factor_contributions}
        exp_map = {f.factor_name: f.weighted_contribution for f in p_exp.factors}
        self.assertEqual(orig_map, exp_map)

    def test_04_confidence_explanation_uses_actual_phase5_values(self):
        """4. Confidence explanation factors and contributions match Phase 5 exactly."""
        raw_m3 = {
            "meeting_id": "TEST_04",
            "action_items": [
                {
                    "task": "Work on the actual working design of the remote control",
                    "responsible_person": "SPEAKER_00",
                    "deadline": "30 minutes",
                    "topic_reference": 40,
                }
            ],
        }
        res = explain_meeting_triage(raw_m3, member2_data=self.mock_topic_40)
        item = res.action_items[0]

        c_orig = item.confidence_assessment
        c_exp = item.explanation.confidence_explanation

        self.assertEqual(c_exp.score, c_orig.score)
        self.assertEqual(c_exp.level, c_orig.level)
        orig_map = {f.factor_name: f.weighted_contribution for f in c_orig.factor_contributions}
        exp_map = {f.factor_name: f.weighted_contribution for f in c_exp.factors}
        self.assertEqual(orig_map, exp_map)

    def test_05_review_explanation_uses_actual_phase6_reason_codes(self):
        """5. Review explanation matches Phase 6 review decision and reason codes."""
        raw_m3 = {
            "meeting_id": "TEST_05",
            "action_items": [
                {
                    "task": "Discuss mascot options",
                    "responsible_person": "SPEAKER_01",
                    "topic_reference": 10,
                }
            ],
            "key_decisions": [
                {"decision": "Mascot A", "topic_reference": 10},
                {"decision": "Mascot B", "topic_reference": 10},
            ],
        }
        m2 = {"topics": [{"topic_id": 10, "summary": "Mascot", "speakers": ["SPEAKER_01"], "segments": []}]}
        res = explain_meeting_triage(raw_m3, member2_data=m2)
        item = res.action_items[0]

        r_orig = item.review_decision
        r_exp = item.explanation.review_explanation

        self.assertEqual(r_exp.status, r_orig.status)
        self.assertEqual(r_exp.reason_codes, r_orig.reason_codes)
        self.assertIn(ReviewReasonCode.CONFLICTING_DECISIONS, r_exp.reason_codes)

    def test_06_factor_contribution_calculations_are_consistent(self):
        """6. Sum of factor contributions equals total score within 1e-4 tolerance."""
        raw_m3 = {
            "meeting_id": "TEST_06",
            "action_items": [
                {
                    "task": "Work on the actual working design of the remote control",
                    "responsible_person": "SPEAKER_00",
                    "deadline": "30 minutes",
                    "topic_reference": 40,
                }
            ],
        }
        res = explain_meeting_triage(raw_m3, member2_data=self.mock_topic_40)
        item = res.action_items[0]

        p_exp = item.explanation.priority_explanation
        p_sum = sum(f.weighted_contribution for f in p_exp.factors)
        self.assertAlmostEqual(p_sum, p_exp.score, places=4)

        c_exp = item.explanation.confidence_explanation
        c_sum = sum(f.weighted_contribution for f in c_exp.factors)
        self.assertAlmostEqual(c_sum, c_exp.score, places=4)

    def test_07_factor_ranking_is_deterministic(self):
        """7. Factors are deterministically sorted by contribution descending."""
        factors = [
            ExplanationFactor(factor_name="b_factor", raw_value=0.5, weight=0.1, weighted_contribution=0.05, interpretation="B"),
            ExplanationFactor(factor_name="a_factor", raw_value=0.8, weight=0.2, weighted_contribution=0.16, interpretation="A"),
            ExplanationFactor(factor_name="c_factor", raw_value=0.1, weight=0.1, weighted_contribution=0.01, interpretation="C"),
        ]
        ranked = rank_explanation_factors(factors)
        self.assertEqual(ranked[0].factor_name, "a_factor")
        self.assertEqual(ranked[1].factor_name, "b_factor")
        self.assertEqual(ranked[2].factor_name, "c_factor")

    def test_08_equal_contribution_tie_breaking_is_deterministic(self):
        """8. Equal contributions break ties via factor_name ascending (alphabetical)."""
        factors = [
            ExplanationFactor(factor_name="zeta_factor", raw_value=1.0, weight=0.1, weighted_contribution=0.10, interpretation="Z"),
            ExplanationFactor(factor_name="alpha_factor", raw_value=1.0, weight=0.1, weighted_contribution=0.10, interpretation="A"),
            ExplanationFactor(factor_name="beta_factor", raw_value=1.0, weight=0.1, weighted_contribution=0.10, interpretation="B"),
        ]
        ranked = rank_explanation_factors(factors)
        names = [f.factor_name for f in ranked]
        self.assertEqual(names, ["alpha_factor", "beta_factor", "zeta_factor"])

    def test_09_evidence_references_point_to_existing_artifacts(self):
        """9. Evidence traces accurately cite real topic ID, segment ID, and deadline."""
        raw_m3 = {
            "meeting_id": "TEST_09",
            "action_items": [
                {
                    "task": "Work on the actual working design of the remote control",
                    "responsible_person": "SPEAKER_00",
                    "deadline": "30 minutes",
                    "topic_reference": 40,
                }
            ],
        }
        res = explain_meeting_triage(raw_m3, member2_data=self.mock_topic_40)
        item = res.action_items[0]

        traces = item.explanation.evidence_traces
        types = [t.source_type for t in traces]

        self.assertIn("topic", types)
        self.assertIn("transcript_segment", types)
        self.assertIn("deadline", types)

        topic_trace = next(t for t in traces if t.source_type == "topic")
        self.assertEqual(topic_trace.source_id, 40)

        seg_trace = next(t for t in traces if t.source_type == "transcript_segment")
        self.assertEqual(seg_trace.source_id, 183)

    def test_10_no_fabricated_speaker_names(self):
        """10. Speakers remain exact source IDs (e.g. SPEAKER_03); zero fabricated names."""
        raw_m3 = {
            "meeting_id": "TEST_10",
            "action_items": [
                {
                    "task": "Work on the actual working design of the remote control",
                    "responsible_person": "SPEAKER_00",
                    "deadline": "30 minutes",
                    "topic_reference": 40,
                }
            ],
        }
        res = explain_meeting_triage(raw_m3, member2_data=self.mock_topic_40)
        item = res.action_items[0]

        for trace in item.explanation.evidence_traces:
            if trace.speaker:
                self.assertIn(trace.speaker, ["SPEAKER_00", "SPEAKER_03"])
                self.assertNotIn("David", trace.speaker)
                self.assertNotIn("Alice", trace.speaker)

    def test_11_no_fabricated_transcript_text(self):
        """11. Transcript excerpts in evidence traces are verbatim substrings from context."""
        raw_m3 = {
            "meeting_id": "TEST_11",
            "action_items": [
                {
                    "task": "Work on the actual working design of the remote control",
                    "responsible_person": "SPEAKER_00",
                    "deadline": "30 minutes",
                    "topic_reference": 40,
                }
            ],
        }
        res = explain_meeting_triage(raw_m3, member2_data=self.mock_topic_40)
        item = res.action_items[0]

        seg_trace = next(t for t in item.explanation.evidence_traces if t.source_type == "transcript_segment")
        self.assertIn(seg_trace.text_excerpt[:30], item.localized_context.window_text)

    def test_12_no_llm_or_external_api_calls(self):
        """12. Verify explainability_engine contains zero references to external APIs or LLMs."""
        engine_path = PROJECT_ROOT / "backend" / "member4" / "explainability_engine.py"
        with open(engine_path, "r", encoding="utf-8") as f:
            code = f.read()

        prohibited = [
            "openai", "anthropic", "requests.post", "requests.get",
            "urllib.request", "http.client", "ollama", "boto3", "socket"
        ]
        for term in prohibited:
            self.assertNotIn(term, code, f"Prohibited external client '{term}' found in explainability_engine.py!")

    def test_13_no_upstream_imports(self):
        """13. Verify explainability_engine does not import Member 1/2/3 pipeline code."""
        engine_path = PROJECT_ROOT / "backend" / "member4" / "explainability_engine.py"
        with open(engine_path, "r", encoding="utf-8") as f:
            code = f.read()

        prohibited = [
            "backend.transcribe", "backend.speaker_aware_transcription",
            "backend.preprocessing", "backend.summarization",
            "backend.extraction", "backend.pipeline"
        ]
        for term in prohibited:
            self.assertNotIn(term, code, f"Prohibited upstream import '{term}' found in explainability_engine.py!")

    def test_14_repeated_execution_identical_output(self):
        """14. Repeated execution yields bit-for-bit identical explainability payload."""
        raw_m3 = {
            "meeting_id": "TEST_14",
            "action_items": [
                {
                    "task": "Work on the actual working design of the remote control",
                    "responsible_person": "SPEAKER_00",
                    "deadline": "30 minutes",
                    "topic_reference": 40,
                }
            ],
        }
        res1 = explain_meeting_triage(raw_m3, member2_data=self.mock_topic_40)
        res2 = explain_meeting_triage(raw_m3, member2_data=self.mock_topic_40)

        self.assertEqual(res1.model_dump(), res2.model_dump())

    def test_15_explainability_does_not_change_priority(self):
        """15. Pre-explanation priority matches post-explanation priority bit-for-bit."""
        raw_m3 = {
            "meeting_id": "TEST_15",
            "action_items": [
                {
                    "task": "Work on the actual working design of the remote control",
                    "responsible_person": "SPEAKER_00",
                    "deadline": "30 minutes",
                    "topic_reference": 40,
                }
            ],
        }
        triage_res = triage_action_items(raw_m3, member2_data=self.mock_topic_40)
        orig_score = triage_res.action_items[0].priority_assessment.score
        orig_level = triage_res.action_items[0].priority_assessment.level

        explained_res = explain_meeting_triage(triage_res)
        new_score = explained_res.action_items[0].priority_assessment.score
        new_level = explained_res.action_items[0].priority_assessment.level

        self.assertEqual(orig_score, new_score)
        self.assertEqual(orig_level, new_level)

    def test_16_explainability_does_not_change_confidence(self):
        """16. Pre-explanation confidence matches post-explanation confidence bit-for-bit."""
        raw_m3 = {
            "meeting_id": "TEST_16",
            "action_items": [
                {
                    "task": "Work on the actual working design of the remote control",
                    "responsible_person": "SPEAKER_00",
                    "deadline": "30 minutes",
                    "topic_reference": 40,
                }
            ],
        }
        triage_res = triage_action_items(raw_m3, member2_data=self.mock_topic_40)
        orig_score = triage_res.action_items[0].confidence_assessment.score
        orig_level = triage_res.action_items[0].confidence_assessment.level

        explained_res = explain_meeting_triage(triage_res)
        new_score = explained_res.action_items[0].confidence_assessment.score
        new_level = explained_res.action_items[0].confidence_assessment.level

        self.assertEqual(orig_score, new_score)
        self.assertEqual(orig_level, new_level)

    def test_17_explainability_does_not_change_review_status(self):
        """17. Pre-explanation review status matches post-explanation review status."""
        raw_m3 = {
            "meeting_id": "TEST_17",
            "action_items": [
                {
                    "task": "Work on the actual working design of the remote control",
                    "responsible_person": "SPEAKER_00",
                    "deadline": "30 minutes",
                    "topic_reference": 40,
                }
            ],
        }
        triage_res = triage_action_items(raw_m3, member2_data=self.mock_topic_40)
        orig_status = triage_res.action_items[0].review_decision.status

        explained_res = explain_meeting_triage(triage_res)
        new_status = explained_res.action_items[0].review_decision.status

        self.assertEqual(orig_status, new_status)

    def test_18_explainability_does_not_change_review_reason_codes(self):
        """18. Pre-explanation reason codes match post-explanation reason codes."""
        raw_m3 = {
            "meeting_id": "TEST_18",
            "action_items": [
                {
                    "task": "Discuss mascot options",
                    "responsible_person": "SPEAKER_01",
                    "topic_reference": 10,
                }
            ],
            "key_decisions": [
                {"decision": "Mascot A", "topic_reference": 10},
                {"decision": "Mascot B", "topic_reference": 10},
            ],
        }
        m2 = {"topics": [{"topic_id": 10, "summary": "Mascot", "speakers": ["SPEAKER_01"], "segments": []}]}
        triage_res = triage_action_items(raw_m3, member2_data=m2)
        orig_codes = triage_res.action_items[0].review_decision.reason_codes

        explained_res = explain_meeting_triage(triage_res)
        new_codes = explained_res.action_items[0].review_decision.reason_codes

        self.assertEqual(orig_codes, new_codes)

    def test_19_missing_optional_evidence_not_labeled_negative(self):
        """19. Missing optional evidence (e.g. no deadline on routine task) is not labeled negative."""
        raw_m3 = {
            "meeting_id": "TEST_19",
            "action_items": [
                {
                    "task": "Introduce team members",
                    "responsible_person": "SPEAKER_03",
                    "deadline": None,
                    "topic_reference": 40,
                }
            ],
        }
        res = explain_meeting_triage(raw_m3, member2_data=self.mock_topic_40)
        item = res.action_items[0]
        c_exp = item.explanation.confidence_explanation

        # Check limiting evidence does not treat missing deadline as failure
        self.assertFalse(any("negative" in lim.lower() for lim in c_exp.limiting_evidence))

    def test_20_pydantic_schema_validation(self):
        """20. Complete output conforms to Member4ExplainedOutput schema."""
        raw_m3 = {
            "meeting_id": "TEST_20",
            "action_items": [
                {
                    "task": "Work on the actual working design of the remote control",
                    "responsible_person": "SPEAKER_00",
                    "deadline": "30 minutes",
                    "topic_reference": 40,
                }
            ],
        }
        res = explain_meeting_triage(raw_m3, member2_data=self.mock_topic_40)

        self.assertIsInstance(res, Member4ExplainedOutput)
        self.assertIsInstance(res.action_items[0], ExplainedActionItem)
        self.assertIsInstance(res.action_items[0].explanation.evidence_traces[0], EvidenceReference)

    def test_21_real_es2002a_data_processed_through_phase7(self):
        """21. Real ES2002a Member 3 + Member 2 data processed end-to-end through Phase 7."""
        m3_path = PROJECT_ROOT / "data" / "processed" / "ES2002a_member3_results.json"
        m2_path = PROJECT_ROOT / "data" / "processed" / "ES2002a_member2_results.json"

        res = explain_meeting_triage(m3_path, member2_data=m2_path)

        self.assertEqual(res.meeting_id, "ES2002a")
        self.assertEqual(res.total_action_items, 32)
        self.assertEqual(res.explained_action_items_count, 32)
        for item in res.action_items:
            self.assertIsNotNone(item.explanation)
            self.assertIsNotNone(item.explanation.priority_explanation)
            self.assertIsNotNone(item.explanation.confidence_explanation)
            self.assertIsNotNone(item.explanation.review_explanation)


if __name__ == "__main__":
    unittest.main()
