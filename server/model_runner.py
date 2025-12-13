# server/model_runner.py

import os
import numpy as np
import pandas as pd
from keras.models import load_model
import joblib
from datetime import datetime

class ModelRunner:
    def __init__(self,
                 model_path="./models/autoencoder.h5",
                 scaler_path="./models/scaler.save",
                 scaled_csv_path="./logs/scaled_features.csv"):

        print("[ModelRunner] Loading Autoencoder + Scaler...")

        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Autoencoder not found at: {model_path}")

        # Load autoencoder WITHOUT compiling
        self.model = load_model(model_path, compile=False)
        print("[ModelRunner] Autoencoder loaded successfully.")

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

        # CSV path for scaled features
        self.scaled_csv_path = scaled_csv_path
        os.makedirs(os.path.dirname(scaled_csv_path), exist_ok=True)
        # Initialize CSV with headers if file does not exist
        if not os.path.exists(self.scaled_csv_path) and self.feature_names:
            df_init = pd.DataFrame(columns=["timestamp"] + self.feature_names)
            df_init.to_csv(self.scaled_csv_path, index=False)
            print(f"[ModelRunner] Created CSV for scaled features at {self.scaled_csv_path}")

    # ----------------------------------------------------------------------

    def predict(self, feature_vector):
        print("\n==================== PREDICTION DEBUG ====================")
        print("[DEBUG] Raw incoming feature_vector:")
        print(feature_vector)
        print("[DEBUG] Length:", len(feature_vector))

        fv = np.array(feature_vector, dtype=float).reshape(1, -1)

        # -------------------------
        # SCALE (CORRECT & SAFE)
        # -------------------------
        if self.scaler is not None:
            try:
                assert fv.shape[1] == len(self.feature_names), \
                    f"Feature vector length {fv.shape[1]} != scaler features {len(self.feature_names)}"
                fv_df = pd.DataFrame(fv, columns=self.feature_names)
                fv_scaled = self.scaler.transform(fv_df)

                # Append scaled features to CSV
                timestamp = datetime.now().isoformat()
                row_df = pd.DataFrame([fv_scaled[0]], columns=self.feature_names)
                row_df.insert(0, "timestamp", timestamp)
                row_df.to_csv(self.scaled_csv_path, mode="a", header=False, index=False)
                print(f"[DEBUG] Scaled features saved to CSV at {self.scaled_csv_path}")

            except Exception as e:
                print("[SCALER ERROR] Could not scale input:", e)
                fv_scaled = fv
        else:
            fv_scaled = fv

        # -------------------------
        # MODEL PREDICTION
        # -------------------------
        try:
            reconstructed = self.model.predict(fv_scaled, verbose=0)
        except Exception as e:
            print("❌ MODEL PREDICT ERROR:", e)
            return {
                "reconstruction_error": 999999,
                "label": "anomaly"
            }

        mse_per_feature = np.square(fv_scaled - reconstructed)
        mse = np.mean(mse_per_feature)
        print("[DEBUG] Reconstruction MSE:", mse)

        # Features contributing high MSE
        if self.feature_names:
            high_mse_indices = np.where(mse_per_feature[0] > 0.5)[0]
            if len(high_mse_indices) > 0:
                print("⚠️ WARNING: Features contributing high MSE (>0.5):")
                for idx in high_mse_indices:
                    print(f"  - {self.feature_names[idx]}: {mse_per_feature[0][idx]}")

        threshold = 0.01
        label = "normal" if mse < threshold else "anomaly"

        print(f"[DEBUG] Prediction label: {label}")
        print("==========================================================\n")

        return {
            "reconstruction_error": float(mse),
            "label": label
        }
