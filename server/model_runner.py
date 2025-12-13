# server/model_runner.py

import os
import numpy as np
import pandas as pd
from keras.models import load_model
import joblib

class ModelRunner:
    def __init__(self,
                 model_path="./models/autoencoder.h5",
                 scaler_path="./models/scaler.save",
                 output_csv="./scaled_features.csv"):

        print("[ModelRunner] Loading Autoencoder + Scaler...")
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Autoencoder not found at: {model_path}")

        self.model = load_model(model_path, compile=False)
        print("[ModelRunner] Autoencoder loaded successfully.")

        if os.path.exists(scaler_path):
            self.scaler = joblib.load(scaler_path)
            self.feature_names = list(self.scaler.feature_names_in_)
            print("[ModelRunner] Scaler loaded.")
            print("[ModelRunner] Scaler feature order:", self.feature_names)
        else:
            self.scaler = None
            self.feature_names = None
            print("[ModelRunner] Warning: scaler not found, running WITHOUT scaling!")

        self.output_csv = output_csv
        # Initialize CSV file
        if not os.path.exists(self.output_csv):
            pd.DataFrame(columns=self.feature_names).to_csv(self.output_csv, index=False)

    def predict(self, feature_vector):
        fv = np.array(feature_vector, dtype=float).reshape(1, -1)

        # -------------------------
        # FIRST SCALING: manual Min-Max 0-1 per feature
        # -------------------------
        fv_min = fv.min(axis=1, keepdims=True)
        fv_max = fv.max(axis=1, keepdims=True)
        fv_scaled_once = (fv - fv_min) / (fv_max - fv_min + 1e-6)

        # Save first-scaled features to CSV
        df_scaled_once = pd.DataFrame(fv_scaled_once, columns=self.feature_names)
        df_scaled_once.to_csv(self.output_csv, mode='a', header=False, index=False)

        # -------------------------
        # SECOND SCALING: apply saved scaler
        # -------------------------
        if self.scaler is not None:
            fv_scaled_df = pd.DataFrame(fv_scaled_once, columns=self.feature_names)
            fv_scaled = self.scaler.transform(fv_scaled_df)
        else:
            fv_scaled = fv_scaled_once

        # -------------------------
        # MODEL PREDICTION
        # -------------------------
        try:
            reconstructed = self.model.predict(fv_scaled, verbose=0)
        except Exception as e:
            print("❌ MODEL PREDICT ERROR:", e)
            return {"reconstruction_error": 999999, "label": "anomaly"}

        mse_per_feature = np.square(fv_scaled - reconstructed)
        mse = np.mean(mse_per_feature)
        label = "normal" if mse < 0.01 else "anomaly"

        return {"reconstruction_error": float(mse), "label": label}
