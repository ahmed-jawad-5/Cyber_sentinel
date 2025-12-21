import socket
import json
import threading
import queue
import numpy as np
import time
import signal
import sys

# =========================================================
# GLOBAL STATE (controlled by API)
# =========================================================
outbound_queue = queue.Queue()
stop_event = threading.Event()
runtime_config = {}
sender_thread = None
sniffer_thread = None


# =========================================================
# DEBUG HELPERS
# =========================================================
def debug_print_flow(flow_data):
    print("\n===================== SENDER DEBUG =====================")
    print("[DEBUG] Sending flow to receiver")
    print("Keys:", list(flow_data.keys()))
    print("Values:", list(flow_data.values()))
    print("Feature count:", len(flow_data))

    arr = np.array(list(flow_data.values()), dtype=float)
    if np.isnan(arr).any():
        print("⚠ WARNING: NaN detected")
    if np.isinf(arr).any():
        print("⚠ WARNING: INF detected")

    print("=======================================================\n")


# =========================================================
# SENDER WORKER
# =========================================================
def sender_worker():
    print("[Sender] Worker started")

    while not stop_event.is_set():
        try:
            flow_data = outbound_queue.get(timeout=1)

            host = runtime_config["host"]
            port = runtime_config["port"]
            delay = runtime_config["delay"]

            debug_print_flow(flow_data)

            payload = json.dumps(flow_data) + "\n"

            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((host, port))
                s.sendall(payload.encode("utf-8"))

            print(f"[Sender] Sent → {host}:{port}")

            time.sleep(delay)

        except queue.Empty:
            continue
        except Exception as e:
            print("[Sender ERROR]", e)


# =========================================================
# FLOW TRACKER INTEGRATION
# =========================================================
def start_flow_tracker():
    from generator.captures import flow_tracker
    from generator.captures import feature_extractor, feature_schema

    flows = flow_tracker.flows
    flows_lock = flow_tracker.flows_lock
    original_expire = flow_tracker._expire_flow

    def patched_expire_flow(key):
        with flows_lock:
            flow_snapshot = flows.get(key)

        if flow_snapshot:
            features = feature_extractor.flow_to_features(flow_snapshot)
            ordered = feature_schema.validate_and_fill(features)

            print("\n📦 [FlowTracker] Flow expired → enqueue")
            print(ordered)

            outbound_queue.put(ordered)

        original_expire(key)

    flow_tracker._expire_flow = patched_expire_flow

    print("[FlowTracker] Packet sniffing started")
    flow_tracker.start_sniff(iface=None, filter="ip")  # blocking


# =========================================================
# PUBLIC API FUNCTIONS (USED BY FASTAPI)
# =========================================================
def start_sender(host: str, port: int, delay: float):
    global sender_thread, sniffer_thread

    if sender_thread and sender_thread.is_alive():
        print("[Sender] Already running")
        return

    runtime_config["host"] = host
    runtime_config["port"] = port
    runtime_config["delay"] = delay

    stop_event.clear()

    sender_thread = threading.Thread(target=sender_worker, daemon=True)
    sniffer_thread = threading.Thread(target=start_flow_tracker, daemon=True)

    sender_thread.start()
    sniffer_thread.start()

    print(f"[Sender] Started → {host}:{port} (delay={delay}s)")


def stop_sender():
    stop_event.set()

    while not outbound_queue.empty():
        try:
            outbound_queue.get_nowait()
        except queue.Empty:
            break

    print("[Sender] Stopped")


# =========================================================
# SAFE SHUTDOWN
# =========================================================
# def signal_handler(sig, frame):
#     print("\n[Shutdown] Sender stopping...")
#     stop_sender()
#     sys.exit(0)


# signal.signal(signal.SIGINT, signal_handler)
