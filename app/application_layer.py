# app/application_layer.py
import json

def make_message(msg_type, payload=None, seq=0):
    obj = {
        "msg_type": msg_type,
        "payload": payload or {},
        "seq": seq
    }
    return json.dumps(obj).encode("utf-8")


def parse_message(raw: bytes):
    try:
        return json.loads(raw.decode("utf-8"))
    except:
        return None
