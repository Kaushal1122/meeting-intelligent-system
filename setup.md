# Development Setup

## 1. Clone repository

git clone https://github.com/Kaushal1122/meeting-intelligent-system.git

cd meeting-intelligence-system

## 2. Create virtual environment

Windows:

python -m venv venv

## 3. Activate

Windows PowerShell:

venv\Scripts\Activate.ps1

## 4. Install dependencies

pip install -r requirements.txt

## 5. Install FFmpeg

Install FFmpeg separately and ensure it is available in PATH.

Verify:

ffmpeg -version
ffprobe -version

## 6. Configure Hugging Face

Create a .env file:

HF_TOKEN=your_token_here

Do NOT commit .env.

## 7. Test preprocessing

python preprocessing\test_text_cleaner.py

python preprocessing\test_transcript_processor.py

python preprocessing\test_speaker_normalizer.py

## 8. Validate existing processed output

python preprocessing\validate_output.py
