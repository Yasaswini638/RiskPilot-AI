import pandas as pd

from src.features import engineer_features


def test_feature_engineering_returns_dataframe():

    transaction = pd.DataFrame([
        {
            "step": 600,
            "type": "TRANSFER",
            "amount": 50000,
            "oldbalanceOrg": 75000,
            "oldbalanceDest": 20000,
        }
    ])

    result = engineer_features(transaction)

    assert isinstance(result, pd.DataFrame)


def test_feature_engineering_preserves_numeric_features():

    transaction = pd.DataFrame([
        {
            "step": 600,
            "type": "TRANSFER",
            "amount": 50000,
            "oldbalanceOrg": 75000,
            "oldbalanceDest": 20000,
        }
    ])

    result = engineer_features(transaction)

    assert result.loc[0, "step"] == 600
    assert result.loc[0, "amount"] == 50000
    assert result.loc[0, "oldbalanceOrg"] == 75000
    assert result.loc[0, "oldbalanceDest"] == 20000


def test_transfer_encoding_is_created():

    transaction = pd.DataFrame([
        {
            "step": 600,
            "type": "TRANSFER",
            "amount": 50000,
            "oldbalanceOrg": 75000,
            "oldbalanceDest": 20000,
        }
    ])

    result = engineer_features(transaction)

    assert "type_TRANSFER" in result.columns
    assert result.loc[0, "type_TRANSFER"] == 1


def test_feature_values_are_numeric():

    transaction = pd.DataFrame([
        {
            "step": 600,
            "type": "TRANSFER",
            "amount": 50000,
            "oldbalanceOrg": 75000,
            "oldbalanceDest": 20000,
        }
    ])

    result = engineer_features(transaction)

    assert all(
        pd.api.types.is_numeric_dtype(
            result[column]
        )
        for column in result.columns
    )