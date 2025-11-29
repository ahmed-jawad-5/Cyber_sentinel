# client.py
import argparse
import threading
import time
from config import BUFFER_SIZE
from network.network_layer import UDPNetworkLayer
from app.application_layer import make_message, parse_message
from utils.logger import get_logger

logger = get_logger("client")

def start_receiver(network: UDPNetworkLayer):
    def on_receive(raw, addr):
        parsed = parse_message(raw)
        if parsed:
            logger.info(f"RECV from {addr}: type={parsed.get('msg_type')} seq={parsed.get('seq')} payload={parsed.get('payload')}")
        else:
            logger.info(f"RECV raw from {addr}: {raw[:100]!r}")

    network.start_listening(on_receive)

def interactive_loop(network: UDPNetworkLayer, server_addr):
    seq = 0
    try:
        while True:
            text = input("Enter message (or /ping or /quit): ").strip()
            if not text:
                continue
            if text == "/quit":
                break
            if text == "/ping":
                pkt = make_message("ping", {}, seq=seq)
            else:
                pkt = make_message("message", {"text": text}, seq=seq)
            network.send(server_addr, pkt)
            logger.debug(f"Sent seq={seq} to {server_addr}")
            seq += 1
    except KeyboardInterrupt:
        pass

def main():
    parser = argparse.ArgumentParser(description="UDP client")
    parser.add_argument("--server-host", required=True)
    parser.add_argument("--server-port", type=int, required=True)
    parser.add_argument("--bind-host", default="0.0.0.0")
    parser.add_argument("--bind-port", type=int, default=0, help="0 = ephemeral port")
    parser.add_argument("--loss", type=float, default=0.0, help="simulate send loss locally")
    args = parser.parse_args()

    bind = (args.bind_host, args.bind_port)
    network = UDPNetworkLayer(bind_addr=bind, loss_rate=args.loss)
    start_receiver(network)

    server = (args.server_host, args.server_port)
    logger.info(f"Client bound to {bind}, sending to {server}")
    interactive_loop(network, server)

    network.stop()
    logger.info("Client exited")

if __name__ == "__main__":
    main()
#python client.py --server-host 192.168.1.50 --server-port 9000
