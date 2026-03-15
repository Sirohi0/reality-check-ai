

import sys
import time
from pathlib import Path

import numpy as np
import torch
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.metrics import (
    roc_auc_score, accuracy_score, f1_score,
    confusion_matrix, classification_report, roc_curve
)
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config
from training.model import DeepfakeDetector
from training.dataset import DeepfakeVideoDataset, get_val_transforms


def load_model():
    checkpoint_path = config.MODEL_CHECKPOINT
    if not checkpoint_path.exists():
        print(f"No checkpoint found at {checkpoint_path}")
        sys.exit(1)

    checkpoint = torch.load(checkpoint_path, map_location=config.DEVICE, weights_only=False)
    ckpt_config = checkpoint.get("config", {})

    model = DeepfakeDetector(
        backbone_name=ckpt_config.get("backbone", config.BACKBONE),
        pretrained=False,
    )
    model.load_state_dict(checkpoint["model_state_dict"])
    model.to(config.DEVICE)
    model.eval()

    epoch = checkpoint.get("epoch", "?")
    val_auc = checkpoint.get("val_auc", "?")
    print(f"Loaded checkpoint: epoch={epoch}, val_auc={val_auc}")
    return model


def evaluate():
    print("=" * 60)
    print("  CELEB-DF TEST SET EVALUATION")
    print("=" * 60)
    print(f"  Device: {config.DEVICE}")

    # Load model
    model = load_model()

    # Load test dataset
    test_dir = config.PROCESSED_DIR / "test"
    if not test_dir.exists():
        print(f"Test directory not found: {test_dir}")
        sys.exit(1)

    dataset = DeepfakeVideoDataset(
        root_dir=test_dir,
        seq_len=config.SEQUENCE_LENGTH,
        transform=get_val_transforms(config.FACE_IMAGE_SIZE),
    )

    if len(dataset) == 0:
        print("No test videos found!")
        sys.exit(1)

    # Run inference on every test video
    all_preds = []
    all_labels = []
    all_ids = []
    misclassified = []

    print(f"\nRunning inference on {len(dataset)} test videos...\n")
    start_time = time.time()

    with torch.no_grad():
        for i in tqdm(range(len(dataset)), desc="Evaluating"):
            frames, label, video_id = dataset[i]
            frames = frames.unsqueeze(0).to(config.DEVICE)

            logits, attn_weights = model(frames)
            prob = torch.sigmoid(logits).item()
            pred_label = 1 if prob > 0.5 else 0

            all_preds.append(prob)
            all_labels.append(label)
            all_ids.append(video_id)

            if pred_label != label:
                true_str = "FAKE" if label == 1 else "REAL"
                pred_str = "FAKE" if pred_label == 1 else "REAL"
                misclassified.append({
                    "video": video_id,
                    "true": true_str,
                    "predicted": pred_str,
                    "fake_prob": round(prob * 100, 2),
                })

    elapsed = time.time() - start_time
    all_preds = np.array(all_preds)
    all_labels = np.array(all_labels)

    # Compute metrics
    auc = roc_auc_score(all_labels, all_preds)
    acc = accuracy_score(all_labels, (all_preds > 0.5).astype(int))
    f1 = f1_score(all_labels, (all_preds > 0.5).astype(int))
    cm = confusion_matrix(all_labels, (all_preds > 0.5).astype(int))

    tn, fp, fn, tp = cm.ravel()

    print(f"\n{'=' * 60}")
    print(f"  TEST SET RESULTS")
    print(f"{'=' * 60}")
    print(f"  Total videos:    {len(dataset)}")
    print(f"  Real videos:     {sum(1 for l in all_labels if l == 0)}")
    print(f"  Fake videos:     {sum(1 for l in all_labels if l == 1)}")
    print(f"  Time:            {elapsed:.1f}s ({elapsed/len(dataset):.2f}s per video)")
    print(f"{'─' * 60}")
    print(f"  AUC-ROC:         {auc:.4f}")
    print(f"  Accuracy:        {acc:.4f} ({acc*100:.2f}%)")
    print(f"  F1 Score:        {f1:.4f}")
    print(f"{'─' * 60}")
    print(f"  True Positives:  {tp} (fakes correctly detected)")
    print(f"  True Negatives:  {tn} (reals correctly identified)")
    print(f"  False Positives: {fp} (reals wrongly called fake)")
    print(f"  False Negatives: {fn} (fakes missed)")
    print(f"{'─' * 60}")
    print(f"  Misclassified:   {len(misclassified)} / {len(dataset)} videos")
    print(f"{'=' * 60}")

    # Print classification report
    print(f"\n  Classification Report:")
    print(classification_report(
        all_labels, (all_preds > 0.5).astype(int),
        target_names=["Real", "Fake"],
        digits=4,
    ))

    # Print misclassified videos
    if misclassified:
        print(f"\n{'=' * 60}")
        print(f"  MISCLASSIFIED VIDEOS ({len(misclassified)} total)")
        print(f"{'=' * 60}")
        print(f"  {'Video':<30} {'True':<8} {'Predicted':<10} {'Fake %'}")
        print(f"  {'─'*65}")
        for m in sorted(misclassified, key=lambda x: x["fake_prob"], reverse=True):
            print(f"  {m['video']:<30} {m['true']:<8} {m['predicted']:<10} {m['fake_prob']}%")
    else:
        print("\n  No misclassifications! Perfect test score.")

    # ── Plot 1: ROC Curve ──
    fpr, tpr, thresholds = roc_curve(all_labels, all_preds)
    plt.figure(figsize=(8, 6))
    plt.plot(fpr, tpr, "dodgerblue", linewidth=2.5, label=f"Test AUC = {auc:.4f}")
    plt.plot([0, 1], [0, 1], "k--", alpha=0.3)
    plt.fill_between(fpr, tpr, alpha=0.1, color="dodgerblue")
    plt.xlabel("False Positive Rate", fontsize=12)
    plt.ylabel("True Positive Rate", fontsize=12)
    plt.title(f"ROC Curve - Celeb-DF Test Set ({len(dataset)} videos)", fontsize=14, fontweight="bold")
    plt.legend(fontsize=12)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig("test_roc_curve.png", dpi=150)
    print(f"\nSaved: test_roc_curve.png")

    # ── Plot 2: Confusion Matrix ──
    fig, ax = plt.subplots(figsize=(7, 6))
    im = ax.imshow(cm, cmap="Blues")
    ax.set_xticks([0, 1])
    ax.set_yticks([0, 1])
    ax.set_xticklabels(["Real", "Fake"], fontsize=12)
    ax.set_yticklabels(["Real", "Fake"], fontsize=12)
    ax.set_xlabel("Predicted", fontsize=13)
    ax.set_ylabel("Actual", fontsize=13)
    ax.set_title(f"Test Confusion Matrix (Acc: {acc*100:.1f}%)", fontsize=14, fontweight="bold")
    for i in range(2):
        for j in range(2):
            color = "white" if cm[i, j] > cm.max() / 2 else "black"
            ax.text(j, i, str(cm[i, j]), ha="center", va="center",
                    fontsize=24, fontweight="bold", color=color)
    plt.colorbar(im)
    plt.tight_layout()
    plt.savefig("test_confusion_matrix.png", dpi=150)
    print(f"Saved: test_confusion_matrix.png")

    # ── Plot 3: Score Distribution ──
    fig, ax = plt.subplots(figsize=(10, 5))
    real_scores = all_preds[all_labels == 0] * 100
    fake_scores = all_preds[all_labels == 1] * 100
    ax.hist(real_scores, bins=40, alpha=0.6, color="mediumseagreen", label=f"Real ({len(real_scores)})", edgecolor="white")
    ax.hist(fake_scores, bins=40, alpha=0.6, color="tomato", label=f"Fake ({len(fake_scores)})", edgecolor="white")
    ax.axvline(50, color="black", linestyle="--", linewidth=1.5, label="Decision threshold (50%)")
    ax.set_xlabel("Fake Probability (%)", fontsize=12)
    ax.set_ylabel("Number of Videos", fontsize=12)
    ax.set_title("Score Distribution - Real vs Fake", fontsize=14, fontweight="bold")
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig("test_score_distribution.png", dpi=150)
    print(f"Saved: test_score_distribution.png")

    # ── Plot 4: Confidence of Misclassified ──
    if misclassified:
        fig, ax = plt.subplots(figsize=(10, max(4, len(misclassified) * 0.35)))
        names = [m["video"][:25] for m in misclassified]
        probs = [m["fake_prob"] for m in misclassified]
        colors = ["tomato" if m["true"] == "FAKE" else "mediumseagreen" for m in misclassified]
        y_pos = range(len(names))
        ax.barh(y_pos, probs, color=colors, edgecolor="white", height=0.7)
        ax.set_yticks(y_pos)
        ax.set_yticklabels(names, fontsize=9)
        ax.set_xlabel("Fake Probability (%)", fontsize=12)
        ax.set_title(f"Misclassified Videos ({len(misclassified)} total)", fontsize=14, fontweight="bold")
        ax.axvline(50, color="black", linestyle="--", linewidth=1.5)
        ax.legend(["Threshold", "Missed Fake", "False Alarm"],
                  loc="lower right", fontsize=10)
        ax.grid(True, alpha=0.3, axis="x")
        plt.tight_layout()
        plt.savefig("test_misclassified.png", dpi=150)
        print(f"Saved: test_misclassified.png")

    print(f"\nDone! All plots saved in: {Path('.').resolve()}")


if __name__ == "__main__":
    evaluate()
