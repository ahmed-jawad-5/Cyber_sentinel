# app/handler.py
from typing import Tuple
from app.application_layer import parse_message, make_message
from utils.logger import get_logger

logger = get_logger("AppHandler")

class AppHandler:
    """
    Simple application handler that:
    - responds to 'ping' with 'pong'
    - prints received 'message' and replies with 'ack'
    - unknown msg_type => ignores
    """
    def __init__(self, network_layer):
        self.network = network_layer

    def handle_raw(self, raw: bytes, addr: Tuple[str,int]):
        msg = parse_message(raw)
        if not msg:
            logger.warning(f"Received unparseable message from {addr}")
            return
        self.handle(msg, addr)

    def handle(self, msg: dict, addr: Tuple[str,int]):
        msg_type = msg.get("msg_type")
        seq = msg.get("seq")
        payload = msg.get("payload", {})

        if msg_type == "ping":
            logger.info(f"ping from {addr} seq={seq}")
            resp = make_message("pong", {"received_seq": seq}, seq=seq)
            self.network.send(addr, resp)

        elif msg_type == "message":
            content = payload.get("text")
            logger.info(f"message from {addr} seq={seq}: {content!r}")
            # Business logic could go here (store to DB, forward, etc.)
            ack = make_message("ack", {"ack_seq": seq}, seq=seq)
            self.network.send(addr, ack)

        elif msg_type == "pong":
            logger.info(f"pong from {addr} seq={seq} payload={payload}")

        elif msg_type == "ack":
            logger.info(f"ack from {addr} seq={seq} payload={payload}")

        else:
            logger.debug(f"Unknown msg_type {msg_type} from {addr}")
