# server/receiver.py

import socket
import threading
import json
import csv
import os
from server.model_runner import ModelRunner
from generator.captures.feature_schema import validate_and_fill

HOST = "0.0.0.0"
PORT = 9000
CSV_PATH = "results.csv"
EXPECTED_FEATURE_COUNT = 18
csv_lock = threading.Lock()

# -------------------------
# CSV helpers
# -------------------------
def init_csv(header):
    if not os.path.exists(CSV_PATH):
        with open(CSV_PATH, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(header)
        print(f"[Receiver] CSV initialized: {CSV_PATH}")

def save_features_only(ordered_features):
    row = list(ordered_features.values())
    with csv_lock:
        with open(CSV_PATH, "a", newline="") as f:
            writer = csv.writer(f)
            # leave placeholders for predicted label + probs
            writer.writerow(row + ["", ""])
        # Return row index (0-based after header)
        return sum(1 for _ in open(CSV_PATH)) - 1

def update_prediction(row_index, label, probs):
    with csv_lock:
        with open(CSV_PATH, "r") as f:
            rows = list(csv.reader(f))

        if row_index >= len(rows):
            print(f"[CSV ERROR] Row index {row_index} out of range.")
            return

        # Save label
        rows[row_index][-2] = label
        # Save probabilities as JSON string
        rows[row_index][-1] = json.dumps(probs)

        with open(CSV_PATH, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerows(rows)

# -------------------------
# Handle incoming connections
# -------------------------
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

        print(f"[DEBUG] Packet from {addr}: {text}")
        obj = json.loads(text)

        if len(obj) != EXPECTED_FEATURE_COUNT:
            print(f"[DISCARDED] Packet has {len(obj)} features (expected {EXPECTED_FEATURE_COUNT})")
            return

        ordered = validate_and_fill(obj)
        fv = list(ordered.values())

        row_index = save_features_only(ordered)
        result = model_runner.predict(fv)
        update_prediction(row_index, result["predicted_label"], result["prediction_probs"])

        print(f"[{addr}] Prediction saved: {result['predicted_label']}")

    except Exception as e:
        print(f"[ERROR] Handling connection {addr}: {e}")

    finally:
        conn.close()

# -------------------------
# Main server loop
# -------------------------
def start_server():
    print("[Receiver] Loading model...")
    model_runner = ModelRunner(
        model_path="models/XGBoost_model.pkl",
        scaler_path="models/scaler.save"
    )

    # Initialize CSV
    sample_order = validate_and_fill({})
    header = list(sample_order.keys()) + ["predicted_label", "prediction_probs"]
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
