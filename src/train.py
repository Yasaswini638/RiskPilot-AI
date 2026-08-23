from pathlib import Path
import json

import joblib
import pandas as pd

from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    average_precision_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)

from src.features import engineer_features, FEATURE_COLUMNS


# ============================================================
# RiskPilot — Reproducible Training Pipeline
# ============================================================

RANDOM_STATE = 42

DATA_PATH = Path(
    "data/raw/paysim/PS_20174392719_1491204439457_log.csv"
)

MODEL_PATH = Path(
    "models/riskpilot_model.joblib"
)

METRICS_PATH = Path(
    "artifacts/metrics.json"
)

CHUNK_SIZE = 200_000

# Same sampling methodology used in Steps 1–50
LEGITIMATE_SAMPLE_FRACTION = 0.015

# Same chronological split used in Steps 1–50
TRAIN_END = 520
VALIDATION_END = 630


def load_modeling_data():
    """
    Read PaySim in chunks and reproduce the modeling dataset
    used in the original notebook experiment.

    All fraud transactions are retained.

    Approximately 1.5% of legitimate transactions are sampled
    from each chunk to keep the modeling dataset manageable.
    """

    fraud_parts = []
    legitimate_parts = []

    print("=" * 60)
    print("RiskPilot reproducible data preparation")
    print("=" * 60)

    print("Dataset:", DATA_PATH.resolve())
    print("Dataset exists:", DATA_PATH.exists())

    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Dataset not found: {DATA_PATH.resolve()}"
        )

    for chunk_number, chunk in enumerate(
        pd.read_csv(
            DATA_PATH,
            chunksize=CHUNK_SIZE
        ),
        start=1
    ):

        fraud_chunk = chunk[
            chunk["isFraud"] == 1
        ]

        legitimate_chunk = chunk[
            chunk["isFraud"] == 0
        ]

        legitimate_sample = legitimate_chunk.sample(
            frac=LEGITIMATE_SAMPLE_FRACTION,
            random_state=RANDOM_STATE
        )

        fraud_parts.append(fraud_chunk)
        legitimate_parts.append(
            legitimate_sample
        )

        print(
            f"Processed chunk {chunk_number}: "
            f"{len(chunk):,} rows"
        )

    df_model = pd.concat(
        fraud_parts + legitimate_parts,
        ignore_index=True
    )

    print("\nModeling dataset shape:")
    print(df_model.shape)

    print("\nFraud distribution:")
    print(
        df_model["isFraud"].value_counts()
    )

    return df_model


def prepare_datasets(df_model):
    """
    Apply the same feature engineering and chronological
    train/validation/test split used in the prototype.
    """

    # --------------------------------------------------------
    # Feature engineering
    # --------------------------------------------------------

    engineered = engineer_features(
        df_model
    )

    # Keep target separately
    y = df_model["isFraud"].copy()

    # Recombine the engineered features with metadata
    # required for chronological splitting.
    engineered["step"] = df_model["step"].values

    engineered["isFraud"] = y.values

    # --------------------------------------------------------
    # Chronological sorting
    # --------------------------------------------------------

    engineered = engineered.sort_values(
        "step"
    ).reset_index(drop=True)

    print("\nChronological range:")
    print(
        "Minimum step:",
        engineered["step"].min()
    )

    print(
        "Maximum step:",
        engineered["step"].max()
    )

    # --------------------------------------------------------
    # Chronological split
    # --------------------------------------------------------

    train_df = engineered[
        engineered["step"] <= TRAIN_END
    ].copy()

    validation_df = engineered[
        (engineered["step"] > TRAIN_END)
        &
        (engineered["step"] <= VALIDATION_END)
    ].copy()

    test_df = engineered[
        engineered["step"] > VALIDATION_END
    ].copy()

    print("\nDataset split:")
    print(
        "Training:",
        train_df.shape
    )

    print(
        "Validation:",
        validation_df.shape
    )

    print(
        "Test:",
        test_df.shape
    )

    print("\nStep ranges:")

    print(
        "Training:",
        train_df["step"].min(),
        "to",
        train_df["step"].max()
    )

    print(
        "Validation:",
        validation_df["step"].min(),
        "to",
        validation_df["step"].max()
    )

    print(
        "Test:",
        test_df["step"].min(),
        "to",
        test_df["step"].max()
    )

    # --------------------------------------------------------
    # Create ML datasets
    # --------------------------------------------------------

    X_train = train_df[FEATURE_COLUMNS]
    y_train = train_df["isFraud"]

    X_validation = validation_df[FEATURE_COLUMNS]
    y_validation = validation_df["isFraud"]

    X_test = test_df[FEATURE_COLUMNS]
    y_test = test_df["isFraud"]

    print("\nML dataset shapes:")

    print(
        "X_train:",
        X_train.shape
    )

    print(
        "y_train:",
        y_train.shape
    )

    print(
        "X_validation:",
        X_validation.shape
    )

    print(
        "y_validation:",
        y_validation.shape
    )

    print(
        "X_test:",
        X_test.shape
    )

    print(
        "y_test:",
        y_test.shape
    )

    return (
        X_train,
        y_train,
        X_validation,
        y_validation,
        X_test,
        y_test,
    )


def train_model(X_train, y_train):
    """
    Train the RiskPilot Random Forest model using the same
    configuration used in the original prototype.
    """

    print("\n" + "=" * 60)
    print("Training Random Forest")
    print("=" * 60)

    model = RandomForestClassifier(
        n_estimators=200,
        max_depth=12,
        min_samples_leaf=5,
        class_weight="balanced",
        random_state=RANDOM_STATE,
        n_jobs=-1
    )

    model.fit(
        X_train,
        y_train
    )

    print("Training completed.")

    return model


def evaluate_model(
    model,
    X_validation,
    y_validation,
    X_test,
    y_test
):
    """
    Evaluate the model on validation and untouched test data.
    """

    print("\n" + "=" * 60)
    print("Model evaluation")
    print("=" * 60)

    # --------------------------------------------------------
    # Validation evaluation
    # --------------------------------------------------------

    validation_probabilities = (
        model.predict_proba(
            X_validation
        )[:, 1]
    )

    validation_predictions = (
        validation_probabilities >= 0.50
    ).astype(int)

    # --------------------------------------------------------
    # Test evaluation
    # --------------------------------------------------------

    test_probabilities = (
        model.predict_proba(
            X_test
        )[:, 1]
    )

    test_predictions = (
        test_probabilities >= 0.50
    ).astype(int)

    # --------------------------------------------------------
    # Calculate metrics
    # --------------------------------------------------------

    test_metrics = {
        "precision": float(
            precision_score(
                y_test,
                test_predictions,
                zero_division=0
            )
        ),

        "recall": float(
            recall_score(
                y_test,
                test_predictions,
                zero_division=0
            )
        ),

        "f1": float(
            f1_score(
                y_test,
                test_predictions,
                zero_division=0
            )
        ),

        "roc_auc": float(
            roc_auc_score(
                y_test,
                test_probabilities
            )
        ),

        "pr_auc": float(
            average_precision_score(
                y_test,
                test_probabilities
            )
        ),

        "test_samples": int(
            len(y_test)
        ),

        "fraud_samples": int(
            y_test.sum()
        ),

        "non_fraud_samples": int(
            (y_test == 0).sum()
        ),

        "threshold": 0.50,
    }

    print("\nValidation confusion matrix:")
    print(
        confusion_matrix(
            y_validation,
            validation_predictions
        )
    )

    print("\nTest confusion matrix:")
    print(
        confusion_matrix(
            y_test,
            test_predictions
        )
    )

    print("\nTest classification report:")
    print(
        classification_report(
            y_test,
            test_predictions,
            digits=4,
            zero_division=0
        )
    )

    print("\nTest metrics:")

    for name, value in test_metrics.items():
        print(
            f"{name}: {value}"
        )

    return test_metrics


def save_model(model):
    """
    Save the trained model for production inference.
    """

    MODEL_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    joblib.dump(
        model,
        MODEL_PATH
    )

    print(
        "\nModel saved to:",
        MODEL_PATH.resolve()
    )


def save_metrics(metrics):
    """
    Save evaluation metrics as JSON.
    """

    METRICS_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        METRICS_PATH,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            metrics,
            file,
            indent=4
        )

    print(
        "Metrics saved to:",
        METRICS_PATH.resolve()
    )


def main():

    # 1. Load and sample dataset
    df_model = load_modeling_data()

    # 2. Feature engineering + chronological split
    (
        X_train,
        y_train,
        X_validation,
        y_validation,
        X_test,
        y_test,
    ) = prepare_datasets(
        df_model
    )

    # 3. Train model
    model = train_model(
        X_train,
        y_train
    )

    # 4. Evaluate model
    metrics = evaluate_model(
        model,
        X_validation,
        y_validation,
        X_test,
        y_test
    )

    # 5. Save model
    save_model(
        model
    )

    # 6. Save evaluation metrics
    save_metrics(
        metrics
    )

    print("\n" + "=" * 60)
    print("RiskPilot training pipeline completed successfully.")
    print("=" * 60)


if __name__ == "__main__":
    main()