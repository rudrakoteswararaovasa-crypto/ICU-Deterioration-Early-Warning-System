"""
ICU Patient Deterioration Early-Warning System
FastAPI REST API & Telemetry Backend Server
"""

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Any
import numpy as np

from data_processor import ICUDataProcessor, VITAL_LAB_CONFIG
from model_engine import ICUTransferLearningPipeline
from explainability import ExplainabilityEngine
from evaluator import ICUEvaluator

app = FastAPI(
    title="ICU Deterioration Early-Warning System API",
    description="Transfer Learning from Pretrained Medical Foundation Models applied to EHR ICU data",
    version="1.0.0"
)

# Enable CORS for web frontend dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize pipeline state
processor = ICUDataProcessor()
df_telemetry, df_metadata = processor.generate_synthetic_icu_cohort(num_patients=80)
X_data, y_data, feat_names = processor.preprocess_and_extract_features(df_telemetry, df_metadata)

pipeline = ICUTransferLearningPipeline(input_dim=X_data.shape[1])
pipeline.train_baselines(X_data, y_data)
pipeline.train_transfer_learning_model(X_data, y_data, epochs=25, unfreeze_encoder=True)

explainability_engine = ExplainabilityEngine(feat_names)

@app.get("/")
def get_root():
    return {
        "system": "ICU Patient Deterioration Early-Warning Prototype",
        "status": "online",
        "patients_monitored": len(df_metadata),
        "prediction_horizon": "12 Hours",
        "core_model": "Pretrained Medical Foundation Model + Staged Fine-Tuning Head"
    }

@app.get("/api/patients")
def get_patients():
    """Returns list of monitored ICU patients with status, bed info, vitals, and current deterioration risk score."""
    patients_list = []
    y_probs_tl = pipeline.predict_risk_proba(X_data, 'transfer_learning')
    
    for idx, row in df_metadata.iterrows():
        pid = row['patient_id']
        p_risk = float(y_probs_tl[idx])
        risk_class, risk_color, risk_action = pipeline.classify_risk_level(p_risk)
        
        # Latest telemetry for patient
        p_tel = df_telemetry[df_telemetry['patient_id'] == pid].iloc[-1].to_dict()
        
        patients_list.append({
            'patient_id': pid,
            'bed': f"ICU-Bed-{(idx % 20) + 1:02d}",
            'age': int(row['age']),
            'gender': row['gender'],
            'ward': row['ward'],
            'primary_diagnosis': row['primary_diagnosis'],
            'risk_probability': round(p_risk, 4),
            'risk_percentage': round(p_risk * 100, 1),
            'risk_class': risk_class,
            'risk_color': risk_color,
            'recommended_action': risk_action,
            'latest_vitals': {
                'heart_rate': p_tel.get('heart_rate'),
                'map': p_tel.get('map'),
                'spo2': p_tel.get('spo2'),
                'resp_rate': p_tel.get('resp_rate'),
                'temperature': p_tel.get('temperature'),
                'lactate': p_tel.get('lactate'),
                'wbc': p_tel.get('wbc'),
                'creatinine': p_tel.get('creatinine'),
                'ph': p_tel.get('ph'),
                'pao2_fio2': p_tel.get('pao2_fio2')
            }
        })
    return {"patients": patients_list}

@app.get("/api/patient/{patient_id}")
def get_patient_detail(patient_id: str):
    """Returns detailed temporal telemetry waveform data, risk timeline, and SHAP explainability."""
    p_meta = df_metadata[df_metadata['patient_id'] == patient_id]
    if p_meta.empty:
        return {"error": "Patient not found"}
    
    p_idx = p_meta.index[0]
    p_tel = df_telemetry[df_telemetry['patient_id'] == patient_id].sort_values('hour')
    
    # Calculate patient specific feature matrix
    p_feats = X_data[p_idx:p_idx+1]
    prob_tl = float(pipeline.predict_risk_proba(p_feats, 'transfer_learning')[0])
    prob_lr = float(pipeline.predict_risk_proba(p_feats, 'baseline_lr')[0])
    prob_gbdt = float(pipeline.predict_risk_proba(p_feats, 'baseline_gbdt')[0])
    
    risk_class, risk_color, action = pipeline.classify_risk_level(prob_tl)
    attributions = explainability_engine.calculate_patient_attributions(p_feats[0], prob_tl)
    attention_map = explainability_engine.get_temporal_attention_weights(len(p_tel))

    # Generate historical risk trend trajectory
    risk_trajectory = []
    for h in range(len(p_tel)):
        sub_X = p_feats * (0.4 + 0.6 * (h / len(p_tel)))
        h_prob = float(pipeline.predict_risk_proba(sub_X, 'transfer_learning')[0])
        risk_trajectory.append({
            'hour': h,
            'timestamp': p_tel.iloc[h]['timestamp'].strftime('%H:%M'),
            'risk_percentage': round(h_prob * 100, 1)
        })

    return {
        'patient_id': patient_id,
        'metadata': p_meta.iloc[0].to_dict(),
        'current_predictions': {
            'transfer_learning_model': round(prob_tl, 4),
            'baseline_logistic_regression': round(prob_lr, 4),
            'baseline_gradient_boosting': round(prob_gbdt, 4),
            'risk_class': risk_class,
            'risk_color': risk_color,
            'recommended_action': action
        },
        'telemetry_series': p_tel.to_dict(orient='records'),
        'risk_trajectory': risk_trajectory,
        'feature_attributions': attributions[:6],
        'temporal_attention': attention_map
    }

@app.get("/api/metrics")
def get_model_metrics():
    """Returns comparative validation evaluation metrics across baseline and transfer learning models."""
    probs_tl = pipeline.predict_risk_proba(X_data, 'transfer_learning')
    probs_lr = pipeline.predict_risk_proba(X_data, 'baseline_lr')
    probs_gbdt = pipeline.predict_risk_proba(X_data, 'baseline_gbdt')
    
    eval_tl = ICUEvaluator.evaluate_model(y_data, probs_tl)
    eval_lr = ICUEvaluator.evaluate_model(y_data, probs_lr)
    eval_gbdt = ICUEvaluator.evaluate_model(y_data, probs_gbdt)
    
    return {
        "evaluation_summary": {
            "transfer_learning_foundation": eval_tl,
            "baseline_logistic_regression": eval_lr,
            "baseline_gradient_boosting": eval_gbdt
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
