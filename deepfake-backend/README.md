# Reality Check AI — Backend

Deepfake video detection system using EfficientNetV2-B3 + Temporal Attention BiLSTM, trained on Celeb-DF v2.

## Project Structure

```
deepfake-backend/
├── config.py                          # All paths, hyperparams, device config
├── requirements.txt                   # Python dependencies
│
├── preprocessing/
│   └── preprocess_celebdf.py          # Full Celeb-DF pipeline (frames → faces)
│
├── training/
│   ├── model.py                       # EfficientNet + BiLSTM + Temporal Attention
│   ├── dataset.py                     # PyTorch Dataset + augmentations
│   └── train.py                       # Training loop + sanity checks + plots
│
├── backend/
│   ├── main.py                        # FastAPI app (CORS, lifespan, routers)
│   ├── routers/
│   │   ├── analysis.py                # POST /api/analyze
│   │   └── health.py                  # GET /health
│   ├── services/
│   │   └── inference.py               # ModelLoader + VideoAnalyzer
│   └── models/
│       └── schemas.py                 # Pydantic request/response models
│
├── data/
│   ├── raw/Celeb-DF-v2/               # ← put dataset here
│   └── processed/                     # preprocessed face sequences
│       ├── train/real/  train/fake/
│       ├── val/real/    val/fake/
│       └── test/real/   test/fake/
│
├── weights/                           # saved model checkpoints
└── logs/                              # TensorBoard + training plots
```

## Setup

```bash
# 1. Create virtual environment
python -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows

# 2. Install dependencies
pip install -r requirements.txt

# 3. Install PyTorch with CUDA (if GPU available)
# Visit https://pytorch.org for your specific CUDA version
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
```

## Step 1: Download Celeb-DF v2

Download from: https://github.com/yuezunli/celeb-deepfakeforensics

Extract into `data/raw/Celeb-DF-v2/` so you have:
```
data/raw/Celeb-DF-v2/
  Celeb-real/
  Celeb-synthesis/
  YouTube-real/
  List_of_testing_videos.txt
```

## Step 2: Preprocess Dataset

```bash
# Dry run — count videos, check paths
python -m preprocessing.preprocess_celebdf --dry-run

# Full preprocessing (extracts faces from all videos)
python -m preprocessing.preprocess_celebdf
```

This will:
- Extract 30 uniform frames per video
- Detect and crop faces with margin
- Split into train/val/test using official Celeb-DF split
- Save face images as numbered JPGs

## Step 3: Train the Model

```bash
# Run sanity checks + train
python -m training.train

# Custom settings
python -m training.train --epochs 50 --batch-size 8 --lr 0.0001

# Skip sanity checks
python -m training.train --skip-sanity
```

Training produces:
- `weights/best_model.pth` — best checkpoint by validation AUC
- `logs/run_YYYYMMDD_HHMMSS/` — TensorBoard logs + plots
  - `training_curves.png` — loss, accuracy, AUC, F1 over epochs
  - `roc_curve.png` — ROC curve on validation set
  - `confusion_matrix.png` — confusion matrix
  - `history.json` — all metrics per epoch

View TensorBoard:
```bash
tensorboard --logdir logs/
```

## Step 4: Run the API Server

```bash
# Development (auto-reload)
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

# Production
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --workers 2
```

## API Endpoints

### `GET /health`
```json
{
  "status": "ok",
  "model_loaded": true,
  "device": "cuda",
  "version": "1.0.0"
}
```

### `POST /api/analyze`
Upload a video file (multipart form data).

```bash
curl -X POST http://localhost:8000/api/analyze \
  -F "file=@test_video.mp4"
```

Response:
```json
{
  "is_fake": true,
  "confidence": 94.32,
  "fake_probability": 94.32,
  "label": "fake",
  "frames_analyzed": 30,
  "faces_detected": 28,
  "attention_weights": [0.031, 0.042, ...],
  "processing_time_ms": 2340,
  "pipeline_steps": [
    {"step": "frame_extraction", "detail": "Extracted 30 frames", "time_ms": 180},
    {"step": "face_detection", "detail": "Detected 28/30 faces", "time_ms": 920},
    {"step": "model_inference", "detail": "EfficientNet + LSTM", "time_ms": 1240}
  ],
  "model_info": {
    "backbone": "tf_efficientnetv2_b3",
    "temporal": "BiLSTM + Attention"
  }
}
```

### Swagger Docs
Open `http://localhost:8000/docs` for interactive API docs.

## Connecting to React Frontend

In your React frontend's `.env`:
```
VITE_API_URL=http://localhost:8000
```

In `src/services/analysisService.js`, the upload call hits:
```javascript
const response = await api.post('/api/analyze', formData, {
  headers: { 'Content-Type': 'multipart/form-data' },
});
// response.data matches AnalysisResponse schema above
```

The Vite proxy in `vite.config.js` forwards `/api/*` to port 8000.
