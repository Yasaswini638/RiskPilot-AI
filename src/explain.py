def explain_decision(
    risk_probability: float,
    amount: float,
    action: str,
    costs: dict,
    transaction: dict,
) -> dict:
    """
    Generate a human-readable explanation for a RiskPilot decision.

    This explanation separates:
    1. Model risk signal
    2. Economic decision reasoning
    3. Transaction-level context
    """

    reasons = []

    # --------------------------------------------------------
    # Risk interpretation
    # --------------------------------------------------------

    if risk_probability < 0.10:
        risk_level = "LOW"

        reasons.append(
            "The model estimates relatively low fraud risk."
        )

    elif risk_probability < 0.50:
        risk_level = "MEDIUM"

        reasons.append(
            "The model estimates moderate fraud risk."
        )

    elif risk_probability < 0.80:
        risk_level = "HIGH"

        reasons.append(
            "The model estimates elevated fraud risk."
        )

    else:
        risk_level = "VERY_HIGH"

        reasons.append(
            "The model estimates very high fraud risk."
        )

    # --------------------------------------------------------
    # Economic reasoning
    # --------------------------------------------------------

    if action == "APPROVE":

        reasons.append(
            "Approving the transaction has the lowest "
            "expected economic cost."
        )

    elif action == "REVIEW":

        reasons.append(
            "Manual review has the lowest expected "
            "economic cost."
        )

    elif action == "BLOCK":

        reasons.append(
            "Blocking the transaction has the lowest "
            "expected economic cost."
        )

    # --------------------------------------------------------
    # Compare costs
    # --------------------------------------------------------

    lowest_cost = min(costs.values())

    if costs["APPROVE"] == lowest_cost:

        reasons.append(
            "Expected fraud loss from approval is lower "
            "than the available alternatives."
        )

    elif costs["REVIEW"] == lowest_cost:

        reasons.append(
            "The review cost is lower than the expected "
            "cost of approving or blocking."
        )

    elif costs["BLOCK"] == lowest_cost:

        reasons.append(
            "The expected cost of blocking is lower than "
            "the expected cost of approval or review."
        )

    # --------------------------------------------------------
    # Transaction context
    # --------------------------------------------------------

    transaction_context = {
        "amount": amount,
        "type": transaction.get("type"),
        "origin_balance": transaction.get(
            "oldbalanceOrg"
        ),
        "destination_balance": transaction.get(
            "oldbalanceDest"
        ),
    }

    return {
        "risk_level": risk_level,
        "risk_probability": risk_probability,
        "decision": action,
        "expected_costs": costs,
        "reasons": reasons,
        "transaction_context": transaction_context,
    }