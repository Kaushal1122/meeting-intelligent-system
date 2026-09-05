"""
Automated Integration and Unit Tests for Phase 10 Backend API.
Verifies endpoints, input validation, error handling, Member 4 schema integrity,
and ES2002a regression baseline.
"""

from pathlib import Path
import json
import sys
import unittest

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi.testclient import TestClient
from backend.api.app import app
from backend.member4 import (
    ConfidenceLevel,
    PriorityLevel,
    ReviewStatus,
)


class TestMeetingAPI(unittest.TestCase):
    """Test suite for Meeting Intelligent System API."""

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_01_health_endpoint(self):
        """1. Health check returns 200 and member4_active=True."""
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["version"], "1.0.0")
        self.assertTrue(data["member4_active"])

    def test_02_missing_input_rejected(self):
        """2. Request with no audio, no file, and no text returns 400."""
        response = self.client.post(
            "/api/meetings/process",
            data={"meeting_id": "TEST_MEETING"},
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("No input provided", response.json()["detail"])

    def test_03_empty_transcript_text_rejected(self):
        """3. Request with whitespace-only transcript text returns 400."""
        response = self.client.post(
            "/api/meetings/process",
            data={
                "meeting_id": "TEST_MEETING",
                "transcript_text": "   \n\t  \n  ",
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Pasted transcript text cannot be empty", response.json()["detail"])

    def test_04_invalid_meeting_id_rejected(self):
        """4. Request with path traversal meeting ID returns 400."""
        response = self.client.post(
            "/api/meetings/process",
            data={
                "meeting_id": "../../malicious_path",
                "transcript_text": "Speaker: Hello",
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Invalid meeting ID", response.json()["detail"])

    def test_05_invalid_transcript_extension_rejected(self):
        """5. Uploading an unsupported file format returns 400."""
        response = self.client.post(
            "/api/meetings/process",
            data={"meeting_id": "TEST_MEETING"},
            files={
                "transcript_file": ("document.pdf", b"%PDF-1.4 dummy", "application/pdf")
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Unsupported transcript format", response.json()["detail"])

    def test_06_invalid_audio_extension_rejected(self):
        """6. Uploading an unsupported audio format returns 400."""
        response = self.client.post(
            "/api/meetings/process",
            data={"meeting_id": "TEST_MEETING"},
            files={
                "audio": ("audio.exe", b"MZ dummy binary", "application/octet-stream")
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Unsupported audio format", response.json()["detail"])

    def test_07_es2002a_regression_via_api(self):
        """7. Process ES2002a through API and verify exact canonical Member 4 metrics."""
        m3_path = PROJECT_ROOT / "data" / "processed" / "ES2002a_member3_results.json"
        with open(m3_path, "rb") as f:
            file_bytes = f.read()

        response = self.client.post(
            "/api/meetings/process",
            data={"meeting_id": "ES2002a"},
            files={"transcript_file": ("ES2002a_member3_results.json", file_bytes, "application/json")},
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()

        self.assertEqual(payload["meeting_id"], "ES2002a")
        self.assertEqual(payload["total_canonical_items"], 32)
        self.assertIn("MANAGER", payload["views"])
        self.assertIn("DEVELOPER", payload["views"])
        self.assertIn("INTERN", payload["views"])
        self.assertIn("DEFAULT", payload["views"])

        mgr_view = payload["views"]["MANAGER"]
        self.assertEqual(mgr_view["total_canonical_items"], 32)
        self.assertEqual(mgr_view["high_priority_count"], 1)
        self.assertEqual(mgr_view["medium_priority_count"], 1)
        self.assertEqual(mgr_view["low_priority_count"], 30)
        self.assertEqual(mgr_view["auto_accept_count"], 25)
        self.assertEqual(mgr_view["review_recommended_count"], 7)
        self.assertEqual(mgr_view["review_required_count"], 0)
        self.assertEqual(mgr_view["has_deadline_count"], 1)
        self.assertEqual(len(payload["key_decisions"]), 9)

    def test_08_member4_fields_preserved_in_api_response(self):
        """8. Verify all canonical Member 4 fields are preserved in API response."""
        response = self.client.post(
            "/api/meetings/process",
            data={
                "meeting_id": "ES2002a",
                "transcript_text": "SPEAKER_00: Hello",
            },
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()

        first_item = data["views"]["MANAGER"]["action_items"][0]
        required_fields = [
            "item_id", "task", "responsible_person", "deadline",
            "priority_score", "priority_level", "confidence_score",
            "confidence_level", "review_status", "review_reason_codes",
            "explanation", "role_emphasis"
        ]
        for field in required_fields:
            self.assertIn(field, first_item, f"Missing required Member 4 field: {field}")

        # Check explanation subfields
        exp = first_item["explanation"]
        self.assertIn("priority_explanation", exp)
        self.assertIn("confidence_explanation", exp)
        self.assertIn("review_explanation", exp)
        self.assertIn("evidence_traces", exp)

    def test_09_member3_values_do_not_overwrite_member4(self):
        """9. Member 3 source confidence/priority must NOT overwrite Member 4 values."""
        response = self.client.post(
            "/api/meetings/process",
            data={"meeting_id": "ES2002a", "transcript_text": "SPEAKER_00: test"},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()

        # Topic 40 remote-control task
        items = data["views"]["MANAGER"]["action_items"]
        topic40_item = next(a for a in items if a["item_id"] == "norm_act_031")

        # In Member 3, priority might be arbitrary, but Member 4 priority is 0.7150 HIGH
        self.assertEqual(topic40_item["priority_level"], "HIGH")
        self.assertAlmostEqual(topic40_item["priority_score"], 0.7150, places=4)
        self.assertEqual(topic40_item["confidence_level"], "HIGH")
        self.assertAlmostEqual(topic40_item["confidence_score"], 0.9600, places=4)

    def test_10_multiple_inputs_rejected(self):
        """10. Supplying both file and pasted text returns 400."""
        response = self.client.post(
            "/api/meetings/process",
            data={
                "meeting_id": "TEST_MEETING",
                "transcript_text": "Speaker: hello",
            },
            files={
                "transcript_file": ("transcript.txt", b"Speaker: hello", "text/plain")
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Multiple inputs provided", response.json()["detail"])

    def test_11_hf_token_never_exposed_in_api(self):
        """11. Verify that HF_TOKEN is never exposed in any API response."""
        import os
        token_val = os.getenv("HF_TOKEN")

        # Health endpoint
        health_resp = self.client.get("/api/health")
        self.assertNotIn("HF_TOKEN", health_resp.text)
        self.assertNotIn("hf_", health_resp.text)
        if token_val:
            self.assertNotIn(token_val, health_resp.text)

        # Process endpoint
        process_resp = self.client.post(
            "/api/meetings/process",
            data={"meeting_id": "ES2002a", "transcript_text": "SPEAKER_00: test"},
        )
        self.assertNotIn("HF_TOKEN", process_resp.text)
        if token_val:
            self.assertNotIn(token_val, process_resp.text)


if __name__ == "__main__":
    unittest.main()

