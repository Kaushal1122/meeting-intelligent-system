# Member 4 Technical Architecture Specification
## Post-Extraction Contextual Intelligence, Multi-Factor Scoring, Human-in-the-Loop Triage, and Role-Personalized Delivery Layer

- **Document Version:** 1.0.0 (Phase 0 Definition)
- **Project:** Meeting Intelligence System (`meeting-intelligent-system`)
- **Component:** Member 4 (Post-Extraction Intelligence & Presentation Layer)
- **Status:** Specification Only (No Implementation Code in Phase 0)
- **Author:** Member 4 Engineering & Research

---

## 1. Project Context & Current System Baseline

The `meeting-intelligent-system` is an offline-capable, local-first meeting intelligence extraction pipeline. It processes multi-party conversational meetings into structured records through sequential modules known as "Members":

```
┌──────────────────────────────┐
│           Audio /            │
│       Text Transcript        │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│           Member 1           │  WhisperX (ASR + Word Alignment)
│ Audio & Diarization Pipeline │  Pyannote Diarization 3.1
└──────────────┬───────────────┘  data/processed/<id>_speaker_transcript.json
               │
               ▼
┌──────────────────────────────┐
│           Member 2           │  all-MiniLM-L6-v2 (Sliding Centroid Segmentation)
│  Segmentation & Summarizer   │  facebook/bart-large-cnn (Chunked Abstractive Summaries)
└──────────────┬───────────────┘  data/processed/<id>_member2_results.json
               │
               ▼
┌──────────────────────────────┐
│           Member 3           │  Ollama qwen2.5:3b (Few-Shot Semantic Extraction)
│  LLM Semantic Task Extractor │  Pydantic Schema Enforcement
└──────────────┬───────────────┘  data/processed/<id>_member3_results.json
               │
               ▼
┌──────────────────────────────┐
│           Member 4           │  [PROPOSED IN THIS SPECIFICATION]
│ Post-Extraction Intelligence │  Context Engine, Multi-Factor Priority, Sub-Attribute
│       & Delivery Layer       │  Confidence, Review Triage, Explainability, Personalization
└──────────────────────────────┘
```

### Module Responsibilities Prior to Member 4:
- **Member 1 (`backend/speaker_aware_transcription.py`, `backend/preprocessing/`):** Transcribes raw audio with speech-to-text, performs word-level acoustic alignment, separates speakers via Pyannote diarization, normalizes speaker tags (`SPEAKER_01`), and exports normalized transcript segments.
- **Member 2 (`backend/summarization/topic_segmenter.py`, `backend/summarization/summarizer.py`):** Ingests transcript segments, applies semantic centroid cosine similarity to cluster segments into coherent topics while filtering conversational noise/fillers, generates BART abstractive summaries per topic, and logs source segment provenance.
- **Member 3 (`backend/extraction/task_extractor.py`, `backend/extraction/schemas.py`):** Batches Member 2 topics, queries local LLM (`qwen2.5:3b`) via Ollama with strict few-shot extraction prompts, enforces Pydantic structured output, and produces isolated action items and key decisions linked by integer `topic_reference`.

---

## 2. Problem Statement

While Member 3 successfully outputs structured JSON containing extracted tasks and decisions, raw LLM-extracted meeting records exhibit substantial operational gaps before they can be effectively consumed in workplace settings:

1. **Lack of Operational Prioritization:** LLMs assign coarse or flat priorities based on surface keywords rather than holistic project constraints, semantic criticality, deadline proximity, or topic importance.
2. **Opaque & Uncalibrated Confidence:** A single floating-point number output by an LLM does not reflect true statistical confidence, nor does it distinguish whether uncertainty stems from the assigned person, the task description, or the deadline timeframe.
3. **Absence of Contextual Provenance:** Extracted items are stripped of surrounding dialogue, topic summaries, and overarching meeting goals, forcing users to navigate back to raw transcripts to verify meaning.
4. **No Automated Review Triage:** Without a confidence-driven human-in-the-loop review mechanism, users must manually inspect 100% of extracted items to catch errors and hallucinations.
5. **One-Size-Fits-All Representation:** Engineering leads, project managers, and individual contributors receive identical uncurated lists, creating cognitive overload and irrelevant notifications.

**Member 4 is designed as an independent intelligence and delivery layer** that transforms raw extracted meeting data into:
- **Priority-aware** intelligence
- **Confidence-aware** intelligence
- **Context-aware** intelligence
- **Human-review-aware** intelligence
- **Explainable** intelligence
- **Role-personalized** delivery

> [!NOTE]
> *Terminology Note:* Techniques described herein are formulated as **candidate technical mechanisms for investigation** and require thorough prior-art and patentability assessment before asserting novelty.

---

## 3. Existing Limitations Analysis

To ensure scientific rigor, system limitations are categorized into three distinct classes:

| Class | Definition |
| :--- | :--- |
| **Class A: Observed Project Limitation** | Specifically verified by inspecting current code, schemas, and processed JSON files in `meeting-intelligent-system`. |
| **Class B: General Design Problem** | Documented industry-wide challenge in natural language processing and meeting intelligence systems. |
| **Class C: Hypothesis for Evaluation** | Testable premise regarding whether Member 4's proposed mechanisms will measurably improve outcomes. |

### Detailed Breakdown:

1. **Priority Granularity & Accuracy**
   - *Class A (Observed):* In `data/processed/ES2002a_member3_results.json`, Member 3 outputs 32 action items where 28 are labeled `"Medium"` or `"Normal"`, with rudimentary `"High"` tags on non-critical introductory tasks. The prompt relies on LLM intuition without objective criteria.
   - *Class B (General):* Keyword-based priority assignment in generative LLMs fails to synthesize multi-factor temporal urgency with semantic dependency.
   - *Class C (Hypothesis):* A multi-factor priority inference model incorporating deadline proximity, active speaker role, and topic context will achieve higher F1-score than raw LLM priority assignment.

2. **Confidence Calibration & Sub-Attribute Granularity**
   - *Class A (Observed):* Member 3 outputs a static `confidence_score` (frequently `0.9` or `0.95` across disparate extractions). If an item has an explicit task but an ambiguous assignee, the entire item receives a single opaque score. Furthermore, in `backend/extraction/schemas.py`, the `needs_human_review` boolean was lost due to class duplication.
   - *Class B (General):* LLM token probabilities and prompted confidence scores correlate poorly with empirical factual correctness (poor calibration).
   - *Class C (Hypothesis):* Decoupling confidence into sub-attributes (`task_confidence`, `person_confidence`, `deadline_confidence`) and grounding them in linguistic and structural evidence yields superior calibration error (ECE).

3. **Context Disconnection**
   - *Class A (Observed):* Member 3 output retains only an integer `topic_reference`. All topic summaries, active dialogue snippets, and speaker rosters computed by Member 2 are dropped from the Member 3 JSON file.
   - *Class B (General):* Isolated action item text often lacks self-contained referents (e.g., *"work on it"* or *"send the file"*), rendering tasks unintelligible without context.
   - *Class C (Hypothesis):* Hydrating tasks with synthesized topic summaries and dialogue context enables accurate downstream classification without re-prompting large foundation models.

4. **Lack of Explainability**
   - *Class A (Observed):* Member 3 provides zero rationale for why an action item was marked high priority or why an assignee was attributed.
   - *Class B (General):* Opaque AI assertions decrease human trust and increase verification overhead in enterprise workflows.
   - *Class C (Hypothesis):* Generating structured evidence trails for priority and confidence flags reduces human verification time in review workflows.

5. **Role-Agnostic Output**
   - *Class A (Observed):* Member 3 produces a single flat array of action items and decisions.
   - *Class B (General):* Different organizational stakeholders require distinct granularities: executives need strategic decisions and deadlines; individual engineers need specific technical action items and dependencies.
   - *Class C (Hypothesis):* Filtering and restructuring a shared meeting state into personalized views improves user task comprehension and reduces task triage duration.

---

## 4. Member 4 Architectural Concept & Technical Contributions

Member 4 sits downstream of Member 3 as an independent post-processing and contextual intelligence layer:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              MEMBER 3 EXTRACTION OUTPUT                                │
│                   (action_items, key_decisions, topic_reference)                       │
└──────────────────────────────────────────┬─────────────────────────────────────────────┘
                                           │
                                           ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              MEMBER 4 INTELLIGENCE LAYER                               │
│                                                                                        │
│  ┌──────────────────────────────────────────────────────────────────────────────────┐  │
│  │ 1. Ingestion, Validation & Adapter Normalization                                 │  │
│  │    - Validates Member 3 payload schema                                           │  │
│  │    - Cross-links with Member 2 topic summaries & speaker rosters                 │  │
│  └───────────────────────────────────────┬──────────────────────────────────────────┘  │
│                                          │                                             │
│                                          ▼                                             │
│  ┌──────────────────────────────────────────────────────────────────────────────────┐  │
│  │ 2. Context Synthesis Engine                                                      │  │
│  │    - Assembles unified Task-Topic-Meeting context bundle                         │  │
│  │    - Resolves anaphoric references, temporal baselines, and speaker metadata     │  │
│  └───────────────────┬──────────────────────────────────────┬───────────────────────┘  │
│                      │                                      │                          │
│                      ▼                                      ▼                          │
│  ┌───────────────────────────────────────┐  ┌───────────────────────────────────────┐  │
│  │ 3. Multi-Factor Priority Inference    │  │ 4. Sub-Attribute Confidence Engine    │  │
│  │    - Deadline urgency scoring         │  │    - Task semantic validity           │  │
│  │    - Semantic criticality analysis    │  │    - Person attribution grounding     │  │
│  │    - Topic & decision relevance       │  │    - Deadline temporal explicitness   │  │
│  │    - Continuous score -> High/Med/Low │  │    - Calibrated composite confidence  │  │
│  └───────────────────┬───────────────────┘  └───────────────────┬───────────────────┘  │
│                      │                                      │                          │
│                      └───────────────────┬──────────────────┘                          │
│                                          │                                             │
│                                          ▼                                             │
│  ┌──────────────────────────────────────────────────────────────────────────────────┐  │
│  │ 5. Human-in-the-Loop Triage Evaluator                                            │  │
│  │    - Threshold-based uncertainty flagging (`needs_human_review: true`)           │  │
│  │    - Contradiction & low-confidence trigger detection                            │  │
│  │    - Review reason categorization                                                │  │
│  └───────────────────────────────────────┬──────────────────────────────────────────┘  │
│                                          │                                             │
│                                          ▼                                             │
│  ┌──────────────────────────────────────────────────────────────────────────────────┐  │
│  │ 6. Explainability & Evidence Generator                                           │  │
│  │    - Priority factor attribution summary                                         │  │
│  │    - Confidence evidence breakdown & dialogue citation                           │  │
│  └───────────────────────────────────────┬──────────────────────────────────────────┘  │
│                                          │                                             │
│                                          ▼                                             │
│  ┌──────────────────────────────────────────────────────────────────────────────────┐  │
│  │ 7. Multi-Role Personalization Transform                                          │  │
│  │    - Manager View: High-level decisions, team allocation, critical deadlines     │  │
│  │    - Developer View: Direct assignments, technical context, immediate blockers   │  │
│  │    - Intern View: Assigned duties, surrounding discussions, background summaries │  │
│  └──────────────────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────┬─────────────────────────────────────────────┘
                                           │
                                           ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        MEMBER 4 ENRICHED INTELLIGENCE ARTIFACT                         │
│                           & INTERACTIVE REVIEW DASHBOARD                               │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Input Data Contract & Normalization Adapter

### 5.1. Actual Inspected Member 3 Output
Inspection of `data/processed/ES2002a_member3_results.json` reveals the exact current structure produced by Member 3:

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

### 5.2. Observed Structural Gaps in Member 3 Output:
1. **No Global Summary:** Top-level meeting summary is absent.
2. **No Embedded Topic Context:** `topics` array from Member 2 is omitted; only the foreign key `topic_reference` exists.
3. **Coarse LLM Fields:** `priority` is a raw string (`"High"`, `"Medium"`, `"Normal"`); `confidence_score` is a single static float.
4. **Missing Review Flag:** `needs_human_review` is not present in the serialized JSON.

### 5.3. Member 4 Ingestion Adapter Strategy
To adhere strictly to the **Absolute Protection Rule** (zero modifications to Member 1, 2, or 3 code), Member 4 incorporates an **Ingestion & Normalization Adapter**:

```
                               ┌──────────────────────────────────────────────┐
                               │  data/processed/<id>_member3_results.json    │
                               │  (Action items, Decisions, topic_reference)  │
                               └──────────────────────┬───────────────────────┘
                                                      │
                                                      ▼
┌─────────────────────────────────────────────┐   ┌───────────────────────────┐
│  data/processed/<id>_member2_results.json   ├──►│ Member 4 Adapter Layer    │
│  (Topic summaries, segments, speakers)      │   │ - Joins via topic_reference│
└─────────────────────────────────────────────┘   │ - Validates schemas       │
                                                  │ - Imputes fallback defaults│
                                                  └───────────┬───────────────┘
                                                              ▼
                                                  Normalized Ingestion Model
```

- If `*_member2_results.json` is available, Member 4 joins on `topic_reference == topic_id` to retrieve topic summaries, start/end timestamps, and active speaker identities.
- If `*_member2_results.json` is missing, the Adapter operates in **degraded standalone mode**, populating context fields with defaults without failing.

### 5.4. Stage 4: Multi-Factor Priority Inference Implementation (Phase 4)
Phase 4 implements a context-aware, deterministic priority inference model ([`backend/member4/priority_engine.py`](file:///c:/Users/chaha/OneDrive/Desktop/meeting-intelligent-system/backend/member4/priority_engine.py)) that computes continuous priority scores and categorical classifications across 7 grounded context factors:

$$\text{Priority Score} = \sum_{i=1}^{7} w_i \times v_i \quad \in [0.0, 1.0]$$

| Factor Name | Weight ($w_i$) | Core Mechanism & Grounded Evidence |
| :--- | :--- | :--- |
| `deadline_urgency` | 0.25 | Evaluates explicit deadlines: session breakout / $\le 60$ min ($0.95$), same day ($0.70$), near term ($0.50$), medium ($0.30$), distant ($0.15$), ambiguous ($0.10–0.40$), missing ($0.0$). |
| `explicit_urgency_language` | 0.15 | Detects critical urgency vocabulary in dialogue/task turns ($0.90$), moderate urgency ($0.50$), ordinary text ($0.0$). |
| `assignment_explicitness` | 0.15 | Identifies second-person imperative commands to assignee in dialogue ($0.85$), self-commitments ($0.50$), metadata only ($0.40$), unassigned ($0.0$). |
| `dependency_blocker` | 0.15 | Detects blockers ($0.85$), sequential breakout milestone prerequisites ($0.60$), none ($0.0$). |
| `decision_linkage` | 0.10 | Aligned single decision ($0.40$), multiple competing alternatives handled conservatively ($0.20$), none ($0.0$). |
| `deliverable_specificity` | 0.10 | Concrete engineering deliverables ($0.85$), standard task ($0.55$), exploratory discussion ($0.30$). |
| `context_quality` | 0.10 | Completeness of context resolution: `RESOLVED` ($1.00$), `PARTIALLY_RESOLVED` ($0.50$), `UNRESOLVED` ($0.20$), `MISSING` ($0.0$). |

**Classification Tiers:**
- $\text{HIGH}: \text{Score} \ge 0.65$
- $\text{MEDIUM}: 0.35 \le \text{Score} < 0.65$
- $\text{LOW}: \text{Score} < 0.35$

**Source Priority Independence:** Member 3's source `priority` string is strictly decoupled from the mathematical inference and retained purely as informational source metadata.

### 5.5. Stage 5: Multi-Factor Confidence Intelligence Implementation (Phase 5)
Phase 5 implements a deterministic, evidence-grounded confidence intelligence model ([`backend/member4/confidence_engine.py`](file:///c:/Users/chaha/OneDrive/Desktop/meeting-intelligent-system/backend/member4/confidence_engine.py)) that estimates the factual reliability of each action item based on 7 grounded evidence factors:

$$\text{Confidence Score} = \sum_{i=1}^{7} w_i \times v_i \quad \in [0.0, 1.0]$$

| Factor Name | Weight ($w_i$) | Grounded Evidence Evaluation Criteria |
| :--- | :---: | :--- |
| `context_resolution` | 0.20 | Degree of topic join completeness: `RESOLVED` ($1.00$), `PARTIALLY_RESOLVED` ($0.50$), `UNRESOLVED` ($0.20$), `MISSING_REFERENCE` ($0.00$). |
| `localized_evidence_grounding` | 0.20 | Structural dialogue/timestamps/speakers (up to $0.40$) + task lexical corroboration in turns (up to $0.60$). |
| `task_assignee_consistency` | 0.15 | Explicit dialogue delegation / commitment ($1.00$), metadata active speaker ($0.70$), metadata passive ($0.50$), unassigned baseline ($0.35$). |
| `deadline_evidence_quality` | 0.15 | Explicit deadline verified by snippet ($1.00$), explicit metadata ($0.80$), missing deadline neutral baseline ($0.60$), ambiguous deadline ($0.30$). |
| `topic_resolution_quality` | 0.10 | Verified topic with abstractive summary ($1.00$), topic metadata only ($0.50$), unresolved ($0.20$), missing ($0.00$). |
| `decision_evidence_consistency` | 0.10 | Aligned single decision ($1.00$), zero decisions neutral baseline ($0.60$), multiple competing alternatives ($0.20$). |
| `structural_completeness` | 0.10 | Item ID ($+0.25$), task length $\ge 3$ words ($+0.25$), provenance tracking ($+0.25$), clean diagnostics ($+0.25$). |


**Classification Tiers:**
- $\text{HIGH}: \text{Score} \ge 0.75$
- $\text{MEDIUM}: 0.50 \le \text{Score} < 0.75$
- $\text{LOW}: \text{Score} < 0.50$

**Architectural Decoupling from Priority:** Confidence measures evidence certainty, not task urgency. A task may be high-priority with low-confidence (e.g. urgent blocker with ambiguous deadline), or low-priority with high-confidence (e.g. routine agenda item with complete dialogue turns).

**Source Confidence Independence:** Member 3's source `confidence_score` is strictly preserved under `source_confidence_score` as informational metadata and has zero influence over Member 4's mathematical inference.

### 5.6. Phase 6: Human Review & Uncertainty Handling Engine

Phase 6 implements a deterministic uncertainty triage layer ([`backend/member4/review_engine.py`](file:///c:/Users/chaha/OneDrive/Desktop/meeting-intelligent-system/backend/member4/review_engine.py)) that consumes the enriched outputs of Phases 1–5 to classify action items into three operational states:
1. **`AUTO_ACCEPT`**: Strong contextual and dialogue evidence; zero material uncertainty signals. Automatically accepted for downstream execution.
2. **`REVIEW_RECOMMENDED`**: Usable but contains moderate uncertainty (e.g. high-priority with medium-confidence, competing topic decisions, weak dialogue grounding, or partial context). Human verification is suggested.
3. **`REVIEW_REQUIRED`**: Material evidence problem or high-risk combination (e.g. high-priority with low-confidence, unresolved/missing topic context, unassigned high-priority deliverable, or ambiguous deadline on an urgent task). Mandatory review prior to execution.

**Priority + Confidence Orthogonal Interaction:**
- The engine explicitly detects cross-dimensional interactions:
  - $\text{HIGH Priority} + \text{LOW Confidence} \implies \mathbf{REVIEW\_REQUIRED}$
  - $\text{HIGH Priority} + \text{MEDIUM Confidence} \implies \mathbf{REVIEW\_RECOMMENDED}$
  - $\text{LOW Priority} + \text{HIGH Confidence} \implies \mathbf{AUTO\_ACCEPT}$
- Neither priority nor confidence scores are recomputed or modified by the triage engine; they serve strictly as input evidence.
- Missing optional information (e.g., missing deadline or missing decision linkage on routine items) does **not** trigger review, preventing human review fatigue while catching genuine contradictions and ungrounded hallucinations.

### 5.7. Phase 7: Explainability Engine

Phase 7 implements a deterministic, read-only explainability layer ([`backend/member4/explainability_engine.py`](file:///c:/Users/chaha/OneDrive/Desktop/meeting-intelligent-system/backend/member4/explainability_engine.py)) that answers *why* specific priority scores, confidence assessments, and triage decisions were assigned:

1. **Read-Only Architecture & Zero Decision Drift:**
   Explainability is an observational interpretation layer. It consumes the outputs of Phases 2–6 and constructs human- and machine-readable explanation trails without altering any priority scores, confidence scores, review states, or reason codes.
2. **Mathematical Consistency:**
   Every factor's weighted contribution ($w_i \times v_i$) is mathematically verified, guaranteeing $\sum (w_i \times v_i) = \text{Score}$ within $10^{-4}$ tolerance.
3. **Deterministic Factor Ranking:**
   Factors are ranked deterministically by contribution descending with alphabetical tie-breaking on factor names.
4. **Verifiable Provenance Traces:**
   Evidence references point directly to concrete source artifacts (topic IDs, segment IDs, verbatim text snippets, and decision IDs) without synthetic or hallucinated evidence.
5. **Supporting vs. Limiting Evidence:**
   Clearly partitions positive reinforcement evidence from limiting uncertainty factors, while accurately treating missing optional fields as neutral baselines.

### 5.8. Phase 8: Personalization Engine

Phase 8 implements a deterministic presentation and role-projection layer ([`backend/member4/personalization_engine.py`](file:///c:/Users/chaha/OneDrive/Desktop/meeting-intelligent-system/backend/member4/personalization_engine.py)) that projects the fully explained canonical intelligence payload into role-specific views (`MANAGER`, `DEVELOPER`, `INTERN`, `DEFAULT`) without modifying underlying intelligence decisions:

1. **Strict Canonical Preservation:**
   Personalization is an observational transformation layer. For every action item, the canonical priority score, priority level, confidence score, confidence level, review status, and review reason codes are strictly preserved.
2. **Role Profiles:**
   - **`MANAGER`**: Emphasizes strategic delivery: highest priority items, near-term deadlines, responsible owners, and review triggers.
   - **`DEVELOPER`**: Emphasizes technical execution: task descriptions, localized context, transcript evidence, and dependency blockers.
   - **`INTERN`**: Emphasizes clarity and actionability: straightforward context summaries, owner coordination, and clear review alerts (uncertainty is never hidden).
   - **`DEFAULT`**: Preserves canonical sequence and complete intelligence metadata.
3. **Deterministic Ordering & Filtering:**
   Sorting applies explicit role-based priority hierarchies with `item_id` ascending tie-breakers. Optional filters select display items without mutating the underlying intelligence records.

### 5.9. Phase 9: React Dashboard / UI Presentation Layer

Phase 9 implements a modern React + TypeScript web dashboard ([`frontend/`](file:///c:/Users/chaha/OneDrive/Desktop/meeting-intelligent-system/frontend/)) to visualize the canonical intelligence produced by Member 4:

1. **Pure Presentation Role:** The dashboard does not execute NLP, priority calculations, confidence calibrations, or triage logic. It consumes structured pre-computed Member 4 payloads.
2. **Component Architecture:**
   - **`Header`**: Displays meeting metadata (`ES2002a`) and role switcher (`MANAGER`, `DEVELOPER`, `INTERN`, `DEFAULT`).
   - **`SummaryCards`**: 8 dynamic cards reflecting total tasks (32), priority counts, review triage counts, and key decisions (9).
   - **`DistributionCharts`**: Visual progress bars illustrating priority distributions, confidence calibrations, and human review status.
   - **`FilterBar`**: Multi-dimensional deterministic filtering (priority, confidence, review status, assignment, deadline, and keyword search).
   - **`ActionItemTable`**: Sortable, accessible table with visual badges for priority, confidence, review status, and role guidance.
   - **`ActionItemDetailModal`**: Deep inspection slide-over exposing priority factor tables ($w_i \times v_i$), confidence assessments, triage reason codes, verbatim transcript segments with timestamps, and linked key decisions.
3. **Canonical Preservation:** Guarantees 100% decision invariance between data source and visual rendering.

### 5.10. Phase 10: End-to-End Integration & API Transport Layer

Phase 10 connects raw user inputs (audio, transcript files, or pasted transcript text) directly to the complete Meeting Intelligent System through a dedicated FastAPI backend ([`backend/api/`](file:///c:/Users/chaha/OneDrive/Desktop/meeting-intelligent-system/backend/api/)):

1. **Pipeline Flow:**
   $$\begin{matrix} \text{React Input Widget} \\ \downarrow \\ \text{FastAPI (POST /api/meetings/process)} \\ \downarrow \\ \text{Input Adapter \& Safe Temp Storage} \\ \downarrow \\ \text{Member 1 (Audio) / Preprocessing (Transcript)} \\ \downarrow \\ \text{Member 2 (Segmentation \& BART Summarization)} \\ \downarrow \\ \text{Member 3 (Qwen 2.5:3b Extraction via Ollama)} \\ \downarrow \\ \text{Member 4 (Intelligence Pipeline: Phases 1–8)} \\ \downarrow \\ \text{Standard DashboardPayload JSON} \\ \downarrow \\ \text{React Dashboard Live State Update} \end{matrix}$$
2. **Strict Upstream Boundary:** Zero modifications were introduced into Member 1, Member 2, Member 3, or `backend/pipeline.py`. All integration coordination is contained within `backend/api/`.
3. **Canonical Invariance & Real Data Precedence:** Upon successful API processing, real backend data replaces any static reference fixture while ensuring 100% mathematical consistency with Member 4 engines.

---

## 11. Proposed Member 4 Enriched Output Specification

The proposed output data contract provides a comprehensive, production-grade schema:

```json





{
    "meeting_id": "ES2002a",
    "processing_stage": "member_4_intelligence_complete",
    "generated_at": "2026-09-03T21:15:00Z",
    "metadata": {
        "source_audio": "data/ami/amicorpus/ES2002a/audio/ES2002a.Mix-Headset.wav",
        "total_topics": 45,
        "total_action_items": 32,
        "total_decisions": 9,
        "items_flagged_for_review": 6
    },
    "meeting_summary": {
        "executive_summary": "Kickoff meeting for remote control design project...",
        "key_themes": ["remote control ergonomics", "mascot selection", "cost constraints"]
    },
    "action_items": [
        {
            "item_id": "act_001",
            "task": "Work on the actual working design of the remote control",
            "responsible_person": "SPEAKER_00",
            "responsible_person_name": "David (Industrial Designer)",
            "deadline": "30 minutes",
            "deadline_standardized": "PT30M",
            "topic_reference": 40,
            
            "priority": {
                "level": "HIGH",
                "score": 0.88,
                "factors": {
                    "deadline_urgency": 0.95,
                    "semantic_criticality": 0.85,
                    "dependency_importance": 0.80,
                    "speaker_authority": 0.90
                },
                "reason": "Immediate relative deadline (30 mins) assigned by Project Manager for core product deliverable."
            },
            
            "confidence": {
                "overall": 0.92,
                "task_confidence": 0.95,
                "person_confidence": 0.90,
                "deadline_confidence": 0.95,
                "priority_confidence": 0.88,
                "calibration_status": "CALIBRATED",
                "evidence": [
                    "Direct imperative assignment by SPEAKER_03 to SPEAKER_00",
                    "Explicit temporal marker 'in 30 minutes' verified in dialogue segment 204",
                    "High lexical similarity to topic 40 summary"
                ]
            },
            
            "triage": {
                "needs_human_review": false,
                "review_priority": "LOW",
                "review_reasons": []
            },
            
            "context": {
                "topic_title": "Post-Break Design Phase Transition",
                "topic_summary": "The team concludes initial presentations and prepares for breakout design work.",
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
            "impact_level": "ARCHITECTURAL",
            "confidence": 0.89,
            "needs_human_review": false
        }
    ],
    "personalized_views": {
        "manager_view": {
            "summary_focus": "Executive overview of project milestones and resource bottlenecks",
            "action_items_count": 32,
            "urgent_deadlines_count": 4,
            "pending_reviews_count": 6,
            "items_by_person": {
                "SPEAKER_00": ["act_001", "act_011"],
                "SPEAKER_01": ["act_006"]
            }
        },
        "developer_view": {
            "focus_user": "SPEAKER_00",
            "assigned_tasks": ["act_001", "act_011"],
            "technical_decisions": ["dec_001"],
            "immediate_blockers": []
        },
        "intern_view": {
            "focus_user": "SPEAKER_01",
            "assigned_tasks": ["act_006"],
            "orientation_notes": "Review mascot design guidelines discussed in Topic 10."
        }
    }
}
```

---

## 7. Ten-Stage Processing Flow

Member 4 executes as a pipeline of ten discrete, testable stages:

```
Stage 1: Input Validation
   │  - Validates Member 3 JSON against expected ingestion schema
   │  - Validates Member 2 JSON if provided
   ▼
Stage 2: Normalization & Adapter Hydration
   │  - Reconciles missing fields and joins Member 2 topic context on topic_reference
   │  - Assigns unique item IDs (act_001, dec_001)
   ▼
Stage 3: Context Construction
   │  - Synthesizes task text, topic summaries, dialogue snippets, and speaker rosters
   │  - Establishes timeline reference anchors
   ▼
Stage 4: Multi-Factor Priority Inference
   │  - Evaluates deadline urgency, semantic criticality, authority, and topic importance
   │  - Computes continuous priority score (0.0 - 1.0) and maps to HIGH / MEDIUM / LOW
   ▼
Stage 5: Sub-Attribute Confidence Estimation
   │  - Evaluates task validity, assignee certainty, and deadline explicitness
   │  - Generates sub-attribute scores and calibrated composite confidence
   ▼
Stage 6: Human Review Decisioning
   │  - Evaluates confidence thresholds, contradictory markers, and missing references
   │  - Sets needs_human_review flag and categorizes review reasons
   ▼
Stage 7: Explainability & Evidence Grounding
   │  - Generates human-readable rationale strings for priority assignment
   │  - Produces evidence trails citing supporting transcript dialogue
   ▼
Stage 8: Meeting-Level Synthesis
   │  - Aggregates topic summaries into global meeting narrative and identifies key themes
   ▼
Stage 9: Multi-Role Personalization Transformation
   │  - Projects enriched meeting state into role-filtered structures (Manager, Dev, Intern)
   ▼
Stage 10: Presentation & Export Formatting
      - Emits verified Member 4 Enriched JSON artifact
      - Prepares structured state for interactive review dashboard
```

---

## 8. Priority Mechanism — Detailed Design

### 8.1. Architectural Philosophy
Priority will **not** be hardcoded via naive keyword rules (e.g., `if "urgent" in text: HIGH`). Rather, Member 4's priority mechanism is formulated as a **multi-factor weighted scoring model** with modular feature extraction:

$$\text{PriorityScore} = \sum_{k} w_k \cdot f_k(\text{Task}, \text{Context})$$

where $\sum w_k = 1.0$ and $f_k \in [0, 1]$.

### 8.2. Evaluated Feature Signals ($f_k$):
1. **Temporal / Deadline Urgency ($f_{\text{deadline}}$):**
   - Imminent relative deadline ($< 2$ hours, e.g. `"30 minutes"`): $1.0$
   - Same-day / next-day deadline: $0.8$
   - Weekly / milestone deadline: $0.5$
   - No deadline specified (`"None mentioned"`): $0.2$
2. **Semantic Task Criticality ($f_{\text{semantic}}$):**
   - Action verbs expressing essential core delivery (*"design"*, *"fix"*, *"implement"*, *"finalize"*): $0.8 - 1.0$
   - Exploratory / optional tasks (*"look into"*, *"maybe consider"*, *"think about"*): $0.2 - 0.4$
   - Administrative / conversational tasks (*"introduce"*, *"announce"*): $0.3$
3. **Speaker Authority & Project Role ($f_{\text{authority}}$):**
   - Assigned by Project Manager / Meeting Chair: $0.9$
   - Peer assignment / self-assignment: $0.6$
4. **Topic Importance & Decision Coupling ($f_{\text{topic}}$):**
   - Task directly linked to a recorded `KeyDecision`: $0.9$
   - Task located in agenda/wrap-up topic: $0.3$

### 8.3. Priority Mapping:
- **HIGH:** $\text{PriorityScore} \ge 0.75$
- **MEDIUM:** $0.40 \le \text{PriorityScore} < 0.75$
- **LOW:** $\text{PriorityScore} < 0.40$

---

## 9. Confidence Mechanism — Detailed Design

### 9.1. Multi-Component Decomposition
Rather than relying on a single prompted LLM estimate, confidence is decoupled into independently verifiable sub-components:

$$\text{Confidence}_{\text{composite}} = \alpha \cdot C_{\text{task}} + \beta \cdot C_{\text{person}} + \gamma \cdot C_{\text{deadline}} + \delta \cdot C_{\text{context}}$$

### 9.2. Sub-Attribute Evidence Signals:
1. **Task Confidence ($C_{\text{task}}$):**
   - Grammatical imperativeness: Presence of clear subject-action predicate.
   - Lexical clarity: Low ambiguity, absence of hedging words (*"might"*, *"could"*).
   - Topic semantic alignment: Embedding cosine similarity between task description and Member 2 topic text.
2. **Person Confidence ($C_{\text{person}}$):**
   - Explicit named attribution: Speaker explicitly named or addressed by ID.
   - Speaker presence in topic: Target speaker participated in the referenced topic.
   - Ambiguous attribution penalty: Decreased if multiple speakers debate responsibility.
3. **Deadline Confidence ($C_{\text{deadline}}$):**
   - Explicit temporal anchor: Explicit numeric/calendar expression present in source dialogue ($1.0$).
   - Vague temporal anchor (*"soon"*, *"later"*): $0.5$.
   - Explicitly missing: If `"None mentioned"`, deadline confidence is high that none exists, but temporal urgency feature receives minimum score.
4. **Context Consistency ($C_{\text{context}}$):**
   - Cross-check with Member 2 transcript segment IDs to ensure no hallucinated topics.

---

## 10. Contextual Intelligence & Human Review Triage

### 10.1. Context Synthesis Engine
Member 4 synthesizes a composite context bundle for each item by combining:
- The task statement from Member 3
- The Member 2 topic summary
- Surrounding dialogue segments ($\pm 2$ utterances around the triggering speech)
- Active participants in that segment
- Overlapping Key Decisions sharing the same `topic_reference`

This resolved context enables anaphoric resolution (e.g., resolving *"David, work on it"* to *"David (SPEAKER_00) must work on the physical remote control design"*).

### 10.2. Human Review Triage Rules
An item is automatically flagged with `needs_human_review = true` if any of the following triggers fire:
1. **Low Composite Confidence:** $\text{Confidence}_{\text{composite}} < \tau_{\text{confidence}}$ (e.g., $< 0.70$).
2. **Attribution Ambiguity:** Multiple candidate assignees detected or unassigned high-priority task.
3. **Temporal Inconsistency:** Contradictory deadlines mentioned in same topic window.
4. **Hallucination Alert:** `topic_reference` does not exist in Member 2 metadata.
5. **High Priority + Moderate Confidence:** Any task where $\text{Priority} == \text{HIGH}$ and $\text{Confidence} < 0.85$ (safeguarding critical deliverables).

---

## 11. Explainability & Personalization Mechanisms

### 11.1. Explainability Mechanism
For every prioritized and scored item, Member 4 produces structured, human-readable explanations:
- **Priority Rationale:** Cites the dominant contributing feature (e.g., *"Marked HIGH due to imminent 30-minute deadline assigned by meeting chair"*).
- **Confidence Evidence:** Cites verbatim dialogue quotes confirming the assignment and timestamps.

### 11.2. Role-Based Personalization Engine
Member 4 transforms the unified enriched meeting state into role-tailored perspectives:
1. **Manager View:**
   - Aggregated workload distribution across all identified team members.
   - Timeline of all upcoming deliverables sorted by priority.
   - Immediate visibility into items flagged for human review.
2. **Developer View:**
   - Strict filter for tasks assigned to the target developer or their immediate technical collaborators.
   - Associated technical decisions and architectural constraints.
   - Dialogue excerpts containing technical specifications.
3. **Intern View:**
   - Filter for onboarding-relevant tasks with step-by-step contextual background.
   - Detailed topic summaries explaining why decisions were made.

---

## 12. Evaluation Framework & Verification Metrics

Member 4 will be experimentally evaluated against the following quantitative criteria:

| Dimension | Metric | Measurement Method | Target Goal |
| :--- | :--- | :--- | :--- |
| **Priority** | Weighted F1-Score | Comparison against human-annotated priority labels (High/Med/Low) | $\text{F1} > 0.82$ |
| **Priority** | Precision on High-Priority | Ratio of true critical items among predicted High priority | $\text{Precision} \ge 0.85$ |
| **Confidence** | Expected Calibration Error (ECE) | Binned error between predicted confidence and empirical accuracy | $\text{ECE} < 0.08$ |
| **Confidence** | AUROC (Uncertainty Detection) | Ability of confidence score to discriminate correct vs erroneous extractions | $\text{AUROC} \ge 0.88$ |
| **Human Review** | Defect Detection Rate (Recall) | Percentage of flawed extractions flagged for human review | $\text{Recall} \ge 0.90$ |
| **Human Review** | False Review Rate | Percentage of clean items unnecessarily flagged | $\le 0.15$ |
| **Personalization**| Role Precision & Recall | Correct inclusion/exclusion of tasks relevant to target role | $> 0.92$ |
| **Performance** | Latency per Meeting | Wall-clock execution time for Member 4 enrichment layer | $< 1.5\text{s}$ (CPU) |

---

## 13. Proposed Future Implementation File Structure

The proposed file structure for future phases organizes Member 4 cleanly in a dedicated directory without touching Members 1, 2, or 3:

```
backend/
└── member4/
    ├── __init__.py                    # Module export definitions
    ├── schemas.py                     # Enriched Member 4 Pydantic data models
    ├── adapter.py                     # Ingestion & normalization adapter for Member 3 & 2 JSON
    ├── context_engine.py              # Dialogue, topic, and metadata context builder
    ├── priority/
    │   ├── __init__.py
    │   ├── features.py                # Feature extractors (deadline, semantic, authority)
    │   └── priority_scorer.py         # Multi-factor priority inference engine
    ├── confidence/
    │   ├── __init__.py
    │   ├── sub_attributes.py          # Task, person, deadline confidence estimators
    │   └── calibrator.py              # Calibration and composite confidence engine
    ├── triage/
    │   ├── __init__.py
    │   └── review_evaluator.py        # Rule & threshold-based human-in-the-loop triage
    ├── explainability/
    │   ├── __init__.py
    │   └── evidence_generator.py      # Natural-language and cited rationale builders
    └── personalization/
        ├── __init__.py
        └── role_projector.py          # Manager, Developer, Intern view transformers
```

---

## 14. Phase 0 Assumptions & Sign-Off Criteria

### Assumptions:
1. **Upstream Invariance:** Members 1, 2, and 3 outputs remain unmodified and serve as the immutable baseline data sources.
2. **Local Inference Constraints:** Member 4 enrichment logic must remain lightweight and executable on standard CPU hardware without requiring external cloud API calls.
3. **Data Completeness:** Member 4 operates effectively whether Member 2 output is present (full context mode) or missing (standalone fallback mode).

### Phase 0 Sign-Off Criteria:
- Complete architectural specification established in `docs/member4_architecture.md`.
- Intellectual property and prior-art questions cataloged in `docs/invention_notes.md`.
- Zero implementation code written in existing Member 1, 2, or 3 directories.
- Zero modifications to `pipeline.py` or existing tests.
- Automated and manual verification checklists satisfied.
