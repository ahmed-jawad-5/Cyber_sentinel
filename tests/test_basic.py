# tests/test_basic.py
import time
from network.network_layer import NetworkLayer
from app.application_layer import make_message, parse_message

def test_send_receive_loopback():
    server = NetworkLayer(local_ip='127.0.0.1', local_port=9999)
    client = NetworkLayer(local_ip='127.0.0.1', local_port=0)  # ephemeral client port

    received = []

    def on_server(data, addr):
        received.append(('server', data, addr))
        # echo an ack
        client.send(make_message("ack", {"ok": True}), addr)

    def on_client(data, addr):
        received.append(('client', data, addr))

    server.start_listening(on_server)
    client.start_listening(on_client)

    # send a message from client to server
    client.send(make_message("message", {"text": "hello"}), ('127.0.0.1', 9999))

    time.sleep(0.5)
    server.stop()
    client.stop()

    assert any(r[0] == 'server' for r in received)
    assert any(r[0] == 'client' for r in received)
