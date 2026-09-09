import {
    predictHeartDisease,
    predictDiabetes,
    models
} from "../core/api.js";

const forms = {
    heart: {
        title: "Heart Disease Risk Screening",

        groups: [
            {
                title: "Demographics",
                fields: [
                    {
                        name: "age",
                        label: "Age",
                        type: "number",
                        min: 18,
                        max: 120,
                        default: 55
                    },

                    {
                        name: "sex",
                        label: "Sex",
                        type: "select",
                        default: 1,
                        options: [
                            { label: "Female", value: 0 },
                            { label: "Male", value: 1 }
                        ]
                    }
                ]
            },

            {
                title: "Clinical Measurements",
                fields: [
                    {
                        name: "trestbps",
                        label: "Resting Blood Pressure",
                        type: "number",
                        min: 70,
                        max: 250,
                        default: 140,
                        help: "Measured in mm Hg"
                    },

                    {
                        name: "chol",
                        label: "Serum Cholesterol",
                        type: "number",
                        min: 80,
                        max: 700,
                        default: 240,
                        help: "Measured in mg/dL"
                    },

                    {
                        name: "fbs",
                        label: "Fasting Blood Sugar",
                        type: "select",
                        default: 1,
                        options: [
                            {
                                label: "120 mg/dL or lower",
                                value: 0
                            },
                            {
                                label: "Above 120 mg/dL",
                                value: 1
                            }
                        ]
                    }
                ]
            },

            {
                title: "Cardiac Assessment",
                fields: [
                    {
                        name: "cp",
                        label: "Chest Pain Type",
                        type: "select",
                        default: 3,
                        options: [
                            { label: "Typical angina", value: 1 },
                            { label: "Atypical angina", value: 2 },
                            { label: "Non-anginal pain", value: 3 },
                            { label: "Asymptomatic", value: 4 }
                        ]
                    },

                    {
                        name: "restecg",
                        label: "Resting ECG",
                        type: "select",
                        default: 0,
                        options: [
                            { label: "Normal", value: 0 },
                            { label: "ST-T abnormality", value: 1 },
                            {
                                label: "Left ventricular hypertrophy",
                                value: 2
                            }
                        ]
                    },

                    {
                        name: "thalach",
                        label: "Maximum Heart Rate",
                        type: "number",
                        min: 60,
                        max: 230,
                        default: 150,
                        help: "Highest recorded beats per minute"
                    },

                    {
                        name: "exang",
                        label: "Exercise-Induced Angina",
                        type: "select",
                        default: 1,
                        options: [
                            { label: "No", value: 0 },
                            { label: "Yes", value: 1 }
                        ]
                    },

                    {
                        name: "oldpeak",
                        label: "ST Depression",
                        type: "number",
                        min: 0,
                        max: 10,
                        step: 0.1,
                        default: 2,
                        help: "Exercise relative to rest"
                    },

                    {
                        name: "slope",
                        label: "ST Segment Slope",
                        type: "select",
                        default: 2,
                        options: [
                            { label: "Upsloping", value: 1 },
                            { label: "Flat", value: 2 },
                            { label: "Downsloping", value: 3 }
                        ]
                    },

                    {
                        name: "ca",
                        label: "Major Vessels",
                        type: "select",
                        default: 1,
                        options: [
                            { label: "0", value: 0 },
                            { label: "1", value: 1 },
                            { label: "2", value: 2 },
                            { label: "3", value: 3 }
                        ]
                    },

                    {
                        name: "thal",
                        label: "Thalassemia Indicator",
                        type: "select",
                        default: 7,
                        options: [
                            { label: "Normal", value: 3 },
                            { label: "Fixed defect", value: 6 },
                            { label: "Reversible defect", value: 7 }
                        ]
                    }
                ]
            }
        ]
    },

    diabetes: {
        title: "Diabetes Risk Screening",

        groups: [
            {
                title: "Clinical Indicators",
                fields: [
                    {
                        name: "pregnancies",
                        label: "Pregnancies",
                        type: "number",
                        min: 0,
                        max: 20,
                        default: 1
                    },

                    {
                        name: "glucose",
                        label: "Glucose",
                        type: "number",
                        min: 0,
                        max: 300,
                        default: 120,
                        help: "Plasma glucose concentration"
                    },

                    {
                        name: "blood_pressure",
                        label: "Blood Pressure",
                        type: "number",
                        min: 0,
                        max: 200,
                        default: 70,
                        help: "Diastolic pressure in mm Hg"
                    },

                    {
                        name: "skin_thickness",
                        label: "Skin Thickness",
                        type: "number",
                        min: 0,
                        max: 100,
                        default: 20,
                        help: "Triceps skin fold in mm"
                    },

                    {
                        name: "insulin",
                        label: "Insulin",
                        type: "number",
                        min: 0,
                        max: 900,
                        default: 79,
                        help: "Two-hour serum insulin"
                    },

                    {
                        name: "bmi",
                        label: "BMI",
                        type: "number",
                        min: 0,
                        max: 80,
                        step: 0.1,
                        default: 32
                    },

                    {
                        name: "diabetes_pedigree",
                        label: "Diabetes Pedigree Function",
                        type: "number",
                        min: 0,
                        max: 3,
                        step: 0.001,
                        default: 0.47,
                        help: "Dataset-specific family history score"
                    },

                    {
                        name: "age",
                        label: "Age",
                        type: "number",
                        min: 18,
                        max: 120,
                        default: 33
                    }
                ]
            }
        ]
    }
};


let selected =
    new URLSearchParams(location.search).get("model") === "diabetes"
        ? "diabetes"
        : "heart";


const picker = document.querySelector("#model-buttons");
const form = document.querySelector("#assessment-form");


/* -------------------------------------------------------
   Render a single form field
------------------------------------------------------- */

function renderField(field) {

    if (field.type === "select") {

        const options = field.options
            .map(option => {

                const isSelected =
                    Number(option.value) === Number(field.default);

                return `
                    <option
                        value="${option.value}"
                        ${isSelected ? "selected" : ""}
                    >
                        ${option.label}
                    </option>
                `;
            })
            .join("");

        return `
            <label>
                ${field.label}

                <select
                    name="${field.name}"
                    required
                >
                    ${options}
                </select>
            </label>
        `;
    }


    return `
        <label>
            ${field.label}

            <input
                name="${field.name}"
                type="number"
                min="${field.min}"
                max="${field.max}"
                value="${field.default ?? ""}"
                ${field.step ? `step="${field.step}"` : ""}
                required
            >

            ${field.help
            ? `<small>${field.help}</small>`
            : ""
        }
        </label>
    `;
}


/* -------------------------------------------------------
   Render model picker
------------------------------------------------------- */

function renderPicker() {

    picker.innerHTML = models
        .map(model => {

            const active = model.status === "Active";

            const selectedClass =
                selected === model.key
                    ? "selected"
                    : "";

            return `
                <button
                    class="${selectedClass}"
                    data-model="${active ? model.key : ""}"
                    ${active ? "" : "disabled"}
                    aria-pressed="${selected === model.key}"
                >
                    <span>${model.name}</span>

                    <small>
                        ${active
                    ? `${model.model} · ${model.explainer}`
                    : "Module not available yet"
                }
                    </small>
                </button>
            `;
        })
        .join("");
}


/* -------------------------------------------------------
   Render assessment form
------------------------------------------------------- */

function renderForm() {

    const spec = forms[selected];

    form.innerHTML = `
        <div class="form-heading">

            <div>
                <p class="eyebrow">
                    Selected model
                </p>

                <h2>
                    ${spec.title}
                </h2>
            </div>

            <span class="status">
                Active
            </span>

        </div>

        ${spec.groups
            .map(group => {

                return `
                    <fieldset>

                        <legend>
                            ${group.title}
                        </legend>

                        <div class="field-grid">

                            ${group.fields
                        .map(renderField)
                        .join("")}

                        </div>

                    </fieldset>
                `;
            })
            .join("")}

        <p
            id="form-error"
            class="form-error"
            style="display:none"
        ></p>

        <button
            class="button"
            type="submit"
        >
            Analyze Risk Pattern
        </button>
    `;
}


/* -------------------------------------------------------
   Model selection
------------------------------------------------------- */

picker.addEventListener("click", event => {

    const button =
        event.target.closest("[data-model]");

    if (!button) return;

    const model =
        button.dataset.model;

    if (!model || !forms[model]) {
        return;
    }

    selected = model;

    renderPicker();
    renderForm();
});


/* -------------------------------------------------------
   Collect form data safely
------------------------------------------------------- */

function collectFormData() {

    const formData = new FormData(form);

    const rawData = {};

    for (const [key, value] of formData.entries()) {

        if (value.trim() === "") {
            throw new Error(
                `Please provide a value for ${key}.`
            );
        }

        const numberValue = Number(value);

        if (!Number.isFinite(numberValue)) {
            throw new Error(
                `Invalid value for ${key}.`
            );
        }

        rawData[key] = numberValue;
    }

    return rawData;
}


/* -------------------------------------------------------
   Convert frontend data → backend data
------------------------------------------------------- */

function preparePayload(rawData) {

    if (selected === "diabetes") {

        return {
            Pregnancies: rawData.pregnancies,
            Glucose: rawData.glucose,
            BloodPressure: rawData.blood_pressure,
            SkinThickness: rawData.skin_thickness,
            Insulin: rawData.insulin,
            BMI: rawData.bmi,
            DiabetesPedigreeFunction:
                rawData.diabetes_pedigree,
            Age: rawData.age
        };
    }

    /*
        Heart field names already match
        the FastAPI HeartDiseaseInput model.
    */

    return rawData;
}

form.addEventListener("submit", async event => {

    event.preventDefault();

    const button =
        form.querySelector('button[type="submit"]');

    const error =
        form.querySelector("#form-error");

    error.style.display = "none";

    try {

        const rawData =
            collectFormData();

        const data =
            preparePayload(rawData);

        console.log(
            "GeneCare payload:",
            data
        );

        button.disabled = true;
        button.textContent = "Analyzing…";

        const result =
            selected === "heart"
                ? await predictHeartDisease(data)
                : await predictDiabetes(data);

        console.log(
            "GeneCare prediction:",
            result
        );

        sessionStorage.setItem(
            "genecare-result",
            JSON.stringify({
                ...result,
                screening: selected
            })
        );

        location.href = "results.html";

    } catch (reason) {

        console.error(
            "GeneCare error:",
            reason
        );

        error.textContent =
            reason?.message ||
            "The prediction service is unavailable.";

        error.style.display = "block";

        button.disabled = false;
        button.textContent =
            "Analyze Risk Pattern";
    }
});


/* -------------------------------------------------------
   Initial render
------------------------------------------------------- */

renderPicker();
renderForm();