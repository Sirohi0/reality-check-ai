"""
═══════════════════════════════════════════════════════════════════
Deepfake Detection Model Architecture
═══════════════════════════════════════════════════════════════════

EfficientNetV2-B3 (spatial) → Temporal Attention BiLSTM → Classifier

Key design decisions:
1. EfficientNetV2-B3 via timm: better accuracy/FLOPS than B4, pretrained
2. Bidirectional LSTM: captures forward + backward temporal patterns
3. Temporal Self-Attention: learns WHICH frames are most suspicious
4. Dropout at multiple stages: prevents overfitting on Celeb-DF
5. Single LSTM layer: research shows 1 layer is optimal (Springer 2025)

References:
- "1 LSTM layer achieves 90.82% AUC, more layers decrease performance"
  (Video deepfake detection using CNN-LSTM-Transformer, Springer 2025)
- EfficientNet-B4 on Celeb-DF: 95.59% AUC (ResearchGate 2024)
- RLNet (ResNet+LSTM): 95.2% accuracy (Frontiers 2025)
═══════════════════════════════════════════════════════════════════
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import timm


class TemporalAttention(nn.Module):
    """
    Self-attention over the temporal dimension.
    Learns which frames in the sequence are most informative for detection.
    Deepfake artifacts are often inconsistent across frames — this module
    automatically focuses on the frames that reveal manipulation.
    """

    def __init__(self, hidden_dim):
        super().__init__()
        self.attention = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.Tanh(),
            nn.Linear(hidden_dim // 2, 1),
        )

    def forward(self, lstm_output):
        """
        Args:
            lstm_output: (batch, seq_len, hidden_dim)
        Returns:
            context: (batch, hidden_dim) — weighted sum of all timesteps
            weights: (batch, seq_len) — attention weights (for interpretability)
        """
        attn_scores = self.attention(lstm_output).squeeze(-1)   # (B, T)
        attn_weights = F.softmax(attn_scores, dim=1)            # (B, T)
        context = torch.bmm(attn_weights.unsqueeze(1), lstm_output).squeeze(1)  # (B, H)
        return context, attn_weights


class DeepfakeDetector(nn.Module):
    """
    Full deepfake detection model.

    Pipeline per video:
        30 face frames → EfficientNet (per frame) → 1536-d features
        → BiLSTM → Temporal Attention → FC → sigmoid

    Args:
        backbone_name: timm model name (default: tf_efficientnetv2_b3)
        lstm_hidden:   LSTM hidden dimension per direction
        lstm_layers:   number of LSTM layers (1 recommended)
        dropout:       dropout rate
        pretrained:    use ImageNet pretrained backbone
    """

    def __init__(
        self,
        backbone_name="tf_efficientnetv2_b3",
        lstm_hidden=256,
        lstm_layers=1,
        dropout=0.4,
        pretrained=True,
    ):
        super().__init__()

        # ── Spatial Feature Extractor ──
        self.backbone = timm.create_model(
            backbone_name,
            pretrained=pretrained,
            num_classes=0,        # remove classification head
            global_pool="avg",    # global average pooling
        )
        feature_dim = self.backbone.num_features  # e.g., 1536 for efficientnetv2_b3
        print(f"[Model] Backbone: {backbone_name}, feature_dim={feature_dim}")

        # Freeze early layers (first 60% of parameters) for faster convergence
        params = list(self.backbone.parameters())
        freeze_until = int(len(params) * 0.6)
        for i, param in enumerate(params):
            if i < freeze_until:
                param.requires_grad = False
        print(f"[Model] Froze {freeze_until}/{len(params)} backbone params")

        # ── Feature Projection ──
        self.feature_proj = nn.Sequential(
            nn.Linear(feature_dim, 512),
            nn.ReLU(inplace=True),
            nn.Dropout(dropout),
        )

        # ── Temporal Modeling ──
        self.lstm = nn.LSTM(
            input_size=512,
            hidden_size=lstm_hidden,
            num_layers=lstm_layers,
            batch_first=True,
            bidirectional=True,
            dropout=0.0,  # no dropout between LSTM layers (only 1 layer)
        )

        # ── Temporal Attention ──
        self.temporal_attention = TemporalAttention(lstm_hidden * 2)  # *2 for bidirectional

        # ── Classifier Head ──
        self.classifier = nn.Sequential(
            nn.Linear(lstm_hidden * 2, 128),
            nn.ReLU(inplace=True),
            nn.Dropout(dropout),
            nn.Linear(128, 1),
        )

    def extract_frame_features(self, frames):
        """
        Extract spatial features from a batch of frames.
        Args:
            frames: (batch * seq_len, C, H, W)
        Returns:
            features: (batch * seq_len, 512)
        """
        with torch.set_grad_enabled(self.training):
            feats = self.backbone(frames)              # (B*T, feature_dim)
        feats = self.feature_proj(feats)               # (B*T, 512)
        return feats

    def forward(self, x):
        """
        Args:
            x: (batch, seq_len, C, H, W) — sequence of face frames
        Returns:
            logits: (batch, 1) — raw logits (apply sigmoid for probability)
            attn_weights: (batch, seq_len) — which frames were attended to
        """
        B, T, C, H, W = x.shape

        # Reshape for backbone: treat all frames as a batch
        frames = x.reshape(B * T, C, H, W)

        # Extract per-frame features
        features = self.extract_frame_features(frames)   # (B*T, 512)
        features = features.reshape(B, T, 512)            # (B, T, 512)

        # Temporal modeling
        lstm_out, _ = self.lstm(features)                 # (B, T, hidden*2)

        # Temporal attention — learn which frames matter
        context, attn_weights = self.temporal_attention(lstm_out)  # (B, hidden*2)

        # Classification
        logits = self.classifier(context)                 # (B, 1)

        return logits, attn_weights

    def get_trainable_params(self):
        """Count trainable vs total parameters."""
        total = sum(p.numel() for p in self.parameters())
        trainable = sum(p.numel() for p in self.parameters() if p.requires_grad)
        return trainable, total


class FocalLoss(nn.Module):
    """
    Focal Loss for handling class imbalance in Celeb-DF.
    Down-weights easy examples, focuses on hard ones.
    gamma=2 is standard; alpha balances real vs fake.
    """

    def __init__(self, alpha=1.0, gamma=2.0, pos_weight=None):
        super().__init__()
        self.alpha = alpha
        self.gamma = gamma
        self.pos_weight = pos_weight

    def forward(self, logits, targets):
        bce = F.binary_cross_entropy_with_logits(
            logits, targets.float(),
            pos_weight=self.pos_weight,
            reduction="none",
        )
        pt = torch.exp(-bce)
        focal_loss = self.alpha * (1 - pt) ** self.gamma * bce
        return focal_loss.mean()


# ──────────────────────────────────────────────────────
# Quick test
# ──────────────────────────────────────────────────────

if __name__ == "__main__":
    model = DeepfakeDetector(pretrained=False)
    trainable, total = model.get_trainable_params()
    print(f"\nParameters: {trainable:,} trainable / {total:,} total")

    # Dummy input: batch=2, seq_len=30, 3x224x224
    dummy = torch.randn(2, 30, 3, 224, 224)
    logits, attn = model(dummy)
    print(f"Logits shape: {logits.shape}")      # (2, 1)
    print(f"Attention shape: {attn.shape}")      # (2, 30)
    print(f"Attention sum: {attn.sum(dim=1)}")   # should be [1.0, 1.0]
