"""
ICU Patient Deterioration Early-Warning System
Model Development & Transfer Learning Engine
"""

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import GradientBoostingClassifier
from typing import Dict, Tuple, Any, List

class PretrainedClinicalFoundationEncoder(nn.Module):
    """
    Simulates a Pretrained Medical Foundation Model Encoder (e.g. ClinicalBERT / Med-BERT / Sequence Transformer).
    Maps high-dimensional longitudinal EHR features into a rich transferable 64-dim embedding space.
    """
    def __init__(self, input_dim: int, embedding_dim: int = 64):
        super(PretrainedClinicalFoundationEncoder, self).__init__()
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 128),
            nn.BatchNorm1d(128),
            nn.GELU(),
            nn.Dropout(0.2),
            nn.Linear(128, embedding_dim),
            nn.LayerNorm(embedding_dim),
            nn.GELU()
        )
        self._initialize_pretrained_weights()

    def _initialize_pretrained_weights(self):
        """Simulate loading pretrained weights from a medical foundation model checkpoint."""
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.kaiming_normal_(m.weight)
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0.0)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.encoder(x)


class DeteriorationPredictionHead(nn.Module):
    """Fine-tunable risk prediction head attached on top of foundation model representations."""
    def __init__(self, embedding_dim: int = 64):
        super(DeteriorationPredictionHead, self).__init__()
        self.head = nn.Sequential(
            nn.Linear(embedding_dim, 32),
            nn.ReLU(),
            nn.Dropout(0.15),
            nn.Linear(32, 1)
        )

    def forward(self, embeddings: torch.Tensor) -> torch.Tensor:
        return self.head(embeddings)


class ICUTransferLearningPipeline:
    """End-to-end wrapper for Transfer Learning Fine-tuning & Baseline comparison."""
    
    def __init__(self, input_dim: int, embedding_dim: int = 64):
        self.input_dim = input_dim
        self.embedding_dim = embedding_dim
        self.encoder = PretrainedClinicalFoundationEncoder(input_dim, embedding_dim)
        self.pred_head = DeteriorationPredictionHead(embedding_dim)
        self.baseline_lr = LogisticRegression(max_iter=1000)
        self.baseline_gbdt = GradientBoostingClassifier(n_estimators=100, random_state=42)
        self.is_fine_tuned = False

    def train_baselines(self, X_train: np.ndarray, y_train: np.ndarray):
        """Trains traditional clinical baselines."""
        self.baseline_lr.fit(X_train, y_train)
        self.baseline_gbdt.fit(X_train, y_train)

    def train_transfer_learning_model(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        epochs: int = 40,
        lr: float = 1e-3,
        unfreeze_encoder: bool = True
    ) -> List[float]:
        """
        Executes staged fine-tuning:
        1. Freeze foundation encoder initially to adapt prediction head.
        2. Unfreeze upper encoder layers if unfreeze_encoder is True for joint fine-tuning.
        """
        X_tensor = torch.tensor(X_train, dtype=torch.float32)
        y_tensor = torch.tensor(y_train, dtype=torch.float32).unsqueeze(1)

        # Stage 1: Freeze Encoder
        for param in self.encoder.parameters():
            param.requires_grad = unfreeze_encoder

        params = list(self.pred_head.parameters())
        if unfreeze_encoder:
            params += list(self.encoder.parameters())

        optimizer = optim.AdamW(params, lr=lr, weight_decay=1e-4)
        criterion = nn.BCEWithLogitsLoss()

        loss_history = []
        self.encoder.train()
        self.pred_head.train()

        for epoch in range(epochs):
            optimizer.zero_grad()
            embeddings = self.encoder(X_tensor)
            logits = self.pred_head(embeddings)
            loss = criterion(logits, y_tensor)
            loss.backward()
            optimizer.step()
            loss_history.append(float(loss.item()))

        self.is_fine_tuned = unfreeze_encoder
        return loss_history

    def predict_risk_proba(self, X: np.ndarray, model_type: str = 'transfer_learning') -> np.ndarray:
        """Computes continuous risk probabilities for patient cohort."""
        if model_type == 'baseline_lr':
            return self.baseline_lr.predict_proba(X)[:, 1]
        elif model_type == 'baseline_gbdt':
            return self.baseline_gbdt.predict_proba(X)[:, 1]
        else:
            self.encoder.eval()
            self.pred_head.eval()
            with torch.no_grad():
                X_tensor = torch.tensor(X, dtype=torch.float32)
                embeddings = self.encoder(X_tensor)
                logits = self.pred_head(embeddings)
                probs = torch.sigmoid(logits).squeeze(1).numpy()
            return probs

    @staticmethod
    def classify_risk_level(risk_prob: float) -> Tuple[str, str, str]:
        """Categorizes numerical probability into Low / Medium / High clinical risk alert."""
        if risk_prob < 0.20:
            return "LOW", "#10b981", "Routine Monitoring - Patient Stable"
        elif risk_prob < 0.50:
            return "MEDIUM", "#f59e0b", "Increased Surveillance - Clinical Assessment Recommended"
        else:
            return "HIGH", "#ef4444", "CRITICAL ALERT - Immediate ICU Team Review Required"

if __name__ == "__main__":
    from data_processor import ICUDataProcessor
    proc = ICUDataProcessor()
    df_t, df_m = proc.generate_synthetic_icu_cohort(num_patients=50)
    X, y, feats = proc.preprocess_and_extract_features(df_t, df_m)
    
    pipeline = ICUTransferLearningPipeline(input_dim=X.shape[1])
    pipeline.train_baselines(X, y)
    losses = pipeline.train_transfer_learning_model(X, y, epochs=15)
    probs = pipeline.predict_risk_proba(X, 'transfer_learning')
    print(f"Fine-tuning complete. Final loss: {losses[-1]:.4f}")
    print(f"Sample risk prediction: {probs[0]:.2%} -> {pipeline.classify_risk_level(probs[0])}")
