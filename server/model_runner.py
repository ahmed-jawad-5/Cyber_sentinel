import os
import pandas as pd
import numpy as np
import joblib
import xgboost as xgb
import pickle

class ModelRunner:
    def __init__(self,
                 model_path="./models/XGBoost_model.pkl",
                 scaler_path="./models/scaler.save",
                 output_csv="./scaled_features.csv"):

        self.output_csv = output_csv
        print("[ModelRunner] Loading XGBoost model + Scaler...")

        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model not found at: {model_path}")

        # Try loading with pickle first
        try:
            with open(model_path, 'rb') as f:
                self.model = pickle.load(f)
            print("[ModelRunner] Model loaded via pickle.")
        except Exception:
            # If pickle fails, try XGBoost native load
            try:
                self.model = xgb.Booster()
                self.model.load_model(model_path)
                print("[ModelRunner] Model loaded via XGBoost native format.")
            except Exception as e:
                raise RuntimeError(f"Failed to load model: {e}")

        # Load scaler
        if os.path.exists(scaler_path):
            self.scaler = joblib.load(scaler_path)
            self.feature_names = list(self.scaler.feature_names_in_)
            print("[ModelRunner] Scaler loaded.")
        else:
            self.scaler = None
            self.feature_names = None
            print("[ModelRunner] Warning: Scaler not found, running WITHOUT scaling!")

    def predict(self, feature_vector):
        fv = np.array(feature_vector, dtype=float).reshape(1, -1)

        # -------------------------
        # SCALE FEATURES
        # -------------------------
        if self.scaler is not None:
            fv_df = pd.DataFrame(fv, columns=self.feature_names)
            fv_scaled = self.scaler.transform(fv_df)

            # Save scaled features to CSV
            df_scaled = pd.DataFrame(fv_scaled, columns=self.feature_names)
            df_scaled.to_csv(self.output_csv, mode='a', header=False, index=False)
        else:
            fv_scaled = fv

        # -------------------------
        # MODEL PREDICTION
        # -------------------------
        try:
            if isinstance(self.model, xgb.Booster):
                dmatrix = xgb.DMatrix(fv_scaled, feature_names=self.feature_names)
                pred = self.model.predict(dmatrix)
            else:
                pred = self.model.predict(fv_scaled)
        except Exception as e:
            print("❌ MODEL PREDICT ERROR:", e)
            return {"prediction": None}

        return {"prediction": pred}
