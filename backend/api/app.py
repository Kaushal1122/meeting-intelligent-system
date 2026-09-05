from contextlib import asynccontextmanager
import os
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Load root project's .env file before loading any dependent modules
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(PROJECT_ROOT / ".env")

from .routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Safe startup configuration check (NEVER logs the actual token)
    if os.getenv("HF_TOKEN"):
        print("[CONFIG] HF_TOKEN is configured")
    else:
        print("[CONFIG] HF_TOKEN is not configured")
    yield


app = FastAPI(
    title="Meeting Intelligent System API",
    description="Backend API connecting raw meeting inputs (audio/transcripts) to the Member 1-4 intelligence pipeline.",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS explicitly for development frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)



if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.api.app:app", host="127.0.0.1", port=8000, reload=True)
