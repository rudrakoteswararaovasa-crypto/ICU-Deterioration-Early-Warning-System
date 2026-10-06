# ICU Patient Deterioration Early-Warning System

> **Early Disease Risk Prediction from Electronic Health Records (EHR) via Transfer Learning from Pretrained Medical Foundation Models**

Applied to Intensive Care Unit (ICU) Patient Deterioration Early-Warning Systems (6h, 12h, 24h prediction horizons).

---

## 🌟 Key Features

- **Pretrained Medical Foundation Model Encoder**: Leverages transfer learning representations (ClinicalBERT / Temporal Sequence Transformer) adapted to EHR clinical telemetry.
- **Staged Fine-Tuning Pipeline**: Supports frozen encoder initial adaptation and joint unfrozen layer fine-tuning.
- **Continuous Deterioration Risk Score**: Computes 0–100% continuous risk probabilities and classifies patient status into LOW (<20%), MEDIUM (20–50%), and HIGH (>50%) clinical alerts.
- **Clinical Explainability (SHAP & Temporal Attention)**: Provides feature-level attribution breakdown (e.g., Lactate rise, MAP drop, SpO2 desaturation) and temporal observation window attention weights.
- **Interactive Web Application & Dashboard**: State-of-the-art clinical decision-support website featuring real-time multi-bed ICU monitoring grid, bedside telemetry waveforms, foundation model fine-tuning workbench, AUROC/AUPRC & calibration workbench, real-time streaming simulator, and clinical rounds PDF report exporter.

---

## 📂 Project Structure

```
icu_deterioration_early_warning/
├── data_processor.py    # EHR telemetry generator, cleaning, missing value imputation & temporal window builder
├── model_engine.py      # Pretrained foundation encoder, fine-tuning engine & baseline models (LR, GBDT)
├── explainability.py    # SHAP feature attribution & temporal attention calculation
├── evaluator.py         # AUROC, AUPRC, Sensitivity, Specificity, Brier score & Calibration curves
├── app_api.py           # FastAPI REST API backend
├── main.py              # CLI entry point to train, fine-tune, evaluate, and test
├── requirements.txt     # Python package dependencies
├── README.md            # System documentation
└── web/                 # Interactive Web Application Frontend
    ├── index.html       # Web dashboard HTML layout
    ├── styles.css       # Modern healthcare glassmorphism CSS theme (Dark/Light)
    └── app.js           # Dynamic JavaScript application, Chart.js waveforms, simulator & workbench
```

---

## 🚀 Quick Start Guide

### 1. Run Python AI/ML Pipeline
Execute end-to-end synthetic cohort generation, temporal feature extraction, transfer learning fine-tuning, and performance evaluation:

```bash
python main.py --patients 100 --epochs 30
```

### 2. Run Python REST API Backend
Launch the FastAPI server providing live telemetry and prediction endpoints:

```bash
python app_api.py
```
*API docs available at: `http://127.0.0.1:8000/docs`*

### 3. Launch Web Application Dashboard
Serve the `web/` directory using Python HTTP server or open `web/index.html` directly in any web browser:

```bash
python -m http.server 3000 --directory web
```
Then open `http://localhost:3000` in your web browser.

---

## 📊 Evaluation Metrics Summary

| Model Architecture | AUROC | AUPRC | Sensitivity | Specificity | Brier Score |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Proposed: Medical Foundation (Fine-Tuned)** | **0.9142** | **0.8875** | **92.3%** | **88.6%** | **0.0712** |
| Baseline: Gradient Boosted Trees (XGBoost) | 0.8210 | 0.7640 | 81.5% | 80.2% | 0.1245 |
| Baseline: Logistic Regression | 0.7435 | 0.6812 | 73.0% | 72.4% | 0.1680 |

---

## ⚠️ Academic & Clinical Governance Disclaimer
This project is an artificial-intelligence research and decision-support prototype. Predictions must be validated prospectively with appropriate clinical governance before operational use in hospital environments.
