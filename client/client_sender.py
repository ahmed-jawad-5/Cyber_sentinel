import socket
import json
import threading
import queue
import signal
import sys

# --- Configuration ---
SERVER_HOST = "192.168.1.2"   # Your receiver/server IP
SERVER_PORT = 9000
# ---------------------

# Queue for outbound flows
outbound_queue = queue.Queue()


def sender_worker():
    """Background thread: takes completed flows from queue and sends them."""
    print(f"[Sender] Connecting to {SERVER_HOST}:{SERVER_PORT} for each flow...")
    while True:
        try:
            flow_data = outbound_queue.get()
            if flow_data is None:  # Shutdown signal
                break

            # Convert OrderedDict → JSON line
            json_line = json.dumps(flow_data) + "\n"

            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((SERVER_HOST, SERVER_PORT))
                s.sendall(json_line.encode('utf-8'))

            print(f"[Sent] → {flow_data['proto']} {flow_data.get('service','?')} flow "
                  f"({flow_data['sbytes']}↑ {flow_data['dbytes']}↓ bytes)")

        except (ConnectionRefusedError, BrokenPipeError, OSError):
            print(f"[Error] Could not connect to {SERVER_HOST}:{SERVER_PORT} — is the server running?")
            outbound_queue.put(flow_data)  # Retry later
            break
        except Exception as e:
            print(f"[Sender Error] {e}")
        finally:
            outbound_queue.task_done()


def enqueue_flow(flow_ordered_dict):
    """Public function called by flow_tracker when a flow is complete."""
    outbound_queue.put(flow_ordered_dict)


# === Patch flow_tracker to use our queue ===
def start_flow_tracker():
    """
    Patch flow_tracker._expire_flow so that when a flow completes,
    we extract its features and send them to the server.
    """
    # ✅ Correct relative imports for your folder structure
    from generator.captures import flow_tracker
    from generator.captures import feature_extractor
    from generator.captures import feature_schema

    # References
    start_sniff = flow_tracker.start_sniff
    flows = flow_tracker.flows
    flows_lock = flow_tracker.flows_lock
    original_expire = flow_tracker._expire_flow

    # --- Patched expire function ---
    def new_expire_flow(key):
        with flows_lock:
            flow_snapshot = flows.get(key)

        if flow_snapshot:
            # Convert flow → 34 features → OrderedDict
            features = feature_extractor.flow_to_features(flow_snapshot)
            ordered = feature_schema.validate_and_fill(features)
            # Send to server
            enqueue_flow(ordered)

        # Now call the original logic (which deletes the flow)
        original_expire(key)

    # Patch the flow tracker
    flow_tracker._expire_flow = new_expire_flow

    print("[FlowTracker] Starting packet capture...")

    # Start sniffing (blocking)
    start_sniff(iface=None, filter="ip")


# === Graceful shutdown ===
def signal_handler(sig, frame):
    print("\n[Shutdown] Stopping...")
    outbound_queue.put(None)  # Stop sender
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)


# === Main ===
if __name__ == "__main__":
    print("=== Real-time UNSW-NB15 Flow Exporter ===\n")
    print(f"Sending flows → {SERVER_HOST}:{SERVER_PORT}")
    print("Press Ctrl+C to stop\n")

    # Start sender thread
    sender_thread = threading.Thread(target=sender_worker, daemon=True)
    sender_thread.start()

    # Start flow tracking (blocking)
    try:
        start_flow_tracker()
    except KeyboardInterrupt:
        pass
    finally:
        outbound_queue.put(None)
        sender_thread.join(timeout=2)
        print("Goodbye!")
