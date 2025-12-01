# server/server_receiver.py
import socket
import json
import csv
import xgboost as xgb
import numpy as np
from utils.logger import get_logger
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logger = get_logger("SERVER")

HOST = "0.0.0.0"
PORT = 9000

# load model
model = xgb.XGBClassifier()
model.load_model("models/xg_boost.pkl")

csv_file = open("output/received_flows.csv", "a", newline="")
writer = None

def predict(features):
    global writer

    if writer is None:
        writer = csv.DictWriter(csv_file, fieldnames=list(features.keys()) + ["anomaly"])
        writer.writeheader()

    X = np.array(list(features.values()), dtype=float).reshape(1, -1)

    pred = model.predict(X)[0]
    features["anomaly"] = int(pred)

    writer.writerow(features)
    csv_file.flush()

    logger.info(f"[FLOW RECEIVED] anomaly={pred}")

def start_server():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((HOST, PORT))
    sock.listen(5)

    logger.info(f"Server listening on {HOST}:{PORT}")

    conn, addr = sock.accept()
    logger.info(f"Connected by {addr}")

    buffer = ""

    while True:
        data = conn.recv(4096)
        if not data:
            break

        buffer += data.decode()
        while "\n" in buffer:
            line, buffer = buffer.split("\n", 1)
            try:
                features = json.loads(line)
                predict(features)
            except Exception as e:
                logger.error(f"JSON error: {e}")

    conn.close()

if __name__ == "__main__":
    start_server()
