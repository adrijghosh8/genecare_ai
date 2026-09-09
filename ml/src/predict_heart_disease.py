import joblib
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR.parent / "models" / "heart_disease_model.joblib"

artifact = joblib.load(MODEL_PATH)

model = artifact["model"]
threshold = artifact["threshold"]

def predict_heart_disease(data):
    df = pd.DataFrame([data])

    probability = model.predict_proba(df)[0][1]

    prediction = int(probability >= threshold)

    return {
        "prediction": prediction,
        "probability": round(float(probability),4),
        "threshold": float(threshold),
        "model": artifact["model_name"],
        "model_version": artifact["model_version"]
    }