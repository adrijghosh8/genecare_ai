import { models } from "../core/api.js";

const resultsArea = document.querySelector("#results-content");

let result = null;


// ============================================================
// LOAD RESULT
// ============================================================

async function loadResult() {

    // Check if this page was opened from Prediction History
    const params = new URLSearchParams(window.location.search);
    const predictionId = params.get("prediction");

    // --------------------------------------------------------
    // OLD RESULT FROM HISTORY
    // --------------------------------------------------------

    if (predictionId) {

        const token = localStorage.getItem("access_token");

        if (!token) {
            window.location.href = "login.html";
            return;
        }

        try {

            const response = await fetch(
                `https://genecare-ai.onrender.com/history/${predictionId}`,
                {
                    method: "GET",
                    headers: {
                        "Authorization": `Bearer ${token}`
                    }
                }
            );

            if (!response.ok) {

                const data = await response.json();

                throw new Error(
                    data.detail ||
                    "Could not load this assessment."
                );
            }

            const historyResult = await response.json();

            // Convert database result into the structure
            // expected by the existing results page.

            result = {
                id: historyResult.id,

                screening:
                    historyResult.disease === "Diabetes"
                        ? "diabetes"
                        : "heart",

                disease: historyResult.disease,

                prediction:
                    historyResult.prediction,

                result:
                    historyResult.result,

                probability:
                    historyResult.probability,

                created_at:
                    historyResult.created_at,

                input_data:
                    historyResult.input_data
                        ? JSON.parse(historyResult.input_data)
                        : {},

                explanation:
                    historyResult.explanation
                        ? JSON.parse(historyResult.explanation)
                        : [],

                model:
                    historyResult.model_name,

                model_version:
                    historyResult.model_version,

                historical: true
            };

            renderResult();

        } catch (error) {

            console.error(
                "Historical result error:",
                error
            );

            resultsArea.innerHTML = `
                <div class="panel empty">

                    <h2>
                        Could not load assessment
                    </h2>

                    <p class="muted">
                        ${escapeHTML(error.message)}
                    </p>

                    <p>
                        <a
                            class="button"
                            href="history.html"
                        >
                            Back to History
                        </a>
                    </p>

                </div>
            `;
        }

        return;
    }


    // --------------------------------------------------------
    // NEW RESULT FROM ACTIVE ASSESSMENT
    // --------------------------------------------------------

    try {

        result = JSON.parse(
            sessionStorage.getItem("genecare-result")
        );

    } catch {

        result = null;

    }


    renderResult();
}


// ============================================================
// ESCAPE HTML
// ============================================================

const escapeHTML = value =>
    String(value ?? "").replace(
        /[&<>"']/g,
        char => ({
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            '"': "&quot;",
            "'": "&#039;"
        }[char])
    );


function formatFeatureName(name) {

    const names = {
        age: "Age",
        sex: "Sex",
        cp: "Chest Pain",
        trestbps: "Resting Blood Pressure",
        chol: "Cholesterol",
        fbs: "Fasting Blood Sugar",
        restecg: "Resting ECG",
        thalach: "Maximum Heart Rate",
        exang: "Exercise Angina",
        oldpeak: "ST Depression",
        slope: "ST Slope",
        ca: "Major Vessels",
        thal: "Thalassemia",

        Pregnancies: "Pregnancies",
        Glucose: "Glucose",
        BloodPressure: "Blood Pressure",
        SkinThickness: "Skin Thickness",
        Insulin: "Insulin",
        BMI: "BMI",
        DiabetesPedigreeFunction:
            "Diabetes Pedigree Function",
        Age: "Age"
    };

    return names[name] || String(name)
        .replace(/_/g, " ")
        .replace(/([a-z])([A-Z])/g, "$1 $2")
        .replace(/\b\w/g, char => char.toUpperCase());
}

function formatFeatureValue(
    feature,
    value,
    disease
) {

    if (disease === "Heart Disease") {

        const mappings = {

            sex: {
                0: "Female",
                1: "Male"
            },

            cp: {
                0: "Typical angina",
                1: "Atypical angina",
                2: "Non-anginal pain",
                3: "Asymptomatic"
            },

            fbs: {
                0: "Below 120 mg/dL",
                1: "Above 120 mg/dL"
            },

            restecg: {
                0: "Normal",
                1: "ST-T wave abnormality",
                2: "Left ventricular hypertrophy"
            },

            exang: {
                0: "No",
                1: "Yes"
            },

            slope: {
                0: "Upsloping",
                1: "Flat",
                2: "Downsloping"
            },

            thal: {
                0: "Normal",
                1: "Fixed defect",
                2: "Normal",
                3: "Reversible defect"
            }
        };

        if (
            mappings[feature] &&
            mappings[feature][value] !== undefined
        ) {
            return mappings[feature][value];
        }
    }

    if (disease === "Diabetes") {

        if (
            feature === "Outcome"
        ) {
            return Number(value) === 1
                ? "Positive"
                : "Negative";
        }
    }

    return String(value);
}

// ============================================================
// RENDER RESULT
// ============================================================

function renderResult() {

    if (!result) {

        resultsArea.innerHTML = `
            <div class="panel empty">

                <h2>
                    No assessment result yet
                </h2>

                <p class="muted">
                    Connect FastAPI and submit an active
                    assessment to view a result.
                </p>

                <p>
                    <a
                        class="button"
                        href="analyze.html"
                    >
                        Start an Assessment
                    </a>
                </p>

            </div>
        `;

        return;
    }


    // ========================================================
    // MODEL
    // ========================================================

    const selectedModel = models.find(
        model =>
            model.key === result.screening
    );


    // ========================================================
    // PROBABILITY
    // ========================================================

    const rawProbability =
        Number(result.probability);

    const probability =
        Number.isFinite(rawProbability)
            ? Math.round(
                (
                    rawProbability <= 1
                        ? rawProbability
                        : rawProbability / 100
                ) * 100
            )
            : 0;

    const safeProbability =
        Math.max(
            0,
            Math.min(100, probability)
        );


    // ========================================================
    // PREDICTION
    // ========================================================

    const prediction =
        escapeHTML(
            result.result ||
            (
                Number(result.prediction) === 1
                    ? "The model returned an elevated-risk estimate."
                    : "The model returned a lower-risk estimate."
            )
        );


    const riskLevel =
        Number(result.prediction) === 1
            ? "Elevated"
            : "Lower";


    // ========================================================
    // SHAP EXPLANATION
    // ========================================================

    const contributions =
        Array.isArray(result.explanation)
            ? result.explanation
            : [];


    const normalized =
        contributions
            .map(item => {

                const value =
                    Number(
                        item?.contribution ??
                        item?.value
                    );

                return {

                    feature:
                        escapeHTML(
                            item?.feature ??
                            item?.name ??
                            "Feature"
                        ),

                    value:
                        Number.isFinite(value)
                            ? value
                            : 0,

                    direction:
                        escapeHTML(
                            item?.direction ?? ""
                        )
                };

            })
            .filter(
                item =>
                    Number.isFinite(item.value)
            );


    const maxContribution =
        Math.max(
            ...normalized.map(
                item =>
                    Math.abs(item.value)
            ),
            0
        );


    const contributionHTML =
        normalized.length

            ? normalized.map(item => {

                const width =
                    maxContribution
                        ? Math.max(
                            3,
                            Math.round(
                                Math.abs(item.value) /
                                maxContribution *
                                100
                            )
                        )
                        : 3;

                const negative =
                    item.value < 0;

                const sign =
                    item.value > 0
                        ? "+"
                        : "";

                return `
                    <div
                        class="contribution
                        ${negative ? "negative" : ""}"
                    >

                        <div class="contribution-head">

                            <b>
                                ${item.feature}
                            </b>

                            <span
                                class="contribution-value"
                            >
                                ${sign}${item.value.toFixed(4)}
                            </span>

                        </div>

                        <div
                            class="contribution-track"
                            aria-label="${item.feature}: ${sign}${item.value.toFixed(4)}"
                        >

                            <i
                                style="width:${width}%"
                            ></i>

                        </div>

                    </div>
                `;

            }).join("")

            : result.historical

                ? `
                    <p class="muted">

                        Feature contribution data is not
                        stored for historical assessments.

                    </p>
                `

                : `
                    <p class="muted">

                        Feature contribution data is
                        unavailable for this assessment.

                    </p>
                `;


    // ========================================================
    // TECHNICAL INFORMATION
    // ========================================================

    const modelName =
        escapeHTML(
            result.model ||
            selectedModel?.model ||
            "Not supplied"
        );


    const modelVersion =
        escapeHTML(
            result.model_version ||
            "Not supplied"
        );


    const dataset =
        escapeHTML(
            selectedModel?.dataset ||
            "Not supplied"
        );


    const explainer =
        escapeHTML(
            selectedModel?.explainer ||
            "Not supplied"
        );

    const inputData =
        result.historical &&
            result.input_data &&
            typeof result.input_data === "object"
            ? result.input_data
            : {};

    const inputEntries =
        Object.entries(inputData);

    const inputHTML =
        inputEntries.length
            ? `
            <div class="assessment-inputs">

                ${inputEntries.map(
                ([key, value]) => `
                        <div class="input-detail">

                            <span>
                                ${escapeHTML(
                    formatFeatureName(key)
                )}
                            </span>

                            <strong>
                                ${escapeHTML(
                                    formatFeatureValue(
                                        key,
                                        value,
                                        result.disease
                                    )
                                )}
                            </strong>

                        </div>
                    `
            ).join("")}

            </div>
        `
            : `
            <p class="muted">
                Input values are not available for
                this assessment.
            </p>
        `;


    // ========================================================
    // DATE
    // ========================================================

    let assessmentDate = "";

    if (result.created_at) {

        const date =
            new Date(
                result.created_at
                    .replace(" ", "T") + "Z"
            );

        if (!isNaN(date.getTime())) {

            assessmentDate =
                date.toLocaleString(
                    "en-US",
                    {
                        month: "short",
                        day: "numeric",
                        year: "numeric",
                        hour: "numeric",
                        minute: "2-digit"
                    }
                );
        }
    }


    // ========================================================
    // RENDER
    // ========================================================

    resultsArea.innerHTML = `

        <p class="eyebrow">

            ${escapeHTML(
        selectedModel?.name ||
        result.disease ||
        "Assessment"
    )}

            risk screening

        </p>


        ${result.historical && assessmentDate
            ? `
                <p class="muted">
                    Assessment from ${assessmentDate}
                </p>
            `
            : ""
        }


        <div class="result-layout">


            <!-- LEFT COLUMN -->

            <section>


                <!-- MODEL ESTIMATE -->

                <div class="panel risk-panel">

                    <div>

                        <p class="eyebrow">
                            Model estimate
                        </p>

                        <h2>
                            ${riskLevel}
                        </h2>

                    </div>


                    <strong>
                        ${safeProbability}%
                    </strong>


                    <div class="progress">

                        <span
                            style="width:${safeProbability}%"
                        ></span>

                    </div>


                    <p class="risk-note">

                        Estimated probability returned
                        by the model. This is a screening
                        estimate, not a diagnosis.

                    </p>

                </div>


                <!-- PREDICTION SUMMARY -->

                <div
                    class="panel"
                    style="margin-top:24px"
                >
                    

                    <p class="eyebrow">
                        Prediction summary
                    </p>


                    <h2
                        style="
                            font-size:22px;
                            margin:7px 0 9px;
                        "
                    >

                        ${prediction}

                    </h2>

                </div>

                ${result.historical ? `
                        <div
                            class="panel"
                            style="margin-top:24px"
                        >

                            <p class="eyebrow">
                                Assessment inputs
                            </p>

                            <h2
                                style="
                                    font-size:22px;
                                    margin:7px 0 8px;
                                "
                            >
                                Values Used for This Assessment
                            </h2>

                            <p class="muted">
                                These are the values submitted when
                                this assessment was performed.
                            </p>

                            <div style="margin-top:20px">

                                ${inputHTML}

                            </div>

                        </div>
                ` : ""}


                <!-- SHAP -->

                <div
                    class="panel"
                    style="margin-top:24px"
                >

                    <p class="eyebrow">
                        Explainability
                    </p>


                    <h2
                        style="
                            font-size:22px;
                            margin:7px 0 8px;
                        "
                    >
                        What Influenced the Model?
                    </h2>


                    <p class="muted">

                        SHAP contributions show how
                        features moved the model output
                        for this assessment. They are not
                        percentages and do not imply
                        medical causation.

                    </p>


                    <div style="margin-top:22px">

                        ${contributionHTML}

                    </div>


                    ${normalized.length
            ? `
                            <p
                                class="muted"
                                style="
                                    font-size:11px;
                                    margin-top:20px;
                                "
                            >

                                Positive and negative values
                                indicate direction of contribution
                                to the model output.

                                Bar lengths are scaled only
                                relative to the largest
                                contribution shown.

                            </p>
                        `
            : ""
        }

                </div>

            </section>


            <!-- RIGHT COLUMN -->

            <aside>


                <!-- TECHNICAL DETAILS -->

                <div class="panel">

                    <p class="eyebrow">
                        Technical details
                    </p>


                    <h2
                        style="
                            font-size:20px;
                            margin:7px 0 2px;
                        "
                    >
                        Model Information
                    </h2>


                    <dl>

                        <div>

                            <dt>
                                Model
                            </dt>

                            <dd>
                                ${modelName}
                            </dd>

                        </div>


                        <div>

                            <dt>
                                Version
                            </dt>

                            <dd>
                                ${modelVersion}
                            </dd>

                        </div>


                        <div>

                            <dt>
                                Dataset
                            </dt>

                            <dd>
                                ${dataset}
                            </dd>

                        </div>


                        <div>

                            <dt>
                                Explainability
                            </dt>

                            <dd>
                                ${explainer}
                            </dd>

                        </div>


                        <div>

                            <dt>
                                Input features
                            </dt>

                            <dd>
                                ${escapeHTML(
            selectedModel?.features ||
            "Not supplied"
        )}
                            </dd>

                        </div>

                    </dl>

                </div>


                <!-- RESPONSIBLE USE -->

                <div
                    class="panel"
                    style="margin-top:24px"
                >

                    <p class="eyebrow">
                        Responsible use
                    </p>


                    <h2
                        style="
                            font-size:20px;
                            margin:7px 0 9px;
                        "
                    >
                        Next Steps
                    </h2>


                    <ul class="list muted">

                        <li>
                            Review the result with a
                            qualified healthcare professional.
                        </li>

                        <li>
                            Discuss relevant risk factors
                            in context.
                        </li>

                        <li>
                            Do not make medical decisions
                            based solely on this screening.
                        </li>

                    </ul>


                    <p style="margin-top:22px">

                        <a
                            class="button"
                            href="analyze.html"
                        >
                            Run Another Assessment
                        </a>

                    </p>


                    <p style="margin-top:9px">

                        <a
                            class="button secondary"
                            href="disease-detail.html?condition=${encodeURIComponent(
            selectedModel?.key ||
            "heart"
        )}"
                        >
                            View Condition Information
                        </a>

                    </p>


                    <button
                        class="button secondary"
                        style="
                            width:100%;
                            margin-top:9px;
                        "
                        disabled
                    >
                        Download Report — unavailable
                    </button>

                </div>

            </aside>

        </div>
    `;
}


// ============================================================
// START
// ============================================================

loadResult();
