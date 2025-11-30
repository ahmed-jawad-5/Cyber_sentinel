# client.py
import time
from network.network_layer import NetworkLayer
from packet_generator import generate_packet_bytes

SERVER_IP = "192.168.1.50"
SERVER_PORT = 9000


def main():
    client = NetworkLayer(bind=("0.0.0.0", 0))

    print(f"[CLIENT] Sending packets to {SERVER_IP}:{SERVER_PORT}")

    while True:
        try:
            pkt = generate_packet_bytes()
            client.send((SERVER_IP, SERVER_PORT), pkt)
            print("[SENT]", pkt[:80], "...")
            time.sleep(1)

        except KeyboardInterrupt:
            print("Stopped.")
            break


if __name__ == "__main__":
    main()
