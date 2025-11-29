import socket
import threading
import random

class NetworkLayer:
    """
    UDP Network Layer with optional simulated packet loss.
    """

    def __init__(self, bind_addr=("0.0.0.0", 5000), buffer_size=1024, loss_rate=0.0):
        self.ip, self.port = bind_addr
        self.buffer_size = buffer_size
        self.loss_rate = loss_rate

        self.running = False
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.ip, self.port))

        self.listen_thread = None

    def start_listening(self, callback):
        """Start listening for UDP packets in a background thread."""
        self.callback = callback
        self.running = True
        self.listen_thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.listen_thread.start()

    def _listen_loop(self):
        """Receive packets in loop."""
        while self.running:
            try:
                data, addr = self.sock.recvfrom(self.buffer_size)

                # Simulated packet loss
                if random.random() < self.loss_rate:
                    # Drop packet silently
                    continue

                # Dispatch to application layer
                self.callback(data, addr)

            except ConnectionResetError:
                # Ignore WinError 10054
                continue
            except OSError:
                break
            except Exception as e:
                print(f"[NetworkLayer] Error: {e}")

    def send(self, data: bytes, dest):
        """Send UDP packet to (IP, port)."""
        try:
            self.sock.sendto(data, dest)
        except ConnectionResetError:
            # Windows ICMP reset — safe to ignore
            pass
        except Exception as e:
            print(f"[NetworkLayer] Send error: {e}")

    def stop(self):
        self.running = False
        try:
            self.sock.close()
        except:
            pass
