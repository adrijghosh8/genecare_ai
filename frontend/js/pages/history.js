// =========================================
// Load History
// =========================================

async function loadHistory() {

    const token = localStorage.getItem("access_token");

    try {

        const response = await fetch(
            "http://localhost:8000/history",
            {
                method: "GET",

                headers: {
                    "Authorization": `Bearer ${token}`
                }
            }
        );


        if (!response.ok) {
            throw new Error(
                "Could not load history."
            );
        }


        const history = await response.json();

        displayHistory(history);


    } catch (error) {

        console.error(
            "History error:",
            error
        );


        document.getElementById(
            "history-container"
        ).innerHTML = `
            <p>${error.message}</p>
        `;
    }
}


// =========================================
// Display History
// =========================================

function displayHistory(history) {

    const container =
        document.getElementById(
            "history-container"
        );


    if (history.length === 0) {

        container.innerHTML = `
            <div class="empty-history">

                <h3>
                    No predictions yet
                </h3>

                <p>
                    Complete an assessment to see your
                    results here.
                </p>

                <a href="analyze.html">
                    Start an Analysis
                </a>

            </div>
        `;

        return;
    }


    container.innerHTML =
        history.map(item => {

            // ==============================
            // Convert UTC → Local Time
            // ==============================

            const date = new Date(
                item.created_at
                    .replace(" ", "T") + "Z"
            );


            const formattedDate =
                date.toLocaleDateString(
                    "en-US",
                    {
                        month: "short",
                        day: "numeric",
                        year: "numeric"
                    }
                );


            const formattedTime =
                date.toLocaleTimeString(
                    "en-US",
                    {
                        hour: "numeric",
                        minute: "2-digit"
                    }
                );


            // ==============================
            // Probability
            // ==============================

            const probability =
                (
                    item.probability * 100
                ).toFixed(1);


            // ==============================
            // Card
            // ==============================

            return `

                <div class="history-card">

                    <div class="history-card-top">

                        <h3>
                            ${item.disease}
                        </h3>

                        <span class="history-result">
                            ${item.result}
                        </span>

                    </div>


                    <div class="history-card-details">

                        <p>

                            <strong>
                                Risk Probability
                            </strong>

                            <br>

                            ${probability}%

                        </p>


                        <p>

                            <strong>
                                Assessment Date
                            </strong>

                            <br>

                            ${formattedDate}
                            ·
                            ${formattedTime}

                        </p>

                    </div>


                    <!-- View Result -->

                    <a
                        class="history-view-result"
                        href="results.html?prediction=${item.id}"
                    >
                        View Assessment →
                    </a>

                </div>

            `;

        }).join("");
}


// =========================================
// Start
// =========================================

loadHistory();