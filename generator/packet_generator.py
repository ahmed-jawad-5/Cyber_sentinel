# generator/packet_generator.py
from scapy.all import IP, TCP, UDP, ICMP, Ether, send, RandIP, RandShort
import random
import time

def make_normal_tcp_packet():
    """Normal TCP packet (HTTP-like)"""
    pkt = IP(src=f"192.168.1.{random.randint(2,254)}",
             dst=f"192.168.1.{random.randint(2,254)}",
             ttl=random.randint(50,64)) / \
          TCP(sport=random.randint(1024,65535),
              dport=80,
              seq=random.randint(0,10000),
              flags="PA",
              window=random.randint(1000,5000)) / \
          ("GET / HTTP/1.1\r\nHost: example.com\r\n\r\n")
    return pkt

def make_normal_udp_packet():
    """Normal UDP packet (DNS-like)"""
    pkt = IP(src=f"192.168.1.{random.randint(2,254)}",
             dst=f"192.168.1.{random.randint(2,254)}",
             ttl=random.randint(50,64)) / \
          UDP(sport=random.randint(1024,65535),
              dport=53) / \
          ("DNS query payload")
    return pkt

def make_malicious_packet():
    """Example: SYN flood style"""
    pkt = IP(src=RandIP(), dst="192.168.1.100", ttl=random.randint(1,5)) / \
          TCP(sport=RandShort(), dport=80, flags="S", seq=random.randint(0,10000)) / \
          ("X"*200)
    return pkt

def send_packets(iface="eth0", count=100, malicious_prob=0.2):
    """Send multiple packets on the network interface"""
    for i in range(count):
        if random.random() < malicious_prob:
            pkt = make_malicious_packet()
        else:
            pkt = make_normal_tcp_packet() if random.random() < 0.7 else make_normal_udp_packet()
        send(pkt, iface=iface, verbose=False)
        time.sleep(0.01)  # small delay to mimic realistic traffic

if __name__ == "__main__":
    send_packets()
