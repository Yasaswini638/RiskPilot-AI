"""
RiskPilot Final Experiment Analysis

Analyzes the difference between:

Strategy A:
    Highest-risk transactions.

Strategy B:
    RiskPilot review queue.

The script recreates the same test set used by the experiment,
compares both review strategies, and saves a reproducible
analysis artifact.
"""

from pathlib import Path
import json

import pandas as pd

from src.evaluation import (
    select_highest_risk,
    calculate_strategy_metrics,
)

from src.evaluate_experiment import (
    create_modeling_dataset,
    engineer_features,
    create_test_set,
    score_test_transactions,
    build_riskpilot_queue,
)


# ============================================================
# Configuration
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"

ARTIFACTS_DIR.mkdir(
    exist_ok=True
)

REVIEW_CAPACITY = 50


# ============================================================
# Utility
# ============================================================

def validate_columns(
    dataframe: pd.DataFrame,
    required_columns: set,
    name: str,
) -> None:

    missing = (
        required_columns
        - set(dataframe.columns)
    )

    if missing:
        raise ValueError(
            f"{name} is missing required columns: "
            + ", ".join(sorted(missing))
        )


# ============================================================
# Main experiment
# ============================================================

def main():

    print("=" * 60)
    print("RiskPilot Final Experiment Analysis")
    print("=" * 60)

    # --------------------------------------------------------
    # Recreate test data
    # --------------------------------------------------------

    print("\nRecreating test dataset...")

    df_model = create_modeling_dataset()

    df_model = engineer_features(
        df_model
    )

    test_df = create_test_set(
        df_model
    )

    test_results = score_test_transactions(
        test_df
    )

    print(
        "\nTest transactions:",
        len(test_results)
    )

    # --------------------------------------------------------
    # Validate test data
    # --------------------------------------------------------

    required_columns = {
        "transaction_id",
        "risk_probability",
        "amount",
        "isFraud",
    }

    validate_columns(
        test_results,
        required_columns,
        "Test results",
    )

    # --------------------------------------------------------
    # Strategy A
    # --------------------------------------------------------

    print("\nBuilding Strategy A...")

    strategy_a = select_highest_risk(
        test_results,
        review_capacity=REVIEW_CAPACITY,
    )

    # --------------------------------------------------------
    # Strategy B
    # --------------------------------------------------------

    print("Building Strategy B...")

    strategy_b = build_riskpilot_queue(
        test_results
    )

    strategy_b = strategy_b.head(
        REVIEW_CAPACITY
    ).copy()

    # --------------------------------------------------------
    # Strategy metrics
    # --------------------------------------------------------

    total_fraud = int(
        test_results["isFraud"].sum()
    )

    metrics_a = calculate_strategy_metrics(
        strategy_a,
        total_fraud,
    )

    metrics_b = calculate_strategy_metrics(
        strategy_b,
        total_fraud,
    )

    # --------------------------------------------------------
    # Transaction IDs
    # --------------------------------------------------------

    ids_a = set(
        strategy_a["transaction_id"]
    )

    ids_b = set(
        strategy_b["transaction_id"]
    )

    common_ids = ids_a & ids_b

    a_only_ids = ids_a - ids_b

    b_only_ids = ids_b - ids_a

    # --------------------------------------------------------
    # Fraud analysis
    # --------------------------------------------------------

    a_only = strategy_a[
        strategy_a["transaction_id"].isin(
            a_only_ids
        )
    ].copy()

    b_only = strategy_b[
        strategy_b["transaction_id"].isin(
            b_only_ids
        )
    ].copy()

    missed_fraud = a_only[
        a_only["isFraud"] == 1
    ].copy()

    additional_fraud = b_only[
        b_only["isFraud"] == 1
    ].copy()

    # --------------------------------------------------------
    # Overlap
    # --------------------------------------------------------

    overlap_percentage = (
        len(common_ids)
        / REVIEW_CAPACITY
        if REVIEW_CAPACITY > 0
        else 0.0
    )

    # --------------------------------------------------------
    # Economic comparison
    # --------------------------------------------------------

    value_difference = (
        metrics_b["total_transaction_value_reviewed"]
        - metrics_a["total_transaction_value_reviewed"]
    )

    fraud_capture_difference = (
        metrics_b["fraud_capture_rate"]
        - metrics_a["fraud_capture_rate"]
    )

    # --------------------------------------------------------
    # Print final comparison
    # --------------------------------------------------------

    print("\n")
    print("=" * 60)
    print("FINAL REVIEW STRATEGY COMPARISON")
    print("=" * 60)

    print(
        "\nReview capacity:",
        REVIEW_CAPACITY,
    )

    print(
        "Total test transactions:",
        len(test_results),
    )

    print(
        "Total fraud transactions:",
        total_fraud,
    )

    print("\nStrategy A — Highest Risk")

    print(
        "Transactions reviewed:",
        metrics_a["transactions_reviewed"],
    )

    print(
        "Fraud captured:",
        metrics_a["fraud_transactions_captured"],
    )

    print(
        "Fraud capture rate:",
        f"{metrics_a['fraud_capture_rate']:.2%}",
    )

    print(
        "Transaction value reviewed:",
        f"₹{metrics_a['total_transaction_value_reviewed']:,.2f}",
    )

    print(
        "Average risk:",
        f"{metrics_a['average_risk_probability']:.4f}",
    )

    print("\nStrategy B — RiskPilot")

    print(
        "Transactions reviewed:",
        metrics_b["transactions_reviewed"],
    )

    print(
        "Fraud captured:",
        metrics_b["fraud_transactions_captured"],
    )

    print(
        "Fraud capture rate:",
        f"{metrics_b['fraud_capture_rate']:.2%}",
    )

    print(
        "Transaction value reviewed:",
        f"₹{metrics_b['total_transaction_value_reviewed']:,.2f}",
    )

    print(
        "Average risk:",
        f"{metrics_b['average_risk_probability']:.4f}",
    )

    print("\nComparison")

    print(
        "Review-set overlap:",
        f"{len(common_ids)} / {REVIEW_CAPACITY}",
    )

    print(
        "Overlap percentage:",
        f"{overlap_percentage:.2%}",
    )

    print(
        "Transaction value difference:",
        f"₹{value_difference:,.2f}",
    )

    print(
        "Fraud capture difference:",
        f"{fraud_capture_difference:.2%}",
    )

    print(
        "Fraud missed by RiskPilot:",
        len(missed_fraud),
    )

    print(
        "Additional fraud captured by RiskPilot:",
        len(additional_fraud),
    )

    # --------------------------------------------------------
    # Save detailed transaction analysis
    # --------------------------------------------------------

    analysis_rows = []

    for _, row in test_results.iterrows():

        transaction_id = row[
            "transaction_id"
        ]

        in_a = transaction_id in ids_a
        in_b = transaction_id in ids_b

        if in_a and in_b:
            category = "BOTH"

        elif in_a:
            category = "STRATEGY_A_ONLY"

        elif in_b:
            category = "RISKPILOT_ONLY"

        else:
            category = "NEITHER"

        analysis_rows.append(
            {
                "transaction_id": transaction_id,
                "risk_probability": row[
                    "risk_probability"
                ],
                "amount": row[
                    "amount"
                ],
                "isFraud": row[
                    "isFraud"
                ],
                "strategy_a_selected": in_a,
                "riskpilot_selected": in_b,
                "selection_category": category,
            }
        )

    analysis_df = pd.DataFrame(
        analysis_rows
    )

    analysis_path = (
        ARTIFACTS_DIR
        / "experiment_analysis.csv"
    )

    analysis_df.to_csv(
        analysis_path,
        index=False,
        encoding="utf-8-sig",
    )

    # --------------------------------------------------------
    # Save summary
    # --------------------------------------------------------

    summary = {
        "review_capacity": REVIEW_CAPACITY,
        "total_test_transactions": int(
            len(test_results)
        ),
        "total_fraud_transactions": total_fraud,
        "strategy_a": metrics_a,
        "strategy_b": metrics_b,
        "comparison": {
            "common_transactions": len(
                common_ids
            ),
            "overlap_percentage": overlap_percentage,
            "strategy_a_only": len(
                a_only_ids
            ),
            "riskpilot_only": len(
                b_only_ids
            ),
            "fraud_missed_by_riskpilot": len(
                missed_fraud
            ),
            "additional_fraud_captured_by_riskpilot": len(
                additional_fraud
            ),
            "transaction_value_difference": (
                value_difference
            ),
            "fraud_capture_rate_difference": (
                fraud_capture_difference
            ),
        },
    }

    summary_path = (
        ARTIFACTS_DIR
        / "experiment_summary.json"
    )

    with open(
        summary_path,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            summary,
            file,
            indent=4,
        )

    # --------------------------------------------------------
    # Save missed fraud
    # --------------------------------------------------------

    missed_fraud_path = (
        ARTIFACTS_DIR
        / "missed_fraud_analysis.csv"
    )

    missed_fraud.to_csv(
        missed_fraud_path,
        index=False,
        encoding="utf-8-sig",
    )

    print("\n")
    print("=" * 60)
    print("ARTIFACTS CREATED")
    print("=" * 60)

    print(
        "\nExperiment analysis:",
        analysis_path,
    )

    print(
        "Experiment summary:",
        summary_path,
    )

    print(
        "Missed fraud analysis:",
        missed_fraud_path,
    )

    print("\nExperiment analysis completed successfully.")


if __name__ == "__main__":
    main()