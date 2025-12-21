import joblib
import os

file_path = './models/scaler.save'

# Ensure the file exists before trying to load it
if not os.path.exists(file_path):
    print(f"Error: File not found at {file_path}")
else:
    # Load the scaler object from the file
    loaded_scaler = joblib.load(file_path)

    print("Scaler loaded successfully!")
    print(type(loaded_scaler))
    print("Feature names:", getattr(loaded_scaler, "feature_names_in_", "No feature names stored"))
