# Member 3 → Member 4 Data Contract & Interface Specification

- **Document Version:** 1.0.0 (Phase 1 Final)
- **Module:** Member 4 Post-Extraction Intelligence Layer
- **Status:** Frozen Boundary Contract
- **Source Code Implementation:** [`backend/member4/schemas.py`](file:///c:/Users/chaha/OneDrive/Desktop/meeting-intelligent-system/backend/member4/schemas.py)

---

## 1. Purpose

This document formally defines and freezes the interface contract between **Member 3 (Semantic Task & Decision Extraction)** and **Member 4 (Post-Extraction Intelligence & Presentation)**.

The primary objectives of this contract are:
1. **Interface Stability:** Establish an immutable boundary allowing Member 4 to develop independently without modifying Member 1, Member 2, or Member 3.
2. **Input/Output Separation:** Disentangle raw upstream extraction data from downstream calculated intelligence.
3. **Context Bridging:** Define how Member 4 cross-references Member 3 items back to Member 2 topic summaries without breaking modularity.
4. **Headless Execution:** Guarantee that all intelligence operations can run programmatically without any dependency on UI components (e.g. Streamlit or web servers).

---

## 2. Member 3 → Member 4 Architectural Boundary

The architecture enforces a strict one-way data flow:

```
┌────────────────────────────────────────┐
│        Member 3 Extraction             │
│   (backend/extraction/task_extractor)  │
└──────────────────┬─────────────────────┘
                   │
                   ▼ Produces: data/processed/<id>_member3_results.json
┌────────────────────────────────────────┐
│       MEMBER 4 INPUT CONTRACT          │  <-- FROZEN BOUNDARY
│   (backend/member4/schemas.py)         │
│   Model: Member4Input                  │
└──────────────────┬─────────────────────┘
                   │
                   ▼ Ingests & Normalizes
┌────────────────────────────────────────┐
│       Member 4 Processing Core         │  (Phases 2-8: Context, Priority,
│   (Independent Post-Processing)        │   Confidence, Triage, Personalization)
└──────────────────┬─────────────────────┘
                   │
                   ▼ Emits: data/processed/<id>_member4_results.json
┌────────────────────────────────────────┐
│       MEMBER 4 OUTPUT CONTRACT         │  <-- FROZEN OUTPUT
│   (backend/member4/schemas.py)         │
│   Model: Member4Output                 │
└──────────────────┬─────────────────────┘
                   │
                   ▼ Consumed by:
┌────────────────────────────────────────┐
│     Downstream Presentation/UI         │  (CLI, REST API, Streamlit Dashboard)
└────────────────────────────────────────┘
```

> [!IMPORTANT]
> **No Circular Dependencies:** Member 4 consumes Member 3 output as an external, read-only artifact. Member 4 never imports or calls Member 3 extraction logic.

---

## 3. Actual Member 3 Input Structure (Inspected Baseline)

Based on direct inspection of the production artifact [`data/processed/ES2002a_member3_results.json`](file:///c:/Users/chaha/OneDrive/Desktop/meeting-intelligent-system/data/processed/ES2002a_member3_results.json), Member 3 emits the following structure:

```json
{
    "meeting_id": "ES2002a",
    "processing_stage": "member_3_complete",
    "total_action_items": 32,
    "total_decisions": 9,
    "action_items": [
        {
            "task": "Work on the actual working design of the remote control",
            "responsible_person": "SPEAKER_00",
            "deadline": "30 minutes",
            "topic_reference": 40,
            "priority": "High",
            "confidence_score": 0.95
        }
    ],
    "key_decisions": [
        {
            "decision": "Remote controls should be designed to work together, even though they are separate for different functions",
            "topic_reference": 36
        }
    ]
}
```

---

## 4. Member 4 Input Schema Specification

Defined in Python Pydantic models in [`backend/member4/schemas.py`](file:///c:/Users/chaha/OneDrive/Desktop/meeting-intelligent-system/backend/member4/schemas.py):

### 4.1. Top-Level Model: `Member4Input`
Represents the complete JSON artifact ingested from Member 3.

| Field Name | Type | Constraint | Description |
| :--- | :--- | :--- | :--- |
| `meeting_id` | `str` | **Required**, non-empty | Unique meeting identifier (e.g. `"ES2002a"`). |
| `processing_stage` | `Optional[str]` | Optional, default `"member_3_complete"` | Upstream stage indicator. |
| `total_action_items` | `Optional[int]` | Optional | Count of action items reported by Member 3. |
| `total_decisions` | `Optional[int]` | Optional | Count of key decisions reported by Member 3. |
| `action_items` | `List[Member4ActionItemInput]` | Optional, default `[]` | List of raw extracted action items. |
| `key_decisions` | `List[Member4DecisionInput]` | Optional, default `[]` | List of raw extracted decisions. |

### 4.2. Action Item Input Model: `Member4ActionItemInput`

| Field Name | Type | Constraint | Description |
| :--- | :--- | :--- | :--- |
| `task` | `str` | **Required**, non-empty | Clear, actionable task statement. |
| `responsible_person` | `Optional[str]` | Optional, nullable | Speaker tag or participant name (e.g. `"SPEAKER_00"`). |
| `deadline` | `Optional[str]` | Optional, nullable | Temporal marker string (e.g. `"30 minutes"`, `"None mentioned"`). |
| `topic_reference` | `Optional[int]` | Optional, nullable | Integer topic identifier referencing Member 2 `topic_id`. |
| `source_priority` *(aliased as `priority`)* | `Optional[str]` | Optional | Raw upstream priority string emitted by Member 3 LLM. |
| `source_confidence_score` *(aliased as `confidence_score`)* | `Optional[float]` | Optional | Raw upstream single float emitted by Member 3 LLM. |

### 4.3. Decision Input Model: `Member4DecisionInput`

| Field Name | Type | Constraint | Description |
| :--- | :--- | :--- | :--- |
| `decision` | `str` | **Required**, non-empty | Strategic agreement or design specification rule. |
| `topic_reference` | `Optional[int]` | Optional, nullable | Integer topic identifier referencing Member 2 `topic_id`. |

---

## 5. Topic-Reference Relationship (Member 2 Context Bridge)

Member 3 retains only a foreign key: `topic_reference: int`.

To prevent modifying Member 3, Member 4 defines a cross-referencing model [`Member2TopicContextInput`](file:///c:/Users/chaha/OneDrive/Desktop/meeting-intelligent-system/backend/member4/schemas.py#L110-L135) to bridge Member 3 items to Member 2 records (`data/processed/<meeting_id>_member2_results.json`):

```
Member 3 Action Item:
    {
        "task": "Work on the actual working design...",
        "topic_reference": 40
    }
           │
           │  Mapped via: topic_reference == topic_id
           ▼
Member 2 Topic Object:
    {
        "topic_id": 40,
        "summary": "The team concludes initial presentations and prepares for breakout...",
        "speakers": ["SPEAKER_03", "SPEAKER_00"],
        "start": 1042.10,
        "end": 1085.40,
        "text": "SPEAKER_03: The next meeting is in 30 minutes. David, as the industrial designer..."
    }
```

### Fallback Policy:
If Member 2 output is missing or corrupt, Member 4 functions in **degraded standalone mode**, processing the action items using only their raw task text without crashing.

---

## 6. Handling of Member 3 Priority and Confidence Fields

In Member 3 output, `priority` (e.g. `"High"`, `"Medium"`) and `confidence_score` (e.g. `0.95`) are produced by the LLM prompt in a single uncalibrated pass.

**Strict Architectural Rule for Member 4:**
1. **Upstream fields are treated as raw source metadata only:** They are mapped to `source_priority` and `source_confidence_score` in `Member4ActionItemInput`.
2. **No Dependency:** Member 4 **never** treats these values as ground truth.
3. **Independent Calculation:** Member 4's downstream modules (Phases 4 & 5) calculate their own multi-factor `priority` and multi-component `confidence` independently.

---

## 7. Validation Expectations & Edge Cases

The contract explicitly handles the following edge cases:

| Scenario | Ingestion Behavior | Downstream Action in Member 4 |
| :--- | :--- | :--- |
| **Missing / Empty `task`** | Rejected by Pydantic validator (`ValueError`). | Task string is strictly required for an action item to exist. |
| **Missing `responsible_person`** | Accepted as `None`. | Trigger for `needs_human_review: true` (unassigned task). |
| **Missing `deadline`** | Accepted as `None`. | Urgency feature defaults to minimum score; no review required unless critical. |
| **Missing `topic_reference`** | Accepted as `None`. | Item processed without topic context; logged with warning. |
| **Invalid `topic_reference` (not in Member 2)** | Accepted as `int`, but unresolved in Member 2 lookup. | Triggers review flag: `review_reasons: ["Orphaned topic reference"]`. |
| **Duplicate action items** | Ingested as separate items. | Normalization layer (Phase 2) will compute lexical similarity and deduplicate. |
| **Extraneous JSON fields** | Safely ignored via `ConfigDict(extra="ignore")`. | Future-proofs against upstream schema additions. |

---

## 8. Phase 2: Member 4 Normalized Internal Representation

Phase 2 introduces a clean internal representation ([`Member4NormalizedOutput`](file:///c:/Users/chaha/OneDrive/Desktop/meeting-intelligent-system/backend/member4/schemas.py#L250)) that validates and normalizes raw Member 3 extractions before downstream intelligence layers (Phases 3–7) operate on them.

### 8.1. Separation of Data Concerns:
1. **Member 3 Source Data:** Immutable upstream extraction. `source_priority` and `source_confidence_score` are retained strictly as source metadata references.
2. **Member 4 Normalized Data:** Validated and sanitized task text, attribution indicators (`is_unassigned: bool`), deadline clarity flags (`is_ambiguous_deadline: bool`), deterministic item IDs (`norm_act_001`), and deterministic duplicate tracking (`is_duplicate`, `duplicate_of`).
3. **Member 2 Topic Enrichment:** Optional reconciliation linking `topic_reference` to `topic_id`. When Member 2 results are supplied, verified topic context (summaries, speakers, timestamps) is attached directly with `context_status = "RESOLVED"`. When unavailable or unmatched, the item is preserved with `context_status = "UNRESOLVED"` or `"MISSING_REFERENCE"`.

### 8.2. Normalized Action Item Schema (`NormalizedActionItem`):
```json
{
    "item_id": "norm_act_001",
    "raw_task": "Work on the actual working design of the remote control",
    "task": "Work on the actual working design of the remote control",
    "responsible_person": "SPEAKER_00",
    "is_unassigned": false,
    "deadline": "30 minutes",
    "is_ambiguous_deadline": false,
    "topic_reference": 40,
    "context_status": "RESOLVED",
    "topic_context": {
        "topic_id": 40,
        "segment_count": 1,
        "speakers": ["SPEAKER_03"],
        "summary": "Right, so it is to wrap up. The next meeting is going to be in 30 minutes...",
        "start": 1042.10,
        "end": 1085.40
    },
    "source_priority": "High",
    "source_confidence_score": 0.95,
    "is_duplicate": false,
    "duplicate_of": null,
    "validation_diagnostics": []
}
```

## 9. Phase 3: Member 4 Contextual Task Intelligence Representation

Phase 3 introduces the context-rich representation ([`Member4ContextOutput`](file:///c:/Users/chaha/OneDrive/Desktop/meeting-intelligent-system/backend/member4/schemas.py#L585)) produced by [`build_task_context(...)`](file:///c:/Users/chaha/OneDrive/Desktop/meeting-intelligent-system/backend/member4/context_engine.py). It answers: *"What does this task actually mean in the context of the meeting?"*

### 9.1. Architectural Purpose & Context Sources:
- **Input Sources:** Normalized Member 3 data (`task`, `responsible_person`, `deadline`, `topic_reference`, source metadata) and Member 2 topic results (`summary`, `speakers`, `start`, `end`, and transcript `segments`).
- **Provenance Preservation:** All Phase 2 normalized attributes remain unchanged. Context attributes enrich rather than mutate or overwrite source statements.

### 9.2. Localized Context-Window Rule:
- **Triggering Segment Identification:** Identifies the segment within the referenced topic that exhibits the highest lexical keyword overlap with the task text and deadline mentions.
- **Turn Window Radius:** Deterministically extracts the triggering segment plus up to $\pm 2$ neighboring utterances ($[\max(0, k-2) \dots \min(len-1, k+2)]$).
- **Window Payload:** Preserves verbatim dialogue turns (`SPEAKER: text`), segment IDs, active window speakers, and boundary timestamps.
- **Zero LLM:** Constructed via 100% deterministic local rules with zero model inference.

### 9.3. Context Quality Status:
- `RESOLVED`: Referenced topic matched, source transcript segments present, and localized dialogue window successfully constructed.
- `PARTIALLY_RESOLVED`: Referenced topic matched with summary/metadata, but detailed transcript segment turns are unavailable.
- `UNRESOLVED`: Topic reference integer provided but absent from Member 2 topic dataset.
- `MISSING_REFERENCE`: Action item has no topic reference (`null`).

### 9.4. Related Decisions Association:
- Action items and key decisions established within the same topic reference are cross-referenced deterministically via [`RelatedDecisionContext`](file:///c:/Users/chaha/OneDrive/Desktop/meeting-intelligent-system/backend/member4/schemas.py#L416).

### 9.5. Context-Rich Action Item Schema (`ContextRichActionItem`):
```json
{
    "item_id": "norm_act_031",
    "task": "Work on the actual working design of the remote control",
    "responsible_person": "SPEAKER_00",
    "is_unassigned": false,
    "deadline": "30 minutes",
    "is_ambiguous_deadline": false,
    "topic_reference": 40,
    "context_status": "RESOLVED",
    "topic_summary": "Right, so it is to wrap up. The next meeting is going to be in 30 minutes...",
    "topic_speakers": ["SPEAKER_03"],
    "localized_context": {
        "window_text": "SPEAKER_03: Right, so it is to wrap up.\nSPEAKER_03: The next meeting is going to be in 30 minutes, so that's about 10 to 12 by my watch.\nSPEAKER_03: In between now and then, as the industrial designer, you're going to be working on the actual working design of it, so you know what you're doing there.\nSPEAKER_03: For our user interface, technical functions, I guess that's what we've been talking about, what it'll actually do.\nSPEAKER_03: And marketing executive, you'll be just thinking about what requirements it has to fulfill...",
        "segment_ids": [183, 184, 185, 186, 187],
        "trigger_segment_id": 185,
        "speakers": ["SPEAKER_03"],
        "start": 976.58,
        "end": 1019.12
    },
    "context_start": 976.58,
    "context_end": 1019.12,
    "related_decisions": [],
    "deadline_context_snippet": "SPEAKER_03: The next meeting is going to be in 30 minutes, so that's about 10 to 12 by my watch.",
    "source_priority": "High",
    "source_confidence_score": 0.95,
    "is_duplicate": false,
    "duplicate_of": null,
    "context_diagnostics": []
}
```

---

## 10. Phase 4: Member 4 Priority Intelligence Representation

Phase 4 introduces continuous priority inference and categorical classification ([`Member4PriorityOutput`](file:///c:/Users/chaha/OneDrive/Desktop/meeting-intelligent-system/backend/member4/schemas.py#L740)) produced by [`infer_task_priorities(...)`](file:///c:/Users/chaha/OneDrive/Desktop/meeting-intelligent-system/backend/member4/priority_engine.py).

### 10.1. Scoring Formula & Configuration
The priority score is a bounded continuous sum:
$$\text{Priority Score} = \sum_{i} w_i \times v_i \quad \in [0.0, 1.0]$$
Categorical tier assignment follows explicit thresholds:
- $\text{HIGH}: \text{Score} \ge 0.65$
- $\text{MEDIUM}: 0.35 \le \text{Score} < 0.65$
- $\text{LOW}: \text{Score} < 0.35$

| Factor Name | Weight ($w_i$) | Evaluation Criteria |
| :--- | :--- | :--- |
| `deadline_urgency` | 0.25 | $\le 60$ min / session breakout (0.95), same day (0.70), near term (0.50), medium (0.30), distant (0.15), ambiguous (0.10–0.40), missing (0.0). |
| `explicit_urgency_language` | 0.15 | Critical / emergency terminology in dialogue/task (0.90), moderate urgency (0.50), ordinary text (0.0). |
| `assignment_explicitness` | 0.15 | Direct second-person/imperative dialogue assignment to owner (0.85), self-commitment (0.50), metadata only (0.40), unassigned (0.0). |
| `dependency_blocker` | 0.15 | Hard blocker/prerequisite (0.85), sequential breakout milestone prerequisite (0.60), none (0.0). |
| `decision_linkage` | 0.10 | Single aligned decision (0.40), multiple competing/alternative decisions (0.20 conservative), none (0.0). |
| `deliverable_specificity` | 0.10 | Concrete engineering artifact/deliverable (0.85), standard task (0.55), exploratory/vague (0.30). |
| `context_quality` | 0.10 | `RESOLVED` (1.00), `PARTIALLY_RESOLVED` (0.50), `UNRESOLVED` (0.20), `MISSING_REFERENCE` (0.00). |

### 10.2. Priority-Enriched Action Item Schema (`PriorityEnrichedActionItem`):
```json
{
    "item_id": "norm_act_031",
    "task": "Work on the actual working design of the remote control",
    "responsible_person": "SPEAKER_00",
    "is_unassigned": false,
    "deadline": "30 minutes",
    "is_ambiguous_deadline": false,
    "topic_reference": 40,
    "context_status": "RESOLVED",
    "source_priority": "High",
    "source_confidence_score": 0.95,
    "priority_assessment": {
        "score": 0.7150,
        "level": "HIGH",
        "factor_contributions": [
            {
                "factor_name": "deadline_urgency",
                "raw_value": 0.95,
                "weight": 0.25,
                "weighted_contribution": 0.2375,
                "has_evidence": true,
                "evidence_text": "Imminent session deadline: '30 minutes'"
            },
            {
                "factor_name": "explicit_urgency_language",
                "raw_value": 0.50,
                "weight": 0.15,
                "weighted_contribution": 0.0750,
                "has_evidence": true,
                "evidence_text": "Moderate urgency indicator detected: 'wrap up'"
            },
            {
                "factor_name": "assignment_explicitness",
                "raw_value": 0.85,
                "weight": 0.15,
                "weighted_contribution": 0.1275,
                "has_evidence": true,
                "evidence_text": "Direct imperative assignment to 'SPEAKER_00' documented in dialogue turns."
            },
            {
                "factor_name": "dependency_blocker",
                "raw_value": 0.60,
                "weight": 0.15,
                "weighted_contribution": 0.0900,
                "has_evidence": true,
                "evidence_text": "Sequential milestone prerequisite: work required before reconvening meeting ('in between now and then')"
            },
            {
                "factor_name": "decision_linkage",
                "raw_value": 0.00,
                "weight": 0.10,
                "weighted_contribution": 0.0000,
                "has_evidence": false,
                "evidence_text": "No key decisions linked to this topic."
            },
            {
                "factor_name": "deliverable_specificity",
                "raw_value": 0.85,
                "weight": 0.10,
                "weighted_contribution": 0.0850,
                "has_evidence": true,
                "evidence_text": "Concrete operational deliverable with specific engineering artifact."
            },
            {
                "factor_name": "context_quality",
                "raw_value": 1.00,
                "weight": 0.10,
                "weighted_contribution": 0.1000,
                "has_evidence": true,
                "evidence_text": "Context fully resolved with localized dialogue turns and topic summary."
            }
        ],
        "scoring_breakdown": {
            "deadline_urgency": 0.2375,
            "explicit_urgency_language": 0.0750,
            "assignment_explicitness": 0.1275,
            "dependency_blocker": 0.0900,
            "decision_linkage": 0.0000,
            "deliverable_specificity": 0.0850,
            "context_quality": 0.1000
        },
        "evidence_summary": [
            "Imminent session deadline: '30 minutes'",
            "Moderate urgency indicator detected: 'wrap up'",
            "Direct imperative assignment to 'SPEAKER_00' documented in dialogue turns.",
            "Sequential milestone prerequisite: work required before reconvening meeting ('in between now and then')",
            "Concrete operational deliverable with specific engineering artifact.",
            "Context fully resolved with localized dialogue turns and topic summary."
        ]
    }
}
```

---

## 11. Phase 5: Member 4 Confidence Intelligence Representation

Phase 5 introduces evidence reliability estimation and categorical confidence classification ([`Member4ConfidenceOutput`](file:///c:/Users/chaha/OneDrive/Desktop/meeting-intelligent-system/backend/member4/schemas.py#L884)) produced by [`infer_task_confidence(...)`](file:///c:/Users/chaha/OneDrive/Desktop/meeting-intelligent-system/backend/member4/confidence_engine.py).

### 11.1. Confidence Scoring Formula & Configuration
Confidence is strictly an estimate of evidence reliability, completely decoupled from priority (task urgency):
$$\text{Confidence Score} = \sum_{i=1}^{7} w_i \times v_i \quad \in [0.0, 1.0]$$

Categorical tier assignment follows explicit thresholds:
- $\text{HIGH}: \text{Score} \ge 0.75$
- $\text{MEDIUM}: 0.50 \le \text{Score} < 0.75$
- $\text{LOW}: \text{Score} < 0.50$

| Factor Name | Weight ($w_i$) | Grounded Evidence Criteria |
| :--- | :---: | :--- |
| `context_resolution` | 0.20 | `RESOLVED` (1.00); `PARTIALLY_RESOLVED` (0.50); `UNRESOLVED` (0.20); `MISSING_REFERENCE` (0.00). |
| `localized_evidence_grounding` | 0.20 | Structural dialogue/timestamps/speakers (up to 0.40) + task lexical corroboration in turns (up to 0.60). |
| `task_assignee_consistency` | 0.15 | Explicit dialogue delegation / commitment (1.00); metadata active speaker (0.70); metadata passive (0.50); unassigned (0.35). |
| `deadline_evidence_quality` | 0.15 | Explicit deadline verified by snippet (1.00); explicit in metadata (0.80); missing deadline neutral baseline (0.60); ambiguous deadline (0.30). |
| `topic_resolution_quality` | 0.10 | Verified topic with summary (1.00); topic metadata only (0.50); unresolved (0.20); missing (0.00). |
| `decision_evidence_consistency` | 0.10 | Single aligned decision (1.00); zero decisions neutral baseline (0.60); competing alternatives (0.20). |
| `structural_completeness` | 0.10 | Valid item ID (+0.25); task length $\ge 3$ words (+0.25); provenance tracking (+0.25); clean diagnostics (+0.25). |

### 11.2. Confidence-Enriched Action Item Schema (`ConfidenceEnrichedActionItem`):
```json
{
    "item_id": "norm_act_031",
    "task": "Work on the actual working design of the remote control",
    "responsible_person": "SPEAKER_00",
    "is_unassigned": false,
    "deadline": "30 minutes",
    "is_ambiguous_deadline": false,
    "topic_reference": 40,
    "context_status": "RESOLVED",
    "source_priority": "High",
    "source_confidence_score": 0.95,
    "priority_assessment": {
        "score": 0.7150,
        "level": "HIGH"
    },
    "confidence_assessment": {
        "score": 0.9600,
        "level": "HIGH",
        "factor_contributions": [
            {
                "factor_name": "context_resolution",
                "raw_value": 1.00,
                "weight": 0.20,
                "weighted_contribution": 0.2000,
                "has_evidence": true,
                "evidence_text": "Context fully resolved with localized dialogue turns and verified topic."
            },
            {
                "factor_name": "localized_evidence_grounding",
                "raw_value": 1.00,
                "weight": 0.20,
                "weighted_contribution": 0.2000,
                "has_evidence": true,
                "evidence_text": "Strong localized grounding: task verified in dialogue (3/5 key terms), 5 segments, timestamps (976.58s–1019.12s), speakers ['SPEAKER_03']."
            },
            {
                "factor_name": "task_assignee_consistency",
                "raw_value": 1.00,
                "weight": 0.15,
                "weighted_contribution": 0.1500,
                "has_evidence": true,
                "evidence_text": "Assignee 'SPEAKER_00' explicitly corroborated by direct dialogue delegation / commitment."
            },
            {
                "factor_name": "deadline_evidence_quality",
                "raw_value": 1.00,
                "weight": 0.15,
                "weighted_contribution": 0.1500,
                "has_evidence": true,
                "evidence_text": "Explicit deadline '30 minutes' verified and corroborated by dialogue snippet."
            },
            {
                "factor_name": "topic_resolution_quality",
                "raw_value": 1.00,
                "weight": 0.10,
                "weighted_contribution": 0.1000,
                "has_evidence": true,
                "evidence_text": "Topic 40 successfully verified with abstractive summary."
            },
            {
                "factor_name": "decision_evidence_consistency",
                "raw_value": 0.60,
                "weight": 0.10,
                "weighted_contribution": 0.0600,
                "has_evidence": false,
                "evidence_text": "No linked decisions; zero contradiction evidence."
            },
            {
                "factor_name": "structural_completeness",
                "raw_value": 1.00,
                "weight": 0.10,
                "weighted_contribution": 0.1000,
                "has_evidence": true,
                "evidence_text": "Payload possesses structural integrity and source provenance."
            }
        ],
        "scoring_breakdown": {
            "context_resolution": 0.2000,
            "localized_evidence_grounding": 0.2000,
            "task_assignee_consistency": 0.1500,
            "deadline_evidence_quality": 0.1500,
            "topic_resolution_quality": 0.1000,
            "decision_evidence_consistency": 0.0600,
            "structural_completeness": 0.1000
        },
        "evidence_quality_notes": [
            "Context fully resolved with localized dialogue turns and verified topic.",
            "Strong localized grounding: task verified in dialogue (3/5 key terms), 5 segments, timestamps (976.58s–1019.12s), speakers ['SPEAKER_03'].",
            "Assignee 'SPEAKER_00' explicitly corroborated by direct dialogue delegation / commitment.",
            "Explicit deadline '30 minutes' verified and corroborated by dialogue snippet.",
            "Topic 40 successfully verified with abstractive summary.",
            "No linked decisions; zero contradiction evidence.",
            "Payload possesses structural integrity and source provenance."
        ]
    }
}
```


---

## 12. Human Review & Uncertainty Triage Contract (Phase 6)

Phase 6 introduces a deterministic triage classification layer ([`backend/member4/review_engine.py`](file:///c:/Users/chaha/OneDrive/Desktop/meeting-intelligent-system/backend/member4/review_engine.py)) that consumes the enriched outputs of Phases 1–5 and determines the appropriate human intervention level:

### 12.1. Triage States & Semantic Definitions
- **`AUTO_ACCEPT`**: Evidence is sufficiently strong and zero material uncertainty signals were detected. Safe for automated downstream ingestion without human bottleneck.
- **`REVIEW_RECOMMENDED`**: The item is operationally usable but exhibits moderate uncertainty (e.g. high-priority with medium-confidence, competing topic decisions, weak dialogue grounding, or partial context). Human verification is suggested.
- **`REVIEW_REQUIRED`**: Mandatory human intervention is required before treating the item as reliable (e.g. high-priority with low-confidence, unresolved/missing topic context, unassigned high-priority deliverable, or ambiguous deadline on an urgent task).

### 12.2. Reason Codes
- **Critical Risk (triggers `REVIEW_REQUIRED`):**
  - `HIGH_PRIORITY_LOW_CONFIDENCE`
  - `HIGH_PRIORITY_AMBIGUOUS_DEADLINE`
  - `UNASSIGNED_HIGH_PRIORITY_TASK`
  - `UNRESOLVED_CONTEXT`
  - `MISSING_TOPIC_REFERENCE`
  - `LOW_CONFIDENCE`
- **Moderate Uncertainty (triggers `REVIEW_RECOMMENDED`):**
  - `HIGH_PRIORITY_MEDIUM_CONFIDENCE`
  - `MEDIUM_CONFIDENCE`
  - `PARTIAL_CONTEXT`
  - `UNASSIGNED_TASK`
  - `AMBIGUOUS_DEADLINE`
  - `WEAK_DIALOGUE_GROUNDING`
  - `CONFLICTING_DECISIONS`

### 12.3. Triage-Enriched Action Item Schema (`TriageEnrichedActionItem`):
```json
{
    "item_id": "norm_act_031",
    "task": "Work on the actual working design of the remote control",
    "responsible_person": "SPEAKER_00",
    "is_unassigned": false,
    "deadline": "30 minutes",
    "is_ambiguous_deadline": false,
    "topic_reference": 40,
    "context_status": "RESOLVED",
    "priority_assessment": {
        "score": 0.7150,
        "level": "HIGH"
    },
    "confidence_assessment": {
        "score": 0.9600,
        "level": "HIGH"
    },
    "review_decision": {
        "status": "AUTO_ACCEPT",
        "review_required": false,
        "review_recommended": false,
        "reason_codes": [],
        "explanation": "Evidence is sufficiently strong with no material uncertainty signals; automatically accepted.",
        "evidence_flags": {}
    }
---

## 13. Explainability Engine Contract (Phase 7)

Phase 7 introduces a read-only interpretability layer ([`backend/member4/explainability_engine.py`](file:///c:/Users/chaha/OneDrive/Desktop/meeting-intelligent-system/backend/member4/explainability_engine.py)) that answers *why* specific priority scores, confidence assessments, and triage decisions were assigned:

### 13.1. Core Architectural Guarantees
1. **Read-Only / Zero Decision Drift:** Running Explainability produces zero side effects on task metadata, priority scores, confidence scores, or triage statuses.
2. **Mathematical Consistency:** For all factor sets, $\sum (w_i \times v_i) = \text{Score}$ within $10^{-4}$ tolerance.
3. **Deterministic Factor Ranking:** Ordered by weighted contribution descending, breaking ties by factor name ascending.
4. **Verifiable Provenance Traces:** Evidence references link directly to concrete topic IDs, segment IDs, verbatim snippets, and decision IDs without synthetic fabrication.

### 13.2. Explained Action Item Schema (`ExplainedActionItem`):
```json
{
    "item_id": "norm_act_031",
    "task": "Work on the actual working design of the remote control",
    "priority_assessment": {
        "score": 0.7150,
        "level": "HIGH"
    },
    "confidence_assessment": {
        "score": 0.9600,
        "level": "HIGH"
    },
    "review_decision": {
        "status": "AUTO_ACCEPT"
    },
    "explanation": {
        "priority_explanation": {
            "score": 0.7150,
            "level": "HIGH",
            "top_contributors": [
                {"factor_name": "deadline_urgency", "weighted_contribution": 0.2375},
                {"factor_name": "assignment_explicitness", "weighted_contribution": 0.1275},
                {"factor_name": "context_quality", "weighted_contribution": 0.1000}
            ],
            "explanation_text": "Priority is HIGH (score: 0.7150), driven primarily by deadline_urgency (+0.2375), assignment_explicitness (+0.1275), context_quality (+0.1000)."
        },
        "confidence_explanation": {
            "score": 0.9600,
            "level": "HIGH",
            "supporting_evidence": [
                "context_resolution (+0.2000): Context fully resolved with localized dialogue turns and verified topic.",
                "localized_evidence_grounding (+0.2000): Strong localized grounding: task verified in dialogue (3/5 key terms), 5 segments, timestamps (976.58s–1019.12s), speakers ['SPEAKER_03']."
            ],
            "limiting_evidence": [],
            "explanation_text": "Confidence is HIGH (score: 0.9600), supported by context_resolution (+0.2000), localized_evidence_grounding (+0.2000), deadline_evidence_quality (+0.1500). Zero material evidence gaps detected."
        },
        "review_explanation": {
            "status": "AUTO_ACCEPT",
            "explanation_text": "Review status is AUTO_ACCEPT: Evidence is sufficiently strong across dialogue and topic grounding with zero material uncertainty signals."
        },
        "evidence_traces": [
            {"source_type": "topic", "source_id": 40, "speaker": "SPEAKER_03"},
            {"source_type": "transcript_segment", "source_id": 183, "speaker": "SPEAKER_03"},
            {"source_type": "deadline", "source_id": "30 minutes"}
        ],
        "unified_explanation": "Item 'norm_act_031': Priority is HIGH (0.7150) and Confidence is HIGH (0.9600). Triage decision is AUTO_ACCEPT..."
    }
---

## 14. Personalization Engine Contract (Phase 8)

Phase 8 introduces a deterministic role-transformation and presentation projection layer ([`backend/member4/personalization_engine.py`](file:///c:/Users/chaha/OneDrive/Desktop/meeting-intelligent-system/backend/member4/personalization_engine.py)). It transforms the fully explained canonical intelligence payload into role-specific views (`MANAGER`, `DEVELOPER`, `INTERN`, `DEFAULT`) without modifying the underlying canonical decisions:

### 14.1. Core Architectural Invariants
1. **Canonical Invariance Guarantee:** For every action item:
   - $\text{Priority Score}_{\text{personalized}} == \text{Priority Score}_{\text{canonical}}$
   - $\text{Confidence Score}_{\text{personalized}} == \text{Confidence Score}_{\text{canonical}}$
   - $\text{Review Status}_{\text{personalized}} == \text{Review Status}_{\text{canonical}}$
   - $\text{Reason Codes}_{\text{personalized}} == \text{Reason Codes}_{\text{canonical}}$
2. **Role-Specific Focus:**
   - **`MANAGER`**: Prioritizes high-priority items, deadlines, owners, and review triggers.
   - **`DEVELOPER`**: Highlights technical dependencies, local dialogue context, and deliverable specificity.
   - **`INTERN`**: Highlights clear task descriptions, owner clarity, and guidance while preserving uncertainty.
   - **`DEFAULT`**: Preserves canonical presentation without rearrangement.

### 14.2. Personalized Meeting View Schema (`PersonalizedMeetingView`):
```json
{
    "meeting_id": "ES2002a",
    "role": "MANAGER",
    "summary_headline": "32 action items tracked, including 1 high-priority item(s), 7 item(s) flagged for review, and 1 with explicit deadlines.",
    "total_canonical_items": 32,
    "displayed_items_count": 32,
    "high_priority_count": 1,
    "medium_priority_count": 1,
    "low_priority_count": 30,
    "auto_accept_count": 25,
    "review_recommended_count": 7,
    "review_required_count": 0,
    "unassigned_count": 0,
    "has_deadline_count": 1,
    "action_items": [
        {
            "item_id": "norm_act_031",
            "task": "Work on the actual working design of the remote control",
            "responsible_person": "SPEAKER_00",
            "is_unassigned": false,
            "deadline": "30 minutes",
            "priority_score": 0.7150,
            "priority_level": "HIGH",
            "confidence_score": 0.9600,
            "confidence_level": "HIGH",
            "review_status": "AUTO_ACCEPT",
            "review_reason_codes": [],
            "role_emphasis": {
                "role": "MANAGER",
                "highlighted_fields": ["task", "responsible_person", "deadline", "priority_level", "review_status"],
                "display_urgency_badge": true,
                "display_review_badge": false,
                "role_guidance": "High-priority deliverable: ensure ownership and timeline commitments are strictly tracked."
            }
        }
    ]
}
---

## 15. Frontend Data Contract (Phase 9 React Dashboard)

Phase 9 introduces the React-based Meeting Intelligence Dashboard ([`frontend/`](file:///c:/Users/chaha/OneDrive/Desktop/meeting-intelligent-system/frontend/)). The frontend acts strictly as a presentation layer consuming pre-computed canonical Member 4 intelligence payloads:

### 15.1. Dashboard Data Payload Schema (`DashboardPayload`)
```json
{
  "meeting_id": "ES2002a",
  "processing_stage": "member_4_dashboard_ready",
  "total_canonical_items": 32,
  "views": {
    "MANAGER": { /* PersonalizedMeetingView */ },
    "DEVELOPER": { /* PersonalizedMeetingView */ },
    "INTERN": { /* PersonalizedMeetingView */ },
    "DEFAULT": { /* PersonalizedMeetingView */ }
  },
  "key_decisions": [ /* ContextRichDecision[] */ ],
  "diagnostics": []
}
```

### 15.2. Core Principles
1. **Zero Client-Side Recalculation:** The React frontend displays priority scores, confidence assessments, review decisions, and explainability traces directly from the payload.
2. **Deterministic UI Filtering:** Multi-criteria filters (`priorityLevel`, `confidenceLevel`, `reviewStatus`, `assignment`, `deadline`, `searchQuery`) select displayed items without modifying underlying attributes.
3. **No External AI / LLM Calls:** Zero network requests or model inference in the client.

---

## 16. API Request & Response Contract (Phase 10 Integration)

Phase 10 defines the production HTTP contracts exposed by the FastAPI server ([`backend/api/`](file:///c:/Users/chaha/OneDrive/Desktop/meeting-intelligent-system/backend/api/)):

### 16.1. Health Check: `GET /api/health`
- **Response `200 OK`**:
```json
{
  "status": "ok",
  "version": "1.0.0",
  "member4_active": true,
  "message": "Meeting Intelligent System API is operational."
}
```

### 16.2. Process Meeting: `POST /api/meetings/process`
- **Request `multipart/form-data`**:
  - `meeting_id`: (string, required) Valid alphanumeric identifier.
  - Exactly one of:
    - `audio`: (file, optional) Supported formats: `.wav`, `.mp3`, `.m4a`, `.flac`, `.ogg`, `.webm`, `.mp4`.
    - `transcript_file`: (file, optional) Supported formats: `.txt`, `.json`.
    - `transcript_text`: (string, optional) Verbatim dialogue turns.
  - `force_reprocess`: (boolean, optional) Default `false`.
- **Response `200 OK`**: Returns `DashboardPayload` matching Section 15.1.
- **Error Responses**:
  - `400 Bad Request`: Validation failure (empty input, conflicting sources, invalid formats, or path traversal).
  - `500 Internal Server Error`: Pipeline execution failure with sanitized error detail.

---

## 17. Proposed Member 4 Output Schema Specification (Phase 10 Final)

The output contract represents the fully enriched intelligence payload emitted after Member 4 processing:

### Top-Level Output: `Member4Output`


```json




{
    "meeting_id": "ES2002a",
    "processing_stage": "member_4_complete",
    "metadata": {
        "source_audio": "data/ami/amicorpus/ES2002a/audio/ES2002a.Mix-Headset.wav",
        "total_action_items": 32,
        "total_decisions": 9,
        "items_flagged_for_review": 6
    },
    "action_items": [
        {
            "item_id": "act_001",
            "task": "Work on the actual working design of the remote control",
            "responsible_person": "SPEAKER_00",
            "deadline": "30 minutes",
            "topic_reference": 40,
            "priority": {
                "level": "HIGH",
                "score": 0.88,
                "factors": {
                    "deadline_urgency": 0.95,
                    "semantic_criticality": 0.85,
                    "dependency_importance": 0.80
                },
                "reason": "Immediate relative deadline (30 mins) assigned by meeting lead."
            },
            "confidence": {
                "overall": 0.92,
                "task_confidence": 0.95,
                "person_confidence": 0.90,
                "deadline_confidence": 0.95,
                "priority_confidence": 0.88,
                "evidence": [
                    "Direct imperative assignment by SPEAKER_03 to SPEAKER_00",
                    "Explicit temporal marker 'in 30 minutes' found in segment 204"
                ]
            },
            "triage": {
                "needs_human_review": false,
                "review_priority": "LOW",
                "review_reasons": []
            },
            "context": {
                "topic_title": "Design Phase Kickoff",
                "topic_summary": "The team concludes presentations and prepares for breakout design.",
                "dialogue_snippet": "SPEAKER_03: The next meeting is in 30 minutes. David, as the industrial designer, work on the physical design.",
                "speaker_roster": ["SPEAKER_03", "SPEAKER_00"]
            }
        }
    ],
    "key_decisions": [
        {
            "decision_id": "dec_001",
            "decision": "Remote controls should be designed to work together, even though they are separate for different functions",
            "topic_reference": 36,
            "topic_summary": "Discussion regarding multi-component remote integration.",
            "confidence": 0.89,
            "needs_human_review": false
        }
    ],
    "personalized_views": {
        "manager_view": {
            "summary": "Executive summary of milestones and review bottlenecks",
            "action_items_count": 32,
            "pending_reviews_count": 6
        },
        "developer_view": {
            "assigned_tasks": ["act_001"],
            "technical_decisions": ["dec_001"]
        },
        "intern_view": {
            "assigned_tasks": [],
            "learning_notes": "Review remote control ergonomic standards."
        }
    }
}
```

---

## 13. Comparative Summary: ACTUAL INPUT vs. PROPOSED OUTPUT

| Characteristic | ACTUAL CURRENT INPUT (`Member4Input`) | PROPOSED MEMBER 4 OUTPUT (`Member4Output`) |
| :--- | :--- | :--- |
| **Origin** | Member 3 extraction JSON | Member 4 post-processing pipeline |
| **Item Identifier** | None (array index only) | Deterministic ID (`act_001`, `dec_001`) |
| **Priority** | Raw string (`"High"`, `"Normal"`) or `None` | Structured object: `level`, `score` (0.0–1.0), `factors`, `reason` |
| **Confidence** | Opaque single float (`0.95`) or `None` | Decomposed vector: `task`, `person`, `deadline`, `overall`, `evidence` |
| **Review Triage** | Not present | Explicit `needs_human_review`, `review_priority`, `review_reasons` |
| **Context** | Integer `topic_reference` only | Hydrated topic summary, speaker roster, dialogue citations |
| **Personalization**| Flat global arrays | Tailored `manager_view`, `developer_view`, `intern_view` |
| **UI Dependency** | **None** (Pure JSON) | **None** (Pure JSON; UI consumes this headless contract) |

---

## 14. UI Independence & Versioning

- **UI Independence:** The data contracts in `backend/member4/schemas.py` are strictly decoupled from rendering libraries. They contain zero references to Streamlit, HTML, CSS, or frontend state.
- **Versioning Strategy:** Member 4 schemas utilize semantic versioning in metadata (`contract_version: "1.0.0"`). Any future schema evolutions will support backward-compatible deserialization via Pydantic default factories.



