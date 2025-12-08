# server/model_runner.py

import pickle
import joblib
import numpy as np
from collections import OrderedDict
from generator.captures.feature_schema import FEATURE_ORDER as FALLBACK_FEATURE_ORDER

MODEL_PATH = "./models/XGBoost_model.pkl"
SCALER_PATH = "./models/scaler.save"     # <-- joblib-saved file


class ModelRunner:
    """Loads model + scaler and performs predictions."""

    def __init__(self,
                 model_path=MODEL_PATH,
                 scaler_path=SCALER_PATH):

        print("[ModelRunner] Loading model + scaler...")

        # ------------------------
        # Load XGBoost model (.pkl)
        # ------------------------
        with open(model_path, "rb") as f:
            self.model = pickle.load(f)

        # ------------------------
        # Load scaler saved via joblib
        # ------------------------
        self.scaler = joblib.load(scaler_path)

        # ------------------------
        # Determine feature order
        # ------------------------
        if hasattr(self.scaler, "feature_names_in_"):
            self.feature_order = list(self.scaler.feature_names_in_)
            print("[ModelRunner] Using feature order from scaler.")
        else:
            self.feature_order = list(FALLBACK_FEATURE_ORDER)
            print("[ModelRunner] Using fallback feature schema.")

        print("[ModelRunner] Model + scaler loaded successfully.")
        print(f"[ModelRunner] Feature order: {self.feature_order}")

    # ----------------------------------------------------------------------
    def _extract_features(self, features):
        """Convert dict/OrderedDict into a numpy vector following model order."""

        if isinstance(features, OrderedDict):
            vals = list(features.values())
            return np.array([vals], dtype=float)

        elif isinstance(features, dict):
            # Build feature row using the correct order
            vals = [features.get(name, 0.0) for name in self.feature_order]
            return np.array([vals], dtype=float)

        else:
            raise TypeError("Features must be OrderedDict or dict.")

    # ----------------------------------------------------------------------
    def predict(self, feature_dict):
        """Scale features and return prediction + probability."""

        X = self._extract_features(feature_dict)

        # Apply scaler
        X_scaled = self.scaler.transform(X)

        # XGBoost model expected to have predict_proba()
        prob = float(self.model.predict_proba(X_scaled)[0, 1])

        label = "anomaly" if prob >= 0.5 else "normal"

        return {
            "prob": prob,
            "label": label
        }
