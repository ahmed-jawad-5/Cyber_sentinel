# network/network_layer.py
import socket
import threading
import random
import logging
from typing import Callable, Tuple

from config import BUFFER_SIZE

logger = logging.getLogger("network_layer")

class UDPNetworkLayer:
    """
    A simple UDP wrapper that:
    - binds to an address
    - provides send(addr, bytes)
    - provides start_listening(callback) where callback(data: bytes, addr: (ip,port))
    - can simulate packet loss by probability (loss_rate)
    """
    def __init__(self, bind_addr: Tuple[str, int], buffer_size:int=BUFFER_SIZE, loss_rate: float=0.0):
        self.bind_addr = bind_addr
        self.buffer_size = buffer_size
        self.loss_rate = max(0.0, min(1.0, loss_rate))
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # allow rebinding quickly during development
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # bind must be explicit for server; client can bind to ('0.0.0.0', 0) for ephemeral
        self.sock.bind(self.bind_addr)
        self._running = False
        logger.info(f"UDPNetworkLayer bound to {self.bind_addr} (loss_rate={self.loss_rate})")

    def send(self, addr: Tuple[str,int], data: bytes):
        """Send raw bytes to addr (ip, port). Simulate loss if configured."""
        if self.loss_rate > 0.0 and random.random() < self.loss_rate:
            logger.debug(f"Simulated packet loss to {addr}")
            return
        try:
            self.sock.sendto(data, addr)
            logger.debug(f"Sent {len(data)} bytes to {addr}")
        except Exception as e:
            logger.exception(f"Error sending to {addr}: {e}")

    def start_listening(self, callback: Callable[[bytes, Tuple[str,int]], None]):
        """Start a background thread that calls `callback(data, addr)` for each packet."""
        if self._running:
            return
        self._running = True

        def loop():
            logger.info("Network listening loop started")
            while self._running:
                try:
                    data, addr = self.sock.recvfrom(self.buffer_size)
                    logger.debug(f"Received {len(data)} bytes from {addr}")
                    # call callback in its own thread to avoid blocking the receiver
                    threading.Thread(target=callback, args=(data, addr), daemon=True).start()
                except Exception as e:
                    logger.exception(f"Receive error: {e}")
                    break
            logger.info("Network listening loop stopped")

        threading.Thread(target=loop, daemon=True).start()

    def stop(self):
        self._running = False
        try:
            self.sock.close()
        except Exception:
            pass
        logger.info("UDPNetworkLayer stopped")
