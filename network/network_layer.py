# network/network_layer.py
import socket
import threading
import random
from utils.logger import get_logger

logger = get_logger("NetworkLayer")


class NetworkLayer:
    def __init__(self, bind=("0.0.0.0", 0), loss_rate=0.0):
        """
        bind = (ip, port)
        loss_rate = 0.0 to 1.0 (simulate packet drops)
        """
        self.bind = bind
        self.loss_rate = loss_rate
        self.buffer_size = 65535
        self.running = False

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(self.bind)

        logger.info(f"NetworkLayer bound on {self.bind}")

    def start_listening(self, callback):
        """
        callback(raw_bytes, addr)
        """
        self.running = True

        t = threading.Thread(target=self._listen_loop, args=(callback,), daemon=True)
        t.start()

        logger.info("Listening thread started.")

    def _listen_loop(self, callback):
        while self.running:
            try:
                data, addr = self.sock.recvfrom(self.buffer_size)

                logger.debug(f"Received {len(data)} bytes from {addr}")

                callback(data, addr)

            except OSError:
                break
            except Exception as e:
                logger.error(f"Receive error: {e}")

    def send(self, addr, data: bytes):
        """
        addr = (ip, port)
        data = bytes only
        """
        try:
            if not isinstance(data, bytes):
                logger.error("SEND ERROR: data must be bytes")
                return

            if random.random() < self.loss_rate:
                logger.warning("Simulated packet loss!")
                return

            self.sock.sendto(data, addr)

        except Exception as e:
            logger.error(f"Send error: {e}")

    def stop(self):
        self.running = False
        try:
            self.sock.close()
        except:
            pass
        logger.info("NetworkLayer stopped.")
