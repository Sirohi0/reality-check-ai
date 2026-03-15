"""
Dataset and augmentation for deepfake detection training.
Loads pre-cropped face sequences from the preprocessed directory.
"""

import os
import random
from pathlib import Path

import cv2
import numpy as np
import torch
from torch.utils.data import Dataset
import albumentations as A
from albumentations.pytorch import ToTensorV2


def get_train_transforms(image_size=224):
    """
    Training augmentations — critical for generalization.
    Includes compression artifacts (JPEG), blur, noise, color jitter.
    These simulate real-world video quality degradation.
    """
    return A.Compose([
        A.HorizontalFlip(p=0.5),
        A.OneOf([
            A.ImageCompression(quality_lower=30, quality_upper=80, p=1.0),
            A.GaussianBlur(blur_limit=(3, 7), p=1.0),
            A.GaussNoise(var_limit=(10, 50), p=1.0),
        ], p=0.5),
        A.OneOf([
            A.RandomBrightnessContrast(brightness_limit=0.2, contrast_limit=0.2, p=1.0),
            A.HueSaturationValue(hue_shift_limit=10, sat_shift_limit=20, val_shift_limit=20, p=1.0),
        ], p=0.3),
        A.ShiftScaleRotate(shift_limit=0.05, scale_limit=0.05, rotate_limit=10, p=0.3),
        A.CoarseDropout(max_holes=4, max_height=20, max_width=20, fill_value=0, p=0.2),
        A.Resize(image_size, image_size),
        A.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ToTensorV2(),
    ])


def get_val_transforms(image_size=224):
    """Validation/test — no augmentation, just resize + normalize."""
    return A.Compose([
        A.Resize(image_size, image_size),
        A.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ToTensorV2(),
    ])


class DeepfakeVideoDataset(Dataset):
    """
    Loads a sequence of face frames for each video.

    Directory structure expected:
        root/real/video_id/00.jpg, 01.jpg, ...
        root/fake/video_id/00.jpg, 01.jpg, ...

    Returns:
        frames: Tensor of shape (seq_len, C, H, W)
        label:  0 for real, 1 for fake
        video_id: string identifier
    """

    def __init__(self, root_dir, seq_len=30, transform=None):
        self.root_dir = Path(root_dir)
        self.seq_len = seq_len
        self.transform = transform
        self.samples = []  # list of (video_dir, label)

        for label_name, label_int in [("real", 0), ("fake", 1)]:
            label_dir = self.root_dir / label_name
            if not label_dir.exists():
                continue
            for video_dir in sorted(label_dir.iterdir()):
                if video_dir.is_dir():
                    frames = sorted(video_dir.glob("*.jpg"))
                    if len(frames) >= 5:  # need at least 5 frames
                        self.samples.append((video_dir, label_int))

        print(f"  [Dataset] {root_dir}: {len(self.samples)} videos "
              f"(real={sum(1 for _, l in self.samples if l == 0)}, "
              f"fake={sum(1 for _, l in self.samples if l == 1)})")

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        video_dir, label = self.samples[idx]
        frame_paths = sorted(video_dir.glob("*.jpg"))

        # Uniform sample to seq_len
        if len(frame_paths) >= self.seq_len:
            indices = np.linspace(0, len(frame_paths) - 1, self.seq_len, dtype=int)
            selected = [frame_paths[i] for i in indices]
        else:
            # Pad by repeating last frame
            selected = list(frame_paths)
            while len(selected) < self.seq_len:
                selected.append(frame_paths[-1])

        frames = []
        for fp in selected:
            img = cv2.imread(str(fp))
            if img is None:
                img = np.zeros((224, 224, 3), dtype=np.uint8)
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

            if self.transform:
                augmented = self.transform(image=img)
                img_tensor = augmented["image"]
            else:
                img_tensor = torch.from_numpy(img).permute(2, 0, 1).float() / 255.0

            frames.append(img_tensor)

        frames_tensor = torch.stack(frames, dim=0)  # (seq_len, C, H, W)
        return frames_tensor, label, video_dir.name
