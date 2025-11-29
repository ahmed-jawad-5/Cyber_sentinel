from typing import Tuple
from app.application_layer import parse_message, make_message
from utils.logger import get_logger
import json

logger = get_logger("AppHandler")

class AppHandler:
    """
    Application-layer handler for incoming UDP packets.

    Responsibilities:
    - parse incoming JSON messages
    - respond to 'ping' with 'pong'
    - respond to 'message' with 'ack'
    - log 'pong' and 'ack' messages
    """

    def __init__(self, network_layer):
        self.network = network_layer

    # -------------------------------
    # ENTRY FROM NETWORK LAYER
    # -------------------------------
    def handle_raw(self, raw: bytes, addr: Tuple[str, int]):
        msg = parse_message(raw)
        if not msg:
            logger.warning(f"Received unparseable message from {addr}")
            return

        self.handle(msg, addr)

    # -------------------------------
    # APPLICATION LOGIC
    # -------------------------------
    def handle(self, msg: dict, addr: Tuple[str, int]):
        msg_type = msg.get("msg_type")
        seq = msg.get("seq")
        payload = msg.get("payload", {})

        if msg_type == "ping":
            logger.info(f"ping from {addr} seq={seq}")

            resp = make_message(
                "pong",
                {"received_seq": seq},
                seq=seq,
            )

            # Encode → send
            resp_bytes = json.dumps(resp).encode("utf-8")
            self.network.send(resp_bytes, addr)

        elif msg_type == "message":
            content = payload.get("text")
            logger.info(f"message from {addr} seq={seq}: {content!r}")

            ack = make_message(
                "ack",
                {"ack_seq": seq},
                seq=seq,
            )

            ack_bytes = json.dumps(ack).encode("utf-8")
            self.network.send(ack_bytes, addr)

        elif msg_type == "pong":
            logger.info(f"pong from {addr} seq={seq} payload={payload}")

        elif msg_type == "ack":
            logger.info(f"ack from {addr} seq={seq} payload={payload}")

        else:
            logger.debug(f"Unknown msg_type {msg_type} from {addr}")
