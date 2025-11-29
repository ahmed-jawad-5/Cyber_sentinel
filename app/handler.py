from typing import Tuple
from app.application_layer import parse_message, make_message
from utils.logger import get_logger

logger = get_logger("AppHandler")

class AppHandler:
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
            resp = make_message("pong", {"received_seq": seq}, seq=seq)
            self.network.send(resp, addr)
        elif msg_type == "message":
            text = payload.get("text")
            logger.info(f"Message from {addr} [seq={seq}]: {text}")
            ack = make_message("ack", {"ack_seq": seq}, seq=seq)
            self.network.send(ack, addr)
        elif msg_type in ("pong","ack"):
            logger.info(f"{msg_type} from {addr}: {payload}")
            self.network.send(ack, addr)

        elif msg_type in ("pong", "ack"):
            logger.info(f"{msg_type} from {addr}: {payload}")