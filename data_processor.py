"""
ICU Patient Deterioration Early-Warning System
Data Processing & Temporal Feature Extraction Module
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any

# Clinical normal ranges and thresholds for ICU telemetry
VITAL_LAB_CONFIG = {
    'heart_rate': {'min': 40, 'max': 180, 'normal_mean': 75, 'normal_std': 10, 'unit': 'bpm'},
    'map': {'min': 40, 'max': 140, 'normal_mean': 85, 'normal_std': 8, 'unit': 'mmHg'},
    'spo2': {'min': 70, 'max': 100, 'normal_mean': 98, 'normal_std': 1.5, 'unit': '%'},
    'resp_rate': {'min': 8, 'max': 40, 'normal_mean': 16, 'normal_std': 3, 'unit': 'breaths/min'},
    'temperature': {'min': 35.0, 'max': 41.0, 'normal_mean': 37.0, 'normal_std': 0.4, 'unit': '°C'},
    'lactate': {'min': 0.5, 'max': 12.0, 'normal_mean': 1.1, 'normal_std': 0.3, 'unit': 'mmol/L'},
    'wbc': {'min': 1.0, 'max': 35.0, 'normal_mean': 7.5, 'normal_std': 2.0, 'unit': 'x10^3/µL'},
    'creatinine': {'min': 0.4, 'max': 8.0, 'normal_mean': 0.9, 'normal_std': 0.2, 'unit': 'mg/dL'},
    'ph': {'min': 6.9, 'max': 7.6, 'normal_mean': 7.40, 'normal_std': 0.04, 'unit': ''},
    'pao2_fio2': {'min': 100, 'max': 500, 'normal_mean': 420, 'normal_std': 40, 'unit': 'mmHg'},
}

FEATURE_NAMES = list(VITAL_LAB_CONFIG.keys())

class ICUDataProcessor:
    """Handles data acquisition, cleaning, temporal window construction, and normalization."""
    
    def __init__(self, observation_window_hours: int = 24, prediction_horizon_hours: int = 12):
        self.observation_window_hours = observation_window_hours
        self.prediction_horizon_hours = prediction_horizon_hours
        self.feature_means = {}
        self.feature_stds = {}

    def generate_synthetic_icu_cohort(self, num_patients: int = 120, time_steps_per_patient: int = 24) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Generates longitudinal synthetic ICU patient observations and outcomes.
        Produces both raw time-series data and patient static/demographic metadata.
        """
        np.random.seed(42)
        patient_records = []
        patient_metadata = []

        wards = ['Medical ICU', 'Surgical ICU', 'Cardiac Care Unit', 'Neuro ICU']
        diagnoses = ['Sepsis / Septic Shock', 'Acute Respiratory Failure', 'Post-Op Coronary Artery Bypass', 'Traumatic Brain Injury', 'Acute Renal Failure']

        for p_idx in range(1, num_patients + 1):
            patient_id = f"ICU-{p_idx:04d}"
            age = int(np.random.randint(25, 88))
            gender = np.random.choice(['M', 'F'])
            ward = np.random.choice(wards)
            primary_diag = np.random.choice(diagnoses)
            
            # Deterioration trajectory flag (approx 25% true positive rate)
            will_deteriorate = np.random.rand() < 0.25
            deterioration_start_step = np.random.randint(14, 20) if will_deteriorate else 999

            # Baseline initial state
            current_vitals = {k: VITAL_LAB_CONFIG[k]['normal_mean'] for k in FEATURE_NAMES}

            for t in range(time_steps_per_patient):
                timestamp = pd.Timestamp('2026-09-27 00:00') + pd.Timedelta(hours=t)
                
                # If deteriorating, shift vitals into critical ranges progressively
                if t >= deterioration_start_step:
                    severity = (t - deterioration_start_step + 1) * 0.25
                    current_vitals['heart_rate'] += np.random.normal(3.5 * severity, 2.0)
                    current_vitals['map'] -= np.random.normal(2.8 * severity, 1.5)
                    current_vitals['spo2'] -= np.random.normal(1.2 * severity, 0.8)
                    current_vitals['resp_rate'] += np.random.normal(1.1 * severity, 0.6)
                    current_vitals['lactate'] += np.random.normal(0.45 * severity, 0.15)
                    current_vitals['wbc'] += np.random.normal(0.8 * severity, 0.3)
                    current_vitals['creatinine'] += np.random.normal(0.12 * severity, 0.05)
                    current_vitals['ph'] -= np.random.normal(0.02 * severity, 0.008)
                    current_vitals['pao2_fio2'] -= np.random.normal(12.0 * severity, 4.0)
                else:
                    # Random clinical noise around normal baseline
                    for feat in FEATURE_NAMES:
                        current_vitals[feat] += np.random.normal(0, VITAL_LAB_CONFIG[feat]['normal_std'] * 0.15)

                # Clip variables to physiological limits
                for feat in FEATURE_NAMES:
                    current_vitals[feat] = np.clip(
                        current_vitals[feat],
                        VITAL_LAB_CONFIG[feat]['min'],
                        VITAL_LAB_CONFIG[feat]['max']
                    )

                # Simulate occasional missing lab value (e.g. 10% missingness)
                row_data = {
                    'patient_id': patient_id,
                    'hour': t,
                    'timestamp': timestamp,
                }
                for feat in FEATURE_NAMES:
                    if np.random.rand() < 0.08 and 'lactate' in feat:
                        row_data[feat] = np.nan
                    else:
                        row_data[feat] = round(float(current_vitals[feat]), 2)
                
                patient_records.append(row_data)

            patient_metadata.append({
                'patient_id': patient_id,
                'age': age,
                'gender': gender,
                'ward': ward,
                'primary_diagnosis': primary_diag,
                'target_deterioration_12h': 1 if will_deteriorate else 0
            })

        df_telemetry = pd.DataFrame(patient_records)
        df_meta = pd.DataFrame(patient_metadata)
        return df_telemetry, df_meta

    def preprocess_and_extract_features(self, df_telemetry: pd.DataFrame, df_meta: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, List[str]]:
        """
        Cleans data, imputes missing values, extracts summary temporal stats (last, mean, min, max, slope),
        and normalizes features. Returns X matrix, y vector, and feature column names.
        """
        # Forward fill and backward fill missing values per patient
        df_cleaned = df_telemetry.copy()
        for col in FEATURE_NAMES:
            df_cleaned[col] = df_cleaned.groupby('patient_id')[col].transform(lambda s: s.ffill().bfill())

        extracted_rows = []
        y_labels = []

        patient_ids = df_meta['patient_id'].values
        meta_dict = df_meta.set_index('patient_id')['target_deterioration_12h'].to_dict()

        for pid in patient_ids:
            p_data = df_cleaned[df_cleaned['patient_id'] == pid].sort_values('hour')
            if p_data.empty:
                continue

            row_features = []
            feature_header = []

            for feat in FEATURE_NAMES:
                vals = p_data[feat].values
                val_last = vals[-1]
                val_mean = np.mean(vals)
                val_min = np.min(vals)
                val_max = np.max(vals)
                val_slope = (vals[-1] - vals[0]) / max(len(vals) - 1, 1)

                row_features.extend([val_last, val_mean, val_min, val_max, val_slope])
                
                if len(extracted_rows) == 0:
                    feature_header.extend([
                        f"{feat}_last", f"{feat}_mean", f"{feat}_min", f"{feat}_max", f"{feat}_slope"
                    ])

            extracted_rows.append(row_features)
            y_labels.append(meta_dict.get(pid, 0))

        X = np.array(extracted_rows, dtype=np.float32)
        y = np.array(y_labels, dtype=np.int64)

        # Standard scaling across feature dimensions
        if len(self.feature_means) == 0:
            self.feature_means = np.mean(X, axis=0)
            self.feature_stds = np.std(X, axis=0) + 1e-6

        X_scaled = (X - self.feature_means) / self.feature_stds
        return X_scaled, y, feature_header

if __name__ == "__main__":
    processor = ICUDataProcessor()
    df_tel, df_meta = processor.generate_synthetic_icu_cohort(num_patients=20)
    X, y, feats = processor.preprocess_and_extract_features(df_tel, df_meta)
    print(f"Generated dataset for {len(df_meta)} ICU patients.")
    print(f"Feature matrix shape: {X.shape}, Target positive rate: {np.mean(y):.2%}")
