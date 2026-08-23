from src.decision_engine import (
    calculate_action_costs,
    riskpilot_decision,
    DEFAULT_MERCHANT_PROFILES,
)


def test_action_costs_are_positive():
    profile = DEFAULT_MERCHANT_PROFILES["E_COMMERCE"]

    costs = calculate_action_costs(
        risk_probability=0.35,
        amount=5000,
        fraud_loss_rate=profile["fraud_loss_rate"],
        false_positive_rate=profile["false_positive_rate"],
        review_fixed_cost=profile["review_fixed_cost"],
        review_percentage=profile["review_percentage"],
    )

    assert costs["APPROVE"] > 0
    assert costs["REVIEW"] > 0
    assert costs["BLOCK"] > 0


def test_low_risk_transaction_is_approved():
    profile = DEFAULT_MERCHANT_PROFILES["E_COMMERCE"]

    action, costs = riskpilot_decision(
        risk_probability=0.005,
        amount=500,
        merchant_profile=profile,
    )

    assert action == "APPROVE"
    assert costs[action] == min(costs.values())


def test_medium_risk_transaction_is_reviewed():
    profile = DEFAULT_MERCHANT_PROFILES["E_COMMERCE"]

    action, costs = riskpilot_decision(
        risk_probability=0.35,
        amount=5000,
        merchant_profile=profile,
    )

    assert action == "REVIEW"
    assert costs[action] == min(costs.values())


def test_decision_always_matches_minimum_cost():
    profile = DEFAULT_MERCHANT_PROFILES["E_COMMERCE"]

    test_cases = [
        (0.01, 1000),
        (0.20, 5000),
        (0.50, 10000),
        (0.90, 10000),
    ]

    for risk_probability, amount in test_cases:

        action, costs = riskpilot_decision(
            risk_probability=risk_probability,
            amount=amount,
            merchant_profile=profile,
        )

        assert action in {
            "APPROVE",
            "REVIEW",
            "BLOCK",
        }

        assert costs[action] == min(
            costs.values()
        )