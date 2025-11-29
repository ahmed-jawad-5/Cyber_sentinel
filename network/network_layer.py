# network/network_layer.py
import socket
import threading
import random

class NetworkLayer:
    """
    UDP Network Layer with optional simulated packet loss.
    """

    def __init__(self, local_ip="0.0.0.0", local_port=5000, buffer_size=4096, loss_rate=0.0):
        self.local_ip = local_ip
        self.local_port = local_port
        self.buffer_size = buffer_size
        self.loss_rate = loss_rate

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.sock.bind((self.local_ip, self.local_port))

        self.running = False
        self.listen_thread = None
        self.on_receive = None

    def start_listening(self, callback):
        """Start listening in a background thread."""
        self.on_receive = callback
        self.running = True
        self.listen_thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.listen_thread.start()

    def _listen_loop(self):
        while self.running:
            try:
                data, addr = self.sock.recvfrom(self.buffer_size)
                print(f"[DEBUG][NetworkLayer] ({self.local_ip}:{self.local_port}) received {len(data)} bytes from {addr}")
                # Simulate packet loss
                if self.loss_rate > 0 and random.random() < self.loss_rate:
                    print("[DEBUG][NetworkLayer] dropping packet due to simulated loss")
                    continue
                if self.on_receive:
                    self.on_receive(data, addr)
            except ConnectionResetError:
                # Ignore Windows ICMP "Port Unreachable"
                continue
            except OSError:
                break
            except Exception as e:
                print(f"[NetworkLayer] Receive error: {e}")

    def send(self, data_bytes, addr):
        """Send bytes to addr (tuple IP, port)."""
        try:
            if not isinstance(data_bytes, bytes):
                raise TypeError(f"NetworkLayer.send() expects bytes, got {type(data_bytes)}")
            print(f"[DEBUG][NetworkLayer] sending {len(data_bytes)} bytes from ({self.local_ip}:{self.local_port}) to {addr}")
            self.sock.sendto(data_bytes, addr)
        except Exception as e:
            print(f"[NetworkLayer] Send error: {e}")

    def stop(self):
        self.running = False
        try:
            self.sock.close()
        except:
            pass
