"""
Export canonical Member 4 intelligence for ES2002a into frontend data fixture.

Executes Phases 1–8 end-to-end:
  Normalization -> Context -> Priority -> Confidence -> Review -> Explainability -> Personalization
Exports pre-computed views for all 4 roles (MANAGER, DEVELOPER, INTERN, DEFAULT)
along with canonical action items and related decisions.
"""

from pathlib import Path
import json
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.member4 import (
    UserRole,
    explain_meeting_triage,
    personalize_meeting_view,
)


def export_data():
    m3_path = PROJECT_ROOT / "data" / "processed" / "ES2002a_member3_results.json"
    m2_path = PROJECT_ROOT / "data" / "processed" / "ES2002a_member2_results.json"
    output_dir = PROJECT_ROOT / "frontend" / "src" / "data"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "es2002a_data.json"

    print("Running Member 4 pipeline for ES2002a...")
    canonical_explained = explain_meeting_triage(m3_path, member2_data=m2_path)

    views = {}
    for role in [UserRole.MANAGER, UserRole.DEVELOPER, UserRole.INTERN, UserRole.DEFAULT]:
        view = personalize_meeting_view(canonical_explained, role=role)
        views[role.value] = view.model_dump()

    export_payload = {
        "meeting_id": canonical_explained.meeting_id,
        "processing_stage": "member_4_dashboard_ready",
        "total_canonical_items": len(canonical_explained.action_items),
        "views": views,
        "key_decisions": [d.model_dump() for d in canonical_explained.key_decisions],
        "diagnostics": canonical_explained.diagnostics,
    }

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(export_payload, f, indent=2)

    print(f"Successfully exported {len(canonical_explained.action_items)} action items to: {output_file}")


if __name__ == "__main__":
    export_data()
