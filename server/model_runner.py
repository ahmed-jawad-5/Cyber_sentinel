# server/model_runner.py

import os
import numpy as np
import pandas as pd
from keras.models import load_model
import joblib


class ModelRunner:
    def __init__(self,
                 model_path="./models/autoencoder.h5",
                 scaler_path="./models/scaler.save"):

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

    # ----------------------------------------------------------------------

    def predict(self, feature_vector):
        print("\n==================== PREDICTION DEBUG ====================")
        print("[DEBUG] Raw incoming feature_vector:")
        print(feature_vector)
        print("[DEBUG] Length:", len(feature_vector))

        fv = np.array(feature_vector, dtype=float).reshape(1, -1)
        print("[DEBUG] fv shape BEFORE scaling:", fv.shape)
        print("[DEBUG] fv values BEFORE scaling:", fv)

        # Check for NaN / INF
        if np.isnan(fv).any():
            print("⚠️ WARNING: fv contains NaN values!")
        if np.isinf(fv).any():
            print("⚠️ WARNING: fv contains INF values!")

        # -------------------------
        # SCALE (CORRECT & SAFE)
        # -------------------------
        if self.scaler is not None:
            try:
                # Ensure feature vector length matches scaler
                assert fv.shape[1] == len(self.feature_names), \
                    f"Feature vector length {fv.shape[1]} != scaler features {len(self.feature_names)}"

                fv_df = pd.DataFrame(fv, columns=self.feature_names)
                fv_scaled = self.scaler.transform(fv_df)

                # Print scaled features clearly
                print("[DEBUG] Scaled features:")
                for name, val in zip(self.feature_names, fv_scaled[0]):
                    print(f"  {name}: {val}")

                # Optional extreme feature check
                large_indices = np.where(np.abs(fv_scaled[0]) > 10)[0]
                if len(large_indices) > 0:
                    print("⚠️ WARNING: Features with extreme values after scaling (>10 std):")
                    for idx in large_indices:
                        print(f"  - {self.feature_names[idx]}: {fv_scaled[0][idx]}")

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

        print("[DEBUG] reconstructed shape:", reconstructed.shape)
        print("[DEBUG] reconstructed values:", reconstructed)

        # -------------------------
        # COMPUTE MSE
        # -------------------------
        mse_per_feature = np.square(fv_scaled - reconstructed)
        mse = np.mean(mse_per_feature)
        print("[DEBUG] Reconstruction MSE:", mse)

        # Features contributing high MSE
        high_mse_indices = np.where(mse_per_feature[0] > 0.5)[0]
        if len(high_mse_indices) > 0:
            print("⚠️ WARNING: Features contributing high MSE (>0.5):")
            for idx in high_mse_indices:
                print(f"  - {self.feature_names[idx]}: {mse_per_feature[0][idx]}")

        # Sorted per-feature MSE (descending)
        sorted_idx = np.argsort(-mse_per_feature[0])
        print("[DEBUG] Features sorted by per-feature MSE:")
        for idx in sorted_idx:
            print(f"  {self.feature_names[idx]}: {mse_per_feature[0][idx]}")

        # -------------------------
        # LABEL DECISION
        # -------------------------
        threshold = 0.01
        label = "normal" if mse < threshold else "anomaly"

        print(f"[DEBUG] Prediction label: {label}")
        print("==========================================================\n")

        return {
            "reconstruction_error": float(mse),
            "label": label
        }
