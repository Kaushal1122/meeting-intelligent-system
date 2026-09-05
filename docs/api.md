# Meeting Intelligent System — API Documentation

## 1. Overview

The backend API is built with **FastAPI** (Python 3.12+) and served via **Uvicorn** on port `8000`. It bridges raw client inputs (audio recordings, transcript files, and pasted dialogue text) to the multi-tier analysis pipeline and exposes structured Member 4 analytical payloads to the frontend.

- **Base URL**: `http://127.0.0.1:8000`
- **Prefix**: `/api`
- **OpenAPI / Swagger UI**: `http://127.0.0.1:8000/docs`
- **ReDoc**: `http://127.0.0.1:8000/redoc`

---

## 2. API Endpoints Table

| HTTP Method | Endpoint | Purpose | Request Body / Form | Response Model | Status Codes | Frontend Caller |
|:---|:---|:---|:---|:---|:---|:---|
| `GET` | `/api/health` | Service health & pipeline readiness check | None | `HealthResponse` | 200 | `MeetingInputWidget.tsx` (optional verification) |
| `POST` | `/api/meetings/process` | Ingests and processes audio, transcript file, or raw text into complete Member 4 dashboard payload | `multipart/form-data` (see parameters below) | `ProcessMeetingResponse` | 200, 400, 500 | `MeetingInputWidget.tsx` via `apiClient.ts` |

---

## 3. Detailed Endpoint Specifications

### 3.1 Health Check Endpoint

```http
GET /api/health
```

#### Purpose
Verifies that the FastAPI server is running, the lifespan context is active, and Member 4 intelligence engines are loaded.

#### Request Parameters
None.

#### Response Schema (`HealthResponse`)
```json
{
  "status": "ok",
  "version": "1.0.0",
  "member4_active": true,
  "message": "Meeting Intelligent System API is operational."
}
```

#### Example cURL Command
```bash
curl -X GET http://127.0.0.1:8000/api/health
```

---

### 3.2 Process Meeting Endpoint

```http
POST /api/meetings/process
```

#### Purpose
Ingests a meeting via one of three mutually exclusive input methods (audio upload, transcript file upload, or pasted transcript text), orchestrates processing through upstream pipeline components, applies Member 4 post-extraction intelligence, and returns personalized persona views, canonical action items, key decisions, and operational diagnostics.

#### Request Content-Type
`multipart/form-data`

#### Form Parameters

| Parameter | Type | Required | Description | Constraints |
|:---|:---|:---|:---|:---|
| `meeting_id` | `string` | **Yes** | Unique identifier for the meeting | Must match regex `^[A-Za-z0-9_\-]+$` (path traversal rejected) |
| `audio` | `UploadFile` | Optional* | Multi-speaker audio file | Extensions: `.wav`, `.mp3`, `.m4a`, `.flac`, `.ogg`, `.aac`, `.wma` |
| `transcript_file` | `UploadFile` | Optional* | Structured transcript file | Extensions: `.txt`, `.json` |
| `transcript_text` | `string` | Optional* | Raw dialogue lines pasted directly | Must contain non-whitespace text; formatted as `Speaker: text` |
| `force_reprocess`| `boolean` | No | Overwrite cached results in `data/processed/` | Default: `false` |

*\*Note: Exactly ONE of `audio`, `transcript_file`, or `transcript_text` must be supplied. Supplying zero or more than one returns an HTTP 400 error.*

#### Response Schema (`ProcessMeetingResponse`)

```json
{
  "meeting_id": "ES2002a",
  "processing_stage": "member_4_dashboard_ready",
  "total_canonical_items": 32,
  "views": {
    "MANAGER": {
      "role": "MANAGER",
      "total_canonical_items": 32,
      "visible_items_count": 32,
      "high_priority_count": 1,
      "medium_priority_count": 1,
      "low_priority_count": 30,
      "auto_accept_count": 25,
      "review_recommended_count": 7,
      "review_required_count": 0,
      "has_deadline_count": 1,
      "action_items": [
        {
          "item_id": "norm_act_031",
          "task": "Develop the functional remote-control prototype incorporating teletext capabilities",
          "responsible_person": "Industrial Designer",
          "deadline": "Tomorrow 5 PM",
          "deadline_iso": "2026-09-06T17:00:00",
          "priority_score": 0.715,
          "priority_level": "HIGH",
          "confidence_score": 0.96,
          "confidence_level": "HIGH",
          "review_status": "AUTO_ACCEPT",
          "review_reason_codes": [],
          "explanation": {
            "priority_explanation": "Critical deadline within 24h (+0.25); explicit urgency keywords (+0.15); explicit assignee (+0.15); blocker on prototype (+0.15).",
            "confidence_explanation": "Explicit grammatical task structure (+0.30); speaker explicitly confirmed (+0.25); grounded in turn 40 (+0.20); agreement from team (+0.15).",
            "review_explanation": "Clear ownership and grounded context. Auto-accepted with high reliability.",
            "evidence_traces": [
              {
                "speaker": "Project Manager",
                "utterance": "We need the prototype with teletext working by tomorrow afternoon.",
                "timestamp_start": 2104.5,
                "timestamp_end": 2108.2
              }
            ]
          },
          "role_emphasis": {
            "is_highlighted": true,
            "badge": "Urgent Blocker",
            "priority_weight_multiplier": 1.2
          }
        }
      ]
    },
    "DEVELOPER": { ... },
    "INTERN": { ... },
    "DEFAULT": { ... }
  },
  "key_decisions": [
    {
      "decision_id": "dec_001",
      "topic_reference": 4,
      "decision": "Adopt double-curved yellow casing with rubberized grips for the remote.",
      "rationale": "High ergonomic ratings in preliminary market surveys.",
      "status": "APPROVED",
      "impacted_roles": ["DEVELOPER", "MANAGER"]
    }
  ],
  "diagnostics": [
    "Loaded 32 canonical items from upstream extraction.",
    "Speaker resolution matched 4 out of 4 participants.",
    "Calculated continuous priority scores [0.1500 - 0.7150]."
  ]
}
```

---

## 4. Error Handling & Validation Responses

The API uses standard HTTP error codes with actionable JSON descriptions:

### HTTP 400 Bad Request
Occurs when input validation fails:
- **Empty meeting ID**: `{"detail": "Meeting ID cannot be empty."}`
- **Path traversal attempt**: `{"detail": "Invalid meeting ID '..\\malicious'. Only alphanumeric characters, underscores, and hyphens are allowed."}`
- **No input provided**: `{"detail": "No input provided. Please provide an audio file, transcript file, or transcript text."}`
- **Multiple inputs provided**: `{"detail": "Multiple inputs provided. Please provide only one of: audio file, transcript file, or transcript text."}`
- **Empty pasted text**: `{"detail": "Pasted transcript text cannot be empty."}`
- **Unsupported audio extension**: `{"detail": "Unsupported audio format '.exe'. Supported formats: .aac, .flac, .m4a, .mp3, .ogg, .wav, .wma"}`
- **Unsupported transcript extension**: `{"detail": "Unsupported transcript format '.pdf'. Supported formats: .txt, .json"}`
- **Malformed JSON file**: `{"detail": "Uploaded transcript JSON is malformed: Expecting value: line 1 column 1 (char 0)"}`

### HTTP 500 Internal Server Error
Occurs when unhandled exceptions arise during pipeline execution:
```json
{
  "detail": "Internal processing failure: <exception message>"
}
```

---

## 5. Security & Token Protection Architecture

1. **Zero Client Secret Exposure**:
   - `HF_TOKEN` is loaded securely on startup into backend memory from the root `.env` file via `dotenv`.
   - The token is used strictly by backend worker threads to initialize `pyannote/speaker-diarization-3.1`.
   - The API response filters out all environment configurations. Responses are strictly tested by automated test suites to guarantee that no substrings of `HF_TOKEN` or `hf_` are leaked in HTTP headers, JSON bodies, or debug logs.
2. **CORS Whitelisting**:
   - CORS is restricted to frontend development origins:
     - `http://localhost:5173`
     - `http://127.0.0.1:5173`
   - Allowed methods: `*`, allowed headers: `*`, with credentials support enabled.

---

## 6. Frontend Integration & API Client

The frontend consumes the API via [`frontend/src/data/apiClient.ts`](file:///c:/Users/chaha/OneDrive/Desktop/meeting-intelligent-system/frontend/src/data/apiClient.ts):

```typescript
export async function processMeeting(
  meetingId: string,
  options: {
    audioFile?: File;
    transcriptFile?: File;
    transcriptText?: string;
  }
): Promise<Member4DashboardPayload> {
  const formData = new FormData();
  formData.append('meeting_id', meetingId);

  if (options.audioFile) {
    formData.append('audio', options.audioFile);
  } else if (options.transcriptFile) {
    formData.append('transcript_file', options.transcriptFile);
  } else if (options.transcriptText) {
    formData.append('transcript_text', options.transcriptText);
  }

  const response = await fetch('http://127.0.0.1:8000/api/meetings/process', {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const err = await response.json();
    throw new Error(err.detail || 'Failed to process meeting');
  }

  return response.json();
}
```
