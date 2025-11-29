# app/application_layer.py
import json
import time
from typing import Optional, Dict, Any

def make_message(msg_type: str, payload: Dict[str, Any], seq: Optional[int]=None) -> bytes:
    """
    Build application-layer message (JSON). Returns bytes ready to send.
    Fields:
      - msg_type: 'message', 'ping', 'ack', ...
      - seq: optional sequence number (int)
      - payload: a JSON-serializable dict
      - ts: timestamp
    """
    if seq is None:
        seq = int(time.time()*1000)  # coarse unique-ish seq
    packet = {
        "msg_type": msg_type,
        "seq": seq,
        "payload": payload,
        "ts": time.time()
    }
    raw = json.dumps(packet).encode("utf-8")
    return raw

def parse_message(data: bytes) -> Optional[Dict]:
    """Parse bytes into a dict; return None on failure."""
    try:
        obj = json.loads(data.decode("utf-8"))
        return obj
    except Exception:
        return None
