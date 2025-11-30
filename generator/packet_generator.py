# generator/packet_generator.py
from scapy.all import IP, TCP, UDP, Ether, send, sendp, RandIP, RandShort
import time
import random
import argparse

def make_tcp_packet(src, dst, sport=None, dport=80, payload=b"Hello"):
    sport = sport or random.randint(1024,65535)
    pkt = IP(src=src, dst=dst, ttl=random.randint(40,64)) / TCP(sport=sport, dport=dport, flags="PA", seq=random.randint(0,1<<30)) / payload
    return pkt

def make_udp_packet(src, dst, sport=None, dport=53, payload=b"DNSQ"):
    sport = sport or random.randint(1024,65535)
    pkt = IP(src=src, dst=dst, ttl=random.randint(40,64)) / UDP(sport=sport, dport=dport) / payload
    return pkt

def send_loop(iface, dst_ip, src_ip=None, count=100, delay=0.05):
    src_ip = src_ip or RandIP()
    for i in range(count):
        pkt = make_tcp_packet(str(src_ip), dst_ip) if random.random() < 0.7 else make_udp_packet(str(src_ip), dst_ip)
        send(pkt, iface=iface, verbose=False)
        time.sleep(delay)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--iface", default="wlan0")
    parser.add_argument("--dst", required=True)
    parser.add_argument("--src", default=None)
    parser.add_argument("--count", type=int, default=200)
    parser.add_argument("--delay", type=float, default=0.02)
    args = parser.parse_args()
    send_loop(args.iface, args.dst, src_ip=args.src, count=args.count, delay=args.delay)
