# server/model_runner.py

import os
import numpy as np
from keras.models import load_model
import joblib


class ModelRunner:
    def __init__(self,
                 model_path="./models/autoencoder.h5",
                 scaler_path="./models/scaler.save"):

        print("[ModelRunner] Loading Autoencoder + Scaler...")

        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Autoencoder not found at: {model_path}")

        # Load AE WITHOUT compiling
        self.model = load_model(model_path, compile=False)
        print("[ModelRunner] Autoencoder loaded successfully.")

        # Load scaler
        if os.path.exists(scaler_path):
            self.scaler = joblib.load(scaler_path)
            print("[ModelRunner] Scaler loaded.")
        else:
            self.scaler = None
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
        # SCALE
        # -------------------------
        if self.scaler is not None:
            try:
                fv_scaled = self.scaler.transform(fv)
                print("[DEBUG] fv shape AFTER scaling:", fv_scaled.shape)
                print("[DEBUG] fv values AFTER scaling:", fv_scaled)
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

        mse = np.mean(np.power(fv_scaled - reconstructed, 2))
        print("[DEBUG] Reconstruction MSE:", mse)

        threshold = 0.01
        label = "normal" if mse < threshold else "anomaly"

        print(f"[DEBUG] Prediction label: {label}")
        print("==========================================================\n")

        return {
            "reconstruction_error": float(mse),
            "label": label
        }
