from typing import Dict

import pandas as pd

from src.decision_engine import calculate_action_costs


def calculate_review_priority(
    risk_probability: float,
    amount: float,
) -> float:
    """
    Calculate expected fraud exposure.

    Formula:

        risk_probability × transaction amount

    This is useful as a simple risk-exposure ranking signal.
    """

    return float(
        risk_probability * amount
    )


def explain_review_priority(
    risk_probability: float,
    amount: float,
    review_priority: float,
) -> str:
    """
    Generate a human-readable explanation for economic exposure.
    """

    return (
        f"Risk probability is "
        f"{risk_probability:.2%} and transaction value is "
        f"₹{amount:,.2f}, producing an estimated "
        f"economic exposure of ₹{review_priority:,.2f}."
    )


def build_review_queue(
    transactions: pd.DataFrame,
    review_capacity: int = 50,
) -> pd.DataFrame:
    """
    Build a simple risk-exposure review queue.

    This function is retained as the baseline queue strategy.
    """

    if review_capacity <= 0:
        raise ValueError(
            "review_capacity must be greater than zero."
        )

    required_columns = {
        "transaction_id",
        "risk_probability",
        "amount",
    }

    missing_columns = (
        required_columns
        - set(transactions.columns)
    )

    if missing_columns:
        raise ValueError(
            "Missing required columns: "
            + ", ".join(
                sorted(missing_columns)
            )
        )

    queue = transactions.copy()

    queue["review_priority"] = (
        queue["risk_probability"]
        * queue["amount"]
    )

    queue = (
        queue
        .sort_values(
            "review_priority",
            ascending=False,
        )
        .head(
            review_capacity
        )
        .copy()
    )

    queue.insert(
        0,
        "review_rank",
        range(
            1,
            len(queue) + 1,
        ),
    )

    return queue.reset_index(
        drop=True
    )


def build_economic_review_queue(
    transactions: pd.DataFrame,
    merchant_profile: Dict[str, float],
    review_capacity: int = 50,
    minimum_risk: float = 0.50,
    critical_risk: float = 0.95,
) -> pd.DataFrame:
    """
    Build the RiskPilot economic review queue.

    Policy:

    1. Only transactions above minimum_risk are eligible.

    2. Critical-risk transactions receive protected priority.

    3. Remaining capacity is allocated using economic
       review value.

    4. Remaining capacity is filled using risk priority.

    5. Every selected transaction receives complete cost
       and explanation information.
    """

    if review_capacity <= 0:
        raise ValueError(
            "review_capacity must be greater than zero."
        )

    if not 0 <= minimum_risk <= 1:
        raise ValueError(
            "minimum_risk must be between 0 and 1."
        )

    if not 0 <= critical_risk <= 1:
        raise ValueError(
            "critical_risk must be between 0 and 1."
        )

    if critical_risk < minimum_risk:
        raise ValueError(
            "critical_risk must be greater than or equal "
            "to minimum_risk."
        )

    required_columns = {
        "transaction_id",
        "risk_probability",
        "amount",
    }

    missing_columns = (
        required_columns
        - set(transactions.columns)
    )

    if missing_columns:
        raise ValueError(
            "Missing required columns: "
            + ", ".join(
                sorted(missing_columns)
            )
        )

    queue = transactions.copy()

    # --------------------------------------------------------
    # Candidate pool
    # --------------------------------------------------------

    queue = queue[
        queue["risk_probability"]
        >= minimum_risk
    ].copy()

    if queue.empty:
        return queue

    # --------------------------------------------------------
    # Calculate expected action costs
    # --------------------------------------------------------

    cost_records = []

    for _, row in queue.iterrows():

        costs = calculate_action_costs(
            risk_probability=float(
                row["risk_probability"]
            ),
            amount=float(
                row["amount"]
            ),
            fraud_loss_rate=merchant_profile[
                "fraud_loss_rate"
            ],
            false_positive_rate=merchant_profile[
                "false_positive_rate"
            ],
            review_fixed_cost=merchant_profile[
                "review_fixed_cost"
            ],
            review_percentage=merchant_profile[
                "review_percentage"
            ],
        )

        cost_records.append(
            costs
        )

    costs_df = pd.DataFrame(
        cost_records,
        index=queue.index,
    )

    queue["approve_cost"] = (
        costs_df["APPROVE"]
    )

    queue["review_cost"] = (
        costs_df["REVIEW"]
    )

    queue["block_cost"] = (
        costs_df["BLOCK"]
    )

    # --------------------------------------------------------
    # Best automatic decision
    # --------------------------------------------------------

    queue["best_automatic_cost"] = (
        queue[
            [
                "approve_cost",
                "block_cost",
            ]
        ]
        .min(axis=1)
    )

    queue["best_automatic_action"] = (
        queue[
            [
                "approve_cost",
                "block_cost",
            ]
        ]
        .idxmin(axis=1)
        .map(
            {
                "approve_cost": "APPROVE",
                "block_cost": "BLOCK",
            }
        )
    )

    # --------------------------------------------------------
    # Economic review value
    # --------------------------------------------------------

    queue["economic_review_value"] = (
        queue["best_automatic_cost"]
        - queue["review_cost"]
    )

    # Keep the older name for compatibility.
    queue["review_value"] = (
        queue["economic_review_value"]
    )

    # --------------------------------------------------------
    # Risk exposure
    # --------------------------------------------------------

    queue["review_priority"] = (
        queue["risk_probability"]
        * queue["amount"]
    )

    # --------------------------------------------------------
    # Critical-risk protection
    # --------------------------------------------------------

    queue["critical_risk_protection"] = (
        queue["risk_probability"]
        >= critical_risk
    )

    # --------------------------------------------------------
    # Selection reason
    # --------------------------------------------------------

    queue["selection_reason"] = "ECONOMIC_PRIORITY"

    queue.loc[
        queue["critical_risk_protection"],
        "selection_reason",
    ] = "CRITICAL_RISK_PROTECTION"

    queue["review_reason"] = queue.apply(
        lambda row: (
            "Critical-risk protection: transaction risk "
            f"is {row['risk_probability']:.2%}, exceeding "
            f"the {critical_risk:.0%} protection threshold."
            if row["critical_risk_protection"]
            else (
                "Economic priority: human review has an "
                f"estimated economic advantage of "
                f"₹{max(row['economic_review_value'], 0):,.2f} "
                "over the best automatic action."
            )
        ),
        axis=1,
    )

    # --------------------------------------------------------
    # Stage 1 — Critical-risk transactions
    # --------------------------------------------------------

    critical = (
        queue[
            queue["critical_risk_protection"]
        ]
        .sort_values(
            [
                "risk_probability",
                "review_priority",
            ],
            ascending=[
                False,
                False,
            ],
        )
        .head(
            review_capacity
        )
        .copy()
    )

    selected_ids = set(
        critical["transaction_id"]
    )

    remaining_capacity = (
        review_capacity
        - len(critical)
    )

    # --------------------------------------------------------
    # Stage 2 — Positive economic value
    # --------------------------------------------------------

    remaining = queue[
        ~queue["transaction_id"].isin(
            selected_ids
        )
    ].copy()

    economic = (
        remaining[
            remaining["economic_review_value"]
            > 0
        ]
        .sort_values(
            [
                "economic_review_value",
                "risk_probability",
            ],
            ascending=[
                False,
                False,
            ],
        )
        .head(
            remaining_capacity
        )
        .copy()
    )

    selected_ids.update(
        economic["transaction_id"]
    )

    remaining_capacity -= len(
        economic
    )

    # --------------------------------------------------------
    # Stage 3 — Risk fallback
    # --------------------------------------------------------

    remaining = queue[
        ~queue["transaction_id"].isin(
            selected_ids
        )
    ].copy()

    fallback = (
        remaining
        .sort_values(
            [
                "risk_probability",
                "review_priority",
            ],
            ascending=[
                False,
                False,
            ],
        )
        .head(
            remaining_capacity
        )
        .copy()
    )

    fallback["selection_reason"] = (
        "HIGH_RISK_FALLBACK"
    )

    fallback["review_reason"] = fallback.apply(
        lambda row: (
            "High-risk fallback selected because review "
            "capacity remained available. "
            f"Risk probability: "
            f"{row['risk_probability']:.2%}."
        ),
        axis=1,
    )

    # --------------------------------------------------------
    # Combine
    # --------------------------------------------------------

    final_queue = pd.concat(
        [
            critical,
            economic,
            fallback,
        ],
        ignore_index=True,
    )

    # --------------------------------------------------------
    # Final ordering
    # --------------------------------------------------------

    final_queue = (
        final_queue
        .sort_values(
            [
                "critical_risk_protection",
                "risk_probability",
                "economic_review_value",
            ],
            ascending=[
                False,
                False,
                False,
            ],
        )
        .head(
            review_capacity
        )
        .reset_index(
            drop=True
        )
    )

    # --------------------------------------------------------
    # Review rank
    # --------------------------------------------------------

    final_queue.insert(
        0,
        "review_rank",
        range(
            1,
            len(final_queue) + 1,
        ),
    )

    return final_queue