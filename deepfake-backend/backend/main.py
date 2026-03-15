"""
═══════════════════════════════════════════════════════════════════
Reality Check AI — FastAPI Backend
═══════════════════════════════════════════════════════════════════

Serves the deepfake detection model as a REST API.

Endpoints:
  GET  /health         → Model status, device info
  POST /api/analyze    → Upload video → get deepfake prediction

Run:
  uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
═══════════════════════════════════════════════════════════════════
"""

import sys
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config
from backend.routers import analysis, health
from backend.services.inference import ModelLoader


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load model on startup, cleanup on shutdown."""
    print("\n" + "=" * 50)
    print("  Reality Check AI — Starting up")
    print("=" * 50)
    try:
        ModelLoader.get_model()
        print("  Model loaded successfully!")
    except FileNotFoundError as e:
        print(f"  WARNING: {e}")
        print("  Server will start but /api/analyze will fail.")
        print("  Train a model first: python -m training.train")
    print("=" * 50 + "\n")
    yield
    print("\nShutting down...")


app = FastAPI(
    title="Reality Check AI",
    description="Deepfake video detection API powered by EfficientNet + Temporal Attention LSTM",
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS — allow your React frontend ──
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",     # Vite dev server
        "http://localhost:5173",     # Vite alt port
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "https://realitycheckai.com",  # production domain
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Register Routers ──
app.include_router(health.router)
app.include_router(analysis.router)


@app.get("/")
async def root():
    return {
        "app": "Reality Check AI",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "analyze": "POST /api/analyze",
    }
