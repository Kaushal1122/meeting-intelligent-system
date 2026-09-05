"""
Unit Tests for Phase 8: Personalization Engine (Member 4).

Verifies role-based presentation transformations (MANAGER, DEVELOPER, INTERN, DEFAULT),
strict canonical result preservation, deterministic ordering and filtering,
and evidence immutability without decision drift.
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
    PersonalizedActionItem,
    PersonalizedMeetingView,
    PersonalizedViewFilter,
    PriorityLevel,
    ReviewReasonCode,
    ReviewStatus,
    UserRole,
    explain_meeting_triage,
    personalize_meeting_view,
)


class TestMember4PersonalizationEngine(unittest.TestCase):
    """Test suite for Member 4 Personalization Engine."""

    def setUp(self):
        """Prepare sample meeting fixtures."""
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
                        {"segment_id": 184, "speaker": "SPEAKER_03", "text": "The next meeting is going to be in 30 minutes.", "start": 979.77, "end": 985.98},
                        {"segment_id": 185, "speaker": "SPEAKER_03", "text": "You're going to be working on the actual working design.", "start": 986.73, "end": 996.17},
                    ],
                }
            ]
        }
        self.raw_m3 = {
            "meeting_id": "TEST_MEETING",
            "action_items": [
                {
                    "task": "Work on the actual working design of the remote control",
                    "responsible_person": "SPEAKER_00",
                    "deadline": "30 minutes",
                    "topic_reference": 40,
                },
                {
                    "task": "Discuss mascot options",
                    "responsible_person": None,
                    "deadline": None,
                    "topic_reference": 40,
                },
            ],
        }

    def test_01_supported_roles_creation(self):
        """1. Verify creation of all supported roles (MANAGER, DEVELOPER, INTERN, DEFAULT)."""
        roles = [UserRole.MANAGER, UserRole.DEVELOPER, UserRole.INTERN, UserRole.DEFAULT]
        for role in roles:
            view = personalize_meeting_view(self.raw_m3, role=role, member2_data=self.mock_topic_40)
            self.assertEqual(view.role, role)
            self.assertEqual(view.total_canonical_items, 2)
            self.assertEqual(view.displayed_items_count, 2)

    def test_02_canonical_result_preservation(self):
        """2. Verify canonical priority, confidence, and review values are 100% preserved."""
        explained = explain_meeting_triage(self.raw_m3, member2_data=self.mock_topic_40)
        orig_0 = explained.action_items[0]

        for role in [UserRole.MANAGER, UserRole.DEVELOPER, UserRole.INTERN, UserRole.DEFAULT]:
            view = personalize_meeting_view(explained, role=role)
            item = next(a for a in view.action_items if a.item_id == orig_0.item_id)

            self.assertEqual(item.priority_score, orig_0.priority_assessment.score)
            self.assertEqual(item.priority_level, orig_0.priority_assessment.level)
            self.assertEqual(item.confidence_score, orig_0.confidence_assessment.score)
            self.assertEqual(item.confidence_level, orig_0.confidence_assessment.level)
            self.assertEqual(item.review_status, orig_0.review_decision.status)
            self.assertEqual(item.review_reason_codes, orig_0.review_decision.reason_codes)

    def test_03_manager_view_ordering(self):
        """3. Verify manager view orders HIGH priority deliverables before LOW/MEDIUM."""
        view = personalize_meeting_view(self.raw_m3, role=UserRole.MANAGER, member2_data=self.mock_topic_40)
        items = view.action_items

        self.assertEqual(items[0].priority_level, PriorityLevel.HIGH)
        self.assertEqual(items[1].priority_level, PriorityLevel.LOW)
        self.assertTrue(items[0].role_emphasis.display_urgency_badge)

    def test_04_developer_view_information(self):
        """4. Verify developer view contains localized context and technical explanations."""
        view = personalize_meeting_view(self.raw_m3, role=UserRole.DEVELOPER, member2_data=self.mock_topic_40)
        item = view.action_items[0]

        self.assertIn("localized_context", item.role_emphasis.highlighted_fields)
        self.assertIn("priority_explanation", item.role_emphasis.highlighted_fields)
        self.assertIsNotNone(item.explanation.priority_explanation)
        self.assertIsNotNone(item.explanation.confidence_explanation)

    def test_05_intern_view_information(self):
        """5. Verify intern view provides clear task, owner, deadline, and topic guidance."""
        view = personalize_meeting_view(self.raw_m3, role=UserRole.INTERN, member2_data=self.mock_topic_40)
        item = view.action_items[0]

        self.assertIn("task", item.role_emphasis.highlighted_fields)
        self.assertIn("responsible_person", item.role_emphasis.highlighted_fields)
        self.assertIn("topic_summary", item.role_emphasis.highlighted_fields)
        self.assertIsNotNone(item.role_emphasis.role_guidance)

    def test_06_default_view_preserves_canonical(self):
        """6. Verify DEFAULT view presents standard intelligence view."""
        view = personalize_meeting_view(self.raw_m3, role=UserRole.DEFAULT, member2_data=self.mock_topic_40)
        self.assertEqual(view.role, UserRole.DEFAULT)
        self.assertIn("Canonical meeting view", view.summary_headline)

    def test_07_filtering_selects_items_without_modification(self):
        """7. Verify filtering selects subset of items while keeping item contents unchanged."""
        filter_high = PersonalizedViewFilter(priority_level=PriorityLevel.HIGH)
        view = personalize_meeting_view(
            self.raw_m3,
            role=UserRole.MANAGER,
            filter_query=filter_high,
            member2_data=self.mock_topic_40,
        )

        self.assertEqual(view.total_canonical_items, 2)
        self.assertEqual(view.displayed_items_count, 1)
        self.assertEqual(view.action_items[0].priority_level, PriorityLevel.HIGH)

    def test_08_missing_deadlines_remain_missing(self):
        """8. Verify missing deadlines are not fabricated into synthetic dates."""
        view = personalize_meeting_view(self.raw_m3, role=UserRole.MANAGER, member2_data=self.mock_topic_40)
        unassigned_item = next(a for a in view.action_items if a.responsible_person is None)
        self.assertIsNone(unassigned_item.deadline)

    def test_09_unassigned_tasks_remain_unassigned(self):
        """9. Verify unassigned tasks remain unassigned across all views."""
        for role in [UserRole.MANAGER, UserRole.DEVELOPER, UserRole.INTERN, UserRole.DEFAULT]:
            view = personalize_meeting_view(self.raw_m3, role=role, member2_data=self.mock_topic_40)
            unassigned_item = next(a for a in view.action_items if a.task == "Discuss mascot options")
            self.assertTrue(unassigned_item.is_unassigned)
            self.assertIsNone(unassigned_item.responsible_person)

    def test_10_review_signals_never_hidden(self):
        """10. Verify REVIEW_RECOMMENDED and REVIEW_REQUIRED signals are preserved in all views."""
        raw = {
            "meeting_id": "TEST_REV",
            "action_items": [
                {"task": "Design mascot", "responsible_person": "SPEAKER_01", "topic_reference": 10},
            ],
            "key_decisions": [
                {"decision": "Proposal A", "topic_reference": 10},
                {"decision": "Proposal B", "topic_reference": 10},
            ],
        }
        m2 = {
            "topics": [
                {
                    "topic_id": 10,
                    "summary": "Mascot discussion",
                    "speakers": ["SPEAKER_01"],
                    "segments": [
                        {"segment_id": 101, "speaker": "SPEAKER_01", "text": "Let's design the mascot.", "start": 10.0, "end": 15.0}
                    ],
                }
            ]
        }


        for role in [UserRole.MANAGER, UserRole.DEVELOPER, UserRole.INTERN, UserRole.DEFAULT]:
            view = personalize_meeting_view(raw, role=role, member2_data=m2)
            item = view.action_items[0]
            self.assertEqual(item.review_status, ReviewStatus.REVIEW_RECOMMENDED)
            self.assertIn(ReviewReasonCode.CONFLICTING_DECISIONS, item.review_reason_codes)
            self.assertTrue(item.role_emphasis.display_review_badge)

    def test_11_evidence_references_remain_identical(self):
        """11. Verify evidence references in personalized item match Phase 7 canonical traces."""
        explained = explain_meeting_triage(self.raw_m3, member2_data=self.mock_topic_40)
        view = personalize_meeting_view(explained, role=UserRole.DEVELOPER)

        orig_traces = explained.action_items[0].explanation.evidence_traces
        proj_traces = view.action_items[0].explanation.evidence_traces

        self.assertEqual(len(orig_traces), len(proj_traces))
        for t1, t2 in zip(orig_traces, proj_traces):
            self.assertEqual(t1.source_type, t2.source_type)
            self.assertEqual(t1.source_id, t2.source_id)

    def test_12_determinism_identical_runs(self):
        """12. Verify running personalization twice produces bit-for-bit identical outputs."""
        view1 = personalize_meeting_view(self.raw_m3, role=UserRole.MANAGER, member2_data=self.mock_topic_40)
        view2 = personalize_meeting_view(self.raw_m3, role=UserRole.MANAGER, member2_data=self.mock_topic_40)

        self.assertEqual(view1.model_dump(), view2.model_dump())

    def test_13_no_llm_or_external_api_calls(self):
        """13. Verify personalization_engine contains zero references to external APIs or LLMs."""
        engine_path = PROJECT_ROOT / "backend" / "member4" / "personalization_engine.py"
        with open(engine_path, "r", encoding="utf-8") as f:
            code = f.read()

        prohibited = [
            "openai", "anthropic", "requests.post", "requests.get",
            "urllib.request", "http.client", "ollama", "boto3", "socket"
        ]
        for term in prohibited:
            self.assertNotIn(term, code, f"Prohibited external client '{term}' found in personalization_engine.py!")

    def test_14_no_upstream_imports(self):
        """14. Verify personalization_engine does not import Member 1/2/3 pipeline code."""
        engine_path = PROJECT_ROOT / "backend" / "member4" / "personalization_engine.py"
        with open(engine_path, "r", encoding="utf-8") as f:
            code = f.read()

        prohibited = [
            "backend.transcribe", "backend.speaker_aware_transcription",
            "backend.preprocessing", "backend.summarization",
            "backend.extraction", "backend.pipeline"
        ]
        for term in prohibited:
            self.assertNotIn(term, code, f"Prohibited upstream import '{term}' found in personalization_engine.py!")

    def test_15_real_es2002a_data_processed_through_phase8(self):
        """15. Real ES2002a data processed through Phase 8 across all 4 roles."""
        m3_path = PROJECT_ROOT / "data" / "processed" / "ES2002a_member3_results.json"
        m2_path = PROJECT_ROOT / "data" / "processed" / "ES2002a_member2_results.json"

        for role in [UserRole.MANAGER, UserRole.DEVELOPER, UserRole.INTERN, UserRole.DEFAULT]:
            view = personalize_meeting_view(m3_path, role=role, member2_data=m2_path)
            self.assertEqual(view.meeting_id, "ES2002a")
            self.assertEqual(view.total_canonical_items, 32)
            self.assertEqual(view.displayed_items_count, 32)


if __name__ == "__main__":
    unittest.main()
