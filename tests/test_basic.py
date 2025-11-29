# tests/test_basic.py
import time
from network.network_layer import UDPNetworkLayer
from app.application_layer import make_message, parse_message

def test_send_receive_loopback():
    server = UDPNetworkLayer(('127.0.0.1', 9999))
    client = UDPNetworkLayer(('127.0.0.1', 0))  # ephemeral client port

    received = []

    def on_server(data, addr):
        received.append(('server', data, addr))
        # echo an ack
        client.send(addr, make_message("ack", {"ok": True}))

    def on_client(data, addr):
        received.append(('client', data, addr))

    server.start_listening(on_server)
    client.start_listening(on_client)

    # send a message from client to server
    client.send(('127.0.0.1', 9999), make_message("message", {"text": "hello"}))

    time.sleep(0.5)
    server.stop()
    client.stop()

    assert any(r[0] == 'server' for r in received)
    assert any(r[0] == 'client' for r in received)
