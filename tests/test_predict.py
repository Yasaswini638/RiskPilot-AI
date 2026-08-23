import pandas as pd

from src.predict import RiskPilotPredictor


def sample_transaction():
    return pd.DataFrame([
        {
            "step": 650,
            "type": "TRANSFER",
            "amount": 5000,
            "oldbalanceOrg": 7500,
            "oldbalanceDest": 1000,
        }
    ])


def test_predictor_loads_model():

    predictor = RiskPilotPredictor()

    assert predictor.model is not None


def test_prediction_is_probability():

    predictor = RiskPilotPredictor()

    transaction = sample_transaction()

    probability = predictor.predict_probability(
        transaction
    )

    assert isinstance(
        probability,
        float
    )

    assert 0.0 <= probability <= 1.0


def test_prediction_is_deterministic():

    predictor = RiskPilotPredictor()

    transaction = sample_transaction()

    probability_1 = (
        predictor.predict_probability(
            transaction
        )
    )

    probability_2 = (
        predictor.predict_probability(
            transaction
        )
    )

    assert probability_1 == probability_2


def test_prediction_changes_with_transaction():

    predictor = RiskPilotPredictor()

    transaction_1 = sample_transaction()

    transaction_2 = pd.DataFrame([
        {
            "step": 650,
            "type": "TRANSFER",
            "amount": 500000,
            "oldbalanceOrg": 500000,
            "oldbalanceDest": 1000,
        }
    ])

    probability_1 = (
        predictor.predict_probability(
            transaction_1
        )
    )

    probability_2 = (
        predictor.predict_probability(
            transaction_2
        )
    )

    assert (
        probability_1 != probability_2
    )