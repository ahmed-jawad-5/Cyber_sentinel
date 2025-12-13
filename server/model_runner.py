# server/model_runner.py

import os
import numpy as np
import pandas as pd
import pickle
import joblib
import xgboost as xgb

class ModelRunner:
    """
    Loads XGBoost multi-class model + scaler.
    Provides a predict method returning class label and probabilities.
    """
    def __init__(self,
                 model_path="./models/XGBoost_model.pkl",
                 scaler_path="./models/scaler.save",
                 output_csv="./scaled_features.csv",
                 label_mapping=None):
        self.output_csv = output_csv
        self.label_mapping = label_mapping or {
            0: "analysis", 1: "backdoor", 2: "backdoors", 3: "dos",
            4: "exploits", 5: "fuzzers", 6: "generic", 7: "normal",
            8: "reconnaissance", 9: "shellcode", 10: "worms"
        }

        print("[ModelRunner] Initializing...")
        self.model = None
        self.scaler = None
        self.feature_names = None

        # -------------------------
        # Load XGBoost model
        # -------------------------
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model not found at: {model_path}")

        with open(model_path, 'rb') as f:
            try:
                self.model = pickle.load(f)
                print("[ModelRunner] Model loaded successfully.")
            except Exception as e:
                raise RuntimeError(f"[ModelRunner] Failed to load model: {e}")

        # -------------------------
        # Load scaler if exists
        # -------------------------
        if os.path.exists(scaler_path):
            try:
                self.scaler = joblib.load(scaler_path)
                self.feature_names = list(self.scaler.feature_names_in_)
                print("[ModelRunner] Scaler loaded successfully.")
            except Exception as e:
                print(f"[ModelRunner WARNING] Failed to load scaler: {e}")
                self.scaler = None
        else:
            print("[ModelRunner WARNING] Scaler not found, running without scaling.")

        # -------------------------
        # Initialize output CSV for scaled features
        # -------------------------
        if self.feature_names and not os.path.exists(self.output_csv):
            df_init = pd.DataFrame(columns=self.feature_names)
            df_init.to_csv(self.output_csv, index=False)

        print("[ModelRunner] Ready for predictions.\n")

    # ----------------------------------------------------------------------
    def predict(self, feature_vector):
        """
        feature_vector: list of features in the correct order
        Returns dict:
            - predicted_label: str
            - prediction_probs: dict of class probabilities
        """
        try:
            fv = np.array(feature_vector, dtype=float).reshape(1, -1)

            # Scale if scaler exists
            if self.scaler:
                fv_df = pd.DataFrame(fv, columns=self.feature_names)
                fv_scaled = self.scaler.transform(fv_df)
            else:
                fv_scaled = fv

            # Save scaled features
            if self.feature_names:
                df_scaled = pd.DataFrame(fv_scaled, columns=self.feature_names)
                df_scaled.to_csv(self.output_csv, mode='a', header=False, index=False)

            # -------------------------
            # Multi-class prediction
            # -------------------------
            if hasattr(self.model, "predict_proba"):
                probs = self.model.predict_proba(fv_scaled)[0]
                pred_class = int(np.argmax(probs))
            else:
                # raw Booster
                dmatrix = xgb.DMatrix(fv_scaled, feature_names=self.feature_names)
                raw_preds = self.model.predict(dmatrix)
                if raw_preds.ndim == 1:
                    # binary output fallback
                    pred_class = int(raw_preds[0] > 0.5)
                    probs = [1 - raw_preds[0], raw_preds[0]]
                else:
                    pred_class = int(np.argmax(raw_preds))
                    probs = raw_preds[0]

            label = self.label_mapping.get(pred_class, f"class_{pred_class}")
            prediction_probs = {self.label_mapping[i]: float(probs[i]) for i in range(len(probs))}

            # Debug
            print("[ModelRunner] Prediction debug:")
            print("Feature vector:", feature_vector)
            print("Predicted class:", pred_class, "Label:", label)
            print("Probabilities:", prediction_probs)
            print("--------------------------------------------------\n")

            return {
                "predicted_label": label,
                "prediction_probs": prediction_probs
            }

        except Exception as e:
            print("[ModelRunner ERROR] Prediction failed:", e)
            return {
                "predicted_label": "error",
                "prediction_probs": {}
            }
