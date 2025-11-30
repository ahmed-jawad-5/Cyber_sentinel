# app/handler.py
from typing import Tuple
from app.application_layer import parse_message, make_message
from utils.logger import get_logger
from packet_logger import log_packet

logger = get_logger("AppHandler")


class AppHandler:
    def __init__(self, network_layer):
        self.network = network_layer

    def handle_raw(self, raw: bytes, addr: Tuple[str, int]):
        log_packet(addr, raw)   # <-- NEW

        msg = parse_message(raw)
        if not msg:
            logger.warning(f"Invalid message from {addr}")
            return

        self.handle(msg, addr)

    def handle(self, msg: dict, addr: Tuple[str, int]):
        t = msg.get("msg_type")
        seq = msg.get("seq")
        p = msg.get("payload", {})

        if t == "ping":
            logger.info(f"Ping from {addr}")
            self.network.send(addr, make_message("pong", seq=seq))

        elif t == "message":
            logger.info(f"Message from {addr}: {p.get('text')}")
            self.network.send(addr, make_message("ack", seq=seq))

        elif t == "pong":
            logger.info(f"Pong received")

        elif t == "ack":
            logger.info(f"ACK received")
