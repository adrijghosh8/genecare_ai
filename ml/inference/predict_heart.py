import joblib
import pandas as pd

MODEL_PATH = "../models/heart_disease_model.joblib"

model = joblib.load(MODEL_PATH)

def predict_heart_disease(data):
    df = pd.DataFrame([data])

    prediction = model.predict(df)[0]
    probability = model.predict_proba(df)[0][1]

    return {
        "prediction": int(prediction),
        "probability": float(probability)
    }