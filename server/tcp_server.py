import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import socket
import json
import pickle
import traceback

HOST = "0.0.0.0"
PORT = 9000

MODEL_PATH = "model/xg_boost.pkl"    # Adjust path if needed

print("[INFO] Starting UDP receiver...")

try:
    with open(MODEL_PATH, "rb") as f:
        model = pickle.load(f)
    print("[INFO] Model loaded successfully!")
except Exception as e:
    print("[ERROR] Model load failed:", e)
    model = None  # continue without prediction

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((HOST, PORT))

print(f"[INFO] Receiver listening on {HOST}:{PORT}")

while True:
    try:
        data, addr = sock.recvfrom(65535)

        print(f"\n[INFO] Packet received from {addr}")
        print(f"[DEBUG RAW] {data}")

        try:
            decoded = json.loads(data.decode())
        except:
            print("[ERROR] JSON decode failed:", traceback.format_exc())
            continue

        print("[DEBUG] Parsed JSON:", decoded)

        # Extract features for the model
        features = [
            len(decoded.get("src_ip", "")),
            len(decoded.get("dst_ip", "")),
            int(decoded.get("src_port", 0)),
            int(decoded.get("dst_port", 0)),
            int(decoded.get("payload_size", 0))
        ]

        print("[DEBUG] Features:", features)

        # If model loaded, predict
        if model:
            try:
                prediction = model.predict([features])[0]
                print("[INFO] Prediction:", "ANOMALY" if prediction == 1 else "NORMAL")
            except Exception as e:
                print("[ERROR] Model prediction failed:", e)
        else:
            print("[WARN] Model not loaded; skipping prediction")

    except Exception as e:
        print("[ERROR] Exception:", e)
        print(traceback.format_exc())
