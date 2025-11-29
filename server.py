# server.py
import argparse
import time
from network.network_layer import NetworkLayer
from app.handler import AppHandler
from utils.logger import get_logger
from config import DEFAULT_HOST, DEFAULT_PORT, SIMULATED_PACKET_LOSS

logger = get_logger("server")

def main():
    parser = argparse.ArgumentParser(description="UDP Server")
    parser.add_argument("--host", default=DEFAULT_HOST, help="Local IP to bind")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Local UDP port")
    parser.add_argument("--loss", type=float, default=SIMULATED_PACKET_LOSS, help="Packet loss 0-1")
    args = parser.parse_args()

    # Correct NetworkLayer initialization
    net = NetworkLayer(local_ip=args.host, local_port=args.port, loss_rate=args.loss)
    handler = AppHandler(net)
    net.start_listening(handler.handle_raw)

    logger.info(f"Server running on {args.host}:{args.port} - Press Ctrl+C to stop")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Server shutting down...")
    finally:
        net.stop()

if __name__ == "__main__":
    main()
