/* ==========================================================
   RiskPilot AI Frontend
========================================================== */


const form =
    document.getElementById("predictionForm");

const resultCard =
    document.getElementById("resultCard");

const analyzeButton =
    document.getElementById("analyzeButton");

const buttonText =
    document.getElementById("buttonText");

const buttonSpinner =
    document.getElementById("buttonSpinner");

const sampleButton =
    document.getElementById("sampleButton");

const statusDot =
    document.getElementById("statusDot");

const statusText =
    document.getElementById("statusText");


/* ==========================================================
   SAMPLE TRANSACTION
========================================================== */

sampleButton.addEventListener(
    "click",
    () => {

        document.getElementById(
            "step"
        ).value = 650;

        document.getElementById(
            "type"
        ).value = "TRANSFER";

        document.getElementById(
            "amount"
        ).value = 5000;

        document.getElementById(
            "oldbalanceOrg"
        ).value = 7500;

        document.getElementById(
            "oldbalanceDest"
        ).value = 1000;

        document.getElementById(
            "merchant"
        ).value = "E_COMMERCE";

    }
);


/* ==========================================================
   API HEALTH
========================================================== */

async function checkApiHealth() {

    try {

        const response =
            await fetch("/health");

        if (!response.ok) {
            throw new Error(
                "API returned an error."
            );
        }

        const data =
            await response.json();

        if (data.model_loaded) {

            statusDot.className =
                "status-dot online";

            statusText.textContent =
                "API online • Model loaded";

        } else {

            statusDot.className =
                "status-dot";

            statusText.textContent =
                "API online • Model unavailable";

        }

    } catch (error) {

        statusDot.className =
            "status-dot offline";

        statusText.textContent =
            "API offline";

    }

}


/* ==========================================================
   FORM DATA
========================================================== */

function getTransactionPayload() {

    return {

        step: Number(
            document.getElementById(
                "step"
            ).value
        ),

        type:
            document.getElementById(
                "type"
            ).value,

        amount: Number(
            document.getElementById(
                "amount"
            ).value
        ),

        oldbalanceOrg: Number(
            document.getElementById(
                "oldbalanceOrg"
            ).value
        ),

        oldbalanceDest: Number(
            document.getElementById(
                "oldbalanceDest"
            ).value
        ),

        merchant:
            document.getElementById(
                "merchant"
            ).value,

    };

}


/* ==========================================================
   FORMAT MONEY
========================================================== */

function formatMoney(value) {

    return new Intl.NumberFormat(
        "en-IN",
        {
            style: "currency",
            currency: "INR",
            maximumFractionDigits: 2,
        }
    ).format(value);

}


/* ==========================================================
   FORMAT RISK
========================================================== */

function formatRisk(probability) {

    return (
        Number(probability) * 100
    ).toFixed(2) + "%";

}


/* ==========================================================
   RISK CLASS
========================================================== */

function getRiskClass(level) {

    const normalized =
        String(level).toLowerCase();

    if (normalized === "low") {

        return "risk-low";

    }

    if (normalized === "high") {

        return "risk-high";

    }

    return "risk-medium";

}


/* ==========================================================
   DECISION CLASS
========================================================== */

function getDecisionClass(decision) {

    switch (
        String(decision).toUpperCase()
    ) {

        case "APPROVE":
            return "decision-approve";

        case "BLOCK":
            return "decision-block";

        default:
            return "decision-review";

    }

}


/* ==========================================================
   RENDER RESULT
========================================================== */

function renderResult(data) {

    const risk =
        formatRisk(
            data.risk_probability
        );

    const riskClass =
        getRiskClass(
            data.risk_level
        );

    const decisionClass =
        getDecisionClass(
            data.decision
        );

    const reasons =
        Array.isArray(data.reasons)
            ? data.reasons
            : [];

    const reasonHtml =
        reasons.map(
            reason => `
                <div class="reason">
                    <span class="reason-icon">✓</span>
                    <span>${escapeHtml(reason)}</span>
                </div>
            `
        ).join("");


    const context =
        data.transaction_context || {};


    resultCard.innerHTML = `

        <div class="result-content">

            <div class="result-top">

                <div>

                    <div class="risk-score-label">
                        FRAUD RISK PROBABILITY
                    </div>

                    <div class="risk-score">
                        ${risk}
                    </div>

                </div>

                <div class="risk-level ${riskClass}">
                    ${escapeHtml(
                        data.risk_level
                    )}
                </div>

            </div>


            <div class="decision-box">

                <div class="decision-label">
                    RECOMMENDED ACTION
                </div>

                <div
                    class="decision-value ${decisionClass}"
                >
                    ${escapeHtml(
                        data.decision
                    )}
                </div>

            </div>


            <div>

                <div class="section-label">
                    EXPECTED ECONOMIC COST
                </div>

                <div class="cost-grid">

                    <div class="cost-item">

                        <div class="cost-name">
                            APPROVE
                        </div>

                        <div class="cost-value">
                            ${formatMoney(
                                data.expected_costs.APPROVE
                            )}
                        </div>

                    </div>


                    <div class="cost-item">

                        <div class="cost-name">
                            REVIEW
                        </div>

                        <div class="cost-value">
                            ${formatMoney(
                                data.expected_costs.REVIEW
                            )}
                        </div>

                    </div>


                    <div class="cost-item">

                        <div class="cost-name">
                            BLOCK
                        </div>

                        <div class="cost-value">
                            ${formatMoney(
                                data.expected_costs.BLOCK
                            )}
                        </div>

                    </div>

                </div>

            </div>


            <div class="explanation">

                <h4>
                    Why RiskPilot chose this decision
                </h4>

                ${reasonHtml}

            </div>


            <div class="context-grid">

                <div class="context-item">

                    <div class="context-key">
                        Transaction
                    </div>

                    <div class="context-value">
                        ${escapeHtml(
                            data.type ||
                            context.type ||
                            data.transaction?.type ||
                            "-"
                        )}
                    </div>

                </div>


                <div class="context-item">

                    <div class="context-key">
                        Merchant
                    </div>

                    <div class="context-value">
                        ${escapeHtml(
                            data.merchant ||
                            "-"
                        )}
                    </div>

                </div>


                <div class="context-item">

                    <div class="context-key">
                        Amount
                    </div>

                    <div class="context-value">
                        ${formatMoney(
                            context.amount ||
                            data.transaction?.amount ||
                            0
                        )}
                    </div>

                </div>


                <div class="context-item">

                    <div class="context-key">
                        Origin Balance
                    </div>

                    <div class="context-value">
                        ${formatMoney(
                            context.origin_balance ||
                            0
                        )}
                    </div>

                </div>

            </div>

        </div>
    `;

}


/* ==========================================================
   ERROR RENDERING
========================================================== */

function renderError(message) {

    resultCard.innerHTML = `

        <div class="error-box">

            <h3>
                Unable to analyze transaction
            </h3>

            <p>
                ${escapeHtml(message)}
            </p>

            <p>
                Make sure the RiskPilot API server
                is running.
            </p>

        </div>

    `;

}


/* ==========================================================
   ESCAPE HTML
========================================================== */

function escapeHtml(value) {

    return String(value)
        .replace(
            /&/g,
            "&amp;"
        )
        .replace(
            /</g,
            "&lt;"
        )
        .replace(
            />/g,
            "&gt;"
        )
        .replace(
            /"/g,
            "&quot;"
        )
        .replace(
            /'/g,
            "&#039;"
        );

}


/* ==========================================================
   PREDICTION
========================================================== */

form.addEventListener(
    "submit",
    async event => {

        event.preventDefault();

        const payload =
            getTransactionPayload();


        analyzeButton.disabled = true;

        buttonText.textContent =
            "Analyzing...";

        buttonSpinner.classList.remove(
            "hidden"
        );


        try {

            const response =
                await fetch(
                    "/predict",
                    {
                        method: "POST",

                        headers: {
                            "Content-Type":
                                "application/json",
                        },

                        body:
                            JSON.stringify(
                                payload
                            ),
                    }
                );


            const data =
                await response.json();


            if (!response.ok) {

                throw new Error(
                    data.detail ||
                    "Prediction failed."
                );

            }


            renderResult(data);

        } catch (error) {

            renderError(
                error.message
            );

        } finally {

            analyzeButton.disabled = false;

            buttonText.textContent =
                "Analyze Transaction";

            buttonSpinner.classList.add(
                "hidden"
            );

        }

    }
);


/* ==========================================================
   INITIALIZATION
========================================================== */

checkApiHealth();