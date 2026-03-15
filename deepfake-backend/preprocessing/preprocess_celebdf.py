"""
═══════════════════════════════════════════════════════════════════
Celeb-DF v2 Preprocessing Pipeline
═══════════════════════════════════════════════════════════════════

This script processes the entire Celeb-DF dataset:
  1. Reads the official test split from List_of_testing_videos.txt
  2. Extracts N uniform frames from each video using PyAV (fast)
  3. Detects faces with RetinaFace and crops with alignment
  4. Saves face sequences as numbered .jpg files
  5. Splits remaining data into train/val (80/20)

Output structure:
  data/processed/
    train/real/video_id/  → 00.jpg, 01.jpg, ..., 29.jpg
    train/fake/video_id/
    val/real/video_id/
    val/fake/video_id/
    test/real/video_id/
    test/fake/video_id/

Usage:
  python -m preprocessing.preprocess_celebdf
  python -m preprocessing.preprocess_celebdf --dry-run   # just count videos
═══════════════════════════════════════════════════════════════════
"""

import sys
import os
import argparse
import random
import shutil
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
from collections import defaultdict

import cv2
import numpy as np
import av
from tqdm import tqdm

# Add parent dir so config is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config


# ──────────────────────────────────────────────────────
# Face Detection
# ──────────────────────────────────────────────────────

class FaceDetector:
    """
    OpenCV DNN face detector (ships with opencv, no extra install).
    Falls back gracefully if RetinaFace is unavailable.
    For better accuracy, install retinaface-pytorch and set USE_RETINAFACE=True.
    """

    def __init__(self, use_retinaface=False):
        self.use_retinaface = use_retinaface
        if use_retinaface:
            try:
                from retinaface import RetinaFace as RF
                self.rf = RF
                print("[FaceDetector] Using RetinaFace (high accuracy)")
            except ImportError:
                print("[FaceDetector] RetinaFace not installed, falling back to OpenCV DNN")
                self.use_retinaface = False

        if not self.use_retinaface:
            # OpenCV's built-in DNN face detector (good enough for preprocessing)
            self.net = cv2.dnn.readNetFromCaffe(
                str(self._get_prototxt()), str(self._get_caffemodel())
            ) if self._models_exist() else None

            if self.net is None:
                # Last resort: Haar cascade
                self.cascade = cv2.CascadeClassifier(
                    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
                )
                print("[FaceDetector] Using Haar cascade (install retinaface-pytorch for better results)")
            else:
                self.cascade = None
                print("[FaceDetector] Using OpenCV DNN")

    def _models_exist(self):
        """Check if OpenCV DNN model files exist."""
        return False  # Skip DNN, use cascade for portability

    def _get_prototxt(self):
        return Path("deploy.prototxt")

    def _get_caffemodel(self):
        return Path("res10_300x300_ssd_iter_140000.caffemodel")

    def detect(self, frame_bgr):
        """
        Returns the largest face bounding box as (x1, y1, x2, y2) or None.
        Box is expanded by FACE_MARGIN_FACTOR for context.
        """
        if self.use_retinaface:
            return self._detect_retinaface(frame_bgr)
        elif hasattr(self, 'cascade') and self.cascade is not None:
            return self._detect_haar(frame_bgr)
        else:
            return self._detect_dnn(frame_bgr)

    def _detect_retinaface(self, frame_bgr):
        resp = self.rf.detect_faces(frame_bgr)
        if not resp:
            return None
        # Pick largest face by area
        best = max(resp.values(), key=lambda f: (
            (f["facial_area"][2] - f["facial_area"][0]) *
            (f["facial_area"][3] - f["facial_area"][1])
        ))
        if best["score"] < config.MIN_FACE_CONFIDENCE:
            return None
        x1, y1, x2, y2 = best["facial_area"]
        return self._expand_box(x1, y1, x2, y2, frame_bgr.shape)

    def _detect_haar(self, frame_bgr):
        gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
        faces = self.cascade.detectMultiScale(gray, 1.1, 5, minSize=(60, 60))
        if len(faces) == 0:
            return None
        # Pick largest
        x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
        return self._expand_box(x, y, x + w, y + h, frame_bgr.shape)

    def _detect_dnn(self, frame_bgr):
        h, w = frame_bgr.shape[:2]
        blob = cv2.dnn.blobFromImage(frame_bgr, 1.0, (300, 300), (104, 177, 123))
        self.net.setInput(blob)
        detections = self.net.forward()
        best_conf, best_box = 0, None
        for i in range(detections.shape[2]):
            conf = detections[0, 0, i, 2]
            if conf > best_conf and conf > config.MIN_FACE_CONFIDENCE:
                best_conf = conf
                box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
                best_box = box.astype(int)
        if best_box is None:
            return None
        return self._expand_box(*best_box, frame_bgr.shape)

    def _expand_box(self, x1, y1, x2, y2, shape):
        """Expand face box by margin factor for more context."""
        h, w = shape[:2]
        cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
        bw, bh = (x2 - x1) * config.FACE_MARGIN_FACTOR, (y2 - y1) * config.FACE_MARGIN_FACTOR
        side = max(bw, bh)  # square crop
        x1 = max(0, int(cx - side / 2))
        y1 = max(0, int(cy - side / 2))
        x2 = min(w, int(cx + side / 2))
        y2 = min(h, int(cy + side / 2))
        return (x1, y1, x2, y2)


# ──────────────────────────────────────────────────────
# Frame Extraction (PyAV — fast)
# ──────────────────────────────────────────────────────

def extract_frames_uniform(video_path, num_frames=30):
    """
    Extract `num_frames` uniformly spaced frames from a video using PyAV.
    Returns list of BGR numpy arrays.
    """
    try:
        container = av.open(str(video_path))
        stream = container.streams.video[0]
        total = stream.frames
        if total == 0:
            # Estimate from duration
            total = int(stream.duration * stream.time_base * stream.average_rate)
        if total <= 0:
            total = 300  # fallback

        indices = set(np.linspace(0, max(total - 1, 0), num_frames, dtype=int))

        frames = []
        for i, frame in enumerate(container.decode(video=0)):
            if i in indices:
                img = frame.to_ndarray(format="bgr24")
                frames.append(img)
            if len(frames) >= num_frames:
                break

        container.close()

        # If we got fewer frames (short video), duplicate last
        while len(frames) < num_frames and len(frames) > 0:
            frames.append(frames[-1].copy())

        return frames[:num_frames]

    except Exception as e:
        print(f"  [ERROR] Failed to read {video_path}: {e}")
        return []


# ──────────────────────────────────────────────────────
# Process a Single Video
# ──────────────────────────────────────────────────────

def process_single_video(args):
    """
    Worker function: extract frames → detect faces → crop → save.
    Returns (video_id, num_saved, num_failed) tuple.
    """
    video_path, output_dir, video_id = args

    out_path = Path(output_dir) / video_id
    out_path.mkdir(parents=True, exist_ok=True)

    # Skip if already processed
    existing = list(out_path.glob("*.jpg"))
    if len(existing) >= config.FRAMES_PER_VIDEO:
        return (video_id, len(existing), 0, "skipped")

    # Extract frames
    frames = extract_frames_uniform(video_path, config.FRAMES_PER_VIDEO)
    if not frames:
        return (video_id, 0, 0, "no_frames")

    # Detect and crop faces
    detector = FaceDetector(use_retinaface=False)  # each worker gets its own
    saved = 0
    failed = 0

    for idx, frame in enumerate(frames):
        box = detector.detect(frame)
        if box is not None:
            x1, y1, x2, y2 = box
            face = frame[y1:y2, x1:x2]
            if face.size > 0:
                face = cv2.resize(face, (config.FACE_IMAGE_SIZE, config.FACE_IMAGE_SIZE))
                cv2.imwrite(str(out_path / f"{idx:02d}.jpg"), face, [cv2.IMWRITE_JPEG_QUALITY, 95])
                saved += 1
                continue

        # If face detection failed, save the center crop as fallback
        h, w = frame.shape[:2]
        side = min(h, w)
        cx, cy = w // 2, h // 2
        crop = frame[cy - side // 2:cy + side // 2, cx - side // 2:cx + side // 2]
        crop = cv2.resize(crop, (config.FACE_IMAGE_SIZE, config.FACE_IMAGE_SIZE))
        cv2.imwrite(str(out_path / f"{idx:02d}.jpg"), crop, [cv2.IMWRITE_JPEG_QUALITY, 95])
        saved += 1
        failed += 1

    return (video_id, saved, failed, "done")


# ──────────────────────────────────────────────────────
# Main Pipeline
# ──────────────────────────────────────────────────────

def parse_test_list(celebdf_root):
    """
    Parse List_of_testing_videos.txt from Celeb-DF.
    Returns set of relative paths that belong to the test split.
    Format per line: "1 Celeb-synthesis/id5_id0_0001.mp4"  (1=fake, 0=real)
    """
    test_file = celebdf_root / "List_of_testing_videos.txt"
    test_videos = set()

    if not test_file.exists():
        print(f"[WARN] {test_file} not found — will use random 80/10/10 split")
        return test_videos

    with open(test_file) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) >= 2:
                rel_path = parts[1].strip()
                test_videos.add(rel_path)

    print(f"[INFO] Loaded {len(test_videos)} test video paths from official split")
    return test_videos


def gather_videos(celebdf_root):
    """
    Gather all videos from Celeb-DF into a list of (path, label, relative_path).
    label: 'real' or 'fake'
    """
    videos = []
    folders = {
        "Celeb-real": "real",
        "YouTube-real": "real",
        "Celeb-synthesis": "fake",
    }

    for folder_name, label in folders.items():
        folder = celebdf_root / folder_name
        if not folder.exists():
            print(f"[WARN] Folder not found: {folder}")
            continue

        for vf in sorted(folder.glob("*.mp4")):
            rel = f"{folder_name}/{vf.name}"
            videos.append((vf, label, rel))

    return videos


def run_preprocessing(dry_run=False):
    celebdf_root = config.CELEBDF_ROOT
    processed_root = config.PROCESSED_DIR

    print("=" * 60)
    print("  CELEB-DF v2 PREPROCESSING PIPELINE")
    print("=" * 60)
    print(f"  Source:       {celebdf_root}")
    print(f"  Output:       {processed_root}")
    print(f"  Frames/video: {config.FRAMES_PER_VIDEO}")
    print(f"  Face size:    {config.FACE_IMAGE_SIZE}x{config.FACE_IMAGE_SIZE}")
    print(f"  Workers:      {config.NUM_WORKERS_PREPROCESS}")
    print("=" * 60)

    if not celebdf_root.exists():
        print(f"\n[ERROR] Celeb-DF not found at: {celebdf_root}")
        print(f"  Download from: https://github.com/yuezunli/celeb-deepfakeforensics")
        print(f"  Extract into:  {config.RAW_DIR}/Celeb-DF-v2/")
        return

    # 1. Gather all videos
    all_videos = gather_videos(celebdf_root)
    print(f"\n[STEP 1/4] Found {len(all_videos)} videos total")

    counts = defaultdict(int)
    for _, label, _ in all_videos:
        counts[label] += 1
    print(f"  Real: {counts['real']},  Fake: {counts['fake']}")

    # 2. Parse official test split
    test_paths = parse_test_list(celebdf_root)

    test_videos = [(p, l, r) for p, l, r in all_videos if r in test_paths]
    remaining = [(p, l, r) for p, l, r in all_videos if r not in test_paths]

    # 3. Split remaining into train/val (80/20)
    random.seed(42)
    random.shuffle(remaining)
    val_size = int(len(remaining) * 0.2)
    val_videos = remaining[:val_size]
    train_videos = remaining[val_size:]

    print(f"\n[STEP 2/4] Split sizes:")
    print(f"  Train: {len(train_videos)}  |  Val: {len(val_videos)}  |  Test: {len(test_videos)}")

    if dry_run:
        print("\n[DRY RUN] — no files will be processed.")
        return

    # 4. Process each split
    for split_name, split_videos in [("train", train_videos), ("val", val_videos), ("test", test_videos)]:
        print(f"\n[STEP 3/4] Processing {split_name} ({len(split_videos)} videos)...")

        tasks = []
        for video_path, label, rel_path in split_videos:
            video_id = Path(rel_path).stem  # e.g., "id5_id0_0001"
            output_dir = processed_root / split_name / label
            output_dir.mkdir(parents=True, exist_ok=True)
            tasks.append((str(video_path), str(output_dir), video_id))

        total_saved = 0
        total_failed_faces = 0
        skipped = 0

        # Use multiprocessing for speed
        with ProcessPoolExecutor(max_workers=config.NUM_WORKERS_PREPROCESS) as executor:
            futures = {executor.submit(process_single_video, t): t for t in tasks}
            pbar = tqdm(as_completed(futures), total=len(futures), desc=f"  {split_name}")

            for future in pbar:
                vid_id, saved, failed, status = future.result()
                if status == "skipped":
                    skipped += 1
                total_saved += saved
                total_failed_faces += failed
                pbar.set_postfix(saved=total_saved, no_face=total_failed_faces, skip=skipped)

        print(f"  Done: {total_saved} faces saved, {total_failed_faces} fallback crops, {skipped} skipped")

    # 5. Summary
    print(f"\n[STEP 4/4] Summary")
    print("=" * 60)
    for split in ["train", "val", "test"]:
        for label in ["real", "fake"]:
            d = processed_root / split / label
            if d.exists():
                num_vids = len(list(d.iterdir()))
                print(f"  {split}/{label}: {num_vids} videos")
    print("=" * 60)
    print("[DONE] Preprocessing complete!")
    print(f"  Output at: {processed_root}")


# ──────────────────────────────────────────────────────
# CLI Entry Point
# ──────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Preprocess Celeb-DF v2 dataset")
    parser.add_argument("--dry-run", action="store_true", help="Count videos without processing")
    args = parser.parse_args()
    run_preprocessing(dry_run=args.dry_run)
