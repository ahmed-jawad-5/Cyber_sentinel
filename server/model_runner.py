import pickle
import numpy as np
from collections import OrderedDict

MODEL_PATH = "./models/XGBoost_model.pkl"
SCALER_PATH = "./models/scaler.pkl"


class ModelRunner:
    """Loads model + scaler and performs predictions."""

    def __init__(self,
                 model_path=MODEL_PATH,
                 scaler_path=SCALER_PATH):

        # ---- Load model ----
        with open(model_path, "rb") as f:
            self.model = pickle.load(f)

        # ---- Load scaler ----
        with open(scaler_path, "rb") as f:
            self.scaler = pickle.load(f)

        # Must match training feature order
        if hasattr(self.scaler, "feature_names_in_"):
            self.feature_order = list(self.scaler.feature_names_in_)
        else:
            raise ValueError(
                "Scaler missing feature_names_in_. "
                "Define feature order manually!"
            )

    def _extract_features(self, features):
        if isinstance(features, OrderedDict):
            vals = list(features.values())
            return np.array([vals], dtype=float)

        elif isinstance(features, dict):
            vals = [features[name] for name in self.feature_order]
            return np.array([vals], dtype=float)

        else:
            raise TypeError("Features must be OrderedDict or dict.")

    def predict(self, feature_dict):

        X = self._extract_features(feature_dict)
        X_scaled = self.scaler.transform(X)
        prob = float(self.model.predict_proba(X_scaled)[0, 1])

        label = "anomaly" if prob >= 0.5 else "normal"

        return {
            "prob": prob,
            "label": label
        }
