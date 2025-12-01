import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# client/client_sender.py
import sys
import socket
import json
import time
import logging
import threading

import netifaces
import numpy as np
from scapy.all import send

from generator.packet_generator import PacketGenerator

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from capture.flow_sniffer import FlowSnifferRunner
from utils.logger import get_logger

logger = get_logger("CLIENT")

# -------------------- CONFIG --------------------
SERVER_IP = "10.5.45.31"  # CHANGE THIS to server's IP
SERVER_PORT = 9000

# ----------------- HELPER FUNCTIONS -----------------
def get_default_interface():
    """Automatically get the primary interface."""
    gateways = netifaces.gateways()
    default_iface = gateways['default'][netifaces.AF_INET][1]
    return default_iface

def json_safe_convert(obj):
    """Convert NumPy types to native Python types for JSON serialization."""
    if isinstance(obj, np.generic):
        return obj.item()
    return obj

def send_flow_to_server(sock, flow_features):
    """Send extracted flow features to the server over TCP.

    flow_features is expected to be a dict mapping feature names to values.
    """
    try:
        # Convert all values to JSON-safe
        safe_flow = {k: json_safe_convert(v) for k, v in flow_features.items()}
        data = json.dumps(safe_flow).encode()
        sock.sendall(data + b"\n")
        logger.info(f"[SENT] {safe_flow}")
    except Exception as e:
        logger.error(f"Send error: {e}")

# ------------------- MAIN -------------------
if __name__ == "__main__":
    # Determine interface
    iface = get_default_interface()
    logger.info(f"Using network interface: {iface}")

    # Connect to TCP server
    logger.info(f"Connecting to server {SERVER_IP}:{SERVER_PORT}...")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((SERVER_IP, SERVER_PORT))
        logger.info("Connected to server!")
    except Exception as e:
        logger.error(f"Connection failed: {e}")
        exit(1)

    # Initialize packet sniffer and packet generator
    runner = FlowSnifferRunner(interface=iface)
    pkt_gen = PacketGenerator()  # uses its default dst_ip

    logger.info("Starting packet sniffer and packet generator...")

    stop_event = threading.Event()

    def on_flow(flow_id, features):
        """Callback invoked by FlowSnifferRunner for each packet.

        `features` is already a dict with schema-defined feature names
        (proto, state, sbytes, dbytes, sttl, ...).
        """
        if not features:
            return

        try:
            # Directly forward the feature dict to the server
            send_flow_to_server(sock, features)
        except Exception as e:
            logger.error(f"Error processing features: {e}")

    def sniffer_thread():
        try:
            runner.start(on_flow)
        except Exception as e:
            logger.error(f"Sniffer error: {e}")
            stop_event.set()

    def generator_thread():
        try:
            while not stop_event.is_set():
                pkt, label = pkt_gen.generate_packet()
                logger.info(f"[GENERATOR] Created {label} packet")
                send(pkt, verbose=False)
                time.sleep(0.1)
        except Exception as e:
            logger.error(f"Packet generator error: {e}")
            stop_event.set()

    t_sniff = threading.Thread(target=sniffer_thread, daemon=True)
    t_gen = threading.Thread(target=generator_thread, daemon=True)

    t_sniff.start()
    t_gen.start()

    try:
        while not stop_event.is_set():
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Stopping due to keyboard interrupt...")
        stop_event.set()
    finally:
        sock.close()
        logger.info("Connection closed.")
