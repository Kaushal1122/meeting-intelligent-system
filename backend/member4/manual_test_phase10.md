# Phase 10: End-to-End Integration Manual Validation Guide

This document details the environment, execution commands, and manual test results for the Phase 10 End-to-End Integration of the Meeting Intelligent System.

---

## 1. Execution Environment
- **Operating System**: Windows 11 (PowerShell)
- **Python Environment**: `venv` (Python 3.13.2)
- **FastAPI / Server**: FastAPI `0.141.1`, Uvicorn `0.52.4`, Starlette `1.6.0`, python-multipart `0.0.32`
- **Frontend Environment**: Node `v24.13.0`, npm `11.6.2`, React `18.3.1`, Vite `6.1.0`, TypeScript `5.7.3`
- **LLM / Model Runtime**: Ollama running locally on `http://localhost:11434` with model `qwen2.5:3b`

---

## 2. Startup Commands

### Step 1: Start Backend API (FastAPI)
From repository root:
```powershell
venv\Scripts\python.exe -m uvicorn backend.api.app:app --host 127.0.0.1 --port 8000
```
API docs available at `http://127.0.0.1:8000/docs`.

### Step 2: Start React Frontend (Vite)
In a separate terminal window:
```powershell
cd frontend
npm run dev
```
Dashboard available at `http://localhost:5173/`.

---

## 3. Transcript Processing Verification

### Test A: Regression Reference (`ES2002a`)
1. In the dashboard input area:
   - Meeting ID: `ES2002a`
   - Mode: `Upload Transcript`
   - File: Select `data/processed/ES2002a_member3_results.json` or `data/processed/ES2002a_speaker_transcript.json`
2. Click **Process Meeting**.
3. **UI State Progression**:
   - Status changes to `Processing Pipeline...`
   - On completion, banner updates with a green **Live API Result** badge.
4. **Verified Metrics**:
   - Total Action Items: `32`
   - HIGH Priority: `1`
   - MEDIUM Priority: `1`
   - LOW Priority: `30`
   - AUTO_ACCEPT: `25`
   - REVIEW_RECOMMENDED: `7`
   - REVIEW_REQUIRED: `0`
   - Explicit Deadline: `1` (`30 minutes`)
   - Linked Key Decisions: `9`
5. **Representative Cases Inspection**:
   - Case A (`norm_act_031`): Priority `0.7150` (HIGH), Confidence `0.9600` (HIGH), Review `AUTO_ACCEPT`.
   - Case B (`norm_act_006`): Priority `0.2650` (LOW), Confidence `0.7950` (HIGH), Review `REVIEW_RECOMMENDED`, Reason `CONFLICTING_DECISIONS`.
   - Case C (`norm_act_011`, `012`, `013`): Priority `0.2450` (LOW), Confidence `0.7050`–`0.7350` (MEDIUM), Review `REVIEW_RECOMMENDED`.
   - Case D (`norm_act_030`): Priority `0.2450` (LOW), Confidence `0.7350` (MEDIUM), Review `REVIEW_RECOMMENDED`.

### Test B: Pasted Transcript Text
1. Select mode: `Paste Transcript`.
2. Enter Meeting ID: `TEST_PASTE_01`.
3. Paste:
   ```text
   SPEAKER_00: Let's discuss the remote control working design.
   SPEAKER_03: The next meeting is in 30 minutes. In between now and then work on the design.
   ```
4. Click **Process Meeting**.
5. Confirm backend parses dialogue turns and generates Member 4 intelligence without crashing.

---

## 4. Audio Input Test Status
- **Status**: `AUDIO TEST NOT EXECUTED — no suitable local audio fixture available.`
- **Details**: `data/ami/amicorpus/ES2002a/audio/` is not present in local workspace storage (only compressed RealMedia `.rm` streams in `ES2002b`). Per project instructions, audio test was not executed and is not marked PASS.
- The audio pipeline adapter in `backend/api/service.py` is fully wired to invoke `backend.pipeline.run_audio_pipeline` whenever a `.wav` or `.mp3` file is uploaded.

---

## 5. Security & Upstream Protection Verification
- Path traversal rejection tested: `../../malicious_path` returns HTTP 400.
- Unsupported extensions rejected: `.exe`, `.pdf` return HTTP 400.
- Empty text rejected: whitespace-only inputs return HTTP 400.
- Upstream Member 1, 2, 3 implementation files and `backend/pipeline.py` remain **100% unmodified**.
