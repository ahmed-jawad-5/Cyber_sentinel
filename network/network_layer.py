import socket
import threading

class NetworkLayer:
    def __init__(self, local_ip="0.0.0.0", local_port=5005, buffer_size=4096, on_receive=None):
        self.local_ip = local_ip
        self.local_port = local_port
        self.buffer_size = buffer_size
        self.on_receive = on_receive
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.sock.bind((self.local_ip, self.local_port))
        self.running = False

    def start_listening(self, callback=None):
        self.on_receive = callback or self.on_receive
        self.running = True
        threading.Thread(target=self._listen_loop, daemon=True).start()

    def _listen_loop(self):
        while self.running:
            try:
                data, addr = self.sock.recvfrom(self.buffer_size)
                if self.on_receive:
                    self.on_receive(data, addr)
            except ConnectionResetError:
                continue
            except OSError:
                break
            except Exception as e:
                print(f"NetworkLayer receive error: {e}")

    def send(self, data_bytes, addr):
        """data_bytes: bytes, addr: tuple(ip, port)"""
        try:
            if not isinstance(data_bytes, bytes):
                raise TypeError(f"send() expects bytes, got {type(data_bytes)}")
            self.sock.sendto(data_bytes, addr)
        except Exception as e:
            print(f"NetworkLayer send error: {e}")

    def stop(self):
        self.running = False
        try:
            self.sock.close()
        except:
            pass
