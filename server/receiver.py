EXPECTED_FEATURE_COUNT = 18
import socket
import threading
import json
import csv
import os

from generator.captures.feature_schema import validate_and_fill
from server.model_runner import ModelRunner
from server.rag_runner import RAGRunner

# ----------------------------
# FAISS IMPORT FIX
# ----------------------------
try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    print("[RAG WARNING] faiss not installed. RAG functionality will be disabled.")
    FAISS_AVAILABLE = False

csv_lock = threading.Lock()
rag_lock = threading.Lock()
rag_trigger_count = 0
MAX_RAG_TRIGGERS = 3

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


def save_features_only(ordered_features):
    row = list(ordered_features.values())
    with csv_lock:
        with open(CSV_PATH, "a", newline="") as f:
            wr = csv.writer(f)
            wr.writerow(row + ["", "", ""])  # placeholders: prediction, label, rag_output
        return sum(1 for _ in open(CSV_PATH)) - 1


def update_prediction(row_index, value, label, rag_output=None):
    with csv_lock:
        with open(CSV_PATH, "r") as f:
            rows = list(csv.reader(f))

        if row_index >= len(rows):
            print(f"[CSV ERROR] Cannot update row {row_index}.")
            return

        rows[row_index][-3] = str(value)
        rows[row_index][-2] = str(label)
        if rag_output is not None:
            rows[row_index][-1] = str(rag_output)

        with open(CSV_PATH, "w", newline="") as f:
            wr = csv.writer(f)
            wr.writerows(rows)


def handle_conn(conn, addr, model_runner, rag_runner):
    global rag_trigger_count
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
            print(f"[DISCARDED] Packet from {addr} has {len(obj)} features")
            return

        ordered = validate_and_fill(obj)
        fv = list(ordered.values())
        row_index = save_features_only(ordered)

        # -----------------------------
        # Prediction
        # -----------------------------
        result = model_runner.predict(fv)
        value = result["prediction"]
        label = result["label"]

        rag_output = None

        # -----------------------------
        # RAG TRIGGER (FIRST 3 ANOMALIES)
        # -----------------------------
        if label != "normal" and FAISS_AVAILABLE:
            with rag_lock:
                if rag_trigger_count < MAX_RAG_TRIGGERS:
                    rag_trigger_count += 1
                    print(f"[RAG] Trigger #{rag_trigger_count} for {addr}")
                    try:
                        # Convert JSON to feature string like training
                        query_str = " | ".join([f"{k}: {v}" for k, v in ordered.items()])

                        # Embed query
                        q_emb = rag_runner.emb_model.encode([query_str], convert_to_numpy=True)
                        faiss.normalize_L2(q_emb)

                        # Check if index exists and has entries
                        if rag_runner.index.ntotal == 0:
                            print("[RAG WARNING] FAISS index is empty.")
                            rag_output = "[RAG] No knowledge available"
                        else:
                            # Retrieve top-K
                            D, I = rag_runner.index.search(q_emb, rag_runner.top_k)
                            retrieved_docs = []
                            for i in I[0].tolist():
                                if i < len(rag_runner.metadata):
                                    retrieved_docs.append(rag_runner.metadata[i])

                            if not retrieved_docs:
                                rag_output = "[RAG] No relevant documents found"
                            else:
                                # Build prompt
                                prompt = rag_runner.build_prompt_with_context(query_str, retrieved_docs, detailed=True)
                                # Generate RAG output
                                rag_output = rag_runner.llm.generate(prompt, max_new_tokens=200)
                                if not rag_output.strip():
                                    rag_output = "[RAG] Model returned empty output"

                        print(f"[RAG OUTPUT]\n{rag_output}")

                    except Exception as e:
                        print("[RAG ERROR]:", e)
                        rag_output = "[RAG ERROR]"

        update_prediction(row_index, value, label, rag_output)
        print(f"[{addr}] Prediction: {label.upper()} (value={value:.6f})")

    except Exception as e:
        print("[ERROR] Handling connection:", e)
    finally:
        conn.close()


def start_server():
    print("[Receiver] Loading model...")
    model_runner = ModelRunner(
        model_path="models/XGBoost_model.pkl",
        scaler_path="models/scaler.save",
        normal_threshold=0.15
    )

    rag_runner = RAGRunner()

    # CSV header
    sample_order = validate_and_fill({})
    header = list(sample_order.keys()) + ["reconstruction_error", "label", "rag_output"]
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
                args=(conn, addr, model_runner, rag_runner),
                daemon=True
            ).start()
    finally:
        s.close()


if __name__ == "__main__":
    start_server()
