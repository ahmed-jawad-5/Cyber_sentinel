import socket
import threading
import json
import csv
import os
import time
import numpy as np

from generator.captures.feature_schema import validate_and_fill
from server.model_runner import ModelRunner

# ----------------------------
# CONFIG
# ----------------------------
HOST = "0.0.0.0"
PORT = 9000
CSV_PATH = "results.csv"
EXPECTED_FEATURE_COUNT = 18

csv_lock = threading.Lock()

# ---------------------------------------------------------
def init_csv(header):
    if not os.path.exists(CSV_PATH):
        with open(CSV_PATH, "w", newline="") as f:
            wr = csv.writer(f)
            wr.writerow(header)
        print(f"[Receiver] Created CSV file: {CSV_PATH}")

def save_features_only(ordered_features):
    # Convert any numpy types to python types for CSV writing
    row = [v.item() if hasattr(v, 'item') else v for v in ordered_features.values()]
    with csv_lock:
        with open(CSV_PATH, "a", newline="") as f:
            wr = csv.writer(f)
            wr.writerow(row + ["", ""])
        
        try:
            with open(CSV_PATH, "r") as f:
                return sum(1 for _ in f) - 1
        except:
            return 0

def update_prediction(row_index, value, label):
    with csv_lock:
        if not os.path.exists(CSV_PATH):
            return
        with open(CSV_PATH, "r") as f:
            rows = list(csv.reader(f))

        if row_index < len(rows):
            # Ensure we save as strings/floats, not numpy types
            rows[row_index][-2] = str(float(value))
            rows[row_index][-1] = str(label)

            with open(CSV_PATH, "w", newline="") as f:
                wr = csv.writer(f)
                wr.writerows(rows)

def handle_conn(conn, addr, model_runner, callback):
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
        fv = list(ordered.values())

        # 1. Save features to CSV
        row_index = save_features_only(ordered)

        # 2. XGBoost Prediction
        result = model_runner.predict(fv)
        
        # Extract and cast NumPy types to standard Python types
        # This prevents the "numpy.float32 is not iterable" error in FastAPI
        raw_value = result["prediction"]
        raw_label = result["label"]
        
        value = float(raw_value) if hasattr(raw_value, 'item') else raw_value
        label = str(raw_label)

        # 3. Update the CSV
        update_prediction(row_index, value, label)

        # 4. Push to UI via API Callback
        if callback:
            # Deep sanitize the ordered dictionary (features)
            clean_flow = {}
            for k, v in ordered.items():
                if hasattr(v, 'item'): # Handle numpy types
                    clean_flow[k] = v.item()
                else:
                    clean_flow[k] = v

            # Add prediction results into the flow object for the UI
            clean_flow["label"] = label
            clean_flow["reconstruction_error"] = round(value, 6)
            clean_flow["id"] = f"PKT-{int(time.time()*1000)}"
            clean_flow["srcip"] = str(addr[0])

            ui_payload = {
                "flow": clean_flow,
                "rag_prompt": None
            }
            
            callback(ui_payload)

        print(f"[{addr}] Processed: {label.upper()} ({value:.4f})")

    except Exception as e:
        print(f"[ERROR] Connection from {addr}: {e}")
    finally:
        conn.close()

def start_server(callback=None):
    print("[Receiver] Initializing Model...")
    model_runner = ModelRunner(
        model_path="models/XGBoost_model.pkl",
        scaler_path="models/scaler.save"
    )

    # Setup CSV
    sample_order = validate_and_fill({})
    header = list(sample_order.keys()) + ["prediction", "label"]
    init_csv(header)

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((HOST, PORT))
    s.listen(10)

    print(f"[Receiver] Running on {HOST}:{PORT}")

    try:
        while True:
            conn, addr = s.accept()
            threading.Thread(
                target=handle_conn,
                args=(conn, addr, model_runner, callback),
                daemon=True
            ).start()
    except KeyboardInterrupt:
        print("\n[Receiver] Shutting down...")
    finally:
        s.close()

if __name__ == "__main__":
    # Test mode
    start_server(callback=lambda x: print(f"DEBUG CALLBACK: {x['flow']['label']}"))