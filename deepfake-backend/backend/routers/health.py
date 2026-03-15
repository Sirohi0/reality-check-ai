"""Health check endpoint."""

from pathlib import Path
from fastapi import APIRouter

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
import config
from backend.services.inference import ModelLoader
from backend.models.schemas import HealthResponse

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="ok",
        model_loaded=ModelLoader.is_loaded(),
        device=str(config.DEVICE),
        version="1.0.0",
    )
