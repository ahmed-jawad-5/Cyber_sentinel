# client/client_sender.py
import socket
import json
import time
import sys
from capture.flow_sniffer import FlowSnifferRunner
from config.settings import SERVER_IP, SERVER_PORT
from utils.logger import get_logger

logger = get_logger("ClientSender")

class FeatureTCPClient:
    def __init__(self, server_ip=SERVER_IP, server_port=SERVER_PORT):
        self.server_ip = server_ip
        self.server_port = server_port
        self.sock = None

    def connect(self, retries=3, retry_delay=2):
        for i in range(retries):
            try:
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.sock.connect((self.server_ip, self.server_port))
                logger.info(f"Connected to server {self.server_ip}:{self.server_port}")
                return True
            except Exception as e:
                logger.warning(f"Connect attempt {i+1} failed: {e}")
                time.sleep(retry_delay)
        logger.error("Could not connect to server")
        return False

    def send_features(self, features: dict):
        try:
            data = json.dumps(features, default=str).encode("utf-8") + b"\n"
            self.sock.sendall(data)
            logger.info("Sent feature vector")
        except Exception:
            logger.exception("Send error")

    def close(self):
        try:
            if self.sock:
                self.sock.close()
        except:
            pass

def main():
    client = FeatureTCPClient()
    if not client.connect():
        sys.exit(1)

    # callback: when sniffer has a features dict ready, send it over TCP
    def on_feature_ready(features):
        client.send_features(features)

    sniffer = FlowSnifferRunner(on_feature_ready=on_feature_ready)
    try:
        sniffer.start()
    except KeyboardInterrupt:
        logger.info("Keyboard Interrupt - stopping")
    finally:
        sniffer.stop()
        client.close()

if __name__ == "__main__":
    main()
