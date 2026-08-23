You're right. The issue is that my previous answer was rendered as a large Markdown block, and the interface can visually collapse/clip very long pasted content. You want one single copy-pasteable block, with the entire README from beginning to end, not pieces or explanations around it.

Below is the complete README in one single code block. Copy everything inside the block directly into `README.md`.


# RiskPilot AI

## Cost-Aware Adaptive Fraud Decision Engine

> Razorpay AI Buildathon 2026 — AI Risk Manager

RiskPilot AI is an end-to-end machine-learning fraud decision platform designed to help merchants make better transaction decisions under financial risk and limited human-review capacity.

Traditional fraud systems primarily answer:

> "Is this transaction fraudulent?"

RiskPilot addresses the more practical business question:

> "Given the predicted fraud risk, transaction value, business costs, merchant policy, and available review capacity, what should the merchant do?"

RiskPilot combines:

- Machine-learning fraud probability prediction
- Economic decision optimization
- Merchant-specific risk profiles
- Human-review prioritization
- Review-capacity constraints
- Explainable decisions
- REST APIs
- Interactive web dashboard
- Reproducible experiments
- Automated testing

The system produces one of three primary decisions:
APPROVE
REVIEW
BLOCK


---

# 1. Problem Statement

Fraud detection in digital payments is not simply a binary classification problem.

A merchant may process thousands of transactions while having only a limited number of analysts available to manually investigate suspicious transactions.

A conventional fraud detection workflow often looks like:
Transaction
    ↓
Fraud Probability
    ↓
Fixed Threshold
    ↓
Approve / Block


This approach can overlook important business considerations:

* Transaction value
* Cost of fraud losses
* Cost of false positives
* Cost of manual investigation
* Merchant-specific risk tolerance
* Limited analyst capacity
* Economic value of human intervention

For example, two transactions can have similar fraud probabilities but very different financial exposure.

Therefore, the core problem addressed by RiskPilot is:

> How can an AI-powered fraud system move beyond fraud prediction and make economically informed APPROVE, REVIEW, or BLOCK decisions while operating under limited human-review capacity?

RiskPilot approaches the problem as:
Fraud Probability
        +
Transaction Value
        +
Merchant Cost Profile
        +
Decision Policy
        +
Human Review Capacity
        ↓
Final Business Decision


---

# 2. Proposed Solution

RiskPilot separates fraud prediction from business decisioning.

Instead of stopping at:

Fraud Probability
        ↓
Fraud / Not Fraud


RiskPilot follows:


Transaction
      ↓
Feature Engineering
      ↓
Fraud Probability
      ↓
Economic Cost Analysis
      ↓
Merchant Risk Policy
      ↓
Review Capacity
      ↓
APPROVE / REVIEW / BLOCK
      ↓
Human-Readable Explanation


The platform therefore contains three major decision layers:

### 1. Prediction

> What is the probability that this transaction is fraudulent?

### 2. Decisioning

> Which action has the lowest expected business cost?

### 3. Review Allocation

> If human review is limited, which transactions should receive analyst attention?

This creates a practical human-in-the-loop fraud decision architecture rather than a prediction-only system.

---

# 3. Why This Problem Matters

Payment fraud creates multiple competing business costs.

A merchant wants to:
Reduce fraud losses
        +
Avoid blocking legitimate customers
        +
Control investigation costs
        +
Use analyst capacity efficiently


Optimizing only fraud recall can result in excessive false positives.

Optimizing only customer approval can increase fraud losses.

Optimizing only transaction value can overlook fraud probability.

RiskPilot therefore treats fraud management as a decision optimization problem, not only as a classification problem.

The goal is not simply:

> "Catch as much fraud as possible."

The goal is:

> "Make the best available business decision for each transaction under the merchant's economic constraints."

---

# 4. Key Innovation

The central principle behind RiskPilot is:

> Prediction alone is not the decision.

RiskPilot combines:

Machine Learning
       +
Economic Reasoning
       +
Merchant Policy
       +
Human Review Capacity
       +
Explainability


to produce:
APPROVE
REVIEW
BLOCK


The ML model and business decision engine are intentionally separated.

This allows merchant policies and economic parameters to evolve independently of the fraud model.

---

# 5. How RiskPilot Works

## Step 1 — Receive Transaction

The system receives transaction information such as:
step
type
amount
oldbalanceOrg
oldbalanceDest
merchant


---

## Step 2 — Generate Fraud Probability

The trained Random Forest model generates:
risk_probability ∈ [0, 1]


For example:
risk_probability = 0.262259


corresponds to an estimated fraud probability of approximately:
26.23%


---

## Step 3 — Evaluate Economic Costs

RiskPilot evaluates the expected cost associated with:
APPROVE
REVIEW
BLOCK


using the merchant's configured economic profile.

---

## Step 4 — Select the Decision

The decision engine compares the expected costs:

Expected Cost(APPROVE)
Expected Cost(REVIEW)
Expected Cost(BLOCK)
          ↓
    Best Action


The selected action is returned as:


APPROVE
REVIEW
BLOCK


---

## Step 5 — Generate Explanation

RiskPilot generates an explanation containing:

* Risk probability
* Risk level
* Selected decision
* Expected costs
* Transaction context
* Decision reasoning

---

## Step 6 — Allocate Human Review

For multiple transactions, RiskPilot constructs a review queue.

The queue considers:


Risk
  +
Economic Exposure
  +
Decision Value
  +
Risk Policy
  +
Review Capacity


This allows limited analyst capacity to be allocated systematically.

---

# 6. System Architecture

                         ┌────────────────────────────┐
                         │      RiskPilot Frontend    │
                         │        HTML/CSS/JS         │
                         └─────────────┬──────────────┘
                                       │
                                       ▼
                         ┌────────────────────────────┐
                         │        FastAPI API         │
                         │                            │
                         │ GET  /health               │
                         │ POST /predict              │
                         │ POST /review-queue         │
                         └─────────────┬──────────────┘
                                       │
             ┌─────────────────────────┼─────────────────────────┐
             │                         │                         │
             ▼                         ▼                         ▼
   ┌──────────────────┐     ┌────────────────────┐     ┌──────────────────┐
   │   Fraud Model    │     │  Decision Engine   │     │  Explainability  │
   │                  │     │                    │     │     Engine        │
   │ Random Forest    │     │ Economic Cost      │     │ Human-readable   │
   │                  │     │ Optimization        │     │ Reasoning        │
   └────────┬─────────┘     └─────────┬──────────┘     └────────┬─────────┘
            │                         │                         │
            └─────────────────────────┼─────────────────────────┘
                                      │
                                      ▼
                         ┌────────────────────────────┐
                         │     Human Review Queue     │
                         │                            │
                         │ Risk + Economic Priority   │
                         │ + Capacity Constraints     │
                         └────────────────────────────┘
```

---

# 7. Features

### Fraud Prediction

Predicts transaction-level fraud probability using a trained Random Forest classifier.

### Economic Decisioning

Evaluates APPROVE, REVIEW, and BLOCK using expected economic costs.

### Merchant Profiles

Supports configurable merchant-specific economic parameters.

### Human Review Queue

Prioritizes transactions for investigation when analyst capacity is limited.

### Explainability

Provides human-readable explanations for decisions.

### REST API

Provides FastAPI endpoints for:
GET  /health
POST /predict
POST /review-queue


### Interactive Dashboard

Provides a browser-based interface for transaction analysis.

### Reproducible Experiments

Compares RiskPilot against a highest-risk review baseline.

### Automated Testing

Provides automated tests for the major system components.

---

# 8. Machine Learning Approach

RiskPilot uses a Random Forest classifier for fraud probability prediction.

The ML pipeline is:


Raw Transaction Data
        ↓
Chunk-Based Processing
        ↓
Feature Engineering
        ↓
Chronological Split
        ↓
Random Forest Training
        ↓
Validation
        ↓
Test Evaluation
        ↓
Persisted Model


The model produces:
risk_probability


where:
0.0 ≤ risk_probability ≤ 1.0


The ML model estimates risk.

The economic decision engine determines the business action.

This separation makes the architecture easier to adapt to different merchant policies.

---

# 9. Economic Decision Engine

The decision engine evaluates:
APPROVE
REVIEW
BLOCK


The merchant economic profile includes configurable parameters such as:
fraud_loss_rate
false_positive_rate
review_fixed_cost
review_percentage


Conceptually:
                  Transaction
                       │
              ┌────────┴────────┐
              │                 │
              ▼                 ▼
       Risk Probability       Amount
              │                 │
              └────────┬────────┘
                       ▼
              Merchant Profile
                       │
                       ▼
              Expected Cost Model
                       │
                ┌──────┼──────┐
                ▼      ▼      ▼
             APPROVE REVIEW BLOCK
                │      │      │
                └──────┼──────┘
                       ▼
                 Selected Action


The objective is to choose an economically appropriate action rather than relying exclusively on a fixed fraud threshold.

---

# 10. Human Review Queue

Human investigation capacity is limited.

In the evaluated experiment:
Test transactions: 2,562
Review capacity:      50


RiskPilot therefore constructs a prioritized review queue.

The queue can contain:
review_rank
transaction_id
risk_probability
amount
approve_cost
review_cost
block_cost
best_automatic_cost
review_value
best_automatic_action
review_reason


The review policy applies the configured risk rules and review capacity.

This allows analysts to focus on transactions where human intervention may provide meaningful value.

---

# 11. Explainability

RiskPilot does not return only:
REVIEW


It also provides context for the decision.

The prediction response can contain:
Risk Probability
Risk Level
Decision
Expected APPROVE Cost
Expected REVIEW Cost
Expected BLOCK Cost
Transaction Context
Reasons


Example:
Risk Probability: 26.23%
Risk Level: MEDIUM
Decision: REVIEW


Explainability is important for:

* Fraud analysts
* Merchant operations teams
* Developers
* Business stakeholders
* Buildathon evaluators

The purpose is to make the decision understandable rather than treating the model as a black box.

---

# 12. Dataset

RiskPilot uses the PaySim transaction dataset for the reproducible fraud-detection experiment.

The final modeling pipeline produced:

| Dataset Property            |   Value |
| --------------------------- | ------: |
| Modeling transactions       | 103,530 |
| Non-fraud transactions      |  95,317 |
| Fraud transactions          |   8,213 |
| Test transactions           |   2,562 |
| Test fraud transactions     |   1,264 |
| Test non-fraud transactions |   1,298 |

The raw dataset is processed in chunks to reduce unnecessary memory usage.

The experiment uses a chronological split:
Training
    ↓
Validation
    ↓
Test


Configuration used in the final experiment:
Validation end step: 630
Test steps: 631 – 743


This chronological evaluation reduces the risk of temporal leakage between training and evaluation.

---

# 13. Results and Evaluation

RiskPilot was evaluated on a held-out chronological test set.

## Evaluation Dataset

Total transactions:       2,562
Fraud transactions:      1,264
Non-fraud transactions:  1,298
Review capacity:            50


Two review strategies were compared.

---

## Strategy A — Highest Risk Baseline

The baseline selects the 50 transactions with the highest predicted fraud probability.

Sort by risk_probability
        ↓
Select top 50


### Results

Transactions reviewed: 50
Fraud captured:        50
Fraud capture rate:    3.96%
Average risk:          1.0000
Transaction value:     ₹291,506,408.78


---

## Strategy B — RiskPilot

RiskPilot applies its review policy under the same review capacity.

### Results

Transactions reviewed: 50
Fraud captured:        50
Fraud capture rate:    3.96%
Average risk:          1.0000
Transaction value:     ₹290,927,770.92


---

## Strategy Comparison

| Metric                     | Highest-Risk Baseline |       RiskPilot |
| -------------------------- | --------------------: | --------------: |
| Transactions reviewed      |                    50 |              50 |
| Fraud captured             |                    50 |              50 |
| Fraud capture rate         |                 3.96% |           3.96% |
| Average risk               |                1.0000 |          1.0000 |
| Transaction value reviewed |       ₹291,506,408.78 | ₹290,927,770.92 |

Additional experiment analysis:

Review-set overlap:        98%
Fraud missed by RiskPilot: 1
Additional fraud captured: 1


### Interpretation

On this evaluated test split, RiskPilot achieved the same fraud capture count as the highest-risk baseline while producing a highly similar review set.

The results demonstrate the feasibility of combining:


Fraud Risk
     +
Economic Decisioning
     +
Review Capacity


into a unified fraud decision system.

### Capacity-Constrained Review Experiment

RiskPilot was evaluated on a held-out test set containing 2,562 transactions,
including 1,264 fraud transactions.

The experiment assumes a human review capacity of 50 transactions.

| Metric | Highest-Risk Baseline | RiskPilot |
|---|---:|---:|
| Review capacity | 50 | 50 |
| Transactions reviewed | 50 | 50 |
| Fraud captured | 50 | 50 |
| Fraud capture rate over test fraud | 3.96% | 3.96% |
| Review-set overlap | — | 98.00% |
| Transaction value reviewed | ₹291.51M | ₹290.93M |
| Average risk probability | 1.0000 | 1.0000 |

RiskPilot therefore preserved the fraud capture achieved by the
highest-risk baseline in this experiment while changing the review
selection objective from raw risk ranking to an economically informed
decision policy.

Important: The experiment does not claim that RiskPilot universally outperforms the highest-risk strategy. The result is specific to the evaluated test split and demonstrates the behavior of the implemented decision framework.

---

# 14. Technology Stack

## Machine Learning

* Python 3.11
* Pandas
* NumPy
* Scikit-learn
* Random Forest
* Joblib

## Backend

* FastAPI
* Pydantic
* Uvicorn

## Frontend

* HTML5
* CSS3
* JavaScript

## Testing

* Pytest
* FastAPI TestClient

## Development

* Git
* GitHub
* Python Virtual Environment

---

# 15. Project Structure

RiskPilot-AI/
│
├── README.md
├── requirements.txt
│
├── backend/
│   └── main.py
│
├── frontend/
│   ├── index.html
│   ├── app.js
│   └── style.css
│
├── src/
│   ├── __init__.py
│   ├── train.py
│   ├── features.py
│   ├── predict.py
│   ├── decision_engine.py
│   ├── explain.py
│   ├── review_queue.py
│   ├── evaluation.py
│   ├── evaluate_experiment.py
│   └── analyze_experiment.py
│
├── tests/
│   ├── test_api.py
│   ├── test_decision_engine.py
│   ├── test_explain.py
│   ├── test_features.py
│   ├── test_predict.py
│   └── test_review_queue.py
│
├── artifacts/
│   ├── metrics.json
│   ├── strategy_comparison.json
│   ├── riskpilot_review_queue.csv
│   ├── experiment_analysis.csv
│   ├── experiment_summary.json
│   └── missed_fraud_analysis.csv
│
├── models/
│
├── data/
│
└── ...


---

# 16. API Documentation

RiskPilot provides a FastAPI backend.

## Base URL

When running locally:
http://127.0.0.1:8000


## Swagger Documentation
http://127.0.0.1:8000/docs


---

## GET /health

Checks API and model availability.

### Example Response

{
  "status": "ok",
  "model_loaded": true
}

---

## POST /predict

Analyzes a single transaction.

### Example Request

{
  "step": 650,
  "type": "TRANSFER",
  "amount": 5000,
  "oldbalanceOrg": 7500,
  "oldbalanceDest": 1000,
  "merchant": "E_COMMERCE"
}

### Response Fields

transaction
merchant
risk_probability
risk_level
decision
expected_costs
reasons
transaction_context


### Example Response

{
  "transaction": {
    "step": 650,
    "type": "TRANSFER",
    "amount": 5000,
    "oldbalanceOrg": 7500,
    "oldbalanceDest": 1000
  },
  "merchant": "E_COMMERCE",
  "risk_probability": 0.262259,
  "risk_level": "MEDIUM",
  "decision": "REVIEW",
  "expected_costs": {
    "APPROVE": 1311.3,
    "REVIEW": 23.0,
    "BLOCK": 295.1
  }
}


---

## POST /review-queue

Builds a review queue for multiple transactions.

### Example Request


{
  "transactions": [
    {
      "step": 650,
      "type": "TRANSFER",
      "amount": 5000,
      "oldbalanceOrg": 7500,
      "oldbalanceDest": 1000,
      "merchant": "E_COMMERCE"
    },
    {
      "step": 700,
      "type": "CASH_OUT",
      "amount": 100000,
      "oldbalanceOrg": 100000,
      "oldbalanceDest": 5000,
      "merchant": "E_COMMERCE"
    }
  ],
  "review_capacity": 2
}


The response contains the transactions selected for human review.

---

# 17. Frontend / Demo

RiskPilot includes an interactive browser dashboard.

The frontend is built using:
HTML5
CSS3
JavaScript


The dashboard allows users to:

* Check backend/model health
* Enter transaction information
* Load example transactions
* Analyze transaction risk
* View fraud probability
* View risk level
* View APPROVE / REVIEW / BLOCK
* View expected costs
* View decision explanations
* Interact with the RiskPilot API

The frontend communicates with the FastAPI backend.

---

# 18. Installation

## Prerequisites

Recommended:
Python 3.11+
Git


## Clone Repository
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd RiskPilot-AI


## Create Virtual Environment
python -m venv .venv


## Activate Virtual Environment

Windows PowerShell:
.\.venv\Scripts\Activate.ps1


## Install Dependencies

pip install -r requirements.txt


---

# 19. How to Run

## Start the Backend

From the project root:
python -m uvicorn backend.main:app --reload


The API will be available at:

http://127.0.0.1:8000


---

## Open Swagger

Navigate to:

http://127.0.0.1:8000/docs


Available endpoints:

GET  /health
POST /predict
POST /review-queue


---

## Run the Frontend

Open:

frontend/index.html


in a browser while the FastAPI backend is running.

The frontend communicates with:
http://127.0.0.1:8000


---

# 20. Testing

RiskPilot includes an automated test suite covering the major components.

Run:

python -m pytest -q .\tests


The final verified test suite produced:
36 passed


Coverage includes:

Decision Engine
Feature Engineering
Prediction
Explainability
Review Queue
FastAPI API
Input Validation


A Starlette/httpx deprecation warning may appear depending on installed dependency versions. It does not cause the tests to fail.

---

# 21. Experiment Reproduction

The project contains a reproducible experimental pipeline.

## Training

Run:
python -m src.train


The training pipeline:

1. Reads the PaySim dataset.
2. Processes raw data in chunks.
3. Creates the modeling dataset.
4. Performs feature engineering.
5. Creates chronological splits.
6. Trains the Random Forest model.
7. Evaluates the model.
8. Persists the model and evaluation artifacts.

---

## Strategy Evaluation

The experiment modules compare the RiskPilot review policy against the highest-risk baseline.

Generated artifacts include:


artifacts/strategy_comparison.json
artifacts/riskpilot_review_queue.csv
artifacts/experiment_analysis.csv
artifacts/experiment_summary.json
artifacts/missed_fraud_analysis.csv


These artifacts provide evidence for:

* Fraud capture
* Review-set overlap
* Transaction value reviewed
* Missed-fraud analysis
* Review prioritization
* Strategy comparison

---

# 22. Limitations

RiskPilot is currently a research and prototype system.

## Dataset

PaySim is a simulated financial transaction dataset.

Real payment traffic can have different:

* Fraud patterns
* Customer behavior
* Merchant behavior
* Class imbalance
* Temporal patterns
* Attack strategies

## Model

The current implementation uses a Random Forest model.

Production deployment would require:

* Probability calibration
* Model monitoring
* Data drift detection
* Concept drift detection
* Regular retraining
* Model versioning

## Economic Parameters

Merchant cost parameters are configurable but would need to be calibrated using real business data.

## Evaluation

The final strategy comparison is based on one evaluated chronological test split.

The results demonstrate feasibility but do not prove universal superiority over all fraud-review strategies.

## Production Security

The current prototype does not represent a complete production payment-security architecture.

A production system would require:

* Authentication
* Authorization
* HTTPS
* Secret management
* Audit logging
* Rate limiting
* Encryption
* Privacy controls
* Monitoring
* Operational alerting

---

# 23. Future Scope

## Machine Learning

Future versions can include:

* Probability calibration
* XGBoost comparison
* Gradient boosting
* Cost-sensitive learning
* SHAP-based explanations
* Model drift detection
* Data drift detection
* Online learning
* Merchant-specific model adaptation

## Fraud Operations

Future versions can support:

* Analyst feedback
* Case management
* Fraud investigation workflows
* Real-time alerts
* Fraud-spike detection
* Analyst performance tracking
* Feedback-driven retraining

## Infrastructure

Future production architecture could include:


Payment Events
      ↓
Kafka
      ↓
RiskPilot Inference Service
      ↓
Decision Engine
      ↓
Redis / Review Queue
      ↓
Fraud Analyst Dashboard


Additional infrastructure could include:


PostgreSQL
Redis
Kafka
Docker
Kubernetes
Cloud Deployment
CI/CD
Observability


## Production Security

Future deployment should include:

* OAuth/JWT authentication
* Role-based access control
* API rate limiting
* Encryption
* Secure secrets
* Audit trails
* Privacy controls

---

# 24. Demo Flow

The recommended project demonstration is:


1. Open RiskPilot Dashboard
        ↓
2. Show System / Model Health
        ↓
3. Enter Example Transaction
        ↓
4. Click Analyze
        ↓
5. Show Fraud Probability
        ↓
6. Show Risk Level
        ↓
7. Show APPROVE / REVIEW / BLOCK
        ↓
8. Show Expected Costs
        ↓
9. Show Explanation
        ↓
10. Open Swagger
        ↓
11. Demonstrate /predict
        ↓
12. Demonstrate /review-queue
        ↓
13. Show Evaluation Results
        ↓
14. Run Automated Tests


---

# 25. Buildathon Submission Summary

## Project

**RiskPilot AI**

## Track

**AI Risk Manager**

## Core Problem

Fraud detection systems need to make economically informed decisions while operating with limited human-review capacity.

## Proposed Solution

A machine-learning-powered fraud decision engine that combines:


Fraud Probability
        +
Economic Cost
        +
Merchant Policy
        +
Human Review Capacity
        +
Explainability


## Primary Decisions


APPROVE
REVIEW
BLOCK


## Machine Learning Model


Random Forest


## Dataset

PaySim


## Final Test Dataset


2,562 transactions
1,264 fraud transactions
1,298 non-fraud transactions


## Human Review Capacity


50 transactions


## Final Strategy Results

### Highest-Risk Baseline


50 reviewed
50 fraud captured
3.96% fraud capture rate


### RiskPilot


50 reviewed
50 fraud captured
3.96% fraud capture rate


### Review-Set Overlap

98%


## Application Components


Machine Learning
Decision Engine
Explainability
Human Review Queue
FastAPI Backend
Frontend Dashboard
Automated Tests
Experiment Pipeline


## Core Value Proposition

> **RiskPilot moves fraud management from prediction to economically informed decision-making.**

---

# 26. Final Submission Checklist

Before submitting the Razorpay AI Buildathon project, verify:


[✓] README.md completed
[✓] Problem statement documented
[✓] Proposed solution documented
[✓] Innovation explained
[✓] Architecture documented
[✓] ML approach documented
[✓] Economic decision engine documented
[✓] Review queue documented
[✓] Explainability documented
[✓] Dataset documented
[✓] Evaluation results documented
[✓] API endpoints documented
[✓] Frontend documented
[✓] Installation instructions documented
[✓] Run instructions documented
[✓] Testing instructions documented
[✓] Experiment reproduction documented
[✓] Limitations documented
[✓] Future scope documented
[✓] Demo flow documented
[✓] Buildathon summary documented
[✓] GitHub repository updated
[✓] Automated tests passing


---

# 27. Conclusion

RiskPilot AI demonstrates an end-to-end approach to fraud decisioning where machine-learning predictions are converted into economically informed business actions.

Traditional fraud systems often focus on:

> "Is this transaction fraudulent?"

RiskPilot expands this into:

> "What should the merchant do?"

The system combines:


Machine Learning
        +
Economic Decisioning
        +
Merchant Policy
        +
Human Review Capacity
        +
Explainability


to determine whether a transaction should be:


APPROVED
REVIEWED
BLOCKED


The project provides:

* A reproducible machine-learning pipeline
* A Random Forest fraud model
* An economic decision engine
* Merchant-specific cost profiles
* A human-review queue
* Explainable decisions
* A FastAPI backend
* An interactive frontend
* Automated tests
* Experiment artifacts
* Strategy comparison

On the evaluated PaySim chronological test split, RiskPilot achieved the same fraud capture count as the highest-risk baseline while producing a 98% overlapping review set.

The current implementation is a prototype and uses simulated transaction data. Future work will focus on real-world transaction integration, calibrated probabilities, online monitoring, model and data drift detection, analyst feedback loops, stronger security, and production-scale deployment.

The central principle of RiskPilot is:


Prediction alone is not the decision.

Fraud Prediction
        +
Economic Cost
        +
Business Policy
        +
Human Review Capacity
        +
Explainability
        =
Better Fraud Decisions


---

## RiskPilot AI

### From fraud prediction to economically informed fraud decisions.



That is the format you were asking for: one continuous Markdown code block, with the entire README from  RiskPilot AI through the conclusion.

