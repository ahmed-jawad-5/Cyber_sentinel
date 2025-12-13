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
                 threshold=0.15,
                 class_mapping = None):
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
    fv = np.array(feature_vector).reshape(1, -1)
    
    # scale features
    if self.scaler:
        fv_df = pd.DataFrame(fv, columns=self.feature_names)
        fv = self.scaler.transform(fv_df)

    # predict probabilities
    dmatrix = xgb.DMatrix(fv, feature_names=self.feature_names)
    probs = self.model.predict(dmatrix)  # shape = [1, 11]

    # predicted class index
    class_idx = int(np.argmax(probs, axis=1)[0])

    # map to string label
    label = self.class_mapping[class_idx] if self.class_mapping else str(class_idx)

    return {
        "prediction_probs": probs.tolist()[0],  # list of 11 probabilities
        "label": label
    }

