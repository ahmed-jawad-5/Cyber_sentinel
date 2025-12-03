import time
import random
from scapy.all import IP, TCP, send, Raw

TARGET_IP = "192.168.1.2"   # change to receiver IP
TARGET_PORT = 5000
INTERFACE = None            # leave None for default, or set "eth0"/"wlan0"

def make_flow(src_port=None, payload_size=50):
    if src_port is None:
        src_port = random.randint(20000, 40000)
    payload = bytes(random.choices(
        b"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", k=payload_size))
    # Basic 3-packet like flow: SYN, PSH+ACK with data, FIN
    syn = IP(dst=TARGET_IP)/TCP(sport=src_port, dport=TARGET_PORT, flags="S", seq=1000)
    data = IP(dst=TARGET_IP)/TCP(sport=src_port, dport=TARGET_PORT, flags="PA", seq=1001, ack=1)/Raw(payload)
    fin = IP(dst=TARGET_IP)/TCP(sport=src_port, dport=TARGET_PORT, flags="F", seq=1002, ack=1)
    return [syn, data, fin]

def generate(n_flows=5, inter_flow_delay=1.0):
    print(f"Generating {n_flows} flows to {TARGET_IP}:{TARGET_PORT}...")
    for i in range(n_flows):
        pkts = make_flow(payload_size=random.randint(20,120))
        for p in pkts:
            send(p, iface=INTERFACE, verbose=False)
            time.sleep(0.01)
        time.sleep(inter_flow_delay)
    print("Done generating flows.")

if __name__ == "__main__":
    generate(n_flows=10, inter_flow_delay=0.5)
