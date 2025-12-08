"""
TCP Inference Server:
Receives JSON, validates schema,
SAVES FEATURES FIRST,
then runs XGBoost model and updates CSV with prediction.
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
        print(f"[Receiver] Created CSV file: {CSV_PATH}")


# ---------------------------------------------------------
# Save ONLY features (no prediction yet)
# Returns: row index written
# ---------------------------------------------------------
def save_features_only(ordered_features):
    row = list(ordered_features.values())

    with open(CSV_PATH, "a", newline="") as f:
        wr = csv.writer(f)
        wr.writerow(row + ["", ""])  # placeholders for prob, label

    # Determine row index (last row)
    with open(CSV_PATH, "r") as f:
        return sum(1 for _ in f) - 2  # subtract header row


# ---------------------------------------------------------
# Update prediction in an existing CSV row
# ---------------------------------------------------------
def update_prediction(row_index, prob, label):
    # Read all rows
    with open(CSV_PATH, "r") as f:
        rows = list(csv.reader(f))

    # Update only the prediction fields
    rows[row_index + 1][-2] = str(prob)       # prob column
    rows[row_index + 1][-1] = str(label)      # label column

    # Rewrite whole CSV
    with open(CSV_PATH, "w", newline="") as f:
        wr = csv.writer(f)
        wr.writerows(rows)


# ---------------------------------------------------------
# Handle each incoming packet/flow
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

        # Parse JSON
        obj = json.loads(text)

        # Reorder features
        ordered = validate_and_fill(obj)

        # ---------------------------------------------------------
        # STEP 1: Save raw incoming features BEFORE prediction
        # ---------------------------------------------------------
        row_index = save_features_only(ordered)

        # ---------------------------------------------------------
        # STEP 2: Perform prediction
        # ---------------------------------------------------------
        result = model_runner.predict(ordered)

        print(
            f"[{addr}] Prediction: {result['label'].upper()} "
            f"(prob={result['prob']:.4f})"
        )

        # ---------------------------------------------------------
        # STEP 3: Update the CSV row with prediction results
        # ---------------------------------------------------------
        update_prediction(row_index, result["prob"], result["label"])

    except Exception as e:
        print("Error handling connection:", e)

    finally:
        conn.close()


# ---------------------------------------------------------
# Main Server Loop
# ---------------------------------------------------------
def start_server():
    print("[Receiver] Loading model...")

    model_runner = ModelRunner(
        model_path="models/XGBoost_model.pkl",
    )

    # CSV header
    header = list(model_runner.feature_order) + ["prob", "label"]
    init_csv(header)

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((HOST, PORT))
    s.listen(5)

    print(f"[Receiver] Listening on {HOST}:{PORT} ...")

    try:
        while True:
            conn, addr = s.accept()

            threading.Thread(
                target=handle_conn,
                args=(conn, addr, model_runner),
                daemon=True
            ).start()

    except KeyboardInterrupt:
        print("Shutting down receiver...")

    finally:
        s.close()


if __name__ == "__main__":
    start_server()
