from pathlib import Path
from typing import Dict, List

import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from src.decision_engine import (
    DEFAULT_MERCHANT_PROFILES,
    riskpilot_decision,
)
from src.explain import explain_decision
from src.predict import RiskPilotPredictor
from src.review_queue import build_economic_review_queue


# ============================================================
# RiskPilot API
# ============================================================

app = FastAPI(
    title="RiskPilot AI",
    description=(
        "Cost-aware adaptive fraud decision engine "
        "for merchants."
    ),
    version="1.0.0",
)


# Load the persisted model once when the API starts.
try:
    predictor = RiskPilotPredictor()
except FileNotFoundError:
    predictor = None


# ============================================================
# Request Models
# ============================================================

class TransactionRequest(BaseModel):
    step: int = Field(..., ge=0)
    type: str
    amount: float = Field(..., ge=0)
    oldbalanceOrg: float = Field(..., ge=0)
    oldbalanceDest: float = Field(..., ge=0)
    merchant: str = "E_COMMERCE"


class BatchTransactionRequest(BaseModel):
    transactions: List[TransactionRequest]
    review_capacity: int = Field(
        default=50,
        ge=1
    )


# ============================================================
# Health Check
# ============================================================

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "model_loaded": predictor is not None,
    }


# ============================================================
# Single Transaction Prediction
# ============================================================

@app.post("/predict")
def predict_transaction(
    request: TransactionRequest
):
    if predictor is None:
        raise HTTPException(
            status_code=503,
            detail="RiskPilot model is not loaded."
        )

    merchant_name = request.merchant.upper()

    if merchant_name not in DEFAULT_MERCHANT_PROFILES:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Unknown merchant profile: "
                f"{request.merchant}"
            )
        )

    transaction = {
        "step": request.step,
        "type": request.type,
        "amount": request.amount,
        "oldbalanceOrg": request.oldbalanceOrg,
        "oldbalanceDest": request.oldbalanceDest,
    }

    transaction_df = pd.DataFrame(
        [transaction]
    )

    # --------------------------------------------------------
    # ML prediction
    # --------------------------------------------------------

    risk_probability = (
        predictor.predict_probability(
            transaction_df
        )
    )

    # --------------------------------------------------------
    # Economic decision
    # --------------------------------------------------------

    merchant_profile = (
        DEFAULT_MERCHANT_PROFILES[
            merchant_name
        ]
    )

    action, costs = riskpilot_decision(
        risk_probability=risk_probability,
        amount=request.amount,
        merchant_profile=merchant_profile,
    )

    # --------------------------------------------------------
    # Explanation
    # --------------------------------------------------------

    explanation = explain_decision(
        risk_probability=risk_probability,
        amount=request.amount,
        action=action,
        costs=costs,
        transaction=transaction,
    )

    return {
        "transaction": transaction,
        "merchant": merchant_name,
        "risk_probability": round(
            risk_probability,
            6
        ),
        "risk_level": explanation[
            "risk_level"
        ],
        "decision": action,
        "expected_costs": {
            key: round(value, 2)
            for key, value in costs.items()
        },
        "reasons": explanation[
            "reasons"
        ],
        "transaction_context": explanation[
            "transaction_context"
        ],
    }


# ============================================================
# Economic Review Queue
# ============================================================

@app.post("/review-queue")
def review_queue(
    request: BatchTransactionRequest
):
    if predictor is None:
        raise HTTPException(
            status_code=503,
            detail="RiskPilot model is not loaded."
        )

    transactions = []

    for transaction_request in request.transactions:

        merchant_name = (
            transaction_request.merchant.upper()
        )

        if merchant_name not in DEFAULT_MERCHANT_PROFILES:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Unknown merchant profile: "
                    f"{transaction_request.merchant}"
                )
            )

        transaction = {
            "transaction_id": len(transactions) + 1,
            "step": transaction_request.step,
            "type": transaction_request.type,
            "amount": transaction_request.amount,
            "oldbalanceOrg": (
                transaction_request.oldbalanceOrg
            ),
            "oldbalanceDest": (
                transaction_request.oldbalanceDest
            ),
            "merchant": merchant_name,
        }

        transaction_df = pd.DataFrame(
            [{
                "step": transaction["step"],
                "type": transaction["type"],
                "amount": transaction["amount"],
                "oldbalanceOrg": (
                    transaction["oldbalanceOrg"]
                ),
                "oldbalanceDest": (
                    transaction["oldbalanceDest"]
                ),
            }]
        )

        risk_probability = (
            predictor.predict_probability(
                transaction_df
            )
        )

        transaction[
            "risk_probability"
        ] = risk_probability

        transactions.append(
            transaction
        )

    scored_df = pd.DataFrame(
        transactions
    )

    # --------------------------------------------------------
    # Current API expects one merchant profile per request.
    # --------------------------------------------------------

    merchant_names = (
        scored_df["merchant"].unique()
    )

    if len(merchant_names) != 1:
        raise HTTPException(
            status_code=400,
            detail=(
                "All transactions in a review-queue "
                "request must use the same merchant."
            )
        )

    merchant_profile = (
        DEFAULT_MERCHANT_PROFILES[
            merchant_names[0]
        ]
    )

    queue = build_economic_review_queue(
        scored_df[
            [
                "transaction_id",
                "risk_probability",
                "amount",
            ]
        ],
        merchant_profile=merchant_profile,
        review_capacity=request.review_capacity,
    )

    return {
        "merchant": merchant_names[0],
        "total_transactions": len(
            scored_df
        ),
        "review_capacity": (
            request.review_capacity
        ),
        "selected_for_review": len(
            queue
        ),
        "queue": queue.to_dict(
            orient="records"
        ),
    }
# ============================================================
# Frontend
# ============================================================

FRONTEND_DIR = (
    Path(__file__).resolve().parent.parent
    / "frontend"
)

app.mount(
    "/",
    StaticFiles(
        directory=str(FRONTEND_DIR),
        html=True,
    ),
    name="frontend",
)