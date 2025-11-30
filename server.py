# server.py
import time
import argparse
from network.network_layer import NetworkLayer
from app.handler import AppHandler
from utils.logger import get_logger

logger = get_logger("server")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=9000)
    parser.add_argument("--loss", type=float, default=0.0)
    args = parser.parse_args()

    net = NetworkLayer(bind=(args.host, args.port), loss_rate=args.loss)
    handler = AppHandler(net)

    net.start_listening(handler.handle_raw)

    logger.info(f"Server running on {args.host}:{args.port}")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        net.stop()


if __name__ == "__main__":
    main()
