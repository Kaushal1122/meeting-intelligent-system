# Meeting Intelligent System — Testing & Evaluation Guide

## 1. Overview of Testing Architecture

The codebase incorporates a multi-tiered test suite guaranteeing correctness across unit models, algorithmic scoring, API integration, regression baselines, and production frontend builds:

- **183 Automated Python Tests**: Fully verified and passing using Python's standard `unittest` framework.
- **Scientific Evaluation & Ablation Suite**: 8 specialized benchmark harnesses in `backend/evaluation/` measuring sensitivity, determinism, and calibration.
- **Standalone Component Scripts**: Diagnostic smoke tests for preprocessing and summarization modules.
- **Frontend TypeScript Build**: Clean compilation and bundling via `tsc` and Vite 6.

---

## 2. Comprehensive Test Suites Table

| Test Suite | Location | Purpose | Execution Command | Expected Result |
|:---|:---|:---|:---|:---|
| **Member 4 Schemas** | `backend/member4/test_schemas.py` | Validates Pydantic v2 data models, strict types, and validation constraints. | `python -m unittest backend/member4/test_schemas.py` | 13 tests passed |
| **Normalizer & Deduplication** | `backend/member4/test_normalizer.py` | Verifies canonical ID assignment, date parsing, and task deduplication. | `python -m unittest backend/member4/test_normalizer.py` | 16 tests passed |
| **Speaker Resolution** | `backend/member4/test_speaker_resolver.py` | Validates transcript-grounded speaker matching and pronoun resolution. | `python -m unittest backend/member4/test_speaker_resolver.py` | 14 tests passed |
| **Contextual Engine** | `backend/member4/test_context_engine.py` | Tests $\pm 2$ utterance dialogue window assembly and topic binding. | `python -m unittest backend/member4/test_context_engine.py` | 15 tests passed |
| **Priority Engine** | `backend/member4/test_priority_engine.py` | Tests 7-factor linear priority scoring, factor bounds, and urgency sorting. | `python -m unittest backend/member4/test_priority_engine.py` | 18 tests passed |
| **Confidence Engine** | `backend/member4/test_confidence_engine.py` | Tests 7-factor confidence calibration and reliability scoring. | `python -m unittest backend/member4/test_confidence_engine.py` | 21 tests passed |
| **Review Triage Engine** | `backend/member4/test_review_engine.py` | Verifies 13 deterministic review reason codes and human-in-the-loop triage. | `python -m unittest backend/member4/test_review_engine.py` | 20 tests passed |
| **Explainability Engine** | `backend/member4/test_explainability_engine.py` | Verifies zero-drift factor attribution and evidence trace provenance. | `python -m unittest backend/member4/test_explainability_engine.py` | 18 tests passed |
| **Personalization Engine** | `backend/member4/test_personalization_engine.py` | Verifies canonical item invariance across Manager, Developer, Intern, and Default views. | `python -m unittest backend/member4/test_personalization_engine.py` | 15 tests passed |
| **All Member 4 Tests** | `backend/member4/` | Executes all 10 Member 4 intelligence test suites in batch. | `python -m unittest discover -s backend/member4 -p "test_*.py"` | **164 tests passed** |
| **Evaluation Suite** | `backend/evaluation/test_phase11.py` | Verifies scientific evaluation metrics (deadline sensitivity, determinism, ablation). | `python -m unittest backend/evaluation/test_phase11.py` | **8 tests passed** |
| **REST API Integration** | `backend/api/test_api.py` | End-to-end endpoint tests, input validation, ES2002a regression baseline, and token safety. | `python -m unittest backend/api/test_api.py` | **11 tests passed** |
| **Combined Core Suite** | Root | Executes all 183 automated tests simultaneously. | `python -m unittest discover -s backend/member4 -p "test_*.py" && python -m unittest backend/evaluation/test_phase11.py backend/api/test_api.py` | **183 tests passed (100% OK)** |
| **Frontend Production Build** | `frontend/` | TypeScript type-checking and Vite production asset bundling. | `cd frontend && npm run build` | 0 TypeScript errors, bundle generated in `dist/` |

---

## 3. How to Execute Tests Step-by-Step

### 3.1 Run Complete Backend Unit & API Test Suite

From the project root directory, run:

```powershell
# Windows PowerShell
.\venv\Scripts\python.exe -m unittest discover -s backend/member4 -p "test_*.py"
.\venv\Scripts\python.exe -m unittest backend/evaluation/test_phase11.py backend/api/test_api.py
```

```bash
# Linux / macOS
source venv/bin/activate
python -m unittest discover -s backend/member4 -p "test_*.py"
python -m unittest backend/evaluation/test_phase11.py backend/api/test_api.py
```

**Expected Console Output**:
```
Ran 164 tests in 0.230s
OK
Ran 19 tests in 0.342s
OK
```

---

### 3.2 Run Scientific Evaluation & Ablation Suite

The `backend/evaluation/` directory contains scientific benchmarks evaluating mathematical consistency:

```powershell
# Run full Phase 11 evaluation suite
.\venv\Scripts\python.exe backend/evaluation/run_phase11.py

# Run individual evaluation benchmarks
.\venv\Scripts\python.exe backend/evaluation/deadline_sensitivity.py
.\venv\Scripts\python.exe backend/evaluation/determinism.py
.\venv\Scripts\python.exe backend/evaluation/ablation.py
```

**Key Invariants Verified**:
1. **Determinism**: 100 iterations of identical input produce bit-for-bit identical floats and strings (zero random seed drift).
2. **Deadline Sensitivity**: Monotonic decrease in urgency as deadline shifts from 2h $\to$ 24h $\to$ 3d $\to$ 1w $\to$ none.
3. **Canonical Invariance**: Switching persona roles preserves exactly the same 32 canonical action item IDs and base scores.

---

### 3.3 Run Standalone Preprocessing & Summarization Smoke Tests

```powershell
# Test speaker label normalization
.\venv\Scripts\python.exe backend/preprocessing/test_speaker_normalizer.py

# Test text cleaning rules
.\venv\Scripts\python.exe backend/preprocessing/test_text_cleaner.py

# Test transcript loader
.\venv\Scripts\python.exe backend/summarization/test_transcript_loader.py
```

---

### 3.4 Run Frontend Build & Type Validation

From the `frontend/` directory:

```powershell
cd frontend
npm run build
```

**Expected Output**:
```
> meeting-intelligent-dashboard@1.0.0 build
> tsc && vite build

vite v6.4.3 building for production...
✓ 1600 modules transformed.
dist/index.html                   1.32 kB
dist/assets/index-*.css          11.22 kB
dist/assets/index-*.js         1,768.40 kB
✓ built in ~2s
```
