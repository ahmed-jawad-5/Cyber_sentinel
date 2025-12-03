"""
server/receiver.py

TCP server that receives JSON rows (one per connection or newline terminated),
validates the schema using the same feature order, and runs the XGBoost model to
predict anomaly vs normal. Prints the result.

Run on the receiver laptop (Laptop B).
"""
import socket
import threading
import json
from collections import OrderedDict
from generator.captures.feature_schema import FEATURE_ORDER, validate_and_fill
from .model_loader import ModelWrapper

HOST = "0.0.0.0"
PORT = 9000

def handle_conn(conn, addr, model):
    try:
        data = b""
        # read until socket closes or newline
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
        pred = model.predict(ordered)
        label = "ANOMALY" if float(pred) > 0.5 else "NORMAL"
        print(f"[{addr}] Prediction: {label} (score={pred:.4f})")
    except Exception as e:
        print("Error handling connection:", e)
    finally:
        conn.close()

def start_server(model_path="model.json"):
    model = ModelWrapper(model_path)
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((HOST, PORT))
    s.listen(5)
    print(f"Receiver listening on {HOST}:{PORT} ...")
    try:
        while True:
            conn, addr = s.accept()
            t = threading.Thread(target=handle_conn, args=(conn, addr, model), daemon=True)
            t.start()
    except KeyboardInterrupt:
        print("Shutting down receiver.")
    finally:
        s.close()

if __name__ == "__main__":
    start_server()
