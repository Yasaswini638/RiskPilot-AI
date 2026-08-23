"""
RiskPilot Reproducible Experiment Runner

This script:

1. Recreates the RiskPilot modeling dataset.
2. Recreates the chronological test split.
3. Loads the persisted Random Forest model.
4. Generates real fraud probabilities.
5. Builds the RiskPilot human-review queue.
6. Compares RiskPilot against highest-risk review.
7. Saves reproducible experiment artifacts.

Review policy
-------------
RiskPilot uses a three-stage review allocation policy:

1. Risk eligibility:
       risk_probability >= MIN_REVIEW_RISK

2. Critical-risk protection:
       risk_probability >= CRITICAL_RISK_THRESHOLD

   These transactions receive protected priority.

3. Economic prioritization:
       Remaining review capacity is allocated according
       to economic review value.

4. Risk fallback:
       If review capacity still remains, the highest-risk
       eligible transactions are selected.

This creates a risk-aware, economic and capacity-aware
human review policy.
"""

from pathlib import Path

import pandas as pd

from src.evaluation import (
    compare_strategies,
    save_evaluation_results,
    print_strategy_comparison,
)

from src.predict import RiskPilotPredictor


# ============================================================
# Configuration
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_PATH = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "paysim"
    / "PS_20174392719_1491204439457_log.csv"
)

VALIDATION_END = 630

LEGITIMATE_SAMPLE_FRACTION = 0.015

RANDOM_STATE = 42

REVIEW_CAPACITY = 50

# ------------------------------------------------------------
# Minimum risk required to enter the review candidate pool
# ------------------------------------------------------------

MIN_REVIEW_RISK = 0.50

# ------------------------------------------------------------
# Critical risk protection threshold
#
# Transactions at or above this probability are protected
# from being displaced by lower-risk economic candidates.
# ------------------------------------------------------------

CRITICAL_RISK_THRESHOLD = 0.95


# ============================================================
# Feature Policy
# ============================================================

FEATURE_COLUMNS = [
    "step",
    "amount",
    "oldbalanceOrg",
    "oldbalanceDest",
    "amount_to_origin_balance",
    "amount_to_destination_balance",
    "type_CASH_IN",
    "type_CASH_OUT",
    "type_DEBIT",
    "type_PAYMENT",
    "type_TRANSFER",
]


# ============================================================
# Recreate Modeling Dataset
# ============================================================

def create_modeling_dataset() -> pd.DataFrame:
    """
    Recreate the exact modeling dataset used during training.

    Fraud transactions:
        Keep all fraud transactions.

    Legitimate transactions:
        Keep approximately 1.5% of legitimate transactions.

    The same random state is used so the sampling is
    reproducible.
    """

    fraud_parts = []
    legitimate_parts = []

    print("=" * 60)
    print("Recreating RiskPilot modeling dataset")
    print("=" * 60)

    print("Dataset:")
    print(DATA_PATH)

    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Dataset not found: {DATA_PATH}"
        )

    for chunk_number, chunk in enumerate(
        pd.read_csv(
            DATA_PATH,
            chunksize=200_000,
        ),
        start=1,
    ):

        fraud_chunk = chunk[
            chunk["isFraud"] == 1
        ]

        legitimate_chunk = chunk[
            chunk["isFraud"] == 0
        ]

        legitimate_sample = (
            legitimate_chunk.sample(
                frac=LEGITIMATE_SAMPLE_FRACTION,
                random_state=RANDOM_STATE,
            )
        )

        fraud_parts.append(
            fraud_chunk
        )

        legitimate_parts.append(
            legitimate_sample
        )

        print(
            f"Processed chunk {chunk_number}: "
            f"{len(chunk):,} rows"
        )

    df_model = pd.concat(
        fraud_parts + legitimate_parts,
        ignore_index=True,
    )

    print(
        "\nModeling dataset shape:",
        df_model.shape,
    )

    print("\nFraud distribution:")

    print(
        df_model["isFraud"].value_counts()
    )

    return df_model


# ============================================================
# Feature Engineering
# ============================================================

def engineer_features(
    df_model: pd.DataFrame,
) -> pd.DataFrame:
    """
    Recreate the exact feature engineering used by training.

    The original transaction type is preserved separately
    for evaluation and reporting.
    """

    df_model = df_model.copy()

    # --------------------------------------------------------
    # Preserve original transaction type
    # --------------------------------------------------------

    df_model["transaction_type"] = (
        df_model["type"]
    )

    # --------------------------------------------------------
    # Engineered feature 1
    # --------------------------------------------------------

    df_model[
        "amount_to_origin_balance"
    ] = (
        df_model["amount"]
        / (
            df_model["oldbalanceOrg"]
            + 1
        )
    )

    # --------------------------------------------------------
    # Engineered feature 2
    # --------------------------------------------------------

    df_model[
        "amount_to_destination_balance"
    ] = (
        df_model["amount"]
        / (
            df_model["oldbalanceDest"]
            + 1
        )
    )

    # --------------------------------------------------------
    # One-hot encode transaction type
    # --------------------------------------------------------

    df_model = pd.get_dummies(
        df_model,
        columns=["type"],
        prefix="type",
        dtype=int,
    )

    # --------------------------------------------------------
    # Guarantee all model features exist
    # --------------------------------------------------------

    for column in FEATURE_COLUMNS:

        if column not in df_model.columns:
            df_model[column] = 0

    return df_model


# ============================================================
# Chronological Test Split
# ============================================================

def create_test_set(
    df_model: pd.DataFrame,
) -> pd.DataFrame:
    """
    Recreate the chronological test set.

    Training:
        step <= 520

    Validation:
        521 <= step <= 630

    Test:
        step > 630
    """

    df_model = (
        df_model
        .sort_values("step")
        .reset_index(drop=True)
    )

    test_df = df_model[
        df_model["step"] > VALIDATION_END
    ].copy()

    if test_df.empty:
        raise ValueError(
            "The reconstructed test dataset is empty."
        )

    print(
        "\nTest dataset:",
        test_df.shape,
    )

    print(
        "Test steps:",
        test_df["step"].min(),
        "to",
        test_df["step"].max(),
    )

    return test_df


# ============================================================
# Score Test Transactions
# ============================================================

def score_test_transactions(
    test_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Generate fraud probabilities using the persisted model.

    The saved model receives exactly the same 11 features
    used during training.
    """

    predictor = RiskPilotPredictor()

    # --------------------------------------------------------
    # Select exactly the model features
    # --------------------------------------------------------

    X_test = test_df[
        FEATURE_COLUMNS
    ].copy()

    # --------------------------------------------------------
    # Safety validation
    # --------------------------------------------------------

    if list(X_test.columns) != FEATURE_COLUMNS:
        raise ValueError(
            "Test feature columns do not match the expected "
            "RiskPilot feature schema."
        )

    # --------------------------------------------------------
    # Generate fraud probabilities
    # --------------------------------------------------------

    probabilities = (
        predictor.model.predict_proba(
            X_test
        )[:, 1]
    )

    # --------------------------------------------------------
    # Validate probabilities
    # --------------------------------------------------------

    if not (
        (probabilities >= 0).all()
        and
        (probabilities <= 1).all()
    ):
        raise ValueError(
            "Model generated invalid fraud probabilities."
        )

    # --------------------------------------------------------
    # Build evaluation dataframe
    # --------------------------------------------------------

    results = test_df[
        [
            "step",
            "transaction_type",
            "amount",
            "oldbalanceOrg",
            "oldbalanceDest",
            "isFraud",
        ]
    ].copy()

    results = results.rename(
        columns={
            "transaction_type": "type"
        }
    )

    # --------------------------------------------------------
    # Create deterministic transaction IDs
    # --------------------------------------------------------

    results.insert(
        0,
        "transaction_id",
        range(
            1,
            len(results) + 1,
        ),
    )

    # --------------------------------------------------------
    # Add model risk probability
    # --------------------------------------------------------

    results[
        "risk_probability"
    ] = probabilities

    return results


# ============================================================
# Build RiskPilot Review Queue
# ============================================================

def build_riskpilot_queue(
    test_results: pd.DataFrame,
) -> pd.DataFrame:
    """
    Build the final RiskPilot human-review queue.

    Policy
    ------

    Stage 1:
        Only transactions with risk_probability >=
        MIN_REVIEW_RISK are eligible.

    Stage 2:
        Transactions with risk_probability >=
        CRITICAL_RISK_THRESHOLD receive protected priority.

    Stage 3:
        Remaining capacity is allocated according to
        economic review value.

    Stage 4:
        If capacity remains, highest-risk transactions
        are selected as fallback.

    The final queue never exceeds REVIEW_CAPACITY.
    """

    from src.decision_engine import (
        DEFAULT_MERCHANT_PROFILES,
        calculate_action_costs,
    )

    merchant_profile = (
        DEFAULT_MERCHANT_PROFILES[
            "E_COMMERCE"
        ]
    )

    # --------------------------------------------------------
    # Validate required columns
    # --------------------------------------------------------

    required_columns = {
        "transaction_id",
        "risk_probability",
        "amount",
    }

    missing_columns = (
        required_columns
        - set(test_results.columns)
    )

    if missing_columns:
        raise ValueError(
            "Missing required columns: "
            + ", ".join(
                sorted(missing_columns)
            )
        )

    # --------------------------------------------------------
    # Stage 1 — Risk eligibility
    # --------------------------------------------------------

    risk_candidates = test_results[
        test_results["risk_probability"]
        >= MIN_REVIEW_RISK
    ].copy()

    print(
        "\nRisk candidates above review threshold:",
        len(risk_candidates),
    )

    print(
        "Minimum review risk threshold:",
        f"{MIN_REVIEW_RISK:.0%}",
    )

    print(
        "Critical risk threshold:",
        f"{CRITICAL_RISK_THRESHOLD:.0%}",
    )

    if risk_candidates.empty:
        raise ValueError(
            "No transactions meet MIN_REVIEW_RISK."
        )

    # --------------------------------------------------------
    # Stage 2 — Calculate economic costs
    #
    # Calculate these for ALL eligible candidates so that
    # even fallback transactions have complete information.
    # --------------------------------------------------------

    cost_records = []

    for _, row in risk_candidates.iterrows():

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
        index=risk_candidates.index,
    )

    risk_candidates[
        "approve_cost"
    ] = costs_df["APPROVE"]

    risk_candidates[
        "review_cost"
    ] = costs_df["REVIEW"]

    risk_candidates[
        "block_cost"
    ] = costs_df["BLOCK"]

    # --------------------------------------------------------
    # Best automatic alternative
    # --------------------------------------------------------

    risk_candidates[
        "best_automatic_cost"
    ] = (
        risk_candidates[
            [
                "approve_cost",
                "block_cost",
            ]
        ]
        .min(axis=1)
    )

    # --------------------------------------------------------
    # Economic value of human review
    # --------------------------------------------------------

    risk_candidates[
        "review_value"
    ] = (
        risk_candidates[
            "best_automatic_cost"
        ]
        -
        risk_candidates[
            "review_cost"
        ]
    )

    # --------------------------------------------------------
    # Best automatic action
    # --------------------------------------------------------

    risk_candidates[
        "best_automatic_action"
    ] = (
        risk_candidates[
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
    # Simple economic exposure score
    # --------------------------------------------------------

    risk_candidates[
        "review_priority"
    ] = (
        risk_candidates[
            "risk_probability"
        ]
        *
        risk_candidates[
            "amount"
        ]
    )

    # --------------------------------------------------------
    # Human-readable explanation
    # --------------------------------------------------------

    risk_candidates[
        "review_reason"
    ] = risk_candidates.apply(
        lambda row: (
            "High-risk transaction selected for human review. "
            f"Risk probability: "
            f"{row['risk_probability']:.2%}. "
            f"Estimated economic review value: "
            f"₹{row['review_value']:,.2f}."
        ),
        axis=1,
    )

    # --------------------------------------------------------
    # Stage 3 — Protect critical-risk transactions
    # --------------------------------------------------------

    critical_candidates = (
        risk_candidates[
            risk_candidates[
                "risk_probability"
            ]
            >= CRITICAL_RISK_THRESHOLD
        ]
        .sort_values(
            [
                "risk_probability",
                "review_value",
            ],
            ascending=[
                False,
                False,
            ],
        )
        .head(
            REVIEW_CAPACITY
        )
        .copy()
    )

    selected_ids = set(
        critical_candidates[
            "transaction_id"
        ]
    )

    remaining_capacity = (
        REVIEW_CAPACITY
        - len(critical_candidates)
    )

    print(
        "Critical-risk candidates:",
        len(critical_candidates),
    )

    print(
        "Capacity remaining after critical-risk "
        "protection:",
        remaining_capacity,
    )

    # --------------------------------------------------------
    # If critical-risk candidates fill capacity
    # --------------------------------------------------------

    if remaining_capacity <= 0:

        final_queue = (
            critical_candidates
            .sort_values(
                [
                    "risk_probability",
                    "review_value",
                ],
                ascending=[
                    False,
                    False,
                ],
            )
            .head(
                REVIEW_CAPACITY
            )
            .copy()
        )

    else:

        # ----------------------------------------------------
        # Stage 4 — Economic prioritization
        # ----------------------------------------------------

        remaining_candidates = (
            risk_candidates[
                ~risk_candidates[
                    "transaction_id"
                ].isin(
                    selected_ids
                )
            ]
            .copy()
        )

        economic_candidates = (
            remaining_candidates[
                remaining_candidates[
                    "review_value"
                ] > 0
            ]
            .sort_values(
                [
                    "review_value",
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
            economic_candidates[
                "transaction_id"
            ]
        )

        remaining_capacity = (
            remaining_capacity
            -
            len(economic_candidates)
        )

        # ----------------------------------------------------
        # Stage 5 — Highest-risk fallback
        # ----------------------------------------------------

        fallback_candidates = (
            remaining_candidates[
                ~remaining_candidates[
                    "transaction_id"
                ].isin(
                    selected_ids
                )
            ]
            .sort_values(
                "risk_probability",
                ascending=False,
            )
            .head(
                remaining_capacity
            )
            .copy()
        )

        fallback_candidates[
            "review_reason"
        ] = fallback_candidates.apply(
            lambda row: (
                "High-risk fallback selected because "
                "human-review capacity remained available. "
                f"Risk probability: "
                f"{row['risk_probability']:.2%}. "
                f"Economic review value: "
                f"₹{row['review_value']:,.2f}."
            ),
            axis=1,
        )

        final_queue = pd.concat(
            [
                critical_candidates,
                economic_candidates,
                fallback_candidates,
            ],
            ignore_index=True,
        )

    # --------------------------------------------------------
    # Final safety check
    # --------------------------------------------------------

    final_queue = (
        final_queue
        .sort_values(
            [
                "risk_probability",
                "review_value",
            ],
            ascending=[
                False,
                False,
            ],
        )
        .head(
            REVIEW_CAPACITY
        )
        .reset_index(
            drop=True
        )
    )

    # --------------------------------------------------------
    # Recreate review rank
    # --------------------------------------------------------

    final_queue.insert(
        0,
        "review_rank",
        range(
            1,
            len(final_queue) + 1,
        ),
    )

    # --------------------------------------------------------
    # Verify ground-truth labels are preserved
    # --------------------------------------------------------

    if "isFraud" not in final_queue.columns:
        final_queue = final_queue.merge(
            test_results[
                [
                    "transaction_id",
                    "isFraud",
                ]
            ],
            on="transaction_id",
            how="left",
        )

    if final_queue["isFraud"].isna().any():
        raise ValueError(
            "RiskPilot queue contains missing isFraud labels."
        )

    return final_queue


# ============================================================
# Save Review Queue
# ============================================================

def save_review_queue(
    riskpilot_queue: pd.DataFrame,
) -> Path:
    """
    Save the final RiskPilot human-review queue.
    """

    queue_path = (
        PROJECT_ROOT
        / "artifacts"
        / "riskpilot_review_queue.csv"
    )

    queue_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    # utf-8-sig ensures the ₹ symbol displays correctly
    # in Excel and Windows applications.
    riskpilot_queue.to_csv(
        queue_path,
        index=False,
        encoding="utf-8-sig",
    )

    return queue_path


# ============================================================
# Main Experiment
# ============================================================

def main():

    print("\n")
    print("=" * 60)
    print("RISK PILOT REPRODUCIBLE EXPERIMENT")
    print("=" * 60)

    # --------------------------------------------------------
    # Step 1 — Recreate modeling dataset
    # --------------------------------------------------------

    df_model = (
        create_modeling_dataset()
    )

    # --------------------------------------------------------
    # Step 2 — Feature engineering
    # --------------------------------------------------------

    df_model = engineer_features(
        df_model
    )

    # --------------------------------------------------------
    # Step 3 — Chronological test set
    # --------------------------------------------------------

    test_df = create_test_set(
        df_model
    )

    # --------------------------------------------------------
    # Step 4 — Generate real ML predictions
    # --------------------------------------------------------

    print(
        "\nGenerating fraud probabilities..."
    )

    test_results = (
        score_test_transactions(
            test_df
        )
    )

    print(
        "Scored transactions:",
        len(test_results),
    )

    print(
        "Fraud transactions:",
        int(
            test_results[
                "isFraud"
            ].sum()
        ),
    )

    print(
        "Non-fraud transactions:",
        int(
            (
                test_results[
                    "isFraud"
                ]
                == 0
            ).sum()
        ),
    )

    # --------------------------------------------------------
    # Step 5 — Build RiskPilot queue
    # --------------------------------------------------------

    riskpilot_queue = (
        build_riskpilot_queue(
            test_results
        )
    )

    print(
        "\nRiskPilot review queue size:",
        len(riskpilot_queue),
    )

    print(
        "Human review capacity:",
        REVIEW_CAPACITY,
    )

    # --------------------------------------------------------
    # Verify capacity
    # --------------------------------------------------------

    if len(riskpilot_queue) > REVIEW_CAPACITY:
        raise ValueError(
            "RiskPilot review queue exceeds human review capacity."
        )

    # --------------------------------------------------------
    # Verify no missing fraud labels
    # --------------------------------------------------------

    if riskpilot_queue[
        "isFraud"
    ].isna().any():
        raise ValueError(
            "RiskPilot review queue contains missing fraud labels."
        )

    # --------------------------------------------------------
    # Display top candidates
    # --------------------------------------------------------

    print(
        "\nTop RiskPilot review candidates:"
    )

    display_columns = [
        "review_rank",
        "transaction_id",
        "risk_probability",
        "amount",
        "review_value",
        "isFraud",
    ]

    available_display_columns = [
        column
        for column in display_columns
        if column in riskpilot_queue.columns
    ]

    print(
        riskpilot_queue[
            available_display_columns
        ]
        .head(10)
        .to_string(
            index=False
        )
    )

    # --------------------------------------------------------
    # Step 6 — Compare strategies
    # --------------------------------------------------------

    print(
        "\nComparing review strategies..."
    )

    # Make absolutely sure the queue uses the labels
    # from the same test_results dataframe used for
    # Strategy A.
    riskpilot_queue = (
        riskpilot_queue
        .drop(
            columns=["isFraud"],
            errors="ignore",
        )
        .merge(
            test_results[
                [
                    "transaction_id",
                    "isFraud",
                ]
            ],
            on="transaction_id",
            how="left",
        )
    )

    if riskpilot_queue[
        "isFraud"
    ].isna().any():
        raise ValueError(
            "Failed to attach ground-truth fraud labels "
            "to RiskPilot review queue."
        )

    results = compare_strategies(
        transactions=test_results,
        riskpilot_queue=riskpilot_queue,
        review_capacity=REVIEW_CAPACITY,
    )

    # --------------------------------------------------------
    # Add experiment configuration
    # --------------------------------------------------------

    results[
        "experiment_configuration"
    ] = {
        "minimum_review_risk": MIN_REVIEW_RISK,
        "critical_risk_threshold": (
            CRITICAL_RISK_THRESHOLD
        ),
        "review_capacity": REVIEW_CAPACITY,
        "legitimate_sample_fraction": (
            LEGITIMATE_SAMPLE_FRACTION
        ),
        "random_state": RANDOM_STATE,
        "validation_end_step": VALIDATION_END,
    }

    # --------------------------------------------------------
    # Step 7 — Save strategy comparison
    # --------------------------------------------------------

    output_path = (
        PROJECT_ROOT
        / "artifacts"
        / "strategy_comparison.json"
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    save_evaluation_results(
        results,
        output_path=output_path,
    )

    # --------------------------------------------------------
    # Step 8 — Print comparison
    # --------------------------------------------------------

    print_strategy_comparison(
        results
    )

    print(
        "\nEvaluation results saved to:"
    )

    print(
        output_path
    )

    # --------------------------------------------------------
    # Step 9 — Save review queue
    # --------------------------------------------------------

    queue_path = save_review_queue(
        riskpilot_queue
    )

    print(
        "\nRiskPilot review queue saved to:"
    )

    print(
        queue_path
    )

    # --------------------------------------------------------
    # Step 10 — Final summary
    # --------------------------------------------------------

    print("\n")
    print("=" * 60)
    print("EXPERIMENT COMPLETED SUCCESSFULLY")
    print("=" * 60)

    print(
        "Test transactions:",
        len(test_results),
    )

    print(
        "Fraud transactions:",
        int(
            test_results[
                "isFraud"
            ].sum()
        ),
    )

    print(
        "Review capacity:",
        REVIEW_CAPACITY,
    )

    print(
        "Minimum review risk:",
        f"{MIN_REVIEW_RISK:.0%}",
    )

    print(
        "Critical risk threshold:",
        f"{CRITICAL_RISK_THRESHOLD:.0%}",
    )

    print(
        "RiskPilot transactions selected:",
        len(riskpilot_queue),
    )


# ============================================================
# Entry Point
# ============================================================

if __name__ == "__main__":
    main()