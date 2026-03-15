"""
Analysis API router — handles video upload and deepfake detection.
"""

import os
import uuid
import tempfile
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
import config
from backend.services.inference import VideoAnalyzer, ModelLoader
from backend.models.schemas import AnalysisResponse, ErrorResponse

router = APIRouter(prefix="/api", tags=["Analysis"])

# Singleton analyzer
_analyzer = None

def get_analyzer():
    global _analyzer
    if _analyzer is None:
        _analyzer = VideoAnalyzer()
    return _analyzer


def cleanup_file(path: str):
    """Background task to clean up temp files after response is sent."""
    try:
        os.unlink(path)
    except OSError:
        pass


@router.post(
    "/analyze",
    response_model=AnalysisResponse,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="Analyze a video for deepfake detection",
    description="""
    Upload a video file (MP4, AVI, MOV, WebM, MKV).
    The API will:
    1. Extract 30 uniform frames
    2. Detect and crop faces using Haar cascade
    3. Run EfficientNet-B3 + BiLSTM + Temporal Attention
    4. Return confidence score, attention weights, and pipeline timing
    """,
)
async def analyze_video(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="Video file to analyze"),
):
    # ── Validate file ──
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    ext = Path(file.filename).suffix.lower()
    if ext not in config.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type '{ext}'. Allowed: {', '.join(config.ALLOWED_EXTENSIONS)}"
        )

    # ── Save to temp file ──
    temp_path = None
    try:
        suffix = ext
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            temp_path = tmp.name
            content = await file.read()

            # Check size
            size_mb = len(content) / (1024 * 1024)
            if size_mb > config.MAX_UPLOAD_SIZE_MB:
                raise HTTPException(
                    status_code=400,
                    detail=f"File too large ({size_mb:.1f}MB). Max: {config.MAX_UPLOAD_SIZE_MB}MB"
                )

            tmp.write(content)

        # ── Run analysis ──
        analyzer = get_analyzer()
        result = analyzer.analyze(temp_path)

        # Check for errors
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])

        # Schedule cleanup
        background_tasks.add_task(cleanup_file, temp_path)

        return AnalysisResponse(**result)

    except HTTPException:
        # Clean up on validation errors
        if temp_path and os.path.exists(temp_path):
            os.unlink(temp_path)
        raise

    except Exception as e:
        # Clean up on unexpected errors
        if temp_path and os.path.exists(temp_path):
            os.unlink(temp_path)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
