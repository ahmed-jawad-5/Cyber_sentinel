# server.py
import argparse
import time
from config import DEFAULT_HOST, DEFAULT_PORT, SIMULATED_PACKET_LOSS
from network.network_layer import UDPNetworkLayer
from app.handler import AppHandler
from utils.logger import get_logger

logger = get_logger("server")

def main():
    parser = argparse.ArgumentParser(description="UDP server (application + network separation)")
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--loss", type=float, default=SIMULATED_PACKET_LOSS,
                        help="Simulated packet loss probability (0.0-1.0)")
    args = parser.parse_args()

    bind = (args.host, args.port)
    net = UDPNetworkLayer(bind_addr=bind, loss_rate=args.loss)
    handler = AppHandler(net)

    # network layer will call handler.handle_raw(data, addr) in a new thread per packet
    net.start_listening(handler.handle_raw)

    logger.info(f"Server running on {bind}. Press Ctrl+C to stop.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down server...")
    finally:
        net.stop()

if __name__ == "__main__":
    main()
#python server.py --host 0.0.0.0 --port 9000
