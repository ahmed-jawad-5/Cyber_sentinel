# server/receiver.py
"""
TCP Inference Server:
Receives JSON, validates schema, runs XGBoost model, prints prediction.
"""

import socket
import threading
import json

from generator.captures.feature_schema import validate_and_fill
from server.model_runner import ModelRunner      

HOST = "0.0.0.0"
PORT = 9000


def handle_conn(conn, addr, model_runner):
    """Handle a single TCP client connection."""
    try:
        data = b""

        # Read until newline or client closes connection
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

        # Parse incoming JSON
        obj = json.loads(text)

        # Ensure proper feature ordering
        ordered = validate_and_fill(obj)

        # Run model prediction
        result = model_runner.predict(ordered)

        print(
            f"[{addr}] Prediction: {result['label'].upper()} "
            f"(prob={result['prob']:.4f})"
        )

    except Exception as e:
        print("Error handling connection:", e)

    finally:
        conn.close()


def start_server():
    """Start the TCP inference server."""
    print("[Receiver] Loading model...")

    # Load model + scaler
    model_runner = ModelRunner(
        model_path="models/XGBoost_model.pkl",
        scaler_path="models/scaler.pkl"
    )

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
