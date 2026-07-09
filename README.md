* [README](https://github.com/Sirohi0/reality-check-ai#)
* [License](https://github.com/Sirohi0/reality-check-ai#)

# 🕵️ Reality Check AI — Deepfake Video Detection
Upload a video, get an instant verdict on whether it's real or AI-manipulated — backed by frame-level attention, not a black box.

## 🧠 Overview
Reality Check AI is a full-stack deepfake detection system that analyzes uploaded videos using deep learning to determine whether they are real or AI-generated.
It extracts frames, isolates faces, runs them through a fine-tuned **EfficientNetV2-B3** backbone, and feeds the resulting sequence into a **Bidirectional LSTM with temporal attention** — so the model doesn't just say "fake," it learns *which frames* gave it away.

## ⚡ Features
* 🎬 **Video-Level Detection** — Upload any video, get a fake/real verdict with confidence score
* 🧩 **Temporal Attention** — Learns which frames matter most (blinking, flicker, unnatural motion)
* 🖼️ **Face-Aware Pipeline** — Detects and crops faces before analysis, not full noisy frames
* 📊 **Explainable Output** — Per-frame attention weights + step-by-step pipeline breakdown in the API response
* ⚡ **FastAPI Backend** — Async inference API with Swagger docs out of the box
* 💻 **React Frontend** — Drag-and-drop upload, live analysis view, confidence gauge
* 🐳 **Dockerized** — One command spins up frontend + backend together

## 🏗️ Architecture
```
Input Video
    ↓
Frame Extraction (FFmpeg/PyAV) — 30 frames sampled uniformly
    ↓
Face Detection + Cropping (Haar/RetinaFace)
    ↓
EfficientNetV2-B3 — spatial feature extraction per frame
    ↓
Bidirectional LSTM + Temporal Attention
    ↓
Fully Connected + Sigmoid — confidence score (0.0–1.0)
```

## 📈 Test Results
Evaluated on the official Celeb-DF v2 test set (518 videos).

| Metric | Score |
|---|---|
| AUC-ROC | 99.54% |
| Accuracy | 96.91% |
| F1 Score | 97.65% |
| Misclassified | 16 / 518 videos |

## 🛠️ Tech Stack
**Frontend**
* React 18 + Vite
* Tailwind CSS
* React Router v6
* Axios

**Backend**
* FastAPI + Uvicorn
* PyTorch + timm (EfficientNetV2-B3)
* OpenCV (face detection)
* PyAV / FFmpeg (frame extraction)
* Albumentations (augmentation)
* scikit-learn (metrics)

**Model**
* Backbone: EfficientNetV2-B3 (ImageNet pretrained, 60% frozen)
* Temporal: Bidirectional LSTM (1 layer, 256 hidden)
* Attention: Temporal self-attention over frame sequence
* Loss: Focal Loss (class imbalance)
* Training: Cosine annealing LR with warmup, early stopping on val AUC

## 🚀 Getting Started

### Option A — Docker (recommended)
```
git clone https://github.com/Sirohi0/reality-check-ai.git
cd reality-check-ai
docker compose up --build
```
* Frontend → http://localhost:3000
* Backend API → http://localhost:8000
* Swagger docs → http://localhost:8000/docs

> Trained model checkpoints aren't included in this repo (see Dataset section below). Place your checkpoint in `deepfake-backend/checkpoints/` before running, or the backend starts without a loaded model.
>
> The Docker image builds a **CPU-only** PyTorch for portability on free-tier hosts — expect inference to take several seconds per video on CPU vs the ~2.3s shown below (measured on GPU).

### Option B — Manual Setup

**1️⃣ Backend**
```
cd deepfake-backend
conda create -n dfake python=3.11 -y
conda activate dfake

pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
pip install fastapi uvicorn[standard] python-multipart timm scikit-learn opencv-python-headless av Pillow albumentations matplotlib tqdm pyyaml

python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

**2️⃣ Frontend**
```
cd reality-check-ai
npm install
npm run dev
```
Open http://localhost:3000 in your browser.

## 📡 API Endpoints

🔹 **Health Check**
```
GET /health
```
```json
{
  "status": "ok",
  "model_loaded": true,
  "device": "cuda",
  "version": "1.0.0"
}
```

🔹 **Analyze Video**
```
POST /api/analyze
```
```
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
  "attention_weights": [0.0322, 0.0341, "..."],
  "processing_time_ms": 2340,
  "pipeline_steps": [
    { "step": "frame_extraction", "detail": "Extracted 30 frames", "time_ms": 180 },
    { "step": "face_detection", "detail": "Detected 30/30 faces", "time_ms": 920 },
    { "step": "model_inference", "detail": "EfficientNet + LSTM", "time_ms": 1240 }
  ]
}
```
📍 Interactive docs: http://localhost:8000/docs (Swagger UI)

## 🎓 Training From Scratch
```
cd deepfake-backend

# 1. Download Celeb-DF v2 into data/
#    https://github.com/yuezunli/celeb-deepfakeforensics

# 2. Preprocess (extract faces from all videos)
python -m preprocessing.preprocess_celebdf

# 3. Train
python -m training.train --batch-size 8

# 4. Evaluate on test set
python evaluate_test.py
```

**Training details:**
* Dataset: Celeb-DF v2 (4,809 train / 1,202 val / 518 test videos)
* Class distribution: 890 real + 5,639 fake (Focal Loss + class weights)
* Augmentations: JPEG compression, Gaussian blur/noise, color jitter, coarse dropout
* Best checkpoint: Epoch 12, validation AUC 99.82%
* Hardware: RTX 4070 Mobile (8GB VRAM), i9-14900HX

## 📦 Dataset
Uses [Celeb-DF v2](https://github.com/yuezunli/celeb-deepfakeforensics):
* 590 real videos from YouTube (59 celebrities)
* 5,639 deepfake videos, improved synthesis quality
* Official train/test split provided

Not included in this repo due to size — download it separately from the link above.

## 🎯 Use Cases
* 🔍 Media authenticity verification
* 🛡️ Content moderation pipelines
* 📰 Journalism / fact-checking tooling
* 🧪 Research baseline for deepfake detection benchmarking

## 📌 Future Improvements
* ✅ Test coverage (pytest for FastAPI routes)
* ✅ CI/CD pipeline (GitHub Actions)
* 🌐 Live hosted demo
* 📁 Support for additional datasets (FaceForensics++)
* 📥 Batch video analysis

## 🤝 Contributing
Contributions are welcome! Feel free to fork and improve.

## 📜 License
This project is licensed under the MIT License.

## 👨‍💻 Authors
Co-built by **Sanchit Sirohi** and **Saanann Roy** — see [CONTRIBUTORS.md](./CONTRIBUTORS.md) for the ownership split.

## 🙏 Acknowledgments
* Celeb-DF — Li et al., *"Celeb-DF: A Large-scale Challenging Dataset for DeepFake Forensics"*
* [timm](https://github.com/huggingface/pytorch-image-models) — PyTorch Image Models
* [Albumentations](https://albumentations.ai/) — Image augmentation library

## ⭐ If you like this project
Give it a star ⭐ — it helps a lot!
