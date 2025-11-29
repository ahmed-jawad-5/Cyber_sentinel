# client.py
import argparse
from network.network_layer import NetworkLayer
from app.application_layer import make_message, parse_message
from utils.logger import get_logger

logger = get_logger("client")

def start_receiver(net: NetworkLayer):
    def on_receive(data, addr):
        print(f"[DEBUG] raw from {addr}: {data!r}")
        msg = parse_message(data)
        logger.info(f"Received from {addr}: {msg}")
    net.start_listening(on_receive)

def interactive_sender(net: NetworkLayer, server_addr):
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
            net.send(packet, server_addr)
            seq += 1
    except KeyboardInterrupt:
        print("\nClient exiting...")

def main():
    parser = argparse.ArgumentParser(description="UDP Client")
    parser.add_argument("--server-host", required=True)
    parser.add_argument("--server-port", type=int, required=True)
    parser.add_argument("--bind-host", default="192.168.223.255")
    parser.add_argument("--bind-port", type=int, default=0)
    args = parser.parse_args()

    net = NetworkLayer(local_ip=args.bind_host, local_port=args.bind_port)
    start_receiver(net)

    server_addr = (args.server_host, args.server_port)
    logger.info(f"Client sending to {server_addr}")

    interactive_sender(net, server_addr)
    net.stop()
    logger.info("Client stopped.")

if __name__ == "__main__":
    main()
