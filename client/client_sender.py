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
SERVER_IP = "10.5.40.102"  # CHANGE THIS to server's IP
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

    # Names for the 34 features produced by FlowTracker.extract_34_features
    feature_names = [
        "total_pkts",          # 1
        "total_bytes",         # 2
        "pkt_size_mean",       # 3
        "pkt_size_std",        # 4
        "pkt_size_max",        # 5
        "pkt_size_min",        # 6
        "pkt_size_sum",        # 7
        "num_iat",             # 8
        "iat_mean",            # 9
        "iat_std",             # 10
        "iat_max",             # 11
        "iat_min",             # 12
        "flow_duration",       # 13
        "pkt_size_p10",        # 14
        "pkt_size_p20",        # 15
        "pkt_size_p30",        # 16
        "pkt_size_p40",        # 17
        "pkt_size_p50",        # 18
        "pkt_size_p60",        # 19
        "pkt_size_p70",        # 20
        "pkt_size_p80",        # 21
        "pkt_size_p90",        # 22
        "pkt_size_var",        # 23
        "iat_var",             # 24
        "last_pkt_size",       # 25
        "last_iat",            # 26
        "avg_bytes_per_pkt",   # 27
        "pkt_size_mean_sq",    # 28
        "iat_mean_sq",         # 29
        "pkt_size_std_sq",     # 30
        "iat_std_sq",          # 31
        "pkt_rate",            # 32
        "byte_rate",           # 33
        "num_pkts",            # 34
    ]

    def on_flow(flow_id, features):
        """Callback invoked by FlowSnifferRunner for each flow update.

        features is a list of 34 numeric values; we convert it to a dict.
        """
        if not features:
            return

        try:
            # Map list -> dict with stable, ordered keys
            features_dict = {
                feature_names[i]: json_safe_convert(features[i])
                for i in range(min(len(features), len(feature_names)))
            }

            # Send features to server for anomaly detection/storage
            send_flow_to_server(sock, features_dict)
        except Exception as e:
            logger.error(f"Error processing flow features: {e}")

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
