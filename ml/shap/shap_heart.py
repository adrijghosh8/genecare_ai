from pathlib import Path

import joblib
import pandas as pd
import shap


BASE_DIR = Path(__file__).resolve().parent

MODEL_PATH = BASE_DIR.parent / "models" / "heart_disease_model.joblib"


artifact = joblib.load(MODEL_PATH)

model = artifact["model"]

preprocessor = model.named_steps["preprocessor"]
classifier = model.named_steps["classifier"]

shap_background = (
    artifact["shap_background"]
)

shap_background_transformed = (
    preprocessor.transform(
        shap_background
    )
)

explainer = shap.LinearExplainer(
    classifier,
    shap_background_transformed
)



NUMERIC_FEATURES = {
    "age": "Age",
    "trestbps": "Resting blood pressure",
    "chol": "Cholesterol",
    "thalach": "Maximum heart rate",
    "oldpeak": "ST depression"
}


CATEGORICAL_FEATURES = {
    "sex": {
        0: "Female",
        1: "Male"
    },

    "cp": {
        1: "Typical angina",
        2: "Atypical angina",
        3: "Non-anginal pain",
        4: "Asymptomatic"
    },

    "fbs": {
        0: "120 mg/dL or lower",
        1: "Above 120 mg/dL"
    },

    "restecg": {
        0: "Normal",
        1: "ST-T abnormality",
        2: "Left ventricular hypertrophy"
    },

    "exang": {
        0: "No",
        1: "Yes"
    },

    "slope": {
        1: "Upsloping",
        2: "Flat",
        3: "Downsloping"
    },

    "ca": {
        0: "0",
        1: "1",
        2: "2",
        3: "3"
    },

    "thal": {
        3: "Normal",
        6: "Fixed defect",
        7: "Reversible defect"
    }
}


def get_base_feature(feature_name):

    feature_name = feature_name.replace(
        "num__",
        ""
    )

    feature_name = feature_name.replace(
        "cat__",
        ""
    )

    if feature_name in NUMERIC_FEATURES:
        return feature_name

    for feature in CATEGORICAL_FEATURES:

        if feature_name.startswith(
            feature + "_"
        ):
            return feature

    return feature_name


def format_feature_name(
    feature,
    patient_value
):
    """
    Create a human-readable feature name
    using the patient's actual value.
    """

    if feature in NUMERIC_FEATURES:
        return NUMERIC_FEATURES[feature]

    if feature in CATEGORICAL_FEATURES:

        value = int(float(patient_value))

        label = CATEGORICAL_FEATURES[
            feature
        ].get(
            value,
            str(value)
        )

        labels = {
            "sex": "Sex",
            "cp": "Chest pain",
            "fbs": "Fasting blood sugar",
            "restecg": "Resting ECG",
            "exang": "Exercise-induced angina",
            "slope": "ST segment slope",
            "ca": "Major vessels",
            "thal": "Thalassemia"
        }

        return f"{labels[feature]}: {label}"

    return feature

def explain_prediction(
    patient_data,
    top_n=5
):

    patient_df = pd.DataFrame(
        [patient_data]
    )

    patient_transformed = (
        preprocessor.transform(patient_df)
    )

    shap_values = explainer.shap_values(
        patient_transformed
    )[0]

    feature_names = (
        preprocessor
        .get_feature_names_out()
    )

    raw_explanation = pd.DataFrame({
        "transformed_feature": feature_names,
        "contribution": shap_values
    })


    raw_explanation["base_feature"] = (
        raw_explanation[
            "transformed_feature"
        ]
        .apply(get_base_feature)
    )

    grouped = (
        raw_explanation
        .groupby(
            "base_feature",
            as_index=False
        )["contribution"]
        .sum()
    )

    grouped["abs_contribution"] = (
        grouped["contribution"].abs()
    )

    explanation = []

    for _, row in grouped.iterrows():

        feature = row["base_feature"]

        contribution = float(
            row["contribution"]
        )

        patient_value = patient_data.get(
            feature
        )

        label = format_feature_name(
            feature,
            patient_value
        )

        direction = (
            "toward_disease"
            if contribution > 0
            else "toward_no_disease"
        )

        explanation.append({
            "feature": label,
            "contribution": round(
                contribution,
                2
            ),
            "direction": direction
        })

    return explanation