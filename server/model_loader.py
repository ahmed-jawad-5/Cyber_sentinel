import pickle
import numpy as np
from collections import OrderedDict

MODEL_PATH = "./model/XGBoost_model.pkl"   # your trained model
SCALER_PATH = "./model/scaler.pkl"         # the StandardScaler or MinMaxScaler

class ModelRunner:
    def __init__(self,
                 model_path=MODEL_PATH,
                 scaler_path=SCALER_PATH):

        # ---- Load model ----
        with open(model_path, "rb") as f:
            self.model = pickle.load(f)

        # ---- Load scaler ----
        with open(scaler_path, "rb") as f:
            self.scaler = pickle.load(f)

        # Extract model input order from scaler or model
        # Important: you MUST ensure features come in the same order
        if hasattr(self.scaler, "feature_names_in_"):
            self.feature_order = list(self.scaler.feature_names_in_)
        else:
            raise ValueError("Scaler has no attribute feature_names_in_. "
                             "You must define the feature order manually!")

    def _extract_features(self, features):
        """
        Convert OrderedDict or dict into a correctly ordered numeric vector.
        """
        if isinstance(features, OrderedDict):
            # Already in correct order
            vals = list(features.values())
            return np.array([vals], dtype=float)

        elif isinstance(features, dict):
            # Must reorder using saved order
            vals = [features[name] for name in self.feature_order]
            return np.array([vals], dtype=float)

        else:
            raise TypeError("Features must be OrderedDict or dict.")

    def predict(self, feature_dict):
        """
        feature_dict: OrderedDict or dict
        RETURNS:
            {
                "prob": float,
                "label": "anomaly" | "normal"
            }
        """
        # 1. Convert JSON → vector
        X = self._extract_features(feature_dict)

        # 2. Apply scaler
        X_scaled = self.scaler.transform(X)

        # 3. Predict (XGBoost sklearn model)
        prob = float(self.model.predict_proba(X_scaled)[0, 1])  # class 1 = anomaly

        label = "anomaly" if prob >= 0.5 else "normal"

        return {
            "prob": prob,
            "label": label
        }


# === Example Usage ===
if __name__ == "__main__":
    # Example dummy input (replace with real 34-feature dict)
    sample = OrderedDict([
        ("proto", 6),
        ("state", 1),
        ("sbytes", 300),
        ("dbytes", 600),
        # ...
    ])

    runner = ModelRunner()
    out = runner.predict(sample)
    print(out)
