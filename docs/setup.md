# Meeting Intelligent System — Setup & Installation Guide

## 1. System Prerequisites

Before installing the project, verify that the following tools are installed and available on your system `PATH`:

| Requirement | Minimum Version | Verification Command | Purpose |
|:---|:---|:---|:---|
| **Python** | 3.12+ | `python --version` | Backend API and pipeline execution |
| **Node.js** | 18+ (20+ recommended) | `node --version` | Frontend development server & bundler |
| **npm** | 9+ (10+ recommended) | `npm --version` | Frontend package management |
| **Git** | 2.30+ | `git --version` | Version control |
| **FFmpeg** | 5.0+ | `ffmpeg -version` | Audio decoding and resampling |
| **Ollama** | Latest | `ollama --version` | Local LLM inference runner |

---

## 2. Step-by-Step Installation

### Step 1: Clone the Repository
```bash
git clone https://github.com/Kaushal1122/meeting-intelligent-system.git
cd meeting-intelligent-system
```

---

### Step 2: Set Up Python Virtual Environment

#### On Windows (PowerShell):
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

#### On Linux / macOS (Bash/Zsh):
```bash
python3 -m venv venv
source venv/bin/activate
```

---

### Step 3: Install Backend Dependencies

With the virtual environment activated, install all required Python packages:

```bash
pip install -r requirements.txt
```

---

### Step 4: Configure Environment Variables

The pipeline uses `pyannote/speaker-diarization-3.1` which requires acceptance of user agreements on Hugging Face and an API access token.

1. Create a `.env` file in the project root by copying `.env.example`:
   ```bash
   cp .env.example .env
   ```
2. Open `.env` and configure your Hugging Face token:
   ```env
   HF_TOKEN=your_huggingface_token_here
   ```

> [!WARNING]
> **Security Guardrail**: Never commit `.env` to version control. The `.gitignore` file is configured to exclude all `.env` files. The API server strictly verifies that this token remains server-side and is never sent over the network to the frontend.

---

### Step 5: Install & Pull Local LLM Model (Ollama)

Member 3 uses the `qwen2.5:3b` model for local, privacy-preserving semantic task extraction:

1. Start the Ollama background service if not already running:
   ```bash
   ollama serve
   ```
2. Pull the required 3-billion parameter model:
   ```bash
   ollama pull qwen2.5:3b
   ```
3. Verify that the model is listed:
   ```bash
   ollama list
   ```

---

### Step 6: Install Frontend Dependencies

Navigate to the `frontend/` directory and install the Node packages:

```bash
cd frontend
npm install
cd ..
```

---

## 3. Running the Complete System

To run the complete interactive platform, start both the backend API server and the frontend development server.

### Terminal 1: Start Backend API (Port 8000)

```powershell
# From project root directory
.\venv\Scripts\python.exe -m uvicorn backend.api.app:app --host 127.0.0.1 --port 8000 --reload
```

- **Health Check**: Open `http://127.0.0.1:8000/api/health` in your browser.
- **API Documentation**: Open `http://127.0.0.1:8000/docs`.

---

### Terminal 2: Start Frontend Web Dashboard (Port 5173)

```powershell
# From project root directory
cd frontend
npm run dev
```

- **Dashboard**: Open `http://localhost:5173` in your browser.

---

## 4. Running the Offline Monolithic Pipeline (CLI)

If you prefer to run the pipeline directly from the command line without the web dashboard:

### Run from Audio File (Full Member 1–4 Execution)
```powershell
.\venv\Scripts\python.exe backend\pipeline.py --audio "data\ami\amicorpus\ES2002a\audio\ES2002a.Mix-Headset.wav"
```

### Run from Pre-existing Transcript (Skips Audio Transcription)
```powershell
.\venv\Scripts\python.exe backend\pipeline.py --transcript "data\processed\ES2002a_speaker_transcript.json"
```

Outputs are automatically generated and cached in `data/processed/`:
- `<meeting_id>_speaker_transcript.json` (Member 1)
- `<meeting_id>_member2_results.json` (Member 2)
- `<meeting_id>_member3_results.json` (Member 3)

---

## 5. Troubleshooting & FAQ

### 1. `ImportError: cannot import name 'Pipeline' from 'pyannote.audio'`
Ensure that `pyannote.audio` is installed via `requirements.txt` and your Hugging Face account has accepted the conditions on the Hugging Face model card (`pyannote/speaker-diarization-3.1` and `pyannote/segmentation-3.0`).

### 2. `ConnectionRefusedError: [Errno 111] Connection refused`
This occurs when Member 3 attempts to connect to Ollama but the Ollama daemon is not running. Run `ollama serve` in a separate terminal.

### 3. `CORS Policy Blocked`
If accessing the frontend from a custom host or port, ensure your origin is whitelisted in `backend/api/app.py` under `CORSMiddleware`. By default, `http://localhost:5173` and `http://127.0.0.1:5173` are whitelisted.

### 4. `ffmpeg not found`
Download FFmpeg and add the `bin` folder to your system environment `PATH` variable.
