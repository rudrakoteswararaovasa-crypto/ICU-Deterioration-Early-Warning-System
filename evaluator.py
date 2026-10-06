"""
ICU Patient Deterioration Early-Warning System
Evaluation Metrics & Calibration Workbench
"""

import numpy as np
from sklearn.metrics import (
    roc_auc_score,
    precision_recall_curve,
    auc,
    roc_curve,
    confusion_matrix,
    f1_score,
    brier_score_loss,
)
from typing import Dict, Any, Tuple

class ICUEvaluator:
    """Computes comprehensive clinical validation metrics and calibration statistics."""

    @staticmethod
    def evaluate_model(y_true: np.ndarray, y_probs: np.ndarray, threshold: float = 0.35) -> Dict[str, Any]:
        """Calculates AUROC, AUPRC, Sensitivity, Specificity, F1, Brier Score, and Confusion Matrix."""
        y_pred = (y_probs >= threshold).astype(int)

        # AUROC
        try:
            auroc = float(roc_auc_score(y_true, y_probs))
        except Exception:
            auroc = 0.5

        # ROC Curve points
        fpr, tpr, roc_thresholds = roc_curve(y_true, y_probs)
        roc_points = [{'fpr': round(float(f), 4), 'tpr': round(float(t), 4)} for f, t in zip(fpr[::2], tpr[::2])]

        # AUPRC
        precision_pts, recall_pts, _ = precision_recall_curve(y_true, y_probs)
        auprc = float(auc(recall_pts, precision_pts))
        pr_points = [{'recall': round(float(r), 4), 'precision': round(float(p), 4)} for r, p in zip(recall_pts[::2], precision_pts[::2])]

        # Confusion Matrix components
        tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
        sensitivity = float(tp / (tp + fn)) if (tp + fn) > 0 else 0.0
        specificity = float(tn / (tn + fp)) if (tn + fp) > 0 else 0.0
        ppv = float(tp / (tp + fp)) if (tp + fp) > 0 else 0.0  # Positive Predictive Value / Precision
        npv = float(tn / (tn + fn)) if (tn + fn) > 0 else 0.0  # Negative Predictive Value
        f1 = float(f1_score(y_true, y_pred)) if (tp + fp + fn) > 0 else 0.0
        brier = float(brier_score_loss(y_true, y_probs))

        # Reliability Calibration Curve (10 bins)
        bin_edges = np.linspace(0.0, 1.0, 11)
        calibration_bins = []

        for i in range(len(bin_edges) - 1):
            mask = (y_probs >= bin_edges[i]) & (y_probs < bin_edges[i + 1])
            if np.sum(mask) > 0:
                mean_pred = float(np.mean(y_probs[mask]))
                actual_freq = float(np.mean(y_true[mask]))
                count = int(np.sum(mask))
            else:
                mean_pred = float((bin_edges[i] + bin_edges[i + 1]) / 2)
                actual_freq = 0.0
                count = 0

            calibration_bins.append({
                'bin': f"{int(bin_edges[i]*100)}-{int(bin_edges[i+1]*100)}%",
                'mean_predicted': round(mean_pred, 4),
                'actual_observed': round(actual_freq, 4),
                'count': count
            })

        return {
            'auroc': round(auroc, 4),
            'auprc': round(auprc, 4),
            'sensitivity': round(sensitivity, 4),
            'specificity': round(specificity, 4),
            'ppv': round(ppv, 4),
            'npv': round(npv, 4),
            'f1_score': round(f1, 4),
            'brier_score': round(brier, 4),
            'confusion_matrix': {'tp': int(tp), 'fp': int(fp), 'tn': int(tn), 'fn': int(fn)},
            'roc_curve': roc_points[:25],
            'pr_curve': pr_points[:25],
            'calibration_curve': calibration_bins
        }

if __name__ == "__main__":
    y_t = np.array([0, 0, 0, 0, 1, 1, 0, 1, 1, 0])
    y_p = np.array([0.1, 0.2, 0.15, 0.4, 0.85, 0.9, 0.3, 0.75, 0.6, 0.2])
    metrics = ICUEvaluator.evaluate_model(y_t, y_p)
    print("Clinical Evaluation Summary:")
    print(f"  AUROC: {metrics['auroc']}, AUPRC: {metrics['auprc']}, Brier: {metrics['brier_score']}")
    print(f"  Sensitivity: {metrics['sensitivity']:.2%}, Specificity: {metrics['specificity']:.2%}")
