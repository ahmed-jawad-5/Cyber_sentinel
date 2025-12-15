"""
TCP Inference Server:
Receives JSON, validates schema,
SAVES FEATURES FIRST,
then runs Autoencoder model and updates CSV with prediction.
"""

import socket
import threading
import json
import csv
import os

from generator.captures.feature_schema import validate_and_fill
from server.model_runner import run_inference, ALERT_BUFFER

HOST = "0.0.0.0"
PORT = 9000
CSV_PATH = "results.csv"

# ---------------- CONTROL FLAGS ----------------
RUNNING = False
server_socket = None

# ---------------- CSV Utilities ----------------
def init_csv(header):
    if not os.path.exists(CSV_PATH):
        with open(CSV_PATH, "w", newline="") as f:
            wr = csv.writer(f)
            wr.writerow(header)
        print(f"[Receiver] Created CSV file: {CSV_PATH}")

def save_features_only(ordered_features):
    row = list(ordered_features.values())
    with open(CSV_PATH, "a", newline="") as f:
        wr = csv.writer(f)
        wr.writerow(row + ["", ""])
    with open(CSV_PATH, "r") as f:
        return sum(1 for _ in f) - 2  # last row index

def update_prediction(row_index, error, label):
    with open(CSV_PATH, "r") as f:
        rows = list(csv.reader(f))
    rows[row_index + 1][-2] = str(error)
    rows[row_index + 1][-1] = str(label)
    with open(CSV_PATH, "w", newline="") as f:
        wr = csv.writer(f)
        wr.writerows(rows)

# ---------------- Packet Handler ----------------
def handle_conn(conn, addr):
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

        obj = json.loads(text)
        ordered = validate_and_fill(obj)

        # Save row
        row_index = save_features_only(ordered)

        # Predict
        result = run_inference(list(ordered.values()))

        print(f"[{addr}] {result['label'].upper()} (error={result['reconstruction_error']:.6f})")

        # Update CSV
        update_prediction(row_index, result["reconstruction_error"], result["label"])

    except Exception as e:
        print(f"[Receiver] Error handling connection {addr}: {e}")
    finally:
        conn.close()

# ---------------- Server Control ----------------
def start_receiver():
    global RUNNING, server_socket

    if RUNNING:
        print("[Receiver] Already running")
        return

    RUNNING = True

    # Init CSV
    sample_order = validate_and_fill({})
    header = list(sample_order.keys()) + ["reconstruction_error", "label"]
    init_csv(header)

    # Start TCP server
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen(5)
    print(f"[Receiver] Listening on {HOST}:{PORT} ...")

    try:
        while RUNNING:
            server_socket.settimeout(1.0)  # check RUNNING every second
            try:
                conn, addr = server_socket.accept()
            except socket.timeout:
                continue

            threading.Thread(target=handle_conn, args=(conn, addr), daemon=True).start()

    except Exception as e:
        print(f"[Receiver] Exception: {e}")

    finally:
        server_socket.close()
        server_socket = None
        RUNNING = False
        print("[Receiver] Stopped")

def stop_receiver():
    global RUNNING, server_socket
    RUNNING = False
    print("[Receiver] Stopping receiver...")
    if server_socket:
        try:
            # Dummy connect to unblock accept()
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((HOST, PORT))
            s.close()
        except:
            pass
