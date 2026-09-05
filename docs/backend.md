# Meeting Intelligent System — Backend Architecture & Module Map

## 1. Overview & Framework

The backend is implemented in **Python 3.12+** using **FastAPI** as the modern, asynchronous web framework and **Uvicorn** as the ASGI web server.

The backend hosts two primary execution pathways:
1. **The REST API Gateway (`backend/api/`)**: Provides endpoints for the React frontend, handling input parsing, audio staging, pipeline dispatching, and Member 4 JSON serialization.
2. **The Offline CLI Pipeline (`backend/pipeline.py`)**: A command-line script capable of executing end-to-end processing across raw WAV files or pre-existing transcripts.

---

## 2. Directory Structure & Module Organization

```
backend/
├── api/                            # FastAPI REST API Layer
│   ├── app.py                      # FastAPI initialization, CORS, lifespan
│   ├── routes.py                   # Route handlers (/api/health, /api/meetings/process)
│   ├── schemas.py                  # API request and response Pydantic models
│   ├── service.py                  # Orchestration service bridging API to pipeline & Member 4
│   └── test_api.py                 # Integration tests for endpoints & schemas
│
├── preprocessing/                  # Ingestion & Text Normalization
│   ├── input_handler.py            # Audio file extension validator
│   ├── speaker_normalizer.py       # Canonical speaker label mapping
│   ├── text_cleaner.py             # Punctuation & whitespace normalization
│   ├── transcript_processor.py     # Sentence splitter & raw line parser
│   └── validate_output.py          # Intermediate schema validator
│
├── summarization/                  # Member 2: Topic Boundaries & Summarization
│   ├── topic_segmenter.py          # Sentence-transformer cosine similarity clustering
│   ├── summarizer.py               # BART-large-CNN abstractive summarization
│   └── transcript_loader.py        # Diarized JSON transcript loader & utility
│
├── extraction/                     # Member 3: LLM Semantic Extraction
│   ├── schemas.py                  # Extraction Pydantic schemas (RawTask, RawDecision)
│   └── task_extractor.py           # Ollama client invoking Qwen 2.5: 3B
│
├── member4/                        # Member 4: Post-Extraction Intelligence Engine
│   ├── __init__.py                 # Public package export API
│   ├── schemas.py                  # Formal Pydantic schemas for all Member 4 stages
│   ├── normalizer.py               # Normalization, deduplication, date parsing
│   ├── speaker_resolver.py         # Dynamic speaker and pronoun resolution
│   ├── context_engine.py           # Utterance window contextualization (±2 turns)
│   ├── priority_engine.py          # 7-factor linear continuous priority scoring
│   ├── confidence_engine.py        # 7-factor extraction confidence calibration
│   ├── review_engine.py            # 13-trigger human-in-the-loop review triage
│   ├── explainability_engine.py    # Zero-drift natural language explanation generator
│   ├── personalization_engine.py   # Role projections (MANAGER, DEVELOPER, INTERN, DEFAULT)
│   ├── export_dashboard_data.py    # Fixture serialization utility
│   └── test_*.py                   # 10 automated unit test suites (164 tests)
│
├── evaluation/                     # Phase 11: Scientific Evaluation & Ablation
│   ├── deadline_sensitivity.py     # Urgency monotonicity & sensitivity tests
│   ├── priority_evaluation.py      # Factor weighting and behavioral verification
│   ├── confidence_evaluation.py    # Calibration and reliability audit
│   ├── review_evaluation.py        # Triage trigger coverage audit
│   ├── explainability_evaluation.py# Natural language rationale validation
│   ├── personalization_evaluation.py# Role invariance and focus validation
│   ├── ablation.py                 # 7-stage engine ablation benchmarks
│   ├── determinism.py              # Bit-for-bit repeatability tests
│   └── test_phase11.py             # Automated unit tests for evaluation suite
│
├── speaker_aware_transcription.py  # Member 1 WhisperX + PyAnnote speech pipeline
├── transcribe.py                   # Standalone transcription script
└── pipeline.py                     # Monolithic CLI pipeline orchestrator
```

---

## 3. Comprehensive Backend Module Map

| Module File | Layer | Primary Responsibility | Key Functions / Classes | Depends On | Called By |
|:---|:---|:---|:---|:---|:---|
| `api/app.py` | API | FastAPI app initialization, CORS setup, lifespan check for `HF_TOKEN`. | `app`, `lifespan()` | `api/routes.py` | Uvicorn server |
| `api/routes.py` | API | Route definitions for health and meeting processing. | `health_check()`, `process_meeting()` | `api/service.py`, `api/schemas.py` | `api/app.py` |
| `api/service.py` | API / Orchestration | Validates inputs, parses files/text, checks cache, dispatches to pipeline and Member 4. | `process_meeting_input()`, `parse_raw_transcript_text()`, `execute_member4_pipeline()` | `backend/pipeline.py`, `backend/member4`, `backend/preprocessing` | `api/routes.py` |
| `api/schemas.py` | API | Pydantic response models for API endpoints. | `HealthResponse`, `ProcessMeetingResponse`, `ErrorResponse` | Pydantic | `api/routes.py` |
| `speaker_aware_transcription.py` | Member 1 | Transcribes audio via WhisperX and diarizes speaker turns via PyAnnote. | `transcribe_audio()` | `whisperx`, `pyannote.audio` | `backend/pipeline.py` |
| `preprocessing/input_handler.py` | Preprocessing | Validates audio file extensions against allowed set. | `validate_audio_path()`, `AUDIO_EXTENSIONS` | `pathlib` | `backend/pipeline.py`, `api/service.py` |
| `preprocessing/speaker_normalizer.py` | Preprocessing | Normalizes raw speaker strings to `SPEAKER_XX` format. | `normalize_speaker_label()` | Standard regex | `api/service.py`, `transcript_processor.py` |
| `preprocessing/text_cleaner.py` | Preprocessing | Cleans dialogue text, standardizes quotes, removes whitespace noise. | `clean_text()` | Standard regex | `transcript_processor.py`, `api/service.py` |
| `preprocessing/transcript_processor.py`| Preprocessing | Parses timestamped text dialogue files and splits sentences. | `parse_line()`, `split_sentences()`, `process_transcript()` | `text_cleaner.py`, `speaker_normalizer.py` | `api/service.py` |
| `summarization/topic_segmenter.py` | Member 2 | Identifies topic transition boundaries using semantic cosine similarity. | `segment_transcript()`, `split_into_topics()` | `sentence_transformers`, `numpy` | `backend/pipeline.py` |
| `summarization/summarizer.py` | Member 2 | Generates abstractive topic summaries. | `summarize_text()`, `summarize_topics()` | `transformers (BART)` | `backend/pipeline.py` |
| `extraction/task_extractor.py` | Member 3 | Prompts local Ollama LLM to extract tasks and decisions. | `extract_actions_and_decisions()` | `requests` (Ollama REST API) | `backend/pipeline.py` |
| `member4/normalizer.py` | Member 4 | Normalizes tasks, validates deadlines, structures decisions. | `normalize_member3_output()` | `schemas.py`, `speaker_resolver.py` | `member4/__init__.py` |
| `member4/speaker_resolver.py` | Member 4 | Dynamically matches mentions/pronouns to transcript speakers. | `resolve_speaker()`, `build_speaker_profile()` | `schemas.py` | `normalizer.py` |
| `member4/context_engine.py` | Member 4 | Binds upstream dialogue turns and context windows to action items. | `enrich_with_context()` | `schemas.py` | `member4/__init__.py` |
| `member4/priority_engine.py` | Member 4 | Calculates 7-factor linear urgency score $[0.0, 1.0]$. | `compute_priority()`, `categorize_priority()` | `schemas.py` | `member4/__init__.py` |
| `member4/confidence_engine.py` | Member 4 | Calculates 7-factor extraction confidence score $[0.0, 1.0]$. | `compute_confidence()`, `categorize_confidence()` | `schemas.py` | `member4/__init__.py` |
| `member4/review_engine.py` | Member 4 | Determines triage category (`AUTO_ACCEPT`, `REVIEW_RECOMMENDED`, `REVIEW_REQUIRED`). | `evaluate_review_triage()` | `schemas.py` | `member4/__init__.py` |
| `member4/explainability_engine.py` | Member 4 | Synthesizes natural language explanations and evidence traces. | `generate_explanations()`, `explain_meeting_triage()` | `schemas.py` | `member4/__init__.py` |
| `member4/personalization_engine.py`| Member 4 | Generates role-specific views (`MANAGER`, `DEVELOPER`, `INTERN`, `DEFAULT`). | `personalize_meeting_view()` | `schemas.py` | `member4/__init__.py` |
| `pipeline.py` | Orchestration | Monolithic CLI script running end-to-end processing. | `run_audio_pipeline()`, `process_transcript()` | All Member 1-3 modules | CLI user |

---

## 4. Error Handling & Resilience Architecture

1. **Subprocess Isolation**:
   - Model inference (PyTorch, WhisperX, Hugging Face Transformers) executes within controlled Python try-except blocks.
   - If audio processing encounters malformed files, clear exceptions (`ValueError`, `FileNotFoundError`) are raised.
2. **Missing Ollama Fallback**:
   - If Ollama is not running on `http://127.0.0.1:11434`, `task_extractor.py` handles connection timeouts gracefully and raises explicit, informative instructions to start the Ollama daemon.
3. **Pydantic Schema Validation**:
   - All input requests and internal pipeline data structures are validated through Pydantic v2 models.
   - Unexpected fields or missing required keys result in immediate, structured validation errors before downstream engines execute.
