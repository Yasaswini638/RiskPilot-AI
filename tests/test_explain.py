from src.explain import explain_decision


def test_explanation_returns_dictionary():

    explanation = explain_decision(
        risk_probability=0.35,
        amount=5000,
        action="REVIEW",
        costs={
            "APPROVE": 1750.0,
            "REVIEW": 23.0,
            "BLOCK": 260.0,
        },
        transaction={
            "type": "TRANSFER",
            "oldbalanceOrg": 7500,
            "oldbalanceDest": 1000,
        },
    )

    assert isinstance(
        explanation,
        dict,
    )


def test_explanation_contains_required_fields():

    explanation = explain_decision(
        risk_probability=0.35,
        amount=5000,
        action="REVIEW",
        costs={
            "APPROVE": 1750.0,
            "REVIEW": 23.0,
            "BLOCK": 260.0,
        },
        transaction={
            "type": "TRANSFER",
            "oldbalanceOrg": 7500,
            "oldbalanceDest": 1000,
        },
    )

    required_fields = {
        "risk_level",
        "risk_probability",
        "decision",
        "expected_costs",
        "reasons",
        "transaction_context",
    }

    assert required_fields.issubset(
        explanation.keys()
    )


def test_medium_risk_is_classified_correctly():

    explanation = explain_decision(
        risk_probability=0.35,
        amount=5000,
        action="REVIEW",
        costs={
            "APPROVE": 1750.0,
            "REVIEW": 23.0,
            "BLOCK": 260.0,
        },
        transaction={
            "type": "TRANSFER",
            "oldbalanceOrg": 7500,
            "oldbalanceDest": 1000,
        },
    )

    assert (
        explanation["risk_level"]
        == "MEDIUM"
    )


def test_explanation_preserves_decision():

    explanation = explain_decision(
        risk_probability=0.35,
        amount=5000,
        action="REVIEW",
        costs={
            "APPROVE": 1750.0,
            "REVIEW": 23.0,
            "BLOCK": 260.0,
        },
        transaction={
            "type": "TRANSFER",
            "oldbalanceOrg": 7500,
            "oldbalanceDest": 1000,
        },
    )

    assert (
        explanation["decision"]
        == "REVIEW"
    )


def test_explanation_contains_reasons():

    explanation = explain_decision(
        risk_probability=0.35,
        amount=5000,
        action="REVIEW",
        costs={
            "APPROVE": 1750.0,
            "REVIEW": 23.0,
            "BLOCK": 260.0,
        },
        transaction={
            "type": "TRANSFER",
            "oldbalanceOrg": 7500,
            "oldbalanceDest": 1000,
        },
    )

    assert isinstance(
        explanation["reasons"],
        list,
    )

    assert len(
        explanation["reasons"]
    ) > 0


def test_transaction_context_is_present():

    explanation = explain_decision(
        risk_probability=0.35,
        amount=5000,
        action="REVIEW",
        costs={
            "APPROVE": 1750.0,
            "REVIEW": 23.0,
            "BLOCK": 260.0,
        },
        transaction={
            "type": "TRANSFER",
            "oldbalanceOrg": 7500,
            "oldbalanceDest": 1000,
        },
    )

    context = explanation[
        "transaction_context"
    ]

    assert context["amount"] == 5000
    assert context["type"] == "TRANSFER"
    assert context["origin_balance"] == 7500
    assert context["destination_balance"] == 1000