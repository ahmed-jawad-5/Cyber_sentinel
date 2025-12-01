# client/client_sender.py
import socket
import json
import time
from capture.flow_sniffer import FlowSnifferRunner
from utils.logger import get_logger

logger = get_logger("CLIENT")

SERVER_IP = "10.5.40.102"     # CHANGE THIS
SERVER_PORT = 9000

def send_flow_to_server(flow_features):
    """Send extracted feature dict to server."""
    try:
        data = json.dumps(flow_features).encode()
        sock.sendall(data + b"\n")
        logger.info(f"[SENT] {flow_features}")
    except Exception as e:
        logger.error(f"Send error: {e}")

if __name__ == "__main__":
    logger.info(f"Connecting to server {SERVER_IP}:{SERVER_PORT}...")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((SERVER_IP, SERVER_PORT))
    logger.info("Connected!")

    # Initialize sniffer
    runner = FlowSnifferRunner()

    logger.info("Starting packet sniffer...")
    for flow in runner.run_sniffer():
        # flow = dict with 34 features
        send_flow_to_server(flow)

    sock.close()
