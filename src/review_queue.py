import pandas as pd


def calculate_review_priority(
    risk_probability: float,
    amount: float
) -> float:
    """
    Calculate the economic priority of a transaction
    for human review.

    Priority is based on:

        risk_probability × transaction amount

    This represents the estimated fraud exposure
    associated with the transaction.
    """

    return float(
        risk_probability * amount
    )


def build_review_queue(
    transactions: pd.DataFrame,
    review_capacity: int = 50,
) -> pd.DataFrame:
    """
    Select the highest-priority transactions for human review.

    Required columns:
        transaction_id
        risk_probability
        amount

    Parameters:
        transactions:
            DataFrame containing scored transactions.

        review_capacity:
            Maximum number of transactions that humans
            can review.

    Returns:
        DataFrame containing the selected transactions,
        sorted by review priority.
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
            + ", ".join(sorted(missing_columns))
        )

    queue = transactions.copy()

    # --------------------------------------------------------
    # Calculate economic review priority
    # --------------------------------------------------------

    queue["review_priority"] = (
        queue["risk_probability"]
        * queue["amount"]
    )

    # --------------------------------------------------------
    # Highest economic exposure first
    # --------------------------------------------------------

    queue = queue.sort_values(
        "review_priority",
        ascending=False
    )

    # --------------------------------------------------------
    # Respect human review capacity
    # --------------------------------------------------------

    queue = queue.head(
        min(
            review_capacity,
            len(queue)
        )
    ).copy()

    # --------------------------------------------------------
    # Add queue position
    # --------------------------------------------------------

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


def explain_review_priority(
    risk_probability: float,
    amount: float,
    review_priority: float,
) -> str:
    """
    Generate a human-readable explanation
    for why a transaction has review priority.
    """

    return (
        f"Risk probability is "
        f"{risk_probability:.2%} and transaction value is "
        f"₹{amount:,.2f}, producing an estimated "
        f"economic exposure of "
        f"₹{review_priority:,.2f}."
    )


def build_economic_review_queue(
    transactions: pd.DataFrame,
    merchant_profile: dict,
    review_capacity: int = 50,
) -> pd.DataFrame:
    """
    Build a review queue using RiskPilot's economic model.

    Transactions are prioritized according to the
    expected economic benefit of human review rather
    than raw fraud probability.

    Required columns:
        transaction_id
        risk_probability
        amount

    Parameters:
        transactions:
            DataFrame containing scored transactions.

        merchant_profile:
            Merchant-specific cost assumptions used by
            the RiskPilot decision engine.

        review_capacity:
            Maximum number of transactions that humans
            can review.

    Returns:
        DataFrame containing economically valuable
        transactions selected for human review.
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
            + ", ".join(sorted(missing_columns))
        )

    from src.decision_engine import calculate_action_costs

    queue = transactions.copy()

    # --------------------------------------------------------
    # Calculate expected cost of each possible action
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

        cost_records.append(costs)

    costs_df = pd.DataFrame(
        cost_records,
        index=queue.index
    )

    queue["approve_cost"] = costs_df[
        "APPROVE"
    ]

    queue["review_cost"] = costs_df[
        "REVIEW"
    ]

    queue["block_cost"] = costs_df[
        "BLOCK"
    ]

    # --------------------------------------------------------
    # Find the cheapest automatic alternative
    #
    # Human review is compared against APPROVE and BLOCK.
    # --------------------------------------------------------

    queue["best_automatic_cost"] = queue[
        [
            "approve_cost",
            "block_cost"
        ]
    ].min(axis=1)

    # --------------------------------------------------------
    # Calculate economic value of human review
    #
    # Positive value means review is cheaper than the
    # best automatic alternative.
    # --------------------------------------------------------

    queue["review_value"] = (
        queue["best_automatic_cost"]
        - queue["review_cost"]
    )

    # --------------------------------------------------------
    # Identify the best automatic alternative
    # --------------------------------------------------------

    queue["best_automatic_action"] = queue[
        [
            "approve_cost",
            "block_cost"
        ]
    ].idxmin(axis=1)

    queue["best_automatic_action"] = (
        queue["best_automatic_action"]
        .map({
            "approve_cost": "APPROVE",
            "block_cost": "BLOCK"
        })
    )

    # --------------------------------------------------------
    # Generate human-readable review explanation
    # --------------------------------------------------------

    queue["review_reason"] = queue.apply(
        lambda row: (
            f"Human review could reduce expected cost by "
            f"₹{row['review_value']:,.2f} compared with "
            f"the best automatic action "
            f"({row['best_automatic_action']})."
        ),
        axis=1
    )

    # --------------------------------------------------------
    # Keep only transactions where human review
    # provides positive economic value
    # --------------------------------------------------------

    queue = queue[
        queue["review_value"] > 0
    ].copy()

    # --------------------------------------------------------
    # Highest economic value first
    # --------------------------------------------------------

    queue = queue.sort_values(
        "review_value",
        ascending=False
    )

    # --------------------------------------------------------
    # Respect human review capacity
    # --------------------------------------------------------

    queue = queue.head(
        min(
            review_capacity,
            len(queue)
        )
    ).copy()

    # --------------------------------------------------------
    # Add review queue position
    # --------------------------------------------------------

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