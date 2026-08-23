from fastapi.testclient import TestClient

from backend.main import app


client = TestClient(app)


def sample_transaction():
    return {
        "step": 650,
        "type": "TRANSFER",
        "amount": 5000,
        "oldbalanceOrg": 7500,
        "oldbalanceDest": 1000,
    }


def test_api_health_endpoint():

    response = client.get("/health")

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, dict)


def test_prediction_endpoint_returns_success():

    response = client.post(
        "/predict",
        json=sample_transaction(),
    )

    assert response.status_code == 200


def test_prediction_contains_risk_probability():

    response = client.post(
        "/predict",
        json=sample_transaction(),
    )

    data = response.json()

    assert "risk_probability" in data

    assert (
        0.0
        <= data["risk_probability"]
        <= 1.0
    )


def test_prediction_contains_risk_level():

    response = client.post(
        "/predict",
        json=sample_transaction(),
    )

    data = response.json()

    assert "risk_level" in data

    assert data["risk_level"] in {
        "LOW",
        "MEDIUM",
        "HIGH",
        "CRITICAL",
    }


def test_prediction_contains_decision():

    response = client.post(
        "/predict",
        json=sample_transaction(),
    )

    data = response.json()

    assert "decision" in data

    assert data["decision"] in {
        "APPROVE",
        "REVIEW",
        "BLOCK",
    }


def test_prediction_contains_transaction():

    response = client.post(
        "/predict",
        json=sample_transaction(),
    )

    data = response.json()

    assert "transaction" in data

    assert (
        data["transaction"]["amount"]
        == 5000.0
    )


def test_prediction_contains_merchant():

    response = client.post(
        "/predict",
        json=sample_transaction(),
    )

    data = response.json()

    assert "merchant" in data

    assert data["merchant"] == "E_COMMERCE"


def test_prediction_rejects_invalid_amount():

    transaction = sample_transaction()

    transaction["amount"] = -5000

    response = client.post(
        "/predict",
        json=transaction,
    )

    assert response.status_code in {
        400,
        422,
    }


def test_prediction_rejects_missing_transaction_field():

    transaction = sample_transaction()

    del transaction["amount"]

    response = client.post(
        "/predict",
        json=transaction,
    )

    assert response.status_code in {
        400,
        422,
    }