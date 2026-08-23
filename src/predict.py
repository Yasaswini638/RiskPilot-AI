from pathlib import Path

import joblib
import pandas as pd

from src.features import engineer_features


MODEL_PATH = Path(
    "models/riskpilot_model.joblib"
)


class RiskPilotPredictor:

    def __init__(self, model_path: Path = MODEL_PATH):

        if not model_path.exists():
            raise FileNotFoundError(
                f"Model not found: {model_path}"
            )

        self.model = joblib.load(model_path)

    def predict_probability(
        self,
        transaction: pd.DataFrame
    ) -> float:
        """
        Return fraud probability for one transaction.
        """

        features = engineer_features(
            transaction
        )

        probability = self.model.predict_proba(
            features
        )[0][1]

        return float(probability)