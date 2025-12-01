# generator/packet_generator.py
from scapy.all import IP, TCP, UDP, Raw
import random
import string
import os

class PacketGenerator:
    def __init__(self, dst_ip="192.168.1.20"):
        self.dst_ip = dst_ip

    def make_normal_packet(self):
        payload = ''.join(random.choices(string.ascii_letters + string.digits, k=50)).encode()
        sport = random.randint(1024, 65535)
        dport = 80
        proto = random.choice(["TCP", "UDP"])
        if proto == "TCP":
            pkt = IP(src="192.168.1.10", dst=self.dst_ip) / TCP(sport=sport, dport=dport) / Raw(payload)
        else:
            pkt = IP(src="192.168.1.10", dst=self.dst_ip) / UDP(sport=sport, dport=dport) / Raw(payload)
        return pkt

    def make_anomalous_packet(self):
        # TCP SYN flood style or abnormal TTL
        payload = os.urandom(200)
        sport = random.randint(1, 1024)
        dport = 80
        abnormal_ttl = random.randint(1, 5)
        pkt_type = random.choice(["SYN_FLOOD", "MALFORMED_TTL"])
        if pkt_type == "SYN_FLOOD":
            pkt = IP(src=f"10.0.{random.randint(0,255)}.{random.randint(0,255)}",
                     dst=self.dst_ip) / TCP(sport=sport, dport=dport, flags="S") / Raw(payload)
        else:
            pkt = IP(src=f"10.0.{random.randint(0,255)}.{random.randint(0,255)}",
                     dst=self.dst_ip, ttl=abnormal_ttl) / TCP(sport=sport, dport=dport) / Raw(payload)
        return pkt

    def generate_packet(self):
        """Randomly choose normal (70%) or anomalous (30%) packet.

        Returns
        -------
        pkt : scapy.Packet
            The generated packet.
        label : str
            "ANOMALY" or "NORMAL" indicating the intended class.
        """
        # if random.random() < 0.3:  # 30% chance of anomaly
        #     return self.make_anomalous_packet(), "ANOMALY"
        # else:
        return self.make_normal_packet(), "NORMAL"
        