"""API request/response schemas."""

from pydantic import BaseModel
from typing import List, Optional


class PipelineStepResponse(BaseModel):
    step: str
    detail: str
    time_ms: int


class ModelInfoResponse(BaseModel):
    backbone: str
    temporal: str


class AnalysisResponse(BaseModel):
    is_fake: bool
    confidence: float
    fake_probability: float
    label: str                             # "real" or "fake"
    frames_analyzed: int
    faces_detected: int
    attention_weights: List[float]
    processing_time_ms: float
    pipeline_steps: List[PipelineStepResponse]
    model_info: ModelInfoResponse


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    device: str
    version: str
