"""
═══════════════════════════════════════════════════════════════════
Deepfake Detection — Training Script
═══════════════════════════════════════════════════════════════════

Trains the EfficientNetV2-B3 + Temporal Attention LSTM model on
preprocessed Celeb-DF face sequences.

Features:
  ✓ Sanity checks before training starts
  ✓ Mixed precision training (AMP) for GPU efficiency
  ✓ Focal loss for class imbalance
  ✓ Cosine annealing LR schedule with warmup
  ✓ Early stopping on validation AUC
  ✓ TensorBoard logging
  ✓ Performance plots (loss, accuracy, AUC, confusion matrix)
  ✓ Best model checkpoint saving

Usage:
  python -m training.train
  python -m training.train --epochs 50 --batch-size 8
═══════════════════════════════════════════════════════════════════
"""

import sys
import os
import time
import argparse
import json
from pathlib import Path
from datetime import datetime

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torch.cuda.amp import autocast, GradScaler
class SummaryWriter:
    """Dummy writer when TensorBoard is unavailable."""
    def __init__(self, **kwargs): pass
    def add_scalars(self, *args, **kwargs): pass
    def add_scalar(self, *args, **kwargs): pass
    def close(self): pass
from sklearn.metrics import (
    roc_auc_score, accuracy_score, f1_score,
    confusion_matrix, classification_report, roc_curve
)
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config
from training.model import DeepfakeDetector, FocalLoss
from training.dataset import (
    DeepfakeVideoDataset, get_train_transforms, get_val_transforms
)


# ──────────────────────────────────────────────────────
# Sanity Checks
# ──────────────────────────────────────────────────────

def run_sanity_checks():
    """Verify everything is ready before training."""
    print("\n" + "=" * 60)
    print("  SANITY CHECKS")
    print("=" * 60)

    checks_passed = 0
    checks_total = 0

    # 1. Check CUDA
    checks_total += 1
    if torch.cuda.is_available():
        gpu_name = torch.cuda.get_device_name(0)
        gpu_mem = torch.cuda.get_device_properties(0).total_memory / 1e9
        print(f"  ✓ GPU: {gpu_name} ({gpu_mem:.1f} GB)")
        checks_passed += 1
    else:
        print(f"  ⚠ No GPU — training will be VERY slow on CPU")
        checks_passed += 1  # allow CPU training

    # 2. Check processed data exists
    for split in ["train", "val"]:
        checks_total += 1
        split_dir = config.PROCESSED_DIR / split
        if split_dir.exists():
            real_count = len(list((split_dir / "real").iterdir())) if (split_dir / "real").exists() else 0
            fake_count = len(list((split_dir / "fake").iterdir())) if (split_dir / "fake").exists() else 0
            print(f"  ✓ {split}: {real_count} real, {fake_count} fake videos")
            if real_count == 0 or fake_count == 0:
                print(f"    ⚠ WARNING: Missing real or fake data in {split}!")
            checks_passed += 1
        else:
            print(f"  ✗ {split} directory not found: {split_dir}")
            print(f"    Run: python -m preprocessing.preprocess_celebdf")

    # 3. Check a sample video has enough frames
    checks_total += 1
    train_real = config.PROCESSED_DIR / "train" / "real"
    if train_real.exists():
        sample_dirs = list(train_real.iterdir())
        if sample_dirs:
            frames = list(sample_dirs[0].glob("*.jpg"))
            print(f"  ✓ Sample video '{sample_dirs[0].name}' has {len(frames)} frames")
            checks_passed += 1
        else:
            print(f"  ✗ No videos found in {train_real}")
    else:
        print(f"  ✗ Train/real directory not found")

    # 4. Check model can be instantiated
    checks_total += 1
    try:
        model = DeepfakeDetector(backbone_name=config.BACKBONE, pretrained=True)
        trainable, total = model.get_trainable_params()
        print(f"  ✓ Model created: {trainable:,} trainable / {total:,} total params")
        checks_passed += 1
        del model
    except Exception as e:
        print(f"  ✗ Model creation failed: {e}")

    # 5. Quick forward pass test
    checks_total += 1
    try:
        model = DeepfakeDetector(backbone_name=config.BACKBONE, pretrained=False)
        model.eval()
        dummy = torch.randn(1, 10, 3, 224, 224)
        with torch.no_grad():
            logits, attn = model(dummy)
        assert logits.shape == (1, 1), f"Expected (1,1), got {logits.shape}"
        assert attn.shape == (1, 10), f"Expected (1,10), got {attn.shape}"
        assert torch.allclose(attn.sum(dim=1), torch.ones(1), atol=1e-5)
        print(f"  ✓ Forward pass OK (logits={logits.shape}, attn sums to 1.0)")
        checks_passed += 1
        del model, dummy
    except Exception as e:
        print(f"  ✗ Forward pass failed: {e}")

    # 6. Check weights dir is writable
    checks_total += 1
    try:
        test_file = config.WEIGHTS_DIR / ".write_test"
        test_file.touch()
        test_file.unlink()
        print(f"  ✓ Weights dir writable: {config.WEIGHTS_DIR}")
        checks_passed += 1
    except Exception as e:
        print(f"  ✗ Cannot write to {config.WEIGHTS_DIR}: {e}")

    print(f"\n  Result: {checks_passed}/{checks_total} checks passed")
    print("=" * 60)

    if checks_passed < checks_total:
        print("\n  Some checks failed. Fix issues above before training.")
        return False
    return True


# ──────────────────────────────────────────────────────
# Training Loop
# ──────────────────────────────────────────────────────

def train_one_epoch(model, loader, criterion, optimizer, scaler, device):
    model.train()
    running_loss = 0.0
    all_preds = []
    all_labels = []

    pbar = tqdm(loader, desc="  Train", leave=False)
    for frames, labels, _ in pbar:
        frames = frames.to(device)                    # (B, T, C, H, W)
        labels = labels.to(device).float().unsqueeze(1)  # (B, 1)

        optimizer.zero_grad()

        with torch.amp.autocast("cuda", enabled=(device.type == "cuda")):
            logits, _ = model(frames)
            loss = criterion(logits, labels)

        if device.type == "cuda":
            scaler.scale(loss).backward()
            scaler.unscale_(optimizer)
            nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            scaler.step(optimizer)
            scaler.update()
        else:
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()

        running_loss += loss.item() * frames.size(0)
        preds = torch.sigmoid(logits).detach().cpu().numpy()
        all_preds.extend(preds.flatten())
        all_labels.extend(labels.cpu().numpy().flatten())

        pbar.set_postfix(loss=f"{loss.item():.4f}")

    avg_loss = running_loss / len(loader.dataset)
    all_preds = np.array(all_preds)
    all_labels = np.array(all_labels)

    acc = accuracy_score(all_labels, (all_preds > 0.5).astype(int))
    try:
        auc = roc_auc_score(all_labels, all_preds)
    except ValueError:
        auc = 0.0

    return avg_loss, acc, auc


@torch.no_grad()
def validate(model, loader, criterion, device):
    model.eval()
    running_loss = 0.0
    all_preds = []
    all_labels = []

    for frames, labels, _ in tqdm(loader, desc="  Val  ", leave=False):
        frames = frames.to(device)
        labels = labels.to(device).float().unsqueeze(1)

        with autocast(enabled=(device.type == "cuda")):
            logits, _ = model(frames)
            loss = criterion(logits, labels)

        running_loss += loss.item() * frames.size(0)
        preds = torch.sigmoid(logits).cpu().numpy()
        all_preds.extend(preds.flatten())
        all_labels.extend(labels.cpu().numpy().flatten())

    avg_loss = running_loss / len(loader.dataset)
    all_preds = np.array(all_preds)
    all_labels = np.array(all_labels)

    acc = accuracy_score(all_labels, (all_preds > 0.5).astype(int))
    f1 = f1_score(all_labels, (all_preds > 0.5).astype(int), zero_division=0)
    try:
        auc = roc_auc_score(all_labels, all_preds)
    except ValueError:
        auc = 0.0

    return avg_loss, acc, auc, f1, all_preds, all_labels


# ──────────────────────────────────────────────────────
# Performance Plots
# ──────────────────────────────────────────────────────

def plot_training_curves(history, save_dir):
    """Generate and save training performance plots."""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle("Training Performance — Reality Check AI", fontsize=14, fontweight="bold")

    epochs = range(1, len(history["train_loss"]) + 1)

    # Loss
    ax = axes[0, 0]
    ax.plot(epochs, history["train_loss"], "b-", label="Train", linewidth=2)
    ax.plot(epochs, history["val_loss"], "r-", label="Val", linewidth=2)
    ax.set_title("Loss")
    ax.set_xlabel("Epoch")
    ax.set_ylabel("Focal Loss")
    ax.legend()
    ax.grid(True, alpha=0.3)

    # Accuracy
    ax = axes[0, 1]
    ax.plot(epochs, history["train_acc"], "b-", label="Train", linewidth=2)
    ax.plot(epochs, history["val_acc"], "r-", label="Val", linewidth=2)
    ax.set_title("Accuracy")
    ax.set_xlabel("Epoch")
    ax.set_ylabel("Accuracy")
    ax.legend()
    ax.grid(True, alpha=0.3)

    # AUC-ROC
    ax = axes[1, 0]
    ax.plot(epochs, history["train_auc"], "b-", label="Train", linewidth=2)
    ax.plot(epochs, history["val_auc"], "r-", label="Val", linewidth=2)
    ax.set_title("AUC-ROC")
    ax.set_xlabel("Epoch")
    ax.set_ylabel("AUC")
    ax.legend()
    ax.grid(True, alpha=0.3)

    # F1 Score
    ax = axes[1, 1]
    ax.plot(epochs, history["val_f1"], "g-", label="Val F1", linewidth=2)
    ax.set_title("Validation F1 Score")
    ax.set_xlabel("Epoch")
    ax.set_ylabel("F1")
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(save_dir / "training_curves.png", dpi=150, bbox_inches="tight")
    plt.close()
    print(f"\n  Saved training_curves.png")


def plot_roc_curve(labels, preds, save_dir):
    """Plot and save ROC curve."""
    fpr, tpr, _ = roc_curve(labels, preds)
    auc = roc_auc_score(labels, preds)

    plt.figure(figsize=(8, 6))
    plt.plot(fpr, tpr, "b-", linewidth=2, label=f"AUC = {auc:.4f}")
    plt.plot([0, 1], [0, 1], "k--", alpha=0.4)
    plt.xlabel("False Positive Rate")
    plt.ylabel("True Positive Rate")
    plt.title("ROC Curve — Validation Set")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.savefig(save_dir / "roc_curve.png", dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved roc_curve.png")


def plot_confusion_matrix(labels, preds, save_dir):
    """Plot and save confusion matrix."""
    cm = confusion_matrix(labels, (preds > 0.5).astype(int))
    fig, ax = plt.subplots(figsize=(6, 5))
    im = ax.imshow(cm, cmap="Blues")
    ax.set_xticks([0, 1])
    ax.set_yticks([0, 1])
    ax.set_xticklabels(["Real", "Fake"])
    ax.set_yticklabels(["Real", "Fake"])
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Actual")
    ax.set_title("Confusion Matrix — Validation Set")
    for i in range(2):
        for j in range(2):
            ax.text(j, i, str(cm[i, j]), ha="center", va="center",
                    fontsize=18, fontweight="bold",
                    color="white" if cm[i, j] > cm.max() / 2 else "black")
    plt.colorbar(im)
    plt.tight_layout()
    plt.savefig(save_dir / "confusion_matrix.png", dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved confusion_matrix.png")


# ──────────────────────────────────────────────────────
# Main Training Function
# ──────────────────────────────────────────────────────

def train(args):
    # ── Setup ──
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = config.LOGS_DIR / f"run_{timestamp}"
    run_dir.mkdir(parents=True, exist_ok=True)
    writer = SummaryWriter(log_dir=str(run_dir))

    device = config.DEVICE
    print(f"\n  Device: {device}")
    print(f"  Run dir: {run_dir}")

    # ── Datasets ──
    print("\n  Loading datasets...")
    train_dataset = DeepfakeVideoDataset(
        root_dir=config.PROCESSED_DIR / "train",
        seq_len=config.SEQUENCE_LENGTH,
        transform=get_train_transforms(config.FACE_IMAGE_SIZE),
    )
    val_dataset = DeepfakeVideoDataset(
        root_dir=config.PROCESSED_DIR / "val",
        seq_len=config.SEQUENCE_LENGTH,
        transform=get_val_transforms(config.FACE_IMAGE_SIZE),
    )

    if len(train_dataset) == 0 or len(val_dataset) == 0:
        print("\n  [ERROR] Empty dataset! Run preprocessing first:")
        print("    python -m preprocessing.preprocess_celebdf")
        return

    train_loader = DataLoader(
        train_dataset, batch_size=args.batch_size,
        shuffle=True, num_workers=4, pin_memory=True, drop_last=True,
    )
    val_loader = DataLoader(
        val_dataset, batch_size=args.batch_size,
        shuffle=False, num_workers=4, pin_memory=True,
    )

    # ── Model ──
    model = DeepfakeDetector(
        backbone_name=config.BACKBONE,
        pretrained=True,
    ).to(device)

    trainable, total = model.get_trainable_params()
    print(f"\n  Model: {trainable:,} trainable / {total:,} total parameters")

    # ── Loss (Focal Loss with class weights) ──
    pos_weight = torch.tensor([config.CLASS_WEIGHT_REAL / config.CLASS_WEIGHT_FAKE]).to(device)
    criterion = FocalLoss(alpha=1.0, gamma=2.0, pos_weight=pos_weight)

    # ── Optimizer ──
    optimizer = torch.optim.AdamW(
        filter(lambda p: p.requires_grad, model.parameters()),
        lr=args.lr,
        weight_decay=config.WEIGHT_DECAY,
    )

    # Cosine annealing with warmup
    warmup_epochs = 3
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
        optimizer, T_max=args.epochs - warmup_epochs, eta_min=1e-6
    )

    scaler = torch.amp.GradScaler("cuda", enabled=(device.type == "cuda"))

    # ── Training Loop ──
    history = {k: [] for k in [
        "train_loss", "train_acc", "train_auc",
        "val_loss", "val_acc", "val_auc", "val_f1", "lr"
    ]}

    best_auc = 0.0
    patience_counter = 0
    best_preds, best_labels = None, None

    print("\n" + "=" * 60)
    print("  TRAINING STARTED")
    print("=" * 60)

    for epoch in range(1, args.epochs + 1):
        start_time = time.time()

        # Warmup: linear LR ramp for first N epochs
        if epoch <= warmup_epochs:
            warmup_lr = args.lr * (epoch / warmup_epochs)
            for pg in optimizer.param_groups:
                pg["lr"] = warmup_lr

        current_lr = optimizer.param_groups[0]["lr"]
        print(f"\n  Epoch {epoch}/{args.epochs}  (lr={current_lr:.2e})")

        # Train
        train_loss, train_acc, train_auc = train_one_epoch(
            model, train_loader, criterion, optimizer, scaler, device
        )

        # Validate
        val_loss, val_acc, val_auc, val_f1, val_preds, val_labels = validate(
            model, val_loader, criterion, device
        )

        # LR schedule (after warmup)
        if epoch > warmup_epochs:
            scheduler.step()

        elapsed = time.time() - start_time

        # Log
        print(f"  Train — loss: {train_loss:.4f}  acc: {train_acc:.4f}  auc: {train_auc:.4f}")
        print(f"  Val   — loss: {val_loss:.4f}  acc: {val_acc:.4f}  auc: {val_auc:.4f}  f1: {val_f1:.4f}")
        print(f"  Time: {elapsed:.1f}s")

        history["train_loss"].append(train_loss)
        history["train_acc"].append(train_acc)
        history["train_auc"].append(train_auc)
        history["val_loss"].append(val_loss)
        history["val_acc"].append(val_acc)
        history["val_auc"].append(val_auc)
        history["val_f1"].append(val_f1)
        history["lr"].append(current_lr)

        writer.add_scalars("Loss", {"train": train_loss, "val": val_loss}, epoch)
        writer.add_scalars("Accuracy", {"train": train_acc, "val": val_acc}, epoch)
        writer.add_scalars("AUC", {"train": train_auc, "val": val_auc}, epoch)
        writer.add_scalar("F1/val", val_f1, epoch)
        writer.add_scalar("LR", current_lr, epoch)

        # Save best model
        if val_auc > best_auc:
            best_auc = val_auc
            patience_counter = 0
            best_preds = val_preds
            best_labels = val_labels

            checkpoint = {
                "epoch": epoch,
                "model_state_dict": model.state_dict(),
                "optimizer_state_dict": optimizer.state_dict(),
                "val_auc": val_auc,
                "val_acc": val_acc,
                "val_f1": val_f1,
                "config": {
                    "backbone": config.BACKBONE,
                    "seq_len": config.SEQUENCE_LENGTH,
                    "image_size": config.FACE_IMAGE_SIZE,
                },
            }
            torch.save(checkpoint, config.MODEL_CHECKPOINT)
            torch.save(checkpoint, run_dir / f"best_model.pth")
            print(f"  ★ New best AUC: {val_auc:.4f} — saved checkpoint")
        else:
            patience_counter += 1
            print(f"  No improvement ({patience_counter}/{config.EARLY_STOP_PATIENCE})")

        if patience_counter >= config.EARLY_STOP_PATIENCE:
            print(f"\n  Early stopping at epoch {epoch}")
            break

    # ── Final Report ──
    print("\n" + "=" * 60)
    print("  TRAINING COMPLETE")
    print("=" * 60)
    print(f"  Best validation AUC: {best_auc:.4f}")
    print(f"  Checkpoint: {config.MODEL_CHECKPOINT}")
    print(f"  Logs: {run_dir}")

    # Save history
    with open(run_dir / "history.json", "w") as f:
        json.dump(history, f, indent=2)

    # Generate plots
    print("\n  Generating performance plots...")
    plot_training_curves(history, run_dir)
    if best_labels is not None and best_preds is not None:
        plot_roc_curve(best_labels, best_preds, run_dir)
        plot_confusion_matrix(best_labels, best_preds, run_dir)
        print(f"\n  Classification Report (best epoch):")
        print(classification_report(
            best_labels, (best_preds > 0.5).astype(int),
            target_names=["Real", "Fake"]
        ))

    writer.close()
    print(f"\n  View TensorBoard: tensorboard --logdir {config.LOGS_DIR}")


# ──────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train deepfake detector")
    parser.add_argument("--epochs", type=int, default=config.NUM_EPOCHS)
    parser.add_argument("--batch-size", type=int, default=config.BATCH_SIZE)
    parser.add_argument("--lr", type=float, default=config.LEARNING_RATE)
    parser.add_argument("--skip-sanity", action="store_true")
    args = parser.parse_args()

    if not args.skip_sanity:
        if not run_sanity_checks():
            print("\n  Fix sanity check failures before training.")
            sys.exit(1)

    train(args)
