# capture/packet_parser.py
from scapy.all import IP, TCP, UDP, ICMP, Raw
import random

def parse_packet(pkt):
    """
    Extract basic header info and payload size for flow tracking.
    Returns dict with protocol, src/dst ports, sequence numbers, TTLs, flags.
    """
    result = {}

    if IP in pkt:
        result["src"] = pkt[IP].src
        result["dst"] = pkt[IP].dst
        result["proto"] = pkt[IP].proto
        result["sttl"] = pkt[IP].ttl
        result["dttl"] = pkt[IP].ttl  # assuming symmetric for now
        result["payload_len"] = len(pkt[IP].payload)

    if TCP in pkt:
        tcp = pkt[TCP]
        result["sport"] = tcp.sport
        result["dport"] = tcp.dport
        result["swin"] = tcp.window
        result["dwin"] = tcp.window
        result["stcpb"] = tcp.seq
        result["dtcpb"] = tcp.ack
        result["flags"] = tcp.flags

    elif UDP in pkt:
        udp = pkt[UDP]
        result["sport"] = udp.sport
        result["dport"] = udp.dport

    elif ICMP in pkt:
        result["sport"] = None
        result["dport"] = None

    # Raw payload length
    if Raw in pkt:
        result["res_bdy_len"] = len(pkt[Raw].load)
    else:
        result["res_bdy_len"] = 0

    return result
