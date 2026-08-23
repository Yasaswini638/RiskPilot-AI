"""
RiskPilot Evaluation Module

Compares two human-review allocation strategies:

Strategy A:
    Highest fraud-risk transactions.

Strategy B:
    RiskPilot economic-priority transactions.

The evaluation uses the same scored test transactions
for both strategies to ensure a fair comparison.
"""

from pathlib import Path

import json
import pandas as pd


# ============================================================
# Configuration
# ============================================================

DEFAULT_REVIEW_CAPACITY = 50

PROJECT_ROOT = Path(__file__).resolve().parent.parent

ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"

ARTIFACTS_DIR.mkdir(
    exist_ok=True
)


# ============================================================
# Strategy A
# ============================================================

def select_highest_risk(
    transactions: pd.DataFrame,
    review_capacity: int = DEFAULT_REVIEW_CAPACITY,
) -> pd.DataFrame:
    """
    Select transactions with the highest fraud probability.

    This represents a conventional risk-based review strategy.
    """

    if review_capacity <= 0:
        raise ValueError(
            "review_capacity must be greater than zero."
        )

    required_columns = {
        "transaction_id",
        "risk_probability",
        "amount",
        "isFraud",
    }

    missing_columns = (
        required_columns
        - set(transactions.columns)
    )

    if missing_columns:
        raise ValueError(
            "Missing required columns: "
            + ", ".join(sorted(missing_columns))
        )

    queue = transactions.copy()

    queue = queue.sort_values(
        "risk_probability",
        ascending=False
    )

    queue = queue.head(
        min(
            review_capacity,
            len(queue)
        )
    ).copy()

    queue.insert(
        0,
        "review_rank",
        range(
            1,
            len(queue) + 1
        )
    )

    return queue.reset_index(
        drop=True
    )


# ============================================================
# Strategy Metrics
# ============================================================

def calculate_strategy_metrics(
    selected_transactions: pd.DataFrame,
    total_fraud_transactions: int,
) -> dict:
    """
    Calculate evaluation metrics for a review strategy.
    """

    reviewed_count = len(
        selected_transactions
    )

    fraud_captured = int(
        selected_transactions["isFraud"].sum()
    )

    total_value_reviewed = float(
        selected_transactions["amount"].sum()
    )

    average_risk = float(
        selected_transactions["risk_probability"].mean()
    ) if reviewed_count > 0 else 0.0

    fraud_capture_rate = (
        fraud_captured / total_fraud_transactions
        if total_fraud_transactions > 0
        else 0.0
    )

    return {
        "transactions_reviewed": reviewed_count,
        "fraud_transactions_captured": fraud_captured,
        "fraud_capture_rate": fraud_capture_rate,
        "total_transaction_value_reviewed": (
            total_value_reviewed
        ),
        "average_risk_probability": average_risk,
    }


# ============================================================
# Strategy Comparison
# ============================================================

def compare_strategies(
    transactions: pd.DataFrame,
    riskpilot_queue: pd.DataFrame,
    review_capacity: int = DEFAULT_REVIEW_CAPACITY,
) -> dict:
    """
    Compare conventional highest-risk review against
    RiskPilot economic-priority review.
    """

    total_fraud_transactions = int(
        transactions["isFraud"].sum()
    )

    # --------------------------------------------------------
    # Strategy A
    # --------------------------------------------------------

    highest_risk_queue = select_highest_risk(
        transactions,
        review_capacity=review_capacity,
    )

    strategy_a_metrics = calculate_strategy_metrics(
        highest_risk_queue,
        total_fraud_transactions,
    )

    # --------------------------------------------------------
    # Strategy B
    # --------------------------------------------------------

    strategy_b_transactions = (
        transactions[
            transactions["transaction_id"].isin(
                riskpilot_queue["transaction_id"]
            )
        ]
        .copy()
    )

    # Preserve RiskPilot queue ordering.
    strategy_b_transactions = (
        riskpilot_queue[
            [
                "transaction_id"
            ]
        ]
        .merge(
            strategy_b_transactions,
            on="transaction_id",
            how="left",
        )
    )

    strategy_b_metrics = calculate_strategy_metrics(
        strategy_b_transactions,
        total_fraud_transactions,
    )

    # --------------------------------------------------------
    # Comparison
    # --------------------------------------------------------

    value_difference = (
        strategy_b_metrics[
            "total_transaction_value_reviewed"
        ]
        -
        strategy_a_metrics[
            "total_transaction_value_reviewed"
        ]
    )

    fraud_capture_difference = (
        strategy_b_metrics[
            "fraud_capture_rate"
        ]
        -
        strategy_a_metrics[
            "fraud_capture_rate"
        ]
    )

    return {
        "review_capacity": review_capacity,
        "total_test_transactions": int(
            len(transactions)
        ),
        "total_fraud_transactions": (
            total_fraud_transactions
        ),
        "strategy_a_highest_risk": (
            strategy_a_metrics
        ),
        "strategy_b_riskpilot_economic": (
            strategy_b_metrics
        ),
        "comparison": {
            "transaction_value_difference": (
                value_difference
            ),
            "fraud_capture_rate_difference": (
                fraud_capture_difference
            ),
        },
    }


# ============================================================
# Save Evaluation Results
# ============================================================

def save_evaluation_results(
    results: dict,
    output_path: Path = (
        ARTIFACTS_DIR
        / "strategy_comparison.json"
    ),
) -> None:
    """
    Save evaluation results as JSON.
    """

    with open(
        output_path,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            results,
            file,
            indent=4,
        )


# ============================================================
# Display Results
# ============================================================

def print_strategy_comparison(
    results: dict,
) -> None:
    """
    Print a human-readable strategy comparison.
    """

    strategy_a = (
        results[
            "strategy_a_highest_risk"
        ]
    )

    strategy_b = (
        results[
            "strategy_b_riskpilot_economic"
        ]
    )

    comparison = (
        results[
            "comparison"
        ]
    )

    print()
    print("=" * 60)
    print("RiskPilot Strategy Comparison")
    print("=" * 60)

    print(
        "\nReview capacity:",
        results["review_capacity"]
    )

    print(
        "Total test transactions:",
        results["total_test_transactions"]
    )

    print(
        "Total fraud transactions:",
        results["total_fraud_transactions"]
    )

    print("\nStrategy A — Highest Risk")

    print(
        "Transactions reviewed:",
        strategy_a[
            "transactions_reviewed"
        ]
    )

    print(
        "Fraud transactions captured:",
        strategy_a[
            "fraud_transactions_captured"
        ]
    )

    print(
        "Fraud capture rate:",
        f"{strategy_a['fraud_capture_rate']:.2%}"
    )

    print(
        "Transaction value reviewed:",
        f"₹{strategy_a['total_transaction_value_reviewed']:,.2f}"
    )

    print(
        "Average risk:",
        f"{strategy_a['average_risk_probability']:.4f}"
    )

    print("\nStrategy B — RiskPilot Economic Priority")

    print(
        "Transactions reviewed:",
        strategy_b[
            "transactions_reviewed"
        ]
    )

    print(
        "Fraud transactions captured:",
        strategy_b[
            "fraud_transactions_captured"
        ]
    )

    print(
        "Fraud capture rate:",
        f"{strategy_b['fraud_capture_rate']:.2%}"
    )

    print(
        "Transaction value reviewed:",
        f"₹{strategy_b['total_transaction_value_reviewed']:,.2f}"
    )

    print(
        "Average risk:",
        f"{strategy_b['average_risk_probability']:.4f}"
    )

    print("\nDifference")

    print(
        "Transaction value difference:",
        f"₹{comparison['transaction_value_difference']:,.2f}"
    )

    print(
        "Fraud capture rate difference:",
        f"{comparison['fraud_capture_rate_difference']:.2%}"
    )

    print("=" * 60)


# ============================================================
# Main
# ============================================================

if __name__ == "__main__":

    print(
        "RiskPilot evaluation module created successfully."
    )

    print(
        "\nThis module expects a scored transaction "
        "DataFrame containing:"
    )

    print(
        "transaction_id, risk_probability, amount, isFraud"
    )

    print(
        "\nThe actual experiment runner will be connected "
        "to the reproducible training pipeline next."
    )