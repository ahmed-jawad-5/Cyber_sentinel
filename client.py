import time
from network.network_layer import NetworkLayer
from packet_generator import generate_packet_bytes

# Change to your actual server IP and port
SERVER_IP = "192.168.1.50"
SERVER_PORT = 9000


def main():
    # Bind to any free local port
    client = NetworkLayer(bind=("0.0.0.0", 0))

    print(f"[CLIENT] Sending packets to {SERVER_IP}:{SERVER_PORT}")
    print("[CLIENT] Press CTRL+C to stop.\n")

    while True:
        try:
            # Generate synthetic packet as bytes
            pkt = generate_packet_bytes()

            # Send packet to server
            client.send((SERVER_IP, SERVER_PORT), pkt)

            # Show short preview
            print("[SENT]", pkt[:80], "...")

            time.sleep(1)

        except KeyboardInterrupt:
            print("\n[CLIENT] Stopped.")
            break


if __name__ == "__main__":
    main()
