import pandas as pd


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


TRANSACTION_TYPES = [
    "CASH_IN",
    "CASH_OUT",
    "DEBIT",
    "PAYMENT",
    "TRANSFER",
]


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert raw PaySim-style transaction data into
    the exact feature representation expected by RiskPilot.

    This function must remain consistent between
    model training and production prediction.
    """

    data = df.copy()

    # Engineered balance-ratio features
    data["amount_to_origin_balance"] = (
        data["amount"] /
        (data["oldbalanceOrg"] + 1)
    )

    data["amount_to_destination_balance"] = (
        data["amount"] /
        (data["oldbalanceDest"] + 1)
    )

    # One-hot encode transaction type
    data = pd.get_dummies(
        data,
        columns=["type"],
        prefix="type",
        dtype=int
    )

    # Guarantee that every expected transaction-type
    # column exists.
    for transaction_type in TRANSACTION_TYPES:

        column_name = f"type_{transaction_type}"

        if column_name not in data.columns:
            data[column_name] = 0

    # Return exactly the features used by the model
    return data[FEATURE_COLUMNS]