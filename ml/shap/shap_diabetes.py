from pathlib import Path

import joblib
import pandas as pd
import shap


BASE_DIR = Path(__file__).resolve().parent

MODEL_PATH = (
    BASE_DIR.parent
    / "models"
    / "diabetes_model.joblib"
)


artifact = joblib.load(MODEL_PATH)

model = artifact["model"]

preprocessor = model.named_steps["preprocessor"]
classifier = model.named_steps["classifier"]


explainer = shap.TreeExplainer(
    classifier
)



FEATURE_NAMES = {
    "Pregnancies": "Pregnancies",
    "Glucose": "Glucose",
    "BloodPressure": "Blood pressure",
    "SkinThickness": "Skin thickness",
    "Insulin": "Insulin",
    "BMI": "BMI",
    "DiabetesPedigreeFunction":
        "Diabetes pedigree function",
    "Age": "Age"
}

def get_shap_values(patient_transformed):

    values = explainer.shap_values(
        patient_transformed
    )

    if isinstance(values, list):
        values = values[1]

    return values[0]



def explain_diabetes_prediction(
    data,
    top_n=5
):

    patient_df = pd.DataFrame(
        [data]
    )

    patient_transformed = (
        preprocessor.transform(
            patient_df
        )
    )

    shap_values = get_shap_values(
        patient_transformed
    )

    feature_names = (
        preprocessor
        .get_feature_names_out()
    )

    explanation = pd.DataFrame({
        "feature": feature_names,
        "contribution": shap_values
    })

    explanation["feature"] = (
        explanation["feature"]
        .str.replace(
            "num__",
            "",
            regex=False
        )
        .str.replace(
            "cat__",
            "",
            regex=False
        )
    )

    explanation["abs_contribution"] = (
        explanation["contribution"]
        .abs()
    )

    explanation = (
        explanation
        .sort_values(
            "abs_contribution",
            ascending=False
        )
        .head(top_n)
    )


    explanation["direction"] = (
        explanation["contribution"]
        .apply(
            lambda value:
                "toward_diabetes"
                if value > 0
                else "toward_no_diabetes"
        )
    )


    explanation["contribution"] = (
        explanation["contribution"]
        .round(2)
    )

    return explanation[
        [
            "feature",
            "contribution",
            "direction"
        ]
    ].to_dict(
        orient="records"
    )