"""
Inference service: loads trained model, processes uploaded videos, returns predictions.
Used by the FastAPI backend for real-time deepfake detection.
"""

import sys
import time
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
import torch
import torch.nn.functional as F
import av

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config
from training.model import DeepfakeDetector
from training.dataset import get_val_transforms


class ModelLoader:
    """
    Singleton model loader — loads the model once and keeps it in memory.
    Thread-safe for FastAPI's async workers.
    """
    _instance = None
    _model = None
    _device = None
    _transform = None

    @classmethod
    def get_model(cls):
        if cls._model is None:
            cls._load()
        return cls._model, cls._device, cls._transform

    @classmethod
    def _load(cls):
        cls._device = config.DEVICE
        print(f"[ModelLoader] Loading model on {cls._device}...")

        checkpoint_path = config.MODEL_CHECKPOINT
        if not checkpoint_path.exists():
            raise FileNotFoundError(
                f"Model checkpoint not found: {checkpoint_path}\n"
                f"Train the model first: python -m training.train"
            )

        # Load checkpoint
        checkpoint = torch.load(checkpoint_path, map_location=cls._device, weights_only=False)

        # Extract config from checkpoint
        ckpt_config = checkpoint.get("config", {})
        backbone = ckpt_config.get("backbone", config.BACKBONE)

        # Build model
        cls._model = DeepfakeDetector(
            backbone_name=backbone,
            pretrained=False,  # we load weights from checkpoint
        )
        cls._model.load_state_dict(checkpoint["model_state_dict"])
        cls._model.to(cls._device)
        cls._model.eval()

        # Transforms
        image_size = ckpt_config.get("image_size", config.FACE_IMAGE_SIZE)
        cls._transform = get_val_transforms(image_size)

        val_auc = checkpoint.get("val_auc", "N/A")
        epoch = checkpoint.get("epoch", "N/A")
        print(f"[ModelLoader] Loaded checkpoint (epoch={epoch}, val_auc={val_auc})")
        print(f"[ModelLoader] Model ready on {cls._device}")

    @classmethod
    def is_loaded(cls):
        return cls._model is not None


class VideoAnalyzer:
    """
    Full inference pipeline for a single video:
      1. Extract frames uniformly
      2. Detect + crop faces (with fallback center crop)
      3. Run through model
      4. Return prediction with confidence and per-frame attention
    """

    def __init__(self):
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )

    def extract_frames(self, video_path: str, num_frames: int = 30):
        """Extract uniformly spaced frames from video."""
        frames = []
        try:
            container = av.open(video_path)
            stream = container.streams.video[0]
            total = stream.frames or 300

            indices = set(np.linspace(0, max(total - 1, 0), num_frames, dtype=int))

            for i, frame in enumerate(container.decode(video=0)):
                if i in indices:
                    img = frame.to_ndarray(format="bgr24")
                    frames.append(img)
                if len(frames) >= num_frames:
                    break

            container.close()
        except Exception as e:
            print(f"[VideoAnalyzer] Frame extraction error: {e}")
            # Fallback: try OpenCV
            try:
                cap = cv2.VideoCapture(video_path)
                total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 300
                indices = set(np.linspace(0, max(total - 1, 0), num_frames, dtype=int))
                for i in range(total):
                    ret, frame = cap.read()
                    if not ret:
                        break
                    if i in indices:
                        frames.append(frame)
                cap.release()
            except Exception as e2:
                print(f"[VideoAnalyzer] OpenCV fallback also failed: {e2}")

        # Pad if needed
        while len(frames) < num_frames and len(frames) > 0:
            frames.append(frames[-1].copy())

        return frames[:num_frames]

    def detect_and_crop_face(self, frame_bgr):
        """Detect largest face, crop with margin. Returns face crop or center crop."""
        gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(50, 50))

        if len(faces) > 0:
            x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
            # Expand with margin
            cx, cy = x + w // 2, y + h // 2
            side = int(max(w, h) * config.FACE_MARGIN_FACTOR)
            fh, fw = frame_bgr.shape[:2]
            x1 = max(0, cx - side // 2)
            y1 = max(0, cy - side // 2)
            x2 = min(fw, cx + side // 2)
            y2 = min(fh, cy + side // 2)
            crop = frame_bgr[y1:y2, x1:x2]
            if crop.size > 0:
                return cv2.resize(crop, (config.FACE_IMAGE_SIZE, config.FACE_IMAGE_SIZE)), True

        # Fallback: center crop
        h, w = frame_bgr.shape[:2]
        side = min(h, w)
        cx, cy = w // 2, h // 2
        crop = frame_bgr[cy - side // 2:cy + side // 2, cx - side // 2:cx + side // 2]
        crop = cv2.resize(crop, (config.FACE_IMAGE_SIZE, config.FACE_IMAGE_SIZE))
        return crop, False

    @torch.no_grad()
    def analyze(self, video_path: str) -> dict:
        """
        Full analysis pipeline. Returns:
        {
            "is_fake": bool,
            "confidence": float (0.0-1.0),
            "label": "fake" | "real",
            "frames_analyzed": int,
            "faces_detected": int,
            "attention_weights": list[float],   # per-frame importance
            "processing_time_ms": float,
            "pipeline_steps": [...]
        }
        """
        start_time = time.time()
        pipeline_steps = []

        # Step 1: Extract frames
        t0 = time.time()
        frames = self.extract_frames(video_path, config.FRAMES_PER_VIDEO)
        pipeline_steps.append({
            "step": "frame_extraction",
            "detail": f"Extracted {len(frames)} frames",
            "time_ms": round((time.time() - t0) * 1000),
        })

        if not frames:
            return {
                "is_fake": False,
                "confidence": 0.0,
                "label": "error",
                "error": "Could not extract frames from video",
                "processing_time_ms": round((time.time() - start_time) * 1000),
            }

        # Step 2: Face detection + cropping
        t0 = time.time()
        model, device, transform = ModelLoader.get_model()
        face_crops = []
        faces_detected = 0

        for frame in frames:
            crop, found = self.detect_and_crop_face(frame)
            if found:
                faces_detected += 1
            crop_rgb = cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)
            augmented = transform(image=crop_rgb)
            face_crops.append(augmented["image"])

        pipeline_steps.append({
            "step": "face_detection",
            "detail": f"Detected {faces_detected}/{len(frames)} faces",
            "time_ms": round((time.time() - t0) * 1000),
        })

        # Step 3: Model inference
        t0 = time.time()
        input_tensor = torch.stack(face_crops, dim=0).unsqueeze(0).to(device)
        # input_tensor shape: (1, seq_len, C, H, W)

        logits, attn_weights = model(input_tensor)

        probability = torch.sigmoid(logits).item()
        is_fake = probability > config.CONFIDENCE_THRESHOLD
        attn_list = attn_weights.squeeze(0).cpu().numpy().tolist()

        pipeline_steps.append({
            "step": "model_inference",
            "detail": f"EfficientNet + LSTM",
            "time_ms": round((time.time() - t0) * 1000),
        })

        total_time = round((time.time() - start_time) * 1000)

        return {
            "is_fake": is_fake,
            "confidence": round(probability * 100, 2) if is_fake else round((1 - probability) * 100, 2),
            "fake_probability": round(probability * 100, 2),
            "label": "fake" if is_fake else "real",
            "frames_analyzed": len(frames),
            "faces_detected": faces_detected,
            "attention_weights": [round(w, 4) for w in attn_list],
            "processing_time_ms": total_time,
            "pipeline_steps": pipeline_steps,
            "model_info": {
                "backbone": config.BACKBONE,
                "temporal": "BiLSTM + Attention",
            },
        }
