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
                 output_csv="./scaled_features.csv",
                 threshold=0.15):
        self.output_csv = output_csv
        self.threshold = threshold

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
          - prediction (float probability of anomaly)
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
            if hasattr(self.model, "predict_proba"):
                # scikit-learn wrapper: get probability
                pred_probs = self.model.predict_proba(fv_scaled)
                pred_val = float(pred_probs[0][1])  # probability of class 1 (anomaly)
            else:
                # raw Booster: predict returns logits, apply sigmoid
                dmatrix = xgb.DMatrix(fv_scaled, feature_names=self.feature_names)
                raw_pred = float(self.model.predict(dmatrix)[0])
                pred_val = 1 / (1 + np.exp(-raw_pred))  # sigmoid normalization

            # Decide label using threshold
            label = "normal" if pred_val < self.threshold else "anomaly"

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
