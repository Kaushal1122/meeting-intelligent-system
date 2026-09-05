"""
Unit Tests for Dynamic Speaker Name Resolution (Member 4).

Verifies the 10 strict requirements:
1. Explicit self-identification ("My name is...", "I'm...", "This is...")
2. Diarization fallback when no self-id exists
3. Third-party mentions vs. self-identification
4. Multiple speakers with mixed explicit and fallback
5. Determinism across runs
6. Novel names support (zero hardcoded rosters)
7. Multi-meeting isolation
8. Canonical ID preservation
9. Adjective / false-positive rejection ("I'm sure", "I'm happy")
10. Real ES2002a dataset resolution
"""

import json
from pathlib import Path
import unittest

from backend.member4.speaker_resolver import (
    detect_explicit_self_id,
    resolve_meeting_speakers,
    format_speaker_display,
)
from backend.member4.schemas import SpeakerIdentity
from backend.member4.normalizer import normalize_member3_input
from backend.member4.personalization_engine import personalize_meeting_view


class TestSpeakerResolver(unittest.TestCase):
    """Test suite for speaker resolution engine."""

    def test_case_1_explicit_self_identification(self):
        """Case 1: Correctly extract name from various explicit introduction patterns."""
        cases = [
            ("Hello everyone, my name is Rahul.", "Rahul"),
            ("Hi, I'm Laura, and I'm the project manager.", "Laura"),
            ("Good morning, I am Priya.", "Priya"),
            ("This is Andrew from marketing.", "Andrew"),
            ("Rahul here, let's get started.", "Rahul"),
            ("Carlos speaking, can everyone hear me?", "Carlos"),
        ]
        for utterance, expected_name in cases:
            detected = detect_explicit_self_id(utterance)
            self.assertEqual(
                detected,
                expected_name,
                f"Failed to extract '{expected_name}' from '{utterance}'. Got '{detected}'",
            )

    def test_case_2_diarization_fallback(self):
        """Case 2: Fallback to speaker_id when no self-introduction exists."""
        segments = [
            {"speaker": "SPEAKER_01", "text": "Let's begin the review.", "start": 0.0, "end": 5.0},
            {"speaker": "SPEAKER_02", "text": "Sure, here are the numbers.", "start": 5.5, "end": 10.0},
        ]
        speakers = resolve_meeting_speakers(segments)
        self.assertIn("SPEAKER_01", speakers)
        self.assertIn("SPEAKER_02", speakers)
        self.assertEqual(speakers["SPEAKER_01"].display_name, "SPEAKER_01")
        self.assertEqual(speakers["SPEAKER_01"].name_source, "diarization_fallback")
        self.assertEqual(speakers["SPEAKER_02"].display_name, "SPEAKER_02")
        self.assertEqual(speakers["SPEAKER_02"].name_source, "diarization_fallback")

    def test_case_3_third_party_mention_vs_self_id(self):
        """Case 3: Third-party mentions MUST NOT be used to identify the speaking person."""
        segments = [
            {"speaker": "SPEAKER_01", "text": "Can you send the file to Rahul?", "start": 0.0, "end": 4.0},
            {"speaker": "SPEAKER_02", "text": "I think David mentioned that earlier.", "start": 5.0, "end": 8.0},
        ]
        speakers = resolve_meeting_speakers(segments)
        # Neither SPEAKER_01 nor SPEAKER_02 should be named Rahul or David
        self.assertEqual(speakers["SPEAKER_01"].display_name, "SPEAKER_01")
        self.assertEqual(speakers["SPEAKER_01"].name_source, "diarization_fallback")
        self.assertEqual(speakers["SPEAKER_02"].display_name, "SPEAKER_02")
        self.assertEqual(speakers["SPEAKER_02"].name_source, "diarization_fallback")

    def test_case_4_multiple_speakers_mixed(self):
        """Case 4: Multiple speakers where some self-identify and others do not."""
        segments = [
            {"speaker": "SPEAKER_01", "text": "Hi, I'm Sunita, lead engineer.", "start": 0.0, "end": 4.0},
            {"speaker": "SPEAKER_02", "text": "Thanks Sunita, I will present the timeline.", "start": 4.5, "end": 8.0},
            {"speaker": "SPEAKER_03", "text": "I'm Marco from design.", "start": 8.5, "end": 11.0},
        ]
        speakers = resolve_meeting_speakers(segments)
        self.assertEqual(speakers["SPEAKER_01"].display_name, "Sunita")
        self.assertEqual(speakers["SPEAKER_01"].name_source, "explicit_transcript")
        self.assertEqual(speakers["SPEAKER_02"].display_name, "SPEAKER_02")
        self.assertEqual(speakers["SPEAKER_02"].name_source, "diarization_fallback")
        self.assertEqual(speakers["SPEAKER_03"].display_name, "Marco")
        self.assertEqual(speakers["SPEAKER_03"].name_source, "explicit_transcript")

    def test_case_5_determinism(self):
        """Case 5: Repeated calls with identical inputs produce identical outputs."""
        segments = [
            {"speaker": "SPEAKER_00", "text": "Hi, I'm David.", "start": 1.0, "end": 3.0},
            {"speaker": "SPEAKER_01", "text": "Hello, good morning.", "start": 3.5, "end": 5.0},
        ]
        res1 = resolve_meeting_speakers(segments)
        res2 = resolve_meeting_speakers(segments)
        self.assertEqual(res1["SPEAKER_00"].model_dump(), res2["SPEAKER_00"].model_dump())
        self.assertEqual(res1["SPEAKER_01"].model_dump(), res2["SPEAKER_01"].model_dump())

    def test_case_6_novel_names(self):
        """Case 6: System seamlessly resolves novel names with zero hardcoded participant lists."""
        segments = [
            {"speaker": "SPEAKER_01", "text": "My name is Chen.", "start": 0.0, "end": 3.0},
            {"speaker": "SPEAKER_02", "text": "Hi, I am Fatima.", "start": 3.5, "end": 6.0},
            {"speaker": "SPEAKER_03", "text": "This is Alejandro.", "start": 6.5, "end": 9.0},
            {"speaker": "SPEAKER_04", "text": "Kavita here.", "start": 9.5, "end": 12.0},
        ]
        speakers = resolve_meeting_speakers(segments)
        self.assertEqual(speakers["SPEAKER_01"].display_name, "Chen")
        self.assertEqual(speakers["SPEAKER_02"].display_name, "Fatima")
        self.assertEqual(speakers["SPEAKER_03"].display_name, "Alejandro")
        self.assertEqual(speakers["SPEAKER_04"].display_name, "Kavita")

    def test_case_7_meeting_isolation(self):
        """Case 7: Speaker identities from meeting A do not bleed into meeting B."""
        meeting_a = [{"speaker": "SPEAKER_01", "text": "I'm Alice.", "start": 0.0, "end": 2.0}]
        meeting_b = [{"speaker": "SPEAKER_01", "text": "Let's review the budget.", "start": 0.0, "end": 2.0}]

        speakers_a = resolve_meeting_speakers(meeting_a)
        speakers_b = resolve_meeting_speakers(meeting_b)

        self.assertEqual(speakers_a["SPEAKER_01"].display_name, "Alice")
        self.assertEqual(speakers_a["SPEAKER_01"].name_source, "explicit_transcript")

        self.assertEqual(speakers_b["SPEAKER_01"].display_name, "SPEAKER_01")
        self.assertEqual(speakers_b["SPEAKER_01"].name_source, "diarization_fallback")

    def test_case_8_canonical_id_preservation(self):
        """Case 8: speaker_id (e.g. SPEAKER_02) is strictly preserved and never mutated."""
        segments = [{"speaker": "SPEAKER_02", "text": "Hello, my name is Viktor.", "start": 0.0, "end": 3.0}]
        speakers = resolve_meeting_speakers(segments)
        identity = speakers["SPEAKER_02"]
        self.assertEqual(identity.speaker_id, "SPEAKER_02")
        self.assertEqual(identity.display_name, "Viktor")
        self.assertNotEqual(identity.speaker_id, identity.display_name)

    def test_case_9_adjective_rejection(self):
        """Case 9: Common false-positive adjectives and statements are rejected."""
        false_positives = [
            "I'm sorry about that delay.",
            "I'm sure we can do this.",
            "I am happy with these results.",
            "I'm going to take notes.",
            "I'm not convinced.",
            "I'm ready when you are.",
            "I'm late, apologies.",
        ]
        for utterance in false_positives:
            detected = detect_explicit_self_id(utterance)
            self.assertIsNone(
                detected,
                f"Adjective/verb was falsely detected as a name: '{detected}' from '{utterance}'",
            )

    def test_case_10_real_es2002a_dataset_resolution(self):
        """Case 10: Verify 100% dynamic resolution on the real ES2002a reference dataset."""
        project_root = Path(__file__).resolve().parent.parent.parent
        m2_path = project_root / "data" / "processed" / "ES2002a_member2_results.json"
        m3_path = project_root / "data" / "processed" / "ES2002a_member3_results.json"

        if not m2_path.exists() or not m3_path.exists():
            self.skipTest("ES2002a processed data not found.")

        # Test standalone resolution
        speakers = resolve_meeting_speakers(m2_path)
        self.assertIn("SPEAKER_03", speakers)
        self.assertEqual(speakers["SPEAKER_03"].display_name, "Laura")
        self.assertEqual(speakers["SPEAKER_03"].name_source, "explicit_transcript")

        self.assertIn("SPEAKER_00", speakers)
        self.assertEqual(speakers["SPEAKER_00"].display_name, "David")
        self.assertEqual(speakers["SPEAKER_00"].name_source, "explicit_transcript")

        self.assertIn("SPEAKER_02", speakers)
        self.assertEqual(speakers["SPEAKER_02"].display_name, "Andrew")
        self.assertEqual(speakers["SPEAKER_02"].name_source, "explicit_transcript")

        self.assertIn("SPEAKER_01", speakers)
        self.assertEqual(speakers["SPEAKER_01"].display_name, "Greg")
        self.assertEqual(speakers["SPEAKER_01"].name_source, "explicit_transcript")

        # Test end-to-end normalization and personalization
        norm_output = normalize_member3_input(m3_path, member2_data=m2_path)
        self.assertGreater(len(norm_output.speakers), 0)
        self.assertEqual(norm_output.speakers["SPEAKER_03"].display_name, "Laura")

        # Action item assigned to SPEAKER_03 should have display_name Laura and speaker_id SPEAKER_03
        item_0 = norm_output.action_items[0]
        self.assertEqual(item_0.speaker_id, "SPEAKER_03")
        self.assertEqual(item_0.display_name, "Laura")
        self.assertEqual(item_0.name_source, "explicit_transcript")


if __name__ == "__main__":
    unittest.main()
