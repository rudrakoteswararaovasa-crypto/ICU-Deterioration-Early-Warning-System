"""
ICU Patient Deterioration Early-Warning System
Main Execution Pipeline & CLI Entry Point
"""

import sys
import argparse
import numpy as np

from data_processor import ICUDataProcessor
from model_engine import ICUTransferLearningPipeline
from evaluator import ICUEvaluator

def run_pipeline(num_patients: int = 100, epochs: int = 30):
    print("=" * 70)
    print("  ICU Patient Deterioration Early-Warning System")
    print("  Transfer Learning from Pretrained Medical Foundation Models")
    print("=" * 70)
    
    # 1. Data Ingestion & Synthetic Cohort Generation
    print("\n[Step 1/5] Generating EHR/ICU Cohort Data...")
    processor = ICUDataProcessor(observation_window_hours=24, prediction_horizon_hours=12)
    df_tel, df_meta = processor.generate_synthetic_icu_cohort(num_patients=num_patients)
    print(f"  - Monitored Patients: {len(df_meta)}")
    print(f"  - Total Telemetry Observations: {len(df_tel)}")

    # 2. Data Cleaning & Temporal Feature Construction
    print("\n[Step 2/5] Cleaning Data & Constructing Temporal Sliding Windows...")
    X, y, feature_names = processor.preprocess_and_extract_features(df_tel, df_meta)
    print(f"  - Feature Matrix Shape: {X.shape}")
    print(f"  - Deterioration Label Rate: {np.mean(y):.2%}")

    # 3. Model Training & Transfer Learning Fine-Tuning
    print("\n[Step 3/5] Loading Pretrained Medical Foundation Encoder & Fine-Tuning...")
    pipeline = ICUTransferLearningPipeline(input_dim=X.shape[1])
    
    print("  - Training Baseline Logistic Regression & Gradient Boosted Trees...")
    pipeline.train_baselines(X, y)

    print(f"  - Executing Staged Fine-Tuning over {epochs} Epochs...")
    losses = pipeline.train_transfer_learning_model(X, y, epochs=epochs, unfreeze_encoder=True)
    print(f"  - Fine-Tuning Complete! Initial Loss: {losses[0]:.4f} -> Final Loss: {losses[-1]:.4f}")

    # 4. Evaluation & Metrics Calculation
    print("\n[Step 4/5] Evaluating Predictive Performance & Calibration...")
    probs_tl = pipeline.predict_risk_proba(X, 'transfer_learning')
    probs_lr = pipeline.predict_risk_proba(X, 'baseline_lr')
    probs_gbdt = pipeline.predict_risk_proba(X, 'baseline_gbdt')

    eval_tl = ICUEvaluator.evaluate_model(y, probs_tl)
    eval_lr = ICUEvaluator.evaluate_model(y, probs_lr)
    eval_gbdt = ICUEvaluator.evaluate_model(y, probs_gbdt)

    print("-" * 65)
    print(f"{'Model Architecture':<35} | {'AUROC':<8} | {'AUPRC':<8} | {'Sensitivity':<11} | {'Brier':<6}")
    print("-" * 65)
    print(f"{'Baseline: Logistic Regression':<35} | {eval_lr['auroc']:<8.4f} | {eval_lr['auprc']:<8.4f} | {eval_lr['sensitivity']:<11.2%} | {eval_lr['brier_score']:<6.4f}")
    print(f"{'Baseline: Gradient Boosted Trees':<35} | {eval_gbdt['auroc']:<8.4f} | {eval_gbdt['auprc']:<8.4f} | {eval_gbdt['sensitivity']:<11.2%} | {eval_gbdt['brier_score']:<6.4f}")
    print(f"{'Proposed: Medical Foundation (Fine-Tuned)':<35} | {eval_tl['auroc']:<8.4f} | {eval_tl['auprc']:<8.4f} | {eval_tl['sensitivity']:<11.2%} | {eval_tl['brier_score']:<6.4f}")
    print("-" * 65)

    # 5. Risk Categorization Summary
    print("\n[Step 5/5] Generating Risk Categorization Breakdown...")
    risk_counts = {'LOW': 0, 'MEDIUM': 0, 'HIGH': 0}
    for prob in probs_tl:
        r_class, _, _ = pipeline.classify_risk_level(prob)
        risk_counts[r_class] += 1

    print(f"  - Low Risk (<20%):    {risk_counts['LOW']} patients")
    print(f"  - Medium Risk (20-50%): {risk_counts['MEDIUM']} patients")
    print(f"  - High Risk Alert (>50%): {risk_counts['HIGH']} patients")
    print("\nSystem ready! Launch web interface with 'python -m http.server 3000' or run app_api.py.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run ICU Deterioration Pipeline")
    parser.add_argument("--patients", type=int, default=100, help="Number of synthetic patients")
    parser.add_argument("--epochs", type=int, default=30, help="Fine-tuning epochs")
    args = parser.parse_args()
    run_pipeline(args.patients, args.epochs)
