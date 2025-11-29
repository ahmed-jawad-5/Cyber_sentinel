import argparse
import time
from network.network_layer import NetworkLayer
from app.application_layer import make_message, parse_message
from utils.logger import get_logger

logger = get_logger("client")


def start_receiver(net: NetworkLayer):
    """Start background receiver."""
    def on_receive(data, addr):
        msg = parse_message(data)
        if msg:
            logger.info(f"Received from {addr}: {msg}")
        else:
            logger.warning(f"Received unparseable data from {addr}: {data}")

    net.start_listening(on_receive)


def interactive_sender(net: NetworkLayer, server_addr):
    """Send messages interactively to the server."""
    seq = 0
    try:
        while True:
            text = input("Enter message (/ping or /quit): ").strip()

            if text.lower() == "/quit":
                break

            if text.lower() == "/ping":
                packet = make_message("ping", {}, seq=seq)
            else:
                packet = make_message("message", {"text": text}, seq=seq)

            # send bytes to server
            net.send(packet, server_addr)
            seq += 1

    except KeyboardInterrupt:
        print("\n[Client] Exiting...")


def main():
    parser = argparse.ArgumentParser(description="UDP Client")
    parser.add_argument("--server-host", required=True, help="Server IP to send packets to")
    parser.add_argument("--server-port", type=int, required=True, help="Server UDP port")
    parser.add_argument("--bind-host", default="0.0.0.0", help="Local IP to bind client")
    parser.add_argument("--bind-port", type=int, default=0, help="Local UDP port (0 = auto)")
    args = parser.parse_args()

    # Initialize network layer
    net = NetworkLayer(local_ip=args.bind_host, local_port=args.bind_port)
    start_receiver(net)

    server_addr = (args.server_host, args.server_port)
    logger.info(f"Client started. Sending to server at {server_addr}")

    interactive_sender(net, server_addr)

    net.stop()
    logger.info("Client stopped.")


if __name__ == "__main__":
    main()
