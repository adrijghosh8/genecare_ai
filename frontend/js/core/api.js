// Change this one value if your FastAPI server uses a different address.
const API_BASE_URL = window.GENECARE_API_BASE_URL || "http://localhost:8000";
async function requestPrediction(model, data) {
    const token = localStorage.getItem("access_token");

    const response = await fetch(
        `${API_BASE_URL}/predict/${model}`,
        {
            method: "POST",

            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${token}`
            },

            body: JSON.stringify(data)
        }
    );

    if (!response.ok) {
        throw new Error(
            "The prediction service could not process this assessment."
        );
    }

    return response.json();
}
export const predictHeartDisease = data => requestPrediction("heart-disease", data);
export const predictDiabetes = data => requestPrediction("diabetes", data);
export const models = [{ key: "heart", name: "Heart Disease", category: "Cardiovascular", status: "Active", model: "Logistic Regression", explainer: "SHAP", dataset: "UCI Cleveland Heart Disease Dataset", summary: "Cardiovascular risk estimation using a machine-learning classification model.", features: "13 clinical inputs" }, { key: "diabetes", name: "Diabetes", category: "Metabolic", status: "Active", model: "XGBoost", explainer: "SHAP", dataset: "Pima Indians Diabetes Database", summary: "Machine-learning screening based on metabolic and clinical risk indicators.", features: "8 clinical inputs" }, { key: "breast-cancer", name: "Breast Cancer", category: "Oncology", status: "In Development", model: "In development", explainer: "Not published", dataset: "Not published", summary: "A future module still undergoing responsible model development.", features: "Not available" }];
