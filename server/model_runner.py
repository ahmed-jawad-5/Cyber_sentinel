# server/model_runner.py

import os
import numpy as np
import pandas as pd
import pickle
import joblib
import xgboost as xgb

class ModelRunner:
    def __init__(self,
                 model_path="./models/XGBoost_model.pkl",
                 scaler_path="./models/scaler.save",
                 output_csv="./scaled_features.csv"):
        self.output_csv = output_csv

        print("[ModelRunner] Loading XGBoost model + Scaler...")

        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model not found at: {model_path}")

        # Load XGBoost model
        with open(model_path, 'rb') as f:
            try:
                self.model = pickle.load(f)
            except Exception as e:
                raise RuntimeError(f"Failed to load model: {e}")

        print("[ModelRunner] Model loaded successfully.")

        # Load scaler
        if os.path.exists(scaler_path):
            self.scaler = joblib.load(scaler_path)
            self.feature_names = list(self.scaler.feature_names_in_)
            print("[ModelRunner] Scaler loaded.")
            print("[ModelRunner] Scaler feature order:", self.feature_names)
        else:
            self.scaler = None
            self.feature_names = None
            print("[ModelRunner] Warning: scaler not found, running WITHOUT scaling!")

        # Initialize CSV
        if not os.path.exists(self.output_csv):
            df_init = pd.DataFrame(columns=self.feature_names)
            df_init.to_csv(self.output_csv, index=False)

    # ----------------------------------------------------------------------

    def predict(self, feature_vector):
        """
        feature_vector: list of 18 features in the order of scaler.feature_names_in_
        Returns dict with:
          - prediction (float)
          - label ('normal'/'anomaly')
        """

        fv = np.array(feature_vector, dtype=float).reshape(1, -1)

        # -------------------------
        # SCALE FEATURES
        # -------------------------
        if self.scaler is not None:
            fv_df = pd.DataFrame(fv, columns=self.feature_names)
            try:
                fv_scaled = self.scaler.transform(fv_df)
            except Exception as e:
                print("[SCALER ERROR] Could not scale input:", e)
                fv_scaled = fv
        else:
            fv_scaled = fv

        # Save scaled features to CSV
        try:
            df_scaled = pd.DataFrame(fv_scaled, columns=self.feature_names)
            df_scaled.to_csv(self.output_csv, mode='a', header=False, index=False)
        except Exception as e:
            print("[CSV ERROR] Could not save scaled features:", e)

        # -------------------------
        # PREDICTION
        # -------------------------
        try:
            if isinstance(self.model, xgb.Booster):
                dmatrix = xgb.DMatrix(fv_scaled, feature_names=self.feature_names)
                pred = self.model.predict(dmatrix)
            else:
                pred = self.model.predict(fv_scaled)

            # Extract single float value
            if isinstance(pred, (np.ndarray, list)):
                pred_val = float(pred[0])
            else:
                pred_val = float(pred)

            # Decide label (binary)
            label = "normal" if pred_val < 0.5 else "anomaly"

        except Exception as e:
            print("[MODEL PREDICT ERROR]:", e)
            pred_val = 999999.0
            label = "anomaly"

        # Debug print
        print("\n[ModelRunner] Prediction debug:")
        print("Feature vector:", feature_vector)
        print("Scaled vector:", fv_scaled.tolist())
        print("Prediction value:", pred_val)
        print("Label:", label)
        print("--------------------------------------------------\n")

        return {
            "prediction": pred_val,
            "label": label
        }
