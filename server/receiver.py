"""
TCP Inference Server:
Receives JSON, validates schema,
SAVES FEATURES FIRST,
then runs Autoencoder model and updates CSV with prediction.
"""
EXPECTED_FEATURE_COUNT = 18
import socket
import threading
import json
import csv
import os

from generator.captures.feature_schema import validate_and_fill
from model_runner import ModelRunner

csv_lock = threading.Lock()

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
# Save features only (append empty prediction columns)
# ---------------------------------------------------------
def save_features_only(ordered_features):
    row = list(ordered_features.values())
    with csv_lock:
        with open(CSV_PATH, "a", newline="") as f:
            wr = csv.writer(f)
            wr.writerow(row + ["", ""])  # placeholders

        # Return row index (zero-based, after header)
        return sum(1 for _ in open(CSV_PATH)) - 1



# ---------------------------------------------------------
# Update a specific CSV row with prediction
# ---------------------------------------------------------
def update_prediction(row_index, value, label):
    with csv_lock:
        with open(CSV_PATH, "r") as f:
            rows = list(csv.reader(f))

        if row_index >= len(rows):
            print(f"[CSV ERROR] Cannot update row {row_index}. CSV has only {len(rows)} rows.")
            return

        rows[row_index][-2] = str(value)
        rows[row_index][-1] = str(label)

        with open(CSV_PATH, "w", newline="") as f:
            wr = csv.writer(f)
            wr.writerows(rows)

# ---------------------------------------------------------
# Handle incoming packet
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

        # Validate and order features
        ordered = validate_and_fill(obj)
        fv = list(ordered.values())

        # -----------------------------
        # Predict first
        # -----------------------------
        result = model_runner.predict(fv)
        label = result['label']
        probs = result['prediction_probs']  # list of 11 probabilities


        print(f"[{addr}] Prediction: {label.upper()} (value={value:.6f})")

        # -----------------------------
        # Save features + prediction atomically
        # -----------------------------
        with csv_lock:
            with open(CSV_PATH, "a", newline="") as f:
                wr = csv.writer(f)
                wr.writerow(list(ordered.values()) + [label] + probs)

    except json.JSONDecodeError as e:
        print(f"[ERROR] Invalid JSON from {addr}: {e}")

    except Exception as e:
        print(f"[ERROR] Handling connection: {e}")

    finally:
        conn.close()


# ---------------------------------------------------------
# Main server loop
# ---------------------------------------------------------
def start_server():
    print("[Receiver] Loading model...")
    CLASS_MAPPING = {
    0: "analysis", 1: "backdoor", 2: "backdoors", 3: "dos",
    4: "exploits", 5: "fuzzers", 6: "generic", 7: "normal",
    8: "reconnaissance", 9: "shellcode", 10: "worms"
    }

    model_runner = ModelRunner(
        model_path="models/XGBoost_model.pkl",
        scaler_path="models/scaler.save",
        class_mapping=CLASS_MAPPING
    )


    # Build CSV header dynamically
 # Build CSV header dynamically
    sample_order = validate_and_fill({})  # empty -> defaults
    header = list(sample_order.keys()) + ["predicted_label"] + [
        "prob_analysis", "prob_backdoor", "prob_backdoors", "prob_dos", "prob_exploits",
        "prob_fuzzers", "prob_generic", "prob_normal", "prob_reconnaissance",
        "prob_shellcode", "prob_worms"
    ]
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
