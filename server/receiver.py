# server/receiver.py

EXPECTED_FEATURE_COUNT = 18
import socket
import threading
import json
import csv
import os

<<<<<<< HEAD
=======
# Count how many anomalous packets have triggered RAG
rag_trigger_count = 0
MAX_RAG_TRIGGERS = 3  # only first 3 anomalous packets
rag_lock = threading.Lock()  # protect counter in multi-threaded server


>>>>>>> b7ffa7520782d2826c15124d9cfe3ee14ed86a66
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
<<<<<<< HEAD
def update_prediction(row_index, value, label):
=======
def update_prediction(row_index, value, label, rag_output=None):
>>>>>>> b7ffa7520782d2826c15124d9cfe3ee14ed86a66
    with csv_lock:
        with open(CSV_PATH, "r") as f:
            rows = list(csv.reader(f))

        if row_index >= len(rows):
<<<<<<< HEAD
            print(f"[CSV ERROR] Cannot update row {row_index}. CSV has only {len(rows)} rows.")
            return

        # store prediction value and label
        rows[row_index][-2] = str(value)
        rows[row_index][-1] = str(label)
=======
            print(f"[CSV ERROR] Cannot update row {row_index}.")
            return

        rows[row_index][-2] = str(value)
        rows[row_index][-1] = str(label)

        if rag_output is not None:
            if len(rows[row_index]) < len(rows[0]):
                rows[row_index].append(str(rag_output))
            else:
                rows[row_index][-1] = str(rag_output)
>>>>>>> b7ffa7520782d2826c15124d9cfe3ee14ed86a66

        with open(CSV_PATH, "w", newline="") as f:
            wr = csv.writer(f)
            wr.writerows(rows)


<<<<<<< HEAD
=======

>>>>>>> b7ffa7520782d2826c15124d9cfe3ee14ed86a66
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

<<<<<<< HEAD
        update_prediction(row_index, value, label)
        print(f"[{addr}] Prediction: {label.upper()} (value={value:.6f})")

=======
        rag_output = None
        global rag_trigger_count

        # Trigger RAG only for first 3 anomalous packets
        if label != "normal":
            with rag_lock:
                if rag_trigger_count < MAX_RAG_TRIGGERS:
                    rag_trigger_count += 1
                    query = json.dumps(obj)  # send packet JSON as query
                    try:
                        rag_output = rag_runner.generate(query, detailed=True)
                        print(f"[RAG OUTPUT] {rag_output}")
                    except Exception as e:
                        print("[RAG ERROR]:", e)

        update_prediction(row_index, value, label, rag_output)

        print(f"[{addr}] Prediction: {label.upper()} (value={value:.6f})")

>>>>>>> b7ffa7520782d2826c15124d9cfe3ee14ed86a66
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
    # Initialize RAG runner
    from server.rag_runner import RAGRunner
    rag_runner = RAGRunner()

<<<<<<< HEAD
    # Build CSV header dynamically
    sample_order = validate_and_fill({})
    header = list(sample_order.keys()) + ["prediction_value", "predicted_label"]
=======


    # Build CSV header dynamically
    sample_order = validate_and_fill({})
    header = list(sample_order.keys()) + ["reconstruction_error", "label", "rag_output"]
>>>>>>> b7ffa7520782d2826c15124d9cfe3ee14ed86a66
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
