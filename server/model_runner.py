# server/model_runner.py

import pickle
import numpy as np
from collections import OrderedDict
from generator.captures.feature_schema import FEATURE_ORDER as FALLBACK_FEATURE_ORDER

MODEL_PATH = "./models/XGBoost_model.pkl"


class ModelRunner:
    """Loads model and performs predictions on raw 18 features.

    The scaler is intentionally disabled; the model is evaluated directly on
    the 18 features defined in FEATURE_SCHEMA / FALLBACK_FEATURE_ORDER.
    """

    def __init__(self,
                 model_path=MODEL_PATH):

        print("[ModelRunner] Loading model (NO scaler, raw 18 features)...")

        # ------------------------
        # Load XGBoost model (.pkl)
        # ------------------------
        with open(model_path, "rb") as f:
            self.model = pickle.load(f)

        # ------------------------
        # Scaler disabled on purpose
        # ------------------------
        # self.scaler = joblib.load(scaler_path)
        self.scaler = None

        # Always use the 18-feature schema order
        self.feature_order = list(FALLBACK_FEATURE_ORDER)
        print("[ModelRunner] Using fallback feature schema (18 features).")

        print("[ModelRunner] Model loaded successfully.")
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
        """Return prediction + probability on raw 18 features.

        No scaler is applied; the model receives the 18 values in
        self.feature_order directly.
        """

        X = self._extract_features(feature_dict)

        # Directly feed raw features into the model (no scaling)
        X_in = X

        # XGBoost model expected to have predict_proba()
        prob = float(self.model.predict_proba(X_in)[0, 1])

        label = "anomaly" if prob >= 0.5 else "normal"

        return {
            "prob": prob,
            "label": label
        }
