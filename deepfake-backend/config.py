"""
Shared configuration for preprocessing, training, and inference.
Edit paths here once — every module reads from this file.
"""

import os
from pathlib import Path

# ── Paths ──────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"           # put Celeb-DF here
PROCESSED_DIR = DATA_DIR / "processed"
WEIGHTS_DIR = BASE_DIR / "weights"
LOGS_DIR = BASE_DIR / "logs"

# Create dirs if needed
for d in [WEIGHTS_DIR, LOGS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ── Celeb-DF Raw Layout ───────────────────────────────
# Expected structure inside RAW_DIR:
#   Celeb-DF-v2/
#     Celeb-real/          ← real celebrity videos
#     Celeb-synthesis/     ← deepfake celebrity videos
#     YouTube-real/        ← real YouTube videos
#     List_of_testing_videos.txt
CELEBDF_ROOT = DATA_DIR

# ── Preprocessing ─────────────────────────────────────
FRAMES_PER_VIDEO = 30          # uniform sample count
FACE_IMAGE_SIZE = 224          # EfficientNet input size
FACE_MARGIN_FACTOR = 1.3       # expand detected face box by 30%
MIN_FACE_CONFIDENCE = 0.9      # RetinaFace threshold
NUM_WORKERS_PREPROCESS = 8  # parallel video workers

# ── Training ──────────────────────────────────────────
BATCH_SIZE = 8
SEQUENCE_LENGTH = 30           # must match FRAMES_PER_VIDEO
LEARNING_RATE = 1e-4
WEIGHT_DECAY = 1e-5
NUM_EPOCHS = 30
EARLY_STOP_PATIENCE = 7
BACKBONE = "tf_efficientnetv2_b3"  # from timm library

# Class weights to handle imbalance (Celeb-DF has ~10:1 fake:real)
# Adjust after checking your split counts
CLASS_WEIGHT_REAL = 2.0
CLASS_WEIGHT_FAKE = 1.0

# ── Inference ─────────────────────────────────────────
MODEL_CHECKPOINT = WEIGHTS_DIR / "best_model.pth"
CONFIDENCE_THRESHOLD = 0.5
MAX_UPLOAD_SIZE_MB = 500
ALLOWED_EXTENSIONS = {".mp4", ".avi", ".mov", ".webm", ".mkv"}

# ── Device ────────────────────────────────────────────
import torch
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
