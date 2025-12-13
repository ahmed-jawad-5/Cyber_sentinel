"""
TCP Inference Server:
Receives JSON, validates schema,
SAVES FEATURES FIRST,
then runs Autoencoder model and updates CSV with prediction.
"""
EXPECTED_FEATURE_COUNT = 18
import socket
import threading # multi threadig ~~~>> for multi therads 
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
# Save features only (append empty prediction columns)
# ---------------------------------------------------------
def save_features_only(ordered_features):
    row = list(ordered_features.values())

    with open(CSV_PATH, "a", newline="") as f:
        wr = csv.writer(f)
        wr.writerow(row + ["", ""])  # placeholders for error and label

    # Determine row index (last row excluding header)
    with open(CSV_PATH, "r") as f:
        return sum(1 for _ in f) - 2


# ---------------------------------------------------------
# Update a specific CSV row with prediction
# ---------------------------------------------------------
def update_prediction(row_index, error, label):
    with open(CSV_PATH, "r") as f:
        rows = list(csv.reader(f))

    # Update specific row
    rows[row_index + 1][-2] = str(error) # this is the mse 
    rows[row_index + 1][-1] = str(label) # this is basicallly the prediction 

    with open(CSV_PATH, "w", newline="") as f:
        wr = csv.writer(f)
        wr.writerows(rows)


# ---------------------------------------------------------
# Handle incoming packet
# ---------------------------------------------------------
def handle_conn(conn, addr, model_runner):
    EXPECTED_FEATURE_COUNT = 18

    try:
        data = b""

        # -------------------------------------------------
        # Receive full JSON line (newline-terminated)
        # -------------------------------------------------
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

        print("\n==================== RECEIVER DEBUG ====================")
        print(f"[DEBUG] Raw packet from {addr}: {text}")

        # -------------------------------------------------
        # Parse JSON
        # -------------------------------------------------
        obj = json.loads(text)

        print("[DEBUG] Parsed JSON keys:", list(obj.keys()))
        print("[DEBUG] Feature count received:", len(obj))

        # -------------------------------------------------
        # STRICT FEATURE COUNT CHECK (DROP BAD PACKETS)
        # -------------------------------------------------
        if len(obj) != EXPECTED_FEATURE_COUNT:
            print(
                f"[DISCARDED] Packet from {addr} "
                f"has {len(obj)} features "
                f"(expected {EXPECTED_FEATURE_COUNT})"
            )
            print("[DISCARDED] Raw JSON:", obj)
            print("========================================================")
            return  # ⛔ STOP HERE — DO NOTHING ELSE

        # -------------------------------------------------
        # Schema validation (safe now)
        # -------------------------------------------------
        ordered = validate_and_fill(obj)

        fv = list(ordered.values())

        print("[DEBUG] Ordered feature dict:")
        print(ordered)
        print("[DEBUG] Feature vector:", fv)
        print("[DEBUG] Feature vector length:", len(fv))
        print("========================================================")

        # -------------------------------------------------
        # Save to CSV (features only)
        # -------------------------------------------------
        row_index = save_features_only(ordered)

        # -------------------------------------------------
        # Predict
        # -------------------------------------------------
        result = model_runner.predict(fv)

        print(
            f"[{addr}] {result['label'].upper()} "
            f"(error={result['reconstruction_error']:.6f})"
        )

        # -------------------------------------------------
        # Update CSV with prediction
        # -------------------------------------------------
        update_prediction(
            row_index,
            result["reconstruction_error"],
            result["label"]
        )

    except json.JSONDecodeError as e:
        print(f"[ERROR] Invalid JSON from {addr}: {e}")

    except Exception as e:
        print("Error handling connection:", e)

    finally:
        conn.close()

# ---------------------------------------------------------
# Main server loop
# ---------------------------------------------------------
def start_server():
    print("[Receiver] Loading model...")

    model_runner = ModelRunner(
        model_path="models/autoencoder.h5",
        scaler_path="models/scaler.save"
    )

    # Build CSV header dynamically
    sample_order = validate_and_fill({})  # empty -> filled with defaults
    header = list(sample_order.keys()) + ["reconstruction_error", "label"]
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
