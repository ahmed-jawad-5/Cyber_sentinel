# capture/utils_capture.py
import csv
import os
from datetime import datetime
from config import CAPTURED_FLOWS_CSV, ANOMALIES_CSV

# Ensure output folder exists
os.makedirs(os.path.dirname(CAPTURED_FLOWS_CSV), exist_ok=True)

# Initialize CSV files if they do not exist
def init_csv_files(feature_columns):
    if not os.path.exists(CAPTURED_FLOWS_CSV):
        with open(CAPTURED_FLOWS_CSV, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=feature_columns)
            writer.writeheader()

    if not os.path.exists(ANOMALIES_CSV):
        with open(ANOMALIES_CSV, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=feature_columns + ["anomaly_score"])
            writer.writeheader()


# Append a row to captured flows CSV
def write_flow_csv(row: dict):
    with open(CAPTURED_FLOWS_CSV, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=row.keys())
        writer.writerow(row)


# Append anomaly to CSV
def write_anomaly_csv(row: dict, score: float):
    row_copy = row.copy()
    row_copy["anomaly_score"] = score
    with open(ANOMALIES_CSV, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=row_copy.keys())
        writer.writerow(row_copy)
