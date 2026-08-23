from typing import Dict, Tuple


DEFAULT_MERCHANT_PROFILES = {

    "SMALL_MERCHANT": {
        "fraud_loss_rate": 1.0,
        "false_positive_rate": 0.02,
        "review_fixed_cost": 5.0,
        "review_percentage": 0.005,
    },

    "E_COMMERCE": {
        "fraud_loss_rate": 1.0,
        "false_positive_rate": 0.08,
        "review_fixed_cost": 8.0,
        "review_percentage": 0.003,
    },

    "HIGH_VALUE_MERCHANT": {
        "fraud_loss_rate": 1.0,
        "false_positive_rate": 0.15,
        "review_fixed_cost": 10.0,
        "review_percentage": 0.002,
    },
}


def calculate_action_costs(
    risk_probability: float,
    amount: float,
    fraud_loss_rate: float,
    false_positive_rate: float,
    review_fixed_cost: float,
    review_percentage: float,
) -> Dict[str, float]:

    approve_cost = (
        risk_probability
        * amount
        * fraud_loss_rate
    )

    block_cost = (
        (1 - risk_probability)
        * amount
        * false_positive_rate
    )

    review_cost = (
        review_fixed_cost
        + amount * review_percentage
    )

    return {
        "APPROVE": approve_cost,
        "REVIEW": review_cost,
        "BLOCK": block_cost,
    }


def riskpilot_decision(
    risk_probability: float,
    amount: float,
    merchant_profile: Dict[str, float],
) -> Tuple[str, Dict[str, float]]:

    costs = calculate_action_costs(
        risk_probability=risk_probability,
        amount=amount,
        fraud_loss_rate=merchant_profile["fraud_loss_rate"],
        false_positive_rate=merchant_profile["false_positive_rate"],
        review_fixed_cost=merchant_profile["review_fixed_cost"],
        review_percentage=merchant_profile["review_percentage"],
    )

    recommended_action = min(
        costs,
        key=costs.get,
    )

    return recommended_action, costs