# server/receiver.py

EXPECTED_FEATURE_COUNT = 18
import socket
import threading
import json
import csv
import os

from generator.captures.feature_schema import validate_and_fill
from server.model_runner import ModelRunner

csv_lock = threading.Lock()
HOST = "0.0.0.0"
PORT = 9000
CSV_PATH = "results.csv"

# ---------------------------------------------------------
def init_csv(header):
    if not os.path.exists(CSV_PATH):
        with open(CSV_PATH, "w", newline="") as f:
            wr = csv.writer(f)
            wr.writerow(header)
        print(f"[Receiver] Created CSV file: {CSV_PATH}")


# ---------------------------------------------------------
def save_features_only(ordered_features):
    row = list(ordered_features.values())
    with csv_lock:
        with open(CSV_PATH, "a", newline="") as f:
            wr = csv.writer(f)
            wr.writerow(row + ["", ""])  # placeholders for prediction & label
        return sum(1 for _ in open(CSV_PATH)) - 1  # zero-based


# ---------------------------------------------------------
def update_prediction(row_index, value, label):
    with csv_lock:
        with open(CSV_PATH, "r") as f:
            rows = list(csv.reader(f))

        if row_index >= len(rows):
            print(f"[CSV ERROR] Cannot update row {row_index}. CSV has only {len(rows)} rows.")
            return

        # store prediction value and label
        rows[row_index][-2] = str(value)
        rows[row_index][-1] = str(label)

        with open(CSV_PATH, "w", newline="") as f:
            wr = csv.writer(f)
            wr.writerows(rows)


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

        print(f"\n[DEBUG] Raw packet from {addr}: {text}")

        obj = json.loads(text)
        if len(obj) != EXPECTED_FEATURE_COUNT:
            print(f"[DISCARDED] Packet from {addr} has {len(obj)} features (expected {EXPECTED_FEATURE_COUNT})")
            return

        ordered = validate_and_fill(obj)
        fv = list(ordered.values())

        row_index = save_features_only(ordered)

        # MULTI-CLASS PREDICTION
        result = model_runner.predict(fv)
        value = result["prediction"]
        label = result["label"]

        update_prediction(row_index, value, label)
        print(f"[{addr}] Prediction: {label.upper()} (value={value:.6f})")

    except json.JSONDecodeError as e:
        print(f"[ERROR] Invalid JSON from {addr}: {e}")
    except Exception as e:
        print("[ERROR] Handling connection:", e)
    finally:
        conn.close()


# ---------------------------------------------------------
def start_server():
    print("[Receiver] Loading model...")
    model_runner = ModelRunner(
        model_path="models/XGBoost_model.pkl",
        scaler_path="models/scaler.save",
        normal_threshold=0.15
    )

    # Build CSV header dynamically
    sample_order = validate_and_fill({})
    header = list(sample_order.keys()) + ["prediction_value", "predicted_label"]
    init_csv(header)

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((HOST, PORT))
    s.listen(5)
    print(f"[Receiver] Listening on {HOST}:{PORT} ...")

    try:
        while True:
            conn, addr = s.accept()
            threading.Thread(target=handle_conn, args=(conn, addr, model_runner), daemon=True).start()
    except KeyboardInterrupt:
        print("Shutting down receiver...")
    finally:
        s.close()


if __name__ == "__main__":
    start_server()
