# server/model_runner.py

import os
import numpy as np
import pandas as pd
import pickle
import joblib
import xgboost as xgb

class ModelRunner:
    """
    Handles multi-class prediction using XGBoost and scales input features.
    Adds a minimum threshold for 'normal' class detection.
    """

    def __init__(self,
                 model_path="./models/XGBoost_model.pkl",
                 scaler_path="./models/scaler.save",
                 output_csv="./scaled_features.csv",
                 normal_threshold=0.15):
        self.output_csv = output_csv
        self.normal_threshold = normal_threshold

        # Label mapping (multi-class)
        self.label_mapping = {
            0: "analysis", 1: "backdoor", 2: "backdoors", 3: "dos",
            4: "exploits", 5: "fuzzers", 6: "generic", 7: "normal",
            8: "reconnaissance", 9: "shellcode", 10: "worms"
        }
        self.normal_index = 7  # Index of 'normal' in mapping

        print("[ModelRunner] Loading XGBoost model + Scaler...")

        # Load model
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model not found at: {model_path}")

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

        # Initialize CSV for scaled features
        if not os.path.exists(self.output_csv):
            df_init = pd.DataFrame(columns=self.feature_names)
            df_init.to_csv(self.output_csv, index=False)

    # ----------------------------------------------------------------------
    def scale_features(self, fv):
        return self.scaler.transform([fv])[0]

    def predict(self, feature_vector):
        """
        feature_vector: list of 18 features in the order of scaler.feature_names_in_
        Returns dict with:
          - prediction (max probability value)
          - label (multi-class label string)
          - all_probs (list of class probabilities)
        """

        fv = np.array(feature_vector, dtype=float).reshape(1, -1)

        # SCALE FEATURES
        if self.scaler is not None:
            fv_df = pd.DataFrame(fv, columns=self.feature_names)
            try:
                fv_scaled = self.scaler.transform(fv_df)
            except Exception as e:
                print("[SCALER ERROR] Could not scale input:", e)
                fv_scaled = fv
        else:
            fv_scaled = fv

        # Save scaled features
        try:
            df_scaled = pd.DataFrame(fv_scaled, columns=self.feature_names)
            df_scaled.to_csv(self.output_csv, mode='a', header=False, index=False)
        except Exception as e:
            print("[CSV ERROR] Could not save scaled features:", e)

        # -------------------------
        # MULTI-CLASS PREDICTION
        # -------------------------
        try:
            if hasattr(self.model, "predict_proba"):
                pred_probs = self.model.predict_proba(fv_scaled)
                probs = pred_probs[0]  # probability for each class
            else:
                # raw XGBoost Booster
                dmatrix = xgb.DMatrix(fv_scaled, feature_names=self.feature_names)
                raw_pred = self.model.predict(dmatrix)
                exp_preds = np.exp(raw_pred)
                probs = exp_preds / np.sum(exp_preds)  # softmax normalization
        except Exception as e:
            print("[MODEL PREDICT ERROR]:", e)
            probs = np.zeros(len(self.label_mapping))

        # Determine predicted label with normal threshold
        max_index = int(np.argmax(probs))
        if probs[self.normal_index] >= self.normal_threshold:
            label = "normal"
            pred_val = probs[self.normal_index]
        else:
            label = self.label_mapping[max_index]
            pred_val = probs[max_index]

        # DEBUG
        print("\n[ModelRunner] Prediction debug:")
        print("Feature vector:", feature_vector)
        print("Scaled vector:", fv_scaled.tolist())
        print("Class probabilities:", probs.tolist())
        print("Predicted label:", label)
        print("Prediction value:", pred_val)
        print("--------------------------------------------------\n")

        return {
            "prediction": pred_val,
            "label": label,
            "all_probs": probs.tolist()
        }
