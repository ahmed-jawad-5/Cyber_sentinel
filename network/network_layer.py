import socket
import threading


class NetworkLayer:
    """
    Low-level UDP networking.
    Handles:
    - binding a socket
    - sending packets
    - receiving packets in background thread
    - ignoring Windows ICMP reset errors (WinError 10054)
    """

    def __init__(self, local_ip="0.0.0.0", local_port=5005, buffer_size=1024, on_receive=None):
        self.local_ip = local_ip
        self.local_port = local_port
        self.buffer_size = buffer_size
        self.on_receive = on_receive if on_receive else self.default_receive_handler

        self.running = False
        self.thread = None

        # Create UDP socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # Enable broadcast support (optional but useful)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        # Bind to port
        self.sock.bind((self.local_ip, self.local_port))

    def default_receive_handler(self, data, addr):
        """Fallback receive handler."""
        print(f"[NetworkLayer] Received from {addr}: {data}")

    def send(self, data: bytes, dest_ip: str, dest_port: int):
        """Sends a UDP packet."""
        try:
            self.sock.sendto(data, (dest_ip, dest_port))
        except ConnectionResetError:
            # Ignore Windows ICMP “port unreachable” error
            print("[NetworkLayer] Ignored WinError 10054 on send()")
        except Exception as e:
            print(f"[NetworkLayer] Send error: {e}")

    def start(self):
        """Start background receiving thread."""
        if self.running:
            return

        self.running = True
        self.thread = threading.Thread(target=self.loop, daemon=True)
        self.thread.start()

        print(f"[NetworkLayer] Listening on {self.local_ip}:{self.local_port}")

    def loop(self):
        """Internal loop for receiving packets."""
        while self.running:
            try:
                data, addr = self.sock.recvfrom(self.buffer_size)

                if data:
                    self.on_receive(data, addr)

            except ConnectionResetError:
                # Windows UDP ICMP error – ignore safely
                continue

            except OSError:
                # Happens when socket is closed during shutdown
                break

            except Exception as e:
                print(f"[NetworkLayer] Receive error: {e}")

    def stop(self):
        """Gracefully stop networking thread."""
        self.running = False
        try:
            self.sock.close()
        except:
            pass
        print("[NetworkLayer] Stopped listening")
