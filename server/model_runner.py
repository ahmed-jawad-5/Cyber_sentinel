# server/model_runner.py

import numpy as np
import pandas as pd
import joblib
from tensorflow.keras.models import load_model
from collections import OrderedDict
from generator.captures.feature_schema import FEATURE_ORDER as FALLBACK_FEATURE_ORDER

MODEL_PATH = "./models/autoencoder.h5"
SCALER_PATH = "./models/scaler.save"

# Choose a threshold for marking anomaly
# You MUST tune it using validation data
RECON_ERROR_THRESHOLD = 0.02    # example value – adjust as needed


class ModelRunner:
    """Loads autoencoder + scaler and performs anomaly scoring."""

    def __init__(self,
                 model_path=MODEL_PATH,
                 scaler_path=SCALER_PATH):

        print("[ModelRunner] Loading Autoencoder model + scaler...")

        # Load autoencoder
        self.model = load_model(model_path)

        # Load scaler
        self.scaler = joblib.load(scaler_path)

        # Determine feature order
        if hasattr(self.scaler, "feature_names_in_"):
            self.feature_order = list(self.scaler.feature_names_in_)
            print("[ModelRunner] Using feature order from scaler.")
        else:
            self.feature_order = list(FALLBACK_FEATURE_ORDER)
            print("[ModelRunner] Using fallback feature schema.")

        print("[ModelRunner] Autoencoder model + scaler loaded successfully.")
        print(f"[ModelRunner] Feature order: {self.feature_order}")

    # -----------------------------------------------------------
    def _extract_features(self, features):
        """Convert dict/OrderedDict → numpy vector following feature order."""

        if isinstance(features, OrderedDict):
            vals = list(features.values())
            return np.array([vals], dtype=float)

        elif isinstance(features, dict):
            vals = [features.get(name, 0.0) for name in self.feature_order]
            return np.array([vals], dtype=float)

        else:
            raise TypeError("Features must be OrderedDict or dict.")

    # -----------------------------------------------------------
    def predict(self, feature_dict):
        """Scale features → autoencoder → reconstruction error → anomaly."""

        X = self._extract_features(feature_dict)

        # Convert to DataFrame if scaler requires feature names
        if hasattr(self.scaler, "feature_names_in_"):
            X_in = pd.DataFrame(X, columns=self.feature_order)
        else:
            X_in = X

        # Scale input
        X_scaled = self.scaler.transform(X_in)

        # Get model reconstruction
        X_recon = self.model.predict(X_scaled, verbose=0)

        # Compute reconstruction error (MSE per row)
        error = float(np.mean((X_scaled - X_recon) ** 2))

        # Decide label
        label = "anomaly" if error > RECON_ERROR_THRESHOLD else "normal"

        return {
            "prob": error,    # Here, prob = reconstruction error
            "label": label
        }
