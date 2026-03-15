# Reality Check AI — Deepfake Video Detection

A full-stack deepfake detection system that analyzes uploaded videos using deep learning to determine if they are real or AI-manipulated. Built with EfficientNetV2-B3 + Temporal Attention BiLSTM, trained on Celeb-DF v2.

## Test Results

| Metric | Score |
|--------|-------|
| AUC-ROC | 99.54% |
| Accuracy | 96.91% |
| F1 Score | 97.65% |
| Misclassified | 16 / 518 videos |

Evaluated on the official Celeb-DF v2 test set (518 videos).

## How It Works

```
Input Video
    |
Frame Extraction (FFmpeg/PyAV) --- 30 frames sampled uniformly
    |
Face Detection + Cropping (Haar/RetinaFace) --- isolate face region
    |
EfficientNetV2-B3 --- spatial feature extraction per frame
    |
Bidirectional LSTM + Temporal Attention --- learns which frames matter
    |
Fully Connected + Sigmoid --- confidence score (0.0 to 1.0)
```

The temporal attention mechanism automatically focuses on frames where manipulation artifacts are most visible, such as inconsistent blinking, flickering, or unnatural facial motion.

## Project Structure

```
reality-check-ai/          # React frontend (Vite + Tailwind)
  src/
    components/             # Navbar, DonutChart, DropZone, ConfidenceGauge...
    pages/                  # Landing, Upload, Analysis, Result
    hooks/                  # useAnalysis (real API call), useFileUpload
    services/               # Axios API layer, Firebase auth
    utils/                  # Constants, formatters

deepfake-backend/           # Python backend
  backend/
    main.py                 # FastAPI app (CORS, startup model loading)
    routers/
      analysis.py           # POST /api/analyze endpoint
      health.py             # GET /health endpoint
    services/
      inference.py          # ModelLoader + VideoAnalyzer pipeline
    models/
      schemas.py            # Pydantic request/response schemas
  training/
    model.py                # EfficientNetV2-B3 + BiLSTM + Temporal Attention
    dataset.py              # PyTorch Dataset + Albumentations augmentations
    train.py                # Training loop with sanity checks + plots
  preprocessing/
    preprocess_celebdf.py   # Full Celeb-DF pipeline (video -> face crops)
  config.py                 # All paths, hyperparameters, device config
  evaluate_test.py          # Test set evaluation with metrics + plots
  generate_plots.py         # Training performance visualization
```

## Tech Stack

### Frontend
- React 18 + Vite
- Tailwind CSS
- React Router v6
- Axios

### Backend
- FastAPI + Uvicorn
- PyTorch + timm (EfficientNetV2-B3)
- OpenCV (face detection)
- PyAV / FFmpeg (frame extraction)
- Albumentations (augmentation)
- scikit-learn (metrics)

### Model Architecture
- **Backbone**: EfficientNetV2-B3 (pretrained on ImageNet, 60% frozen)
- **Temporal**: Bidirectional LSTM (1 layer, 256 hidden)
- **Attention**: Temporal self-attention over frame sequence
- **Loss**: Focal Loss (handles class imbalance)
- **Training**: Cosine annealing LR with warmup, early stopping on val AUC

## Setup

### Prerequisites
- Python 3.11+
- Node.js 18+
- NVIDIA GPU with CUDA (recommended)

### Backend Setup

```bash
cd deepfake-backend

# Create environment
conda create -n dfake python=3.11 -y
conda activate dfake

# Install dependencies
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
pip install fastapi uvicorn[standard] python-multipart timm scikit-learn opencv-python-headless av Pillow albumentations matplotlib tqdm pyyaml

# Start the API server
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

### Frontend Setup

```bash
cd reality-check-ai
npm install
npm run dev
```

Open http://localhost:3000 in your browser.

### Training from Scratch

```bash
cd deepfake-backend

# 1. Download Celeb-DF v2 and place in data/ folder
#    https://github.com/yuezunli/celeb-deepfakeforensics

# 2. Preprocess (extract faces from all videos)
python -m preprocessing.preprocess_celebdf

# 3. Train
python -m training.train --batch-size 8

# 4. Evaluate on test set
python evaluate_test.py
```

## API Reference

### `GET /health`
Returns model status and device info.

```json
{
  "status": "ok",
  "model_loaded": true,
  "device": "cuda",
  "version": "1.0.0"
}
```

### `POST /api/analyze`
Upload a video file for deepfake analysis.

```bash
curl -X POST http://localhost:8000/api/analyze -F "file=@video.mp4"
```

```json
{
  "is_fake": true,
  "confidence": 99.74,
  "fake_probability": 99.74,
  "label": "fake",
  "frames_analyzed": 30,
  "faces_detected": 30,
  "attention_weights": [0.0322, 0.0341, ...],
  "processing_time_ms": 2340,
  "pipeline_steps": [
    {"step": "frame_extraction", "detail": "Extracted 30 frames", "time_ms": 180},
    {"step": "face_detection", "detail": "Detected 30/30 faces", "time_ms": 920},
    {"step": "model_inference", "detail": "EfficientNet + LSTM", "time_ms": 1240}
  ]
}
```

### Interactive API Docs
Visit http://localhost:8000/docs for Swagger UI.

## Training Details

- **Dataset**: Celeb-DF v2 (4,809 train / 1,202 val / 518 test videos)
- **Class distribution**: 890 real + 5,639 fake (handled by Focal Loss + class weights)
- **Augmentations**: JPEG compression, Gaussian blur/noise, color jitter, coarse dropout
- **Best checkpoint**: Epoch 12, validation AUC 99.82%
- **Hardware**: Trained on RTX 4070 Mobile (8GB VRAM), i9-14900HX

## Dataset

This project uses [Celeb-DF v2](https://github.com/yuezunli/celeb-deepfakeforensics):
- 590 real videos from YouTube (59 celebrities)
- 5,639 deepfake videos generated with improved synthesis
- Official train/test split provided

The dataset is not included in this repository due to size. Download it separately from the link above.

## Acknowledgments

- [Celeb-DF](https://github.com/yuezunli/celeb-deepfakeforensics) — Li et al., "Celeb-DF: A Large-scale Challenging Dataset for DeepFake Forensics"
- [timm](https://github.com/huggingface/pytorch-image-models) — PyTorch Image Models
- [Albumentations](https://albumentations.ai/) — Image augmentation library
