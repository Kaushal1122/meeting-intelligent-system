# Meeting Intelligent System — Complete Technical Architecture & System Documentation

**System Title:** Meeting Intelligent System  
**Lead Focus Layer:** Member 4 (Post-Extraction Intelligence & Multi-Perspective Presentation)  
**System Type:** AI-Powered Audio/Text Meeting Intelligence Platform  
**Architecture:** Multi-Tiered Modular Pipeline Architecture with FastAPI Backend & React Frontend  
**Date:** September 2026  
**Status:** Certified, Complete, and Frozen (Phases 0–11)

---

## Executive Summary

The **Meeting Intelligent System** is an end-to-end meeting analysis and operational intelligence platform. It transforms raw multi-speaker meeting audio or transcripts into calibrated, verifiable, role-tailored action items and key decisions.

The system is organized into a four-member pipeline:
1. **Member 1 (Audio Processing & Diarization):** Ingests raw audio, cleans acoustic streams, performs automatic speech recognition (ASR) via WhisperX, and segments turns using PyAnnote speaker diarization.
2. **Member 2 (Topic Segmentation & Summarization):** Ingests diarized dialogue turns, executes semantic sentence embeddings, clusters coherent topic boundaries, and generates abstractive topic summaries using Hugging Face transformers (`facebook/bart-large-cnn`).
3. **Member 3 (Semantic Information Extraction):** Ingests structured topic transcripts and uses a local Large Language Model (`qwen2.5:3b` via Ollama) to extract raw action items and candidate key decisions.
4. **Member 4 (Post-Extraction Intelligence & Multi-Perspective Presentation):** Consumes raw candidate outputs and applies a deterministic, mathematical, 7-stage intelligence pipeline:
   - Dynamic Speaker Resolution (transcript-grounded names with deterministic diarization fallback)
   - Validation & Normalization (deduplication, date parsing, timeline validation)
   - Contextual Intelligence ($\pm 2$ utterance dialogue windows and topic boundaries)
   - Continuous Urgency & Operational Priority Inference (7-factor linear model)
   - Evidence-Grounded Confidence Calibration (7-factor reliability scoring)
   - Human-in-the-Loop Review Triage (13 deterministic triage reason codes)
   - Natural Language Explainability (zero-drift factor attribution & verbatim dialogue provenance)
   - Persona Projections (`MANAGER`, `DEVELOPER`, `INTERN`, `DEFAULT` views with strict canonical invariance)
   - Interactive Glassmorphism Dashboard (React + TypeScript + Vite)
   - End-to-End REST API (FastAPI)

---

# PHASE 1 — COMPLETE PROJECT STRUCTURE ANALYSIS

## 1.1 High-Level Directory Tree

```
meeting-intelligent-system/
├── .env                                # Server-side environment secrets (gitignored)
├── .env.example                        # Template for environment configuration
├── .gitignore                          # Git ignore rules (Python, Node, cache, media)
├── README.md                           # Repository introduction and baseline overview
├── setup.md                            # Initial environment setup notes
├── requirements.txt                    # Backend Python dependencies
├── run_member3_test.py                 # Standalone Member 3 extraction runner
│
├── backend/                            # Complete backend Python codebase
│   ├── __init__.py                     # Package marker
│   ├── pipeline.py                     # Monolithic upstream pipeline runner (Members 1–3)
│   ├── speaker_aware_transcription.py  # Member 1 WhisperX + PyAnnote transcription pipeline
│   ├── transcribe.py                   # Standalone audio transcription helper
│   ├── test_diarization.py             # Diarization verification script
│   ├── test_transcription.py           # Transcription verification script
│   │
│   ├── preprocessing/                  # Member 1 & Shared Preprocessing
│   │   ├── input_handler.py            # Audio file extension validator & path handler
│   │   ├── speaker_normalizer.py       # Speaker label normalizer (SPEAKER_00, etc.)
│   │   ├── text_cleaner.py             # Transcript text regex cleaner
│   │   ├── transcript_processor.py     # Sentence splitter & raw line parser
│   │   ├── validate_output.py          # Intermediate schema validator
│   │   └── test_*.py                   # Preprocessing unit tests
│   │
│   ├── summarization/                  # Member 2 Summarization & Topic Segmentation
│   │   ├── __init__.py                 # Package marker
│   │   ├── topic_segmenter.py          # Semantic cosine similarity topic segmenter
│   │   ├── summarizer.py               # BART-large-CNN abstractive summarizer
│   │   ├── transcript_loader.py        # Diarized JSON transcript loader
│   │   └── test_*.py                   # Member 2 unit tests
│   │
│   ├── extraction/                     # Member 3 Semantic Task Extraction
│   │   ├── __init__.py                 # Package marker
│   │   ├── schemas.py                  # Pydantic extraction schemas
│   │   └── task_extractor.py           # Ollama / Qwen2.5:3b batch task extractor
│   │
│   ├── member4/                        # Member 4 Core Intelligence Layer
│   │   ├── __init__.py                 # Unified export interface for Member 4
│   │   ├── schemas.py                  # Formal Pydantic data contracts (Phases 1–8)
│   │   ├── speaker_resolver.py         # Dynamic transcript-grounded speaker resolver
│   │   ├── normalizer.py               # Phase 2 Validation & Normalization
│   │   ├── context_engine.py           # Phase 3 Localized Dialogue Window contextualizer
│   │   ├── priority_engine.py          # Phase 4 7-Factor Urgency & Priority engine
│   │   ├── confidence_engine.py        # Phase 5 7-Factor Evidence Reliability engine
│   │   ├── review_engine.py            # Phase 6 Human Review Triage engine
│   │   ├── explainability_engine.py    # Phase 7 Natural Language Explainability engine
│   │   ├── personalization_engine.py   # Phase 8 Role-Specific Persona Projection engine
│   │   ├── export_dashboard_data.py    # Fixture serialization utility
│   │   ├── manual_test_*.py            # Manual inspection scripts for phases 6, 7, 8
│   │   └── test_*.py                   # 10 automated test suites (164 test cases)
│   │
│   ├── evaluation/                     # Phase 11 Scientific Evaluation & Ablation Suite
│   │   ├── __init__.py                 # Package marker
│   │   ├── deadline_sensitivity.py     # Temporal sensitivity & monotonicity analysis
│   │   ├── priority_evaluation.py      # Priority factor weighting & behavioral cases
│   │   ├── confidence_evaluation.py    # Confidence reliability & orthogonality check
│   │   ├── review_evaluation.py        # Triage trigger coverage & reduction audit
│   │   ├── explainability_evaluation.py# Natural language explainability audit
│   │   ├── personalization_evaluation.py# Invariance verification across roles
│   │   ├── ablation.py                 # 7-stage engine ablation study
│   │   ├── determinism.py              # Bit-for-bit repeatability test suite
│   │   ├── run_phase11.py              # Master evaluation orchestrator
│   │   ├── manual_test_phase11.py      # Standalone evaluation runner
│   │   └── test_phase11.py             # Phase 11 automated test suite (8 tests)
│   │
│   └── api/                            # Phase 10 REST API Layer
│       ├── __init__.py                 # Package marker
│       ├── app.py                      # FastAPI application instance & CORS middleware
│       ├── routes.py                   # API router (/api/health, /api/meetings/process)
│       ├── schemas.py                  # API request/response Pydantic models
│       ├── service.py                  # Input adapter & Member 4 orchestration service
│       └── test_api.py                 # API automated test suite (11 tests)
│
├── frontend/                           # Modern React 18 + TypeScript + Vite Dashboard
│   ├── index.html                      # HTML5 root template
│   ├── package.json                    # Frontend dependencies & scripts
│   ├── package-lock.json               # Node dependency lockfile
│   ├── tsconfig.json                   # TypeScript compiler configuration
│   ├── tsconfig.node.json              # TypeScript Node environment configuration
│   ├── vite.config.ts                  # Vite development and build bundler configuration
│   └── src/
│       ├── main.tsx                    # Application entry point & DOM bootstrap
│       ├── App.tsx                     # Top-level state coordinator & conditional view layout
│       ├── index.css                   # Design tokens, themes, glassmorphism, responsive styles
│       ├── types/
│       │   └── meeting.ts              # TypeScript data interfaces matching Member 4 schemas
│       ├── utils/
│       │   └── formatters.ts           # Score, percentage, badge, and timestamp formatters
│       ├── data/
│       │   ├── apiClient.ts            # Fetch-based API client for FastAPI backend
│       │   ├── dataService.ts          # Client-side filtering & fixture access service
│       │   └── es2002a_data.json       # Precomputed reference fixture (ES2002a)
│       └── components/
│           ├── Header.tsx              # Application header & persona role selector
│           ├── MeetingInputWidget.tsx  # Upload audio, upload transcript, paste text form
│           ├── SummaryCards.tsx        # High/Med/Low priority and triage metric cards
│           ├── DistributionCharts.tsx  # Priority, confidence, and review progress charts
│           ├── DecisionsList.tsx       # Collapsible key decisions grounding viewer
│           ├── FilterBar.tsx           # Search, priority, confidence, triage filters
│           ├── ActionItemTable.tsx     # Action item data table with priority sorting
│           └── ActionItemDetailModal.tsx # Slide-over explainability drawer modal
│
├── data/                               # Dataset, artifacts, and upload directory
│   ├── ami/amicorpus/                  # AMI corpus audio/transcript fixtures
│   ├── processed/                      # Intermediate & final JSON pipeline artifacts
│   ├── raw/                            # Raw data inputs
│   └── temp_uploads/                   # Temporary storage for live API multipart uploads
│
└── docs/                               # Comprehensive Project Documentation
    ├── data_contract.md                # Phase 1 Data Contract and Schemas
    ├── invention_notes.md              # Technical specification and patent disclosures
    ├── member4_architecture.md         # Detailed Member 4 architecture specification
    ├── phase11_evaluation_report.md    # Phase 11 Evaluation and Ablation report
    └── evaluation_results/
        └── phase11_metrics.json        # Serialized evaluation metrics output
```

---

## 1.2 Important Files and Architectural Roles

| File Path | Layer | Purpose & Architectural Role | Inward Dependencies (What depends on it) | Outward Dependencies (What it depends on) |
| :--- | :--- | :--- | :--- | :--- |
| `backend/api/app.py` | API | FastAPI instance entry point; configures CORS middleware and registers API router. | Uvicorn server, external HTTP requests | `backend/api/routes.py` |
| `backend/api/routes.py` | API | Defines HTTP endpoints (`/api/health`, `/api/meetings/process`). | `backend/api/app.py`, `test_api.py` | `backend/api/service.py`, `backend/api/schemas.py` |
| `backend/api/service.py` | API Service | Orchestrates input routing: verifies audio, transcript, or raw text; invokes upstream pipelines or Member 4. | `backend/api/routes.py` | `backend/pipeline.py`, `backend/member4`, `backend/preprocessing` |
| `backend/member4/schemas.py` | Core Model | Defines Pydantic data contracts for all Member 4 intelligence stages. | All Member 4 engines, API schemas, evaluation suite | `pydantic` |
| `backend/member4/speaker_resolver.py` | Core Engine | Resolves participant identities dynamically from transcript evidence with zero hardcoding. | `priority_engine.py`, `explainability_engine.py` | `backend/member4/schemas.py` |
| `backend/member4/normalizer.py` | Core Engine | Cleans raw Member 3 items, validates temporal deadlines, deduplicates tasks. | `context_engine.py`, Member 4 pipeline | `backend/member4/schemas.py` |
| `backend/member4/context_engine.py` | Core Engine | Builds localized $\pm 2$ utterance dialogue windows and links topic segments. | `priority_engine.py`, `confidence_engine.py` | `backend/member4/schemas.py` |
| `backend/member4/priority_engine.py` | Core Engine | Computes continuous urgency score via 7-factor model and assigns HIGH/MEDIUM/LOW tiers. | `explainability_engine.py`, `personalization_engine.py` | `backend/member4/schemas.py`, `speaker_resolver.py` |
| `backend/member4/confidence_engine.py`| Core Engine | Evaluates 7 reliability factors to assign HIGH/MEDIUM/LOW confidence. | `explainability_engine.py`, `review_engine.py` | `backend/member4/schemas.py` |
| `backend/member4/review_engine.py` | Core Engine | Evaluates 13 deterministic reason codes to classify tasks into AUTO_ACCEPT, REVIEW_RECOMMENDED, or REVIEW_REQUIRED. | `explainability_engine.py` | `backend/member4/schemas.py` |
| `backend/member4/explainability_engine.py` | Core Engine | Synthesizes factor rankings and quotes verbatim dialogue evidence traces into natural language explanations. | `personalization_engine.py` | `backend/member4/schemas.py` |
| `backend/member4/personalization_engine.py`| Core Engine | Generates deterministic role projections (`MANAGER`, `DEVELOPER`, `INTERN`, `DEFAULT`) with zero decision drift. | `backend/api/service.py` | `backend/member4/schemas.py` |
| `backend/pipeline.py` | Pipeline | End-to-end processing pipeline orchestrating Member 1 ASR/diarization, Member 2 topic summarization, and Member 3 extraction. | `backend/api/service.py` | `whisperx`, `transformers`, `ollama` |
| `frontend/src/App.tsx` | UI Root | Main React application state container: tracks selected role, active payload, filters, and conditional rendering. | `frontend/src/main.tsx` | All frontend components, `dataService.ts` |
| `frontend/src/components/MeetingInputWidget.tsx` | UI Component | Input widget supporting audio upload, transcript upload, and pasted dialogue text. | `frontend/src/App.tsx` | `frontend/src/data/apiClient.ts` |
| `frontend/src/components/ActionItemTable.tsx` | UI Component | Renders action items with priority sorting, owner identity, topic tags, and status badges. | `frontend/src/App.tsx` | `frontend/src/utils/formatters.ts` |
| `frontend/src/components/ActionItemDetailModal.tsx`| UI Component | Deep inspection slide-over drawer showing 5 factor decomposition and dialogue evidence sections. | `frontend/src/App.tsx` | `frontend/src/utils/formatters.ts` |
| `frontend/src/data/apiClient.ts` | UI Service | Fetch API wrapper calling `/api/health` and `/api/meetings/process`. | `MeetingInputWidget.tsx` | Browser Fetch API |

---

# PHASE 2 — FRONTEND ANALYSIS

## 2.1 Major Views & Presentation Architecture

The frontend is a **single-page responsive application (SPA)** built with React 18, TypeScript, and Vite. Rather than traditional multi-page navigation, it uses **perspective-based rendering**:
1. **Initial Empty State View:** A clean dashboard greeting with empty inputs, prompting the user to submit an audio file, transcript file, or pasted text.
2. **Processing Lifecycle View:** Displays an animated spinner card while the backend pipeline analyzes the meeting.
3. **Intelligence Results View:** Once results are loaded, the page renders executive headlines, metric summary cards, intelligence distribution progress charts, collapsible key decisions, multi-criteria filter controls, and the action items table.
4. **Deep Explainability Modal / Drawer:** A slide-over modal triggered by clicking any action item row, exposing the underlying audit trail and evidence provenance.

---

## 2.2 Component Hierarchy & Tree

```
App (frontend/src/App.tsx)
 ├── Header (frontend/src/components/Header.tsx)
 ├── MeetingInputWidget (frontend/src/components/MeetingInputWidget.tsx)
 │    └── [Form / Audio File Input / Transcript File Input / Textarea]
 │
 ├── [Initial Empty State Card — when !payload && !isProcessing]
 ├── [Processing State Card — when isProcessing && !payload]
 │
 └── [Results Section — when payload && view]
      ├── Executive Focus Banner
      ├── SummaryCards (frontend/src/components/SummaryCards.tsx)
      ├── DistributionCharts (frontend/src/components/DistributionCharts.tsx)
      ├── DecisionsList (frontend/src/components/DecisionsList.tsx)
      ├── FilterBar (frontend/src/components/FilterBar.tsx)
      ├── ActionItemTable (frontend/src/components/ActionItemTable.tsx)
      └── ActionItemDetailModal (frontend/src/components/ActionItemDetailModal.tsx)
```

---

## 2.3 Comprehensive Component Inventory

### 1. `App`
- **File:** `frontend/src/App.tsx`
- **Purpose:** Top-level application coordinator and state store.
- **Parent:** `main.tsx`
- **Children:** `Header`, `MeetingInputWidget`, `SummaryCards`, `DistributionCharts`, `DecisionsList`, `FilterBar`, `ActionItemTable`, `ActionItemDetailModal`.
- **Props:** None (root component).
- **State:**
  - `selectedRole: UserRole` (`'MANAGER'`, `'DEVELOPER'`, `'INTERN'`, `'DEFAULT'`)
  - `selectedItem: PersonalizedActionItem | null`
  - `payload: DashboardPayload | null` (starts empty)
  - `isLiveApiData: boolean`
  - `isProcessing: boolean`
  - `filter: FilterState` (stores active search query, priority, confidence, review status, assignment, and deadline filters)
- **Data Consumed:** `DashboardPayload` from API or `dataService`.
- **Data Produced:** Slices of `PersonalizedMeetingView` passed down to child components.

### 2. `Header`
- **File:** `frontend/src/components/Header.tsx`
- **Purpose:** Renders branding, title, dynamic meeting pill, and the role perspective selector.
- **Parent:** `App.tsx`
- **Props:**
  - `meetingId: string`
  - `selectedRole: UserRole`
  - `onSelectRole: (role: UserRole) => void`
- **State:** None (stateless presentational component).
- **Events:** Clicking any role button fires `onSelectRole(role)`.

### 3. `MeetingInputWidget`
- **File:** `frontend/src/components/MeetingInputWidget.tsx`
- **Purpose:** User input interface for submitting audio files, transcript files (.json/.txt), or pasting raw text.
- **Parent:** `App.tsx`
- **Props:**
  - `onProcessingSuccess: (payload: DashboardPayload) => void`
  - `onProcessingStart?: () => void`
  - `onProcessingError?: (err: string) => void`
- **State:**
  - `isOpen: boolean` (collapsible toggle)
  - `meetingId: string` (starts empty)
  - `mode: 'AUDIO' | 'TRANSCRIPT_FILE' | 'TRANSCRIPT_TEXT'`
  - `audioFile: File | null`
  - `transcriptFile: File | null`
  - `transcriptText: string`
  - `status: 'IDLE' | 'UPLOADING' | 'PROCESSING' | 'SUCCESS' | 'ERROR'`
  - `statusMessage: string`
  - `errorMessage: string | null`
- **API Calls:** Calls `apiClient.processMeeting(...)`.

### 4. `SummaryCards`
- **File:** `frontend/src/components/SummaryCards.tsx`
- **Purpose:** Displays high-level executive metric cards (Total Tasks, High Priority, Med Priority, Low Priority, Auto Accepted, Needs Review, Review Required).
- **Parent:** `App.tsx`
- **Props:**
  - `view: PersonalizedMeetingView`
  - `totalDecisions: number`
  - `onSelectPriorityFilter?: (priority: 'ALL' | 'HIGH' | 'MEDIUM' | 'LOW') => void`
- **State:** None.
- **Events:** Clicking High, Med, or Low Priority cards fires `onSelectPriorityFilter` to filter the table.

### 5. `DistributionCharts`
- **File:** `frontend/src/components/DistributionCharts.tsx`
- **Purpose:** Visual progress bars displaying distribution percentages across Priority (`HIGH`/`MED`/`LOW`), Confidence Calibration (`HIGH`/`MED`/`LOW`), and Review Triage (`AUTO_ACCEPT`/`REVIEW_RECOMMENDED`/`REVIEW_REQUIRED`).
- **Parent:** `App.tsx`
- **Props:**
  - `items: PersonalizedActionItem[]`
- **State:** None.

### 6. `DecisionsList`
- **File:** `frontend/src/components/DecisionsList.tsx`
- **Purpose:** Collapsible panel listing all key decisions extracted from the meeting, showing associated topic references and speaker attributions.
- **Parent:** `App.tsx`
- **Props:**
  - `decisions: ContextRichDecision[]`
- **State:** `isExpanded: boolean` (defaults to collapsed).

### 7. `FilterBar`
- **File:** `frontend/src/components/FilterBar.tsx`
- **Purpose:** Multi-dimensional filter toolbar containing a full-text search input and 5 dropdown selectors (Priority, Confidence, Review Status, Assignment, Deadline), plus a reset button.
- **Parent:** `App.tsx`
- **Props:**
  - `filter: FilterState`
  - `onChangeFilter: (newFilter: FilterState) => void`
  - `displayedCount: number`
  - `totalCount: number`
- **State:** None (controlled component).

### 8. `ActionItemTable`
- **File:** `frontend/src/components/ActionItemTable.tsx`
- **Purpose:** Renders the primary tabular list of action items, including task text, persona guidance, owner identity, deadline, topic badge, priority badge with score, confidence badge, and triage status.
- **Parent:** `App.tsx`
- **Props:**
  - `items: PersonalizedActionItem[]`
  - `onSelectItem: (item: PersonalizedActionItem) => void`
- **State:**
  - `prioritySort: 'DESC' | 'ASC' | 'DEFAULT'` (defaults to `DESC`)
- **Features:**
  - Orders by Priority (`HIGH` $\to$ `MEDIUM` $\to$ `LOW`) by default.
  - Clicking `Priority` header toggles descending/ascending sorting with visual indicators.
  - Clicking any row triggers `onSelectItem` to open the detail modal.

### 9. `ActionItemDetailModal`
- **File:** `frontend/src/components/ActionItemDetailModal.tsx`
- **Purpose:** Slide-over drawer providing comprehensive explainability for a selected task.
- **Parent:** `App.tsx`
- **Props:**
  - `item: PersonalizedActionItem | null`
  - `allDecisions: ContextRichDecision[]`
  - `onClose: () => void`
- **Sections Rendered:**
  1. Executive Badges Bar (Priority, Confidence, Triage, High Priority indicator)
  2. Persona Projection Guidance Callout
  3. Ownership & Deadline Metadata (with speaker provenance source)
  4. Section 1: Human Review Triage Assessment (with triggered reason codes)
  5. Section 2: Priority Multi-Factor Decomposition Table (raw values, weights, contributions)
  6. Section 3: Confidence Reliability Calibration Table (evidence reliability factors)
  7. Section 4: Verifiable Dialogue Provenance & Evidence Traces (verbatim quotes, timestamps)
  8. Section 5: Linked Decisions in Meeting Context

---

## 2.4 Frontend Data Flow

```
[User Action in UI]
       │
       ▼
[MeetingInputWidget.tsx] ──(FormData: meeting_id + audio/transcript/text)──▶ [apiClient.ts]
                                                                                   │
                                                                       (HTTP POST /api/meetings/process)
                                                                                   ▼
                                                                        [FastAPI Backend Server]
                                                                                   │
                                                                         (JSON Response Payload)
                                                                                   ▼
[App.tsx (handleProcessingSuccess)] ◀──────────────────────────────────────────────┘
       │
       ├─▶ setPayload(newPayload)
       ├─▶ setIsProcessing(false)
       ├─▶ setSelectedItem(null)
       │
       ▼
[Active Role View Computed via useMemo]
       │
       ├─▶ view = payload.views[selectedRole]
       ├─▶ decisions = payload.key_decisions
       ├─▶ filteredItems = dataService.filterItems(view.action_items, filter)
       │
       ▼
[Render Child Components]
       ├─▶ Header (meetingId, role switcher)
       ├─▶ Executive Banner (view.summary_headline)
       ├─▶ SummaryCards (counts, click-to-filter priority)
       ├─▶ DistributionCharts (distributions across filtered items)
       ├─▶ DecisionsList (key decisions)
       ├─▶ FilterBar (active filter counts and controls)
       ├─▶ ActionItemTable (sorted items list)
       └─▶ ActionItemDetailModal (drawer for selected item)
```

---

# PHASE 3 — BACKEND ANALYSIS

## 3.1 Backend Architecture Overview

The backend is built with **FastAPI** running on the **Uvicorn** ASGI web server. It provides a non-blocking asynchronous REST API designed to accept multipart file uploads and JSON payloads, route them through the appropriate preprocessing and extraction modules, and return structured Member 4 intelligence views.

- **Entry Point:** `backend/api/app.py`
- **Host & Port:** `127.0.0.1:8000`
- **CORS Policy:** Wildcard (`allow_origins=["*"]`) enabled for seamless communication with the Vite dev server (`http://localhost:5173`).

---

## 3.2 API Endpoints Reference Table

| Method | Endpoint | Purpose | Request Parameters / Body | Response Model | Frontend Caller |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `GET` | `/api/health` | Health check endpoint confirming backend server and Member 4 readiness. | None | `HealthResponse` (`status`, `version`, `member4_active`, `message`) | `apiClient.checkHealth` |
| `POST` | `/api/meetings/process` | Primary meeting processing endpoint. Ingests audio file, transcript file, or text and executes pipeline. | Multipart Form: `meeting_id: str` (required), `audio: UploadFile` (optional), `transcript_file: UploadFile` (optional), `transcript_text: str` (optional), `force_reprocess: bool` (optional) | `ProcessMeetingResponse` (`meeting_id`, `processing_stage`, `total_canonical_items`, `views`, `key_decisions`, `diagnostics`) | `apiClient.processMeeting` in `MeetingInputWidget.tsx` |

---

## 3.3 Error Handling & Status Codes

- **HTTP 200 OK:** Processing succeeded; returns complete dashboard payload.
- **HTTP 400 Bad Request:** Triggered by client validation errors:
  - Missing meeting ID or invalid characters (alphanumeric, hyphens, underscores only; path traversal characters rejected).
  - Providing zero inputs or multiple inputs simultaneously (exclusive input contract).
  - Unsupported audio extensions (supported: `.wav`, `.mp3`, `.m4a`, `.flac`, `.ogg`, `.webm`, `.mp4`).
  - Unsupported transcript extensions (supported: `.txt`, `.json`).
  - Empty or whitespace-only transcript text.
- **HTTP 500 Internal Server Error:** Returned if unexpected internal pipeline or model execution failures occur.

---

# PHASE 4 — COMPLETE PROCESSING PIPELINE

The end-to-end meeting processing pipeline progresses through four distinct stages:

```
                      [ USER INPUT (Frontend) ]
             Audio File (.wav/.mp3) | Transcript File (.json/.txt) | Pasted Text
                                       │
                                       ▼
                   [ FASTAPI BACKEND API LAYER (Phase 10) ]
                            backend/api/service.py
                                       │
         ┌─────────────────────────────┼─────────────────────────────┐
         ▼                             ▼                             ▼
   [ Audio Upload ]          [ Transcript File ]              [ Pasted Text ]
         │                             │                             │
         ▼                             │                             ▼
[ MEMBER 1 (Phase 0) ]                 │                 [ Preprocessing Splitter ]
backend/speaker_aware_transcription.py │                 backend/preprocessing/
WhisperX ASR + PyAnnote Diarization   │                 transcript_processor.py
         │                             │                             │
         └─────────────────────────────┼─────────────────────────────┘
                                       │
                                       ▼
                        [ MEMBER 2 (Topic & Summary) ]
                            backend/summarization/
                   Topic Segmenter (Cosine Embeddings)
                                       ↓
                   BART-large-CNN Abstractive Summaries
                                       │
                                       ▼
                      [ MEMBER 3 (Semantic Extraction) ]
                             backend/extraction/
                      Ollama LLM (qwen2.5:3b) Inference
                                       │
                                       ▼
                      [ MEMBER 4 INTELLIGENCE PIPELINE ]
                             backend/member4/
  1. speaker_resolver.py       ── Dynamic Transcript-Grounded Speaker Resolution
  2. normalizer.py             ── Phase 2 Validation, Deduplication, & Normalization
  3. context_engine.py         ── Phase 3 Localized Dialogue Window (±2 turns)
  4. priority_engine.py        ── Phase 4 7-Factor Linear Operational Priority Scoring
  5. confidence_engine.py      ── Phase 5 7-Factor Evidence Reliability Calibration
  6. review_engine.py          ── Phase 6 Deterministic Human Review Triage (13 Triggers)
  7. explainability_engine.py  ── Phase 7 Factor Attribution & Evidence Provenance Traces
  8. personalization_engine.py ── Phase 8 Deterministic Role Projections
                                       │
                                       ▼
                     [ STRUCTURED DASHBOARD PAYLOAD ]
                       views: MANAGER | DEVELOPER | INTERN | DEFAULT
                                       │
                                       ▼
                       [ REACT 18 DASHBOARD (Frontend) ]
```

---

## 4.1 Stage-by-Stage Breakdown

| Stage | Input Data | Processing Performed | Output Data | Responsible Module | Next Stage |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **1. Ingestion & Validation** | Audio bytes, transcript file, or raw text | Validates meeting ID, verifies input exclusivity, creates temporary directory. | Clean file paths or normalized text chunks | `backend/api/service.py` | Member 1 or Member 2 |
| **2. Member 1 (ASR & Diarization)** | Raw audio stream | Faster-Whisper ASR + PyAnnote diarization + word-level speaker alignment. | Diarized JSON transcript with timestamps & speaker turns | `backend/speaker_aware_transcription.py` | Member 2 |
| **3. Member 2 (Topic Segmentation)** | Diarized dialogue turns | Computes sentence transformer embeddings, identifies semantic shifts, clusters topics, runs BART summarization. | Topic-segmented transcript with topic summaries and speaker rosters | `backend/summarization/topic_segmenter.py`, `summarizer.py` | Member 3 |
| **4. Member 3 (Extraction)** | Topic segments & summaries | Prompts local Ollama (`qwen2.5:3b`) with structured JSON schema to identify tasks and decisions. | Raw action items and candidate key decisions | `backend/extraction/task_extractor.py` | Member 4 Normalizer |
| **5. Member 4 (Speaker Resolution)** | Diarized turns & transcript | Analyzes introduction patterns ("I am...", "My name is...") to map `SPEAKER_XX` to real names with diarization fallback. | `SpeakerIdentity` registry | `backend/member4/speaker_resolver.py` | Normalizer & Priority |
| **6. Member 4 (Normalization)** | Raw Member 3 JSON | Deduplicates tasks, parses deadlines, flags ambiguous deadlines, validates speaker assignments. | `NormalizedActionItem[]` | `backend/member4/normalizer.py` | Context Engine |
| **7. Member 4 (Context Engine)** | Normalized tasks & Member 2 turns | Extracts $\pm 2$ utterance dialogue windows, trigger segment IDs, and links co-occurring topic decisions. | `ContextRichActionItem[]` | `backend/member4/context_engine.py` | Priority & Confidence |
| **8. Member 4 (Priority Scoring)** | Context-rich items | Computes weighted sum of 7 operational factors (deadline, crisis words, assignment, blockers, decisions, specificity, context). | Continuous score $[0.0, 1.0]$ & tier (`HIGH`/`MED`/`LOW`) | `backend/member4/priority_engine.py` | Explainability Engine |
| **9. Member 4 (Confidence Scoring)**| Context-rich items | Computes weighted sum of 7 evidence factors (context resolution, dialogue grounding, consistency, deadline quality). | Continuous score $[0.0, 1.0]$ & tier (`HIGH`/`MED`/`LOW`) | `backend/member4/confidence_engine.py` | Review Engine |
| **10. Member 4 (Review Triage)** | Priority & Confidence assessments | Evaluates 13 deterministic rule triggers (6 required, 7 recommended) to assign triage category. | `AUTO_ACCEPT`, `REVIEW_RECOMMENDED`, or `REVIEW_REQUIRED` | `backend/member4/review_engine.py` | Explainability Engine |
| **11. Member 4 (Explainability)** | Triage, Priority, and Confidence assessments | Ranks factor contributions, generates human-readable audit explanations, and attaches verbatim quotes. | `ExplainedActionItem[]` | `backend/member4/explainability_engine.py` | Personalization Engine |
| **12. Member 4 (Personalization)** | Explained action items | Projects items into 4 distinct role perspectives (`MANAGER`, `DEVELOPER`, `INTERN`, `DEFAULT`) with zero decision drift. | `PersonalizedMeetingView` per role | `backend/member4/personalization_engine.py` | API Response / Frontend |

---

# PHASE 5 — DATABASE ANALYSIS

> [!NOTE]
> **Database Findings:**
> **No persistent database is currently used.**

### Storage Architecture & Data Lifecycle
The Meeting Intelligent System operates as a **stateless, artifact-backed analytical pipeline**:
1. **No RDBMS or NoSQL Database:** There is no PostgreSQL, MySQL, SQLite, MongoDB, or Redis instance involved in the data path.
2. **File-Based Artifact Caching:** Intermediate and final results are persisted as deterministic JSON files in the `data/processed/` directory:
   - `<meeting_id>_speaker_transcript.json` — Member 1 diarized transcript
   - `<meeting_id>_member2_results.json` — Member 2 topic summaries
   - `<meeting_id>_member3_results.json` — Member 3 extracted items
3. **Session & Live API Uploads:** Uploaded audio files are written to isolated temporary directories under `data/temp_uploads/audio_upload_*`, processed in-memory, and cleaned up via `shutil.rmtree` upon pipeline completion.
4. **Client-Side State:** The frontend stores the returned payload in React component memory (`App.tsx` state). Refreshing the browser resets the dashboard to its clean, empty state.

---

# PHASE 6 — ARCHITECTURE ANALYSIS

## 6.1 Architectural Patterns

The system adheres to three well-defined architectural design patterns:
1. **Multi-Tiered Client-Server Architecture:** Clean separation of concerns between presentation (React SPA), API gateway/orchestration (FastAPI), and scientific intelligence calculation (Python Member 4).
2. **Deterministic Pipeline Pattern:** Unidirectional data flow where each engine transforms an immutable input contract into a progressively enriched output contract ($Phase\ 2 \to Phase\ 3 \to \dots \to Phase\ 8$).
3. **Canonical Invariance Pattern:** Decisions made by core intelligence engines (priority score, confidence level, review status) are immutable canonical truths. Presentation layers (personalization, frontend) may reorder, filter, or emphasize fields for specific audiences, but can **never alter or recalculate** core scores.

## 6.2 Architectural Diagram

```
┌────────────────────────────────────────────────────────────────────────┐
│                        FRONTEND PRESENTATION LAYER                     │
│                 React 18 + TypeScript + Vite Dashboard                 │
│                                                                        │
│   Header  │  MeetingInputWidget  │  SummaryCards  │ DistributionCharts │
│   DecisionsList  │  FilterBar  │  ActionItemTable  │  DetailModal      │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ HTTP (REST JSON / FormData)
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        BACKEND API & ADAPTER LAYER                     │
│                            FastAPI + Uvicorn                           │
│                                                                        │
│        app.py (CORS)  │  routes.py  │  schemas.py  │  service.py       │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                  MEMBER 1–3 UPSTREAM PROCESSING PIPELINE               │
│                                                                        │
│   Member 1: WhisperX (ASR) + PyAnnote (Speaker Diarization)           │
│   Member 2: Topic Segmentation + Hugging Face BART-large-CNN           │
│   Member 3: Ollama LLM (Qwen2.5:3b) Semantic Task & Decision Extractor │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Structured JSON Extraction
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│              MEMBER 4 POST-EXTRACTION INTELLIGENCE LAYER               │
│                                                                        │
│   1. Dynamic Speaker Resolver (Transcript Grounding + Fallback)        │
│   2. Validation & Normalization Engine (Deduplication, Deadlines)      │
│   3. Context Intelligence Engine (±2 Utterance Dialogue Windows)       │
│   4. Priority Intelligence Engine (7-Factor Urgent Operational Model)  │
│   5. Confidence Intelligence Engine (7-Factor Reliability Scoring)     │
│   6. Human Review Triage Engine (13 Deterministic Trigger Codes)       │
│   7. Explainability Engine (Factor Attribution & Provenance Traces)   │
│   8. Personalization Engine (Manager, Dev, Intern, Default Views)      │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                         FILE-BASED STORAGE LAYER                       │
│                        Directory: data/processed/                      │
│                                                                        │
│   <meeting_id>_speaker_transcript.json │ <meeting_id>_member2_results  │
│   <meeting_id>_member3_results.json    │ ES2002a Reference Fixtures    │
└────────────────────────────────────────────────────────────────────────┘
```

---

# PHASE 7 — COMPONENT + MODULE DEPENDENCY ANALYSIS

```
[App.tsx]
   │
   ├──▶ [MeetingInputWidget.tsx] ──▶ [apiClient.ts]
   │                                     │
   │                                     ▼ (HTTP POST /api/meetings/process)
   ├──▶ [backend/api/routes.py] ─────────┘
   │         │
   │         ▼
   ├──▶ [backend/api/service.py]
   │         │
   │         ├─▶ [backend/pipeline.py] (if raw audio)
   │         │        ├─▶ [whisperx] (Member 1)
   │         │        ├─▶ [summarizer.py] (Member 2)
   │         │        └─▶ [task_extractor.py] (Member 3 via Ollama)
   │         │
   │         └─▶ [backend/member4/]
   │                  ├─▶ speaker_resolver.py
   │                  ├─▶ normalizer.py
   │                  ├─▶ context_engine.py
   │                  ├─▶ priority_engine.py
   │                  ├─▶ confidence_engine.py
   │                  ├─▶ review_engine.py
   │                  ├─▶ explainability_engine.py
   │                  └─▶ personalization_engine.py
   │
   ▼
[App State (payload)]
   │
   ├──▶ [SummaryCards.tsx] (high/med/low counts, interactive filter trigger)
   ├──▶ [DistributionCharts.tsx] (priority, confidence, review bars)
   ├──▶ [DecisionsList.tsx] (linked decisions)
   ├──▶ [FilterBar.tsx] (search and multi-criteria filters)
   ├──▶ [ActionItemTable.tsx] (priority sorting and row selection)
   │         │
   │         ▼ (selectedItem)
   └──▶ [ActionItemDetailModal.tsx] (5 factor decomposition sections)
```

---

# PHASE 8 — ROLE / VIEW ANALYSIS

Member 4 implements **Multi-Perspective Persona Projections** (Phase 8). Four distinct perspectives are generated deterministically from the same canonical intelligence:

| Dimension | `MANAGER` | `DEVELOPER` | `INTERN` | `DEFAULT` |
| :--- | :--- | :--- | :--- | :--- |
| **Primary Audience** | Engineering leads, project managers, directors | Software engineers, technical implementers | Junior engineers, onboarding teammates | General meeting attendees, auditors |
| **Summary Headline Focus** | High-priority milestones, items flagged for review, and deadline commitments. | Technical deliverables, dialogue context, and prerequisite blockers. | Task clarity, assigned ownership, deadlines, and guidance signals. | Canonical meeting overview with total extracted counts. |
| **Default Item Sorting** | 1. Priority tier (`HIGH` $\to$ `LOW`)<br>2. Has deadline first<br>3. Review status (`REQUIRED` first)<br>4. Item ID | 1. Technical blocker present first<br>2. Priority score descending<br>3. Medium confidence first (uncertainty)<br>4. Item ID | 1. Assigned tasks first<br>2. Priority tier (`HIGH` $\to$ `LOW`)<br>3. Item ID | 1. Item ID ascending (`norm_act_001` $\dots$) or Table Priority Sort |
| **Highlighted Fields** | `task`, `owner`, `deadline`, `priority_level`, `review_status`, `related_decisions` | `task`, `owner`, `deadline`, `context_window`, `segments`, `explanations` | `task`, `owner`, `deadline`, `role_guidance`, `review_status` | `item_id`, `task`, `owner`, `deadline`, `priority`, `confidence`, `review` |
| **Urgency Badge Policy** | Red `<Flame /> High Priority` shown **strictly** when `priority_level === HIGH`. | Red `<Flame /> High Priority` shown **strictly** when `priority_level === HIGH`. | Red `<Flame /> High Priority` shown **strictly** when `priority_level === HIGH`. | Standard priority badges. |

### Strict Canonical Invariance Guarantee
Persona projection **never alters decisions**. Automated test assertions verify that across all 4 role views:
$$\text{priority\_score}_{\text{role}} = \text{priority\_score}_{\text{canonical}}$$
$$\text{confidence\_score}_{\text{role}} = \text{confidence\_score}_{\text{canonical}}$$
$$\text{review\_status}_{\text{role}} = \text{review\_status}_{\text{canonical}}$$

---

# PHASE 9 — PRIORITY SYSTEM ANALYSIS

## 9.1 Mathematical Formula & Factor Weights

The Member 4 Priority Engine assigns priority as a linear combination of 7 orthogonal factors:

$$\text{Priority Score} = \sum_{i=1}^7 w_i \cdot v_i \quad \text{where} \quad \sum_{i=1}^7 w_i = 1.00$$

```
                                  PRIORITY SCORE (S)
                                 [ Range: 0.00 to 1.00 ]
                                          │
      ┌──────────────┬──────────────┬─────┴────────┬──────────────┬──────────────┬──────────────┐
      ▼              ▼              ▼              ▼              ▼              ▼              ▼
Deadline       Explicit       Assignment     Dependency      Decision      Deliverable      Context
Urgency        Urgency        Explicitness   Blocker         Linkage       Specificity      Quality
(w = 0.25)     (w = 0.15)     (w = 0.15)     (w = 0.15)      (w = 0.10)    (w = 0.10)       (w = 0.10)
```

### Threshold Tiers:
- **`HIGH` Priority:** $\text{Score} \ge \mathbf{0.65}$
- **`MEDIUM` Priority:** $\mathbf{0.35} \le \text{Score} < \mathbf{0.65}$
- **`LOW` Priority:** $\text{Score} < \mathbf{0.35}$

---

## 9.2 Factor Decomposition & Evidence Criteria

1. **`deadline_urgency` ($w = 0.25$):**
   - Imminent session deadline ($\le 1$ hour, today, before next meeting): $v = 0.95$
   - Short-term deadline (this afternoon, end of day, few hours): $v = 0.70$
   - Near-term deadline (tomorrow, 1-2 days): $v = 0.50$
   - Medium-term deadline (this Friday, next Monday, next week): $v = 0.30$
   - Distant deadline (next month, next quarter): $v = 0.15$
   - No deadline: $v = 0.00$
2. **`explicit_urgency_language` ($w = 0.15$):** Detects crisis keywords (*critical*, *urgent*, *emergency*, *asap*, *immediately*).
3. **`assignment_explicitness` ($w = 0.15$):** Evaluates direct verbal commitment vs. passive attribution vs. unassigned task.
4. **`dependency_blocker` ($w = 0.15$):** Scans for blocker terminology (*blocker*, *prerequisite*, *dependency*, *cannot proceed without*).
5. **`decision_linkage` ($w = 0.10$):** Checks for co-occurring key decisions in the same topic context.
6. **`deliverable_specificity` ($w = 0.10$):** Measures operational clarity and technical concreteness.
7. **`context_quality` ($w = 0.10$):** Rewards complete dialogue window coverage and topic boundary resolution.

---

## 9.3 Why "Tomorrow" Does Not Automatically Force `HIGH`

A task due "tomorrow" provides near-term urgency ($0.50 \times 0.25 = +0.1250$), raising the task from baseline `LOW` up into `MEDIUM` ($0.4350$). 

However, if the task is not an active bottleneck ($w_{\text{blocker}} = 0.15$), contains no crisis words ($w_{\text{urgency}} = 0.15$), and is not tied to a key executive decision ($w_{\text{decision}} = 0.10$), it forfeits $0.40$ in potential weight. 

Its theoretical score ceiling is:
$$1.00 - 0.40 = \mathbf{0.60}$$

Because `HIGH` requires $\ge 0.65$, it mathematically caps in the `MEDIUM` tier. This prevents routine non-blocking deliverables from inflating into false emergencies.

---

## 9.4 Frontend Priority Presentation & Sorting

- **Default Order:** `ActionItemTable.tsx` displays items ordered by Priority descending (`HIGH` $\to$ `MEDIUM` $\to$ `LOW`, with scores descending within the same tier).
- **Interactive Header Sorting:** Clicking the **Priority** column header toggles between descending, ascending, and default order.
- **Summary Cards Filtering:** Clicking the **High Priority**, **Med Priority**, or **Low Priority** cards filters the table to only show items matching that tier.
- **Case-Insensitive Matching:** `filterItems` matches priority levels regardless of casing (`HIGH`, `High`, `high`).
- **Urgency Flame Icon:** Rendered strictly when `priority_level === 'HIGH'`.

---

# PHASE 10 — TESTING & EVALUATION ANALYSIS

The repository contains **183 automated tests** across three test suites. All 183 tests pass with 100% success.

## 10.1 Automated Test Suites Reference Table

| Test Suite | File Location | Tests | Purpose | Exact Execution Command | Expected Result |
| :--- | :--- | :---: | :--- | :--- | :--- |
| **Member 4 Unit Tests** | `backend/member4/test_*.py` | **164** | Verifies schemas, normalization, dialogue context windowing, 7-factor priority, 7-factor confidence, review triage, explainability, personalization, and dynamic speaker resolution. | `.\venv\Scripts\python.exe -m unittest discover -s backend/member4 -p "test_*.py"` | `Ran 164 tests in ~0.24s ... OK` |
| **Phase 11 Evaluation Suite**| `backend/evaluation/test_phase11.py` | **8** | Scientifically evaluates temporal monotonicity, score determinism across 5 runs, ablation error propagation, and upstream score decoupling. | `.\venv\Scripts\python.exe -m unittest backend/evaluation/test_phase11.py` | `Ran 8 tests in ~0.15s ... OK` |
| **FastAPI REST API Tests** | `backend/api/test_api.py` | **11** | Tests `/api/health`, `/api/meetings/process` with audio/transcript/text inputs, validation rejections (path traversal, invalid extensions). | `.\venv\Scripts\python.exe -m unittest backend/api/test_api.py` | `Ran 11 tests in ~0.21s ... OK` |
| **Frontend Production Build**| `frontend/` | — | Validates TypeScript type checking (`tsc`) and production bundler rollup (`vite build`). | `cd frontend; npm run build` | `✓ 1600 modules transformed ... built in ~2.0s` |

---

# PHASE 11 — ENVIRONMENT & INSTALLATION ANALYSIS

## 11.1 System Prerequisites

- **Operating System:** Windows 10/11, macOS, or Linux
- **Python:** Version `3.10`, `3.11`, `3.12`, or `3.13` (Tested on `Python 3.13.2`)
- **Node.js:** Version `18.x` or higher (Tested on `v24.13.0`)
- **npm:** Version `9.x` or higher (Tested on `11.6.2`)
- **Ollama:** Running locally on `http://localhost:11434` with model `qwen2.5:3b` (Required only if running full Member 3 LLM extraction).

---

## 11.2 Package Dependencies Breakdown

### Backend Dependencies (`requirements.txt`)
- **ASR & Audio:** `whisperx==3.8.6`, `faster-whisper==1.2.1`, `pyannote-audio==4.0.7`, `ctranslate2==4.8.1`
- **PyTorch & ML:** `torch==2.8.0`, `torchaudio==2.8.0`, `torchvision==0.23.0`, `pytorch-lightning==2.6.5`
- **NLP & LLM:** `transformers==4.57.6`, `huggingface_hub==0.36.2`, `sentence-transformers==2.7.0`, `ollama==0.6.2`, `nltk==3.10.2`
- **API & Server:** `fastapi==0.141.1`, `uvicorn==0.52.4`, `starlette==1.6.0`, `python-multipart==0.0.32`
- **Data & Contracts:** `pydantic==2.13.4`, `numpy==2.5.2`, `pandas==3.0.5`, `scipy==1.18.0`, `python-dotenv==1.1.1`

### Frontend Dependencies (`frontend/package.json`)
- **Core:** `react@^18.3.1`, `react-dom@^18.3.1`
- **Icons & Styling:** `lucide-react@^0.475.0`, `clsx@^2.1.1`
- **Development & Build:** `vite@^6.1.0`, `typescript@^5.7.3`, `@vitejs/plugin-react@^4.3.4`

---

## 11.3 Environment Variables

The project uses a root-level `.env` file loaded by `python-dotenv` on the backend:

| Variable Name | Required? | Location | Description & Purpose | Security Scope |
| :--- | :---: | :--- | :--- | :--- |
| `HF_TOKEN` | Optional* | Root `.env` | Hugging Face user access token required by PyAnnote for speaker diarization models (`pyannote/speaker-diarization-3.1`). | **Server-side only.** Never exposed to React frontend, API responses, or client logs. |
| `OLLAMA_HOST` | Optional | Backend | URL of local Ollama daemon (defaults to `http://localhost:11434`). | Server-side only. |

*\*Note: `HF_TOKEN` is only required when processing raw audio from scratch through Member 1. Transcript processing and Member 4 evaluation operate 100% offline without external tokens.*

---

# PHASE 12 — COMPLETE RUNNING GUIDE

Follow this step-by-step guide to run and verify the complete Meeting Intelligent System from scratch.

## Step 1: Clone Repository & Create Virtual Environment

Open PowerShell or Terminal:

```powershell
# Clone the repository
git clone https://github.com/Kaushal1122/meeting-intelligent-system.git
cd meeting-intelligent-system

# Create Python virtual environment
python -m venv venv

# Activate virtual environment
# Windows PowerShell:
.\venv\Scripts\Activate.ps1
# Linux / macOS:
source venv/bin/activate

# Install backend dependencies
pip install -r requirements.txt
pip install fastapi uvicorn python-multipart
```

---

## Step 2: Configure Environment Secrets

Create a `.env` file in the project root:

```powershell
# Copy example template
Copy-Item .env.example .env

# Edit .env and add your Hugging Face token if running audio diarization:
# HF_TOKEN=your_huggingface_token_here
```

---

## Step 3: Install Frontend Dependencies

```powershell
cd frontend
npm install
cd ..
```

---

## Step 4: Launch Backend & Frontend Servers

Open two separate terminal windows:

### Terminal 1 — Start FastAPI Backend:
```powershell
# From project root:
.\venv\Scripts\python.exe -m uvicorn backend.api.app:app --host 127.0.0.1 --port 8000 --reload
```
- API Health: `http://127.0.0.1:8000/api/health`
- Interactive Swagger Docs: `http://127.0.0.1:8000/docs`

### Terminal 2 — Start Vite React Frontend:
```powershell
# From project root:
cd frontend
npm run dev
```
- Dashboard URL: `http://localhost:5173/`

---

## Step 5: Test the System in Browser

1. Open **`http://localhost:5173/`** in your browser.
2. Confirm the initial state is clean:
   - Meeting ID input is empty.
   - Clean placeholder message: *"No Meeting Results Loaded"*.
   - No previous results, tables, or charts are shown.
3. In the **Process Meeting Input** area:
   - Enter **Meeting ID**: `ES2002a`
   - Select Input Source: **Upload Transcript**
   - Click **Select Transcript File** and choose:
     `data/processed/ES2002a_member3_results.json`
   - Click **Process Meeting**.
4. Observe the results view:
   - Green **Live API Result** badge appears.
   - 32 action items and 9 key decisions load instantly.
   - Table is ordered by Priority (`HIGH` $\to$ `MEDIUM` $\to$ `LOW`).
   - Click the **Priority** column header to toggle ascending/descending order.
   - Click **High Priority**, **Med Priority**, or **Low Priority** cards in Summary Cards to filter.
   - Click any action item row to open the deep explainability inspection drawer.
   - Switch persona roles (**Manager**, **Developer**, **Intern**, **Default**) to see tailored views.

---

## Step 6: Run Full Automated Verification

```powershell
# 1. Run all Member 4 unit tests (164 tests)
.\venv\Scripts\python.exe -m unittest discover -s backend/member4 -p "test_*.py"

# 2. Run Phase 11 scientific evaluation suite (8 tests)
.\venv\Scripts\python.exe -m unittest backend/evaluation/test_phase11.py

# 3. Run FastAPI REST API integration tests (11 tests)
.\venv\Scripts\python.exe -m unittest backend/api/test_api.py

# 4. Run Frontend production build check
cd frontend
npm run build
cd ..
```

**All 183 automated tests will pass with 100% success and 0 errors.**
