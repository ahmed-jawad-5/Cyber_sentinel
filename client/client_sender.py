# client/client_sender.py
import socket
import json
import threading
import queue
import signal
import sys
import numpy as np
import time  # ← new import for delay

# --- Configuration ---
SERVER_HOST = "10.5.41.146"
SERVER_PORT = 9000
PACKET_DELAY = 60  # seconds between packets
# ---------------------

# Queue for outbound flows
outbound_queue = queue.Queue()


def debug_print_flow(flow_data):
    print("\n========================= SENDER DEBUG =========================")
    print("[DEBUG] About to send flow to server...")
    print("\n[DEBUG] Feature Keys (in order):")
    print(list(flow_data.keys()))
    print("\n[DEBUG] Feature Values:")
    print(list(flow_data.values()))
    print("\n[DEBUG] Feature Count:", len(flow_data))

    arr = np.array(list(flow_data.values()), dtype=float)
    if np.isnan(arr).any():
        print("⚠️ WARNING: Feature vector contains NaN values!")
    if np.isinf(arr).any():
        print("⚠️ WARNING: Feature vector contains INF values!")
    print("===============================================================\n")


def sender_worker():
    """Background thread: takes completed flows from queue and sends them."""
    print(f"[Sender] Connecting to {SERVER_HOST}:{SERVER_PORT} for each flow...")

    while True:
        try:
            flow_data = outbound_queue.get()
            if flow_data is None:
                break  # Shutdown

            # Debug print before sending
            debug_print_flow(flow_data)

            # Convert OrderedDict/dict → JSON line
            json_line = json.dumps(flow_data) + "\n"

            # Send TCP packet
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((SERVER_HOST, SERVER_PORT))
                s.sendall(json_line.encode('utf-8'))

            # Log sent info
            sbytes = flow_data.get('sbytes', 0)
            dbytes = flow_data.get('dbytes', 0)
            print(f"[Sent] → flow ({sbytes}↑ {dbytes}↓ bytes)")

            # --- NEW: delay between packets ---
            time.sleep(PACKET_DELAY)

        except (ConnectionRefusedError, BrokenPipeError, OSError):
            print(f"[Error] Could not connect to {SERVER_HOST}:{SERVER_PORT} — server down?")
            outbound_queue.put(flow_data)  # retry
            break

        except Exception as e:
            print(f"[Sender Error] {e}")

        finally:
            try:
                outbound_queue.task_done()
            except Exception:
                pass


def enqueue_flow(flow_ordered_dict):
    outbound_queue.put(flow_ordered_dict)


def start_flow_tracker():
    from generator.captures import flow_tracker
    from generator.captures import feature_extractor, feature_schema

    start_sniff = flow_tracker.start_sniff
    flows = flow_tracker.flows
    flows_lock = flow_tracker.flows_lock
    original_expire = flow_tracker._expire_flow

    def new_expire_flow(key):
        with flows_lock:
            flow_snapshot = flows.get(key)

        if flow_snapshot:
            features = feature_extractor.flow_to_features(flow_snapshot)
            ordered = feature_schema.validate_and_fill(features)
            print("\n📦 [FlowTracker] Extracted features for flow:")
            print(ordered)
            enqueue_flow(ordered)

        original_expire(key)  # delete flow

    flow_tracker._expire_flow = new_expire_flow
    print("[FlowTracker] Starting packet capture...")
    start_sniff(iface=None, filter="ip")  # blocking


def signal_handler(sig, frame):
    print("\n[Shutdown] Stopping...")
    outbound_queue.put(None)
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)


if __name__ == "__main__":
    print("=== Real-time UNSW-NB15 Flow Exporter (18-features) ===\n")
    print(f"Sending flows → {SERVER_HOST}:{SERVER_PORT}")
    print("Press Ctrl+C to stop\n")

    sender_thread = threading.Thread(target=sender_worker, daemon=True)
    sender_thread.start()

    try:
        start_flow_tracker()
    except KeyboardInterrupt:
        pass
    finally:
        outbound_queue.put(None)
        sender_thread.join(timeout=2)
        print("Goodbye!")
