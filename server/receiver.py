"""
TCP Inference Server:
Receives JSON, validates schema, runs XGBoost model, prints prediction,
AND saves results into results.csv
"""

import socket
import threading
import json
import csv
import os

from generator.captures.feature_schema import validate_and_fill
from server.model_runner import ModelRunner

HOST = "0.0.0.0"
PORT = 9000

CSV_PATH = "results.csv"


# ---------------------------------------------------------
# Initialize CSV file with header if missing
# ---------------------------------------------------------
def init_csv(header):
    if not os.path.exists(CSV_PATH):
        with open(CSV_PATH, "w", newline="") as f:
            wr = csv.writer(f)
            wr.writerow(header)
        print(f"[Receiver] Created CSV file with header: {CSV_PATH}")


# ---------------------------------------------------------
# Save a single flow + prediction into CSV
# ---------------------------------------------------------
def save_to_csv(ordered_features, prediction):
    row = list(ordered_features.values())  # feature values in order
    row += [prediction["prob"], prediction["label"]]

    # Append to file
    with open(CSV_PATH, "a", newline="") as f:
        wr = csv.writer(f)
        wr.writerow(row)


# ---------------------------------------------------------
# Handle each incoming connection
# ---------------------------------------------------------
def handle_conn(conn, addr, model_runner):
    try:
        data = b""

        while True:
            chunk = conn.recv(4096)
            if not chunk:
                break
            data += chunk
            if b"\n" in chunk:
                break

        text = data.decode().strip()
        if not text:
            return

        # Load JSON
        obj = json.loads(text)

        # Validate and reorder features
        ordered = validate_and_fill(obj)

        # Run prediction
        result = model_runner.predict(ordered)

        print(
            f"[{addr}] Prediction: {result['label'].upper()} "
            f"(prob={result['prob']:.4f})"
        )

        # Save features + prediction
        save_to_csv(ordered, result)

    except Exception as e:
        print("Error handling connection:", e)

    finally:
        conn.close()


# ---------------------------------------------------------
# Start Receiver Server
# ---------------------------------------------------------
def start_server():
    print("[Receiver] Loading model...")

    model_runner = ModelRunner(
        model_path="models/XGBoost_model.pkl",
    )

    # CSV header = feature names + prob + label
    header = list(model_runner.feature_order) + ["prob", "label"]
    init_csv(header)

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((HOST, PORT))
    s.listen(5)

    print(f"Receiver listening on {HOST}:{PORT} ...")

    try:
        while True:
            conn, addr = s.accept()

            thread = threading.Thread(
                target=handle_conn,
                args=(conn, addr, model_runner),
                daemon=True
            )
            thread.start()

    except KeyboardInterrupt:
        print("Shutting down receiver...")

    finally:
        s.close()


if __name__ == "__main__":
    start_server()
