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

        # Load AE WITHOUT compiling (fixes Keras 3 mse error)
        self.model = load_model(model_path, compile=False)
        print("[ModelRunner] Autoencoder loaded successfully.")

        if os.path.exists(scaler_path):
            self.scaler = joblib.load(scaler_path)
            print("[ModelRunner] Scaler loaded.")
        else:
            self.scaler = None
            print("[ModelRunner] Warning: scaler not found, continuing WITHOUT scaling.")

    # ----------------------------------------------------------------------

    def predict(self, feature_vector):
        fv = np.array(feature_vector).reshape(1, -1)

        if self.scaler is not None:
            fv = self.scaler.transform(fv)

        reconstructed = self.model.predict(fv, verbose=0)

        mse = np.mean(np.power(fv - reconstructed, 2))

        threshold = 0.01

        label = "normal" if mse < threshold else "anomaly"

        return {
            "reconstruction_error": float(mse),
            "label": label
        }
