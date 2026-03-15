

import json
import sys
from pathlib import Path
import numpy as np

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Find the latest run directory
logs_dir = Path("logs")
if not logs_dir.exists():
    print("No logs directory found!")
    sys.exit(1)

run_dirs = sorted(logs_dir.iterdir())
if not run_dirs:
    print("No training runs found in logs/")
    sys.exit(1)

run_dir = run_dirs[-1]  # latest run
print(f"Using run: {run_dir}")

# Check for history.json first
history_file = run_dir / "history.json"
if history_file.exists():
    with open(history_file) as f:
        history = json.load(f)
    print(f"Loaded history.json with {len(history['train_loss'])} epochs")
else:
    # Build history from the training output you pasted
    print("No history.json found — using hardcoded results from training output")
    history = {
        "train_loss": [0.1272, 0.0619, 0.0570, 0.0359, 0.0328, 0.0218, 0.0155, 0.0213, 0.0187, 0.0164, 0.0117, 0.0148, 0.0138, 0.0090, 0.0092, 0.0079, 0.0075, 0.0015],
        "train_acc":  [0.9035, 0.9603, 0.9644, 0.9788, 0.9829, 0.9881, 0.9919, 0.9892, 0.9892, 0.9902, 0.9936, 0.9938, 0.9938, 0.9956, 0.9963, 0.9960, 0.9965, 0.9990],
        "train_auc":  [0.8691, 0.9703, 0.9734, 0.9907, 0.9922, 0.9965, 0.9980, 0.9970, 0.9981, 0.9958, 0.9993, 0.9992, 0.9992, 0.9984, 0.9990, 0.9988, 0.9999, 1.0000],
        "val_loss":   [0.0661, 0.0811, 0.1271, 0.0834, 0.0589, 0.0313, 0.0620, 0.0405, 0.0410, 0.0402, 0.0465, 0.0317, 0.0353, 0.0560, 0.0513, 0.0377, 0.0374, 0.0534],
        "val_acc":    [0.9609, 0.9725, 0.9501, 0.9684, 0.9734, 0.9892, 0.9792, 0.9859, 0.9875, 0.9892, 0.9850, 0.9908, 0.9875, 0.9867, 0.9842, 0.9892, 0.9875, 0.9867],
        "val_auc":    [0.9833, 0.9893, 0.9853, 0.9909, 0.9903, 0.9964, 0.9882, 0.9965, 0.9976, 0.9971, 0.9975, 0.9982, 0.9973, 0.9955, 0.9959, 0.9967, 0.9977, 0.9956],
        "val_f1":     [0.9777, 0.9842, 0.9711, 0.9817, 0.9850, 0.9938, 0.9881, 0.9920, 0.9929, 0.9938, 0.9915, 0.9948, 0.9929, 0.9924, 0.9909, 0.9938, 0.9929, 0.9924],
    }

epochs = range(1, len(history["train_loss"]) + 1)
best_epoch = int(np.argmax(history["val_auc"])) + 1
best_auc = max(history["val_auc"])

# ═══════════════════════════════════════════════
# Plot 1: Training Curves (2x2 grid)
# ═══════════════════════════════════════════════
fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.suptitle("Reality Check AI — Training Performance", fontsize=16, fontweight="bold", y=0.98)

# Loss
ax = axes[0, 0]
ax.plot(epochs, history["train_loss"], "dodgerblue", label="Train", linewidth=2)
ax.plot(epochs, history["val_loss"], "tomato", label="Validation", linewidth=2)
ax.axvline(best_epoch, color="green", linestyle="--", alpha=0.5, label=f"Best (epoch {best_epoch})")
ax.set_title("Focal Loss", fontsize=13, fontweight="bold")
ax.set_xlabel("Epoch")
ax.set_ylabel("Loss")
ax.legend()
ax.grid(True, alpha=0.3)

# Accuracy
ax = axes[0, 1]
ax.plot(epochs, [a * 100 for a in history["train_acc"]], "dodgerblue", label="Train", linewidth=2)
ax.plot(epochs, [a * 100 for a in history["val_acc"]], "tomato", label="Validation", linewidth=2)
ax.axvline(best_epoch, color="green", linestyle="--", alpha=0.5)
ax.set_title("Accuracy (%)", fontsize=13, fontweight="bold")
ax.set_xlabel("Epoch")
ax.set_ylabel("Accuracy %")
ax.set_ylim(90, 100)
ax.legend()
ax.grid(True, alpha=0.3)

# AUC-ROC
ax = axes[1, 0]
ax.plot(epochs, history["train_auc"], "dodgerblue", label="Train", linewidth=2)
ax.plot(epochs, history["val_auc"], "tomato", label="Validation", linewidth=2)
ax.axvline(best_epoch, color="green", linestyle="--", alpha=0.5)
ax.axhline(best_auc, color="green", linestyle=":", alpha=0.3)
ax.set_title(f"AUC-ROC (Best: {best_auc:.4f} @ epoch {best_epoch})", fontsize=13, fontweight="bold")
ax.set_xlabel("Epoch")
ax.set_ylabel("AUC")
ax.set_ylim(0.96, 1.002)
ax.legend()
ax.grid(True, alpha=0.3)

# F1 Score
ax = axes[1, 1]
ax.plot(epochs, history["val_f1"], "mediumseagreen", label="Validation F1", linewidth=2, marker="o", markersize=4)
ax.axvline(best_epoch, color="green", linestyle="--", alpha=0.5)
ax.set_title("Validation F1 Score", fontsize=13, fontweight="bold")
ax.set_xlabel("Epoch")
ax.set_ylabel("F1")
ax.set_ylim(0.96, 1.0)
ax.legend()
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(run_dir / "training_curves.png", dpi=150, bbox_inches="tight")
plt.savefig("training_curves.png", dpi=150, bbox_inches="tight")
print(f"Saved: training_curves.png")

# ═══════════════════════════════════════════════
# Plot 2: Model Summary Card
# ═══════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(10, 6))
ax.axis("off")

summary_text = f"""
    REALITY CHECK AI — MODEL PERFORMANCE SUMMARY
    {'='*55}

    Architecture:     EfficientNetV2-B3 + BiLSTM + Temporal Attention
    Dataset:          Celeb-DF v2 (4,809 train / 1,202 val / 518 test)
    Class Balance:    561 real + 4,248 fake (handled by Focal Loss)
    Training Epochs:  {len(history['train_loss'])} (early stop patience: 7)

    BEST VALIDATION RESULTS (Epoch {best_epoch}):
    {'─'*55}
    AUC-ROC:          {best_auc:.4f}
    Accuracy:         {history['val_acc'][best_epoch-1]*100:.2f}%
    F1 Score:         {history['val_f1'][best_epoch-1]:.4f}
    Val Loss:         {history['val_loss'][best_epoch-1]:.4f}

    FINAL TRAINING METRICS (Epoch {len(history['train_loss'])}):
    {'─'*55}
    Train AUC:        {history['train_auc'][-1]:.4f}
    Train Accuracy:   {history['train_acc'][-1]*100:.2f}%
    Train Loss:       {history['train_loss'][-1]:.4f}
"""

ax.text(0.05, 0.95, summary_text, transform=ax.transAxes,
        fontsize=11, fontfamily="monospace", verticalalignment="top",
        bbox=dict(boxstyle="round,pad=0.8", facecolor="#0d1520", edgecolor="#00e5a0", alpha=0.9),
        color="#00e5a0")

plt.savefig(run_dir / "model_summary.png", dpi=150, bbox_inches="tight", facecolor="#0d1520")
plt.savefig("model_summary.png", dpi=150, bbox_inches="tight", facecolor="#0d1520")
print(f"Saved: model_summary.png")

# ═══════════════════════════════════════════════
# Plot 3: Training vs Validation Gap (Overfitting Check)
# ═══════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(10, 5))
gap = [t - v for t, v in zip(history["train_auc"], history["val_auc"])]
colors = ["tomato" if g > 0.01 else "mediumseagreen" for g in gap]
ax.bar(epochs, gap, color=colors, alpha=0.7, edgecolor="white", linewidth=0.5)
ax.axhline(0, color="white", linewidth=0.5)
ax.axhline(0.01, color="tomato", linestyle="--", alpha=0.4, label="Overfitting threshold (0.01)")
ax.set_title("Train-Val AUC Gap (Overfitting Monitor)", fontsize=13, fontweight="bold")
ax.set_xlabel("Epoch")
ax.set_ylabel("AUC Gap (train - val)")
ax.legend()
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(run_dir / "overfitting_check.png", dpi=150, bbox_inches="tight")
plt.savefig("overfitting_check.png", dpi=150, bbox_inches="tight")
print(f"Saved: overfitting_check.png")

# ═══════════════════════════════════════════════
# Print summary
# ═══════════════════════════════════════════════
print(f"\n{'='*55}")
print(f"  TRAINING RESULTS SUMMARY")
print(f"{'='*55}")
print(f"  Best epoch:      {best_epoch}")
print(f"  Best val AUC:    {best_auc:.4f}")
print(f"  Best val acc:    {history['val_acc'][best_epoch-1]*100:.2f}%")
print(f"  Best val F1:     {history['val_f1'][best_epoch-1]:.4f}")
print(f"  Epochs trained:  {len(history['train_loss'])}")
print(f"  Checkpoint:      weights/best_model.pth")
print(f"  Plots saved to:  {run_dir}/")
print(f"{'='*55}")
print(f"\n  Your model is READY for deployment!")
print(f"  Next: start the API server:")
print(f"    D:\\Newfolder\\anaconda3\\envs\\dfake\\python.exe -m uvicorn backend.main:app --host 0.0.0.0 --port 8000")
