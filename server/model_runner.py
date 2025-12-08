# server/model_runner.py

import pickle
import joblib
import numpy as np
import pandas as pd
from collections import OrderedDict
from generator.captures.feature_schema import FEATURE_ORDER as FALLBACK_FEATURE_ORDER

# Label mapping for multi-class XGBoost model
LABEL_MAP = {
    "analysis": 0,
    "backdoor": 1,
    "backdoors": 2,
    "dos": 3,
    "exploits": 4,
    "fuzzers": 5,
    "generic": 6,
    "normal": 7,
    "reconnaissance": 8,
    "shellcode": 9,
    "worms": 10,
}
INT_TO_LABEL = {v: k for k, v in LABEL_MAP.items()}

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

        # Introspect model classes for multi-class mapping (if available)
        self.model_classes_ = getattr(self.model, "classes_", None)
        if self.model_classes_ is not None:
            print(f"[ModelRunner] Detected model classes_: {self.model_classes_}")
        else:
            print("[ModelRunner] Warning: model has no 'classes_' attribute; "
                  "falling back to index-based labels.")

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
        """Scale features and return top-class label + its probability.

        For multi-class XGBoost models, this uses predict_proba and
        returns the class with maximum probability, mapped back to the
        human-readable label using LABEL_MAP where possible.
        """

        X = self._extract_features(feature_dict)

        # Prepare input for scaler. If the scaler was fitted on a pandas
        # DataFrame with feature names, we must provide a DataFrame with
        # the same column names to avoid sklearn's
        # "X does not have valid feature names" error.
        if hasattr(self.scaler, "feature_names_in_"):
            X_in = pd.DataFrame(X, columns=self.feature_order)
        else:
            X_in = X

        # Apply scaler
        X_scaled = self.scaler.transform(X_in)

        # XGBoost model expected to have predict_proba() with shape (1, n_classes)
        proba = self.model.predict_proba(X_scaled)[0]

        # Guard for unexpected shapes
        if np.ndim(proba) == 0:
            best_prob = float(proba)
            best_label = "unknown"
        else:
            # Index of most probable class
            best_idx = int(np.argmax(proba))
            best_prob = float(proba[best_idx])

            # If model exposes explicit class labels, use them
            if self.model_classes_ is not None and len(self.model_classes_) == len(proba):
                raw_class = self.model_classes_[best_idx]
                try:
                    # Try to interpret as integer class id and map via INT_TO_LABEL
                    cid = int(raw_class)
                    best_label = INT_TO_LABEL.get(cid, str(raw_class))
                except (TypeError, ValueError):
                    # Non-integer labels (e.g. strings) – just stringify
                    best_label = str(raw_class)
            else:
                # Fallback: assume indices 0..K-1 correspond to INT_TO_LABEL keys
                best_label = INT_TO_LABEL.get(best_idx, str(best_idx))

        return {
            "prob": best_prob,
            "label": best_label,
        }
