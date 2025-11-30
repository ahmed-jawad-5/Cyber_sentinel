# capture/packet_parser.py
from scapy.all import IP, IPv6, TCP, UDP, Raw
from utils.logger import get_logger
logger = get_logger("PacketParser")

def parse_packet(pkt):
    """
    Convert a scapy pkt into a minimal dictionary used by flow_tracker.
    Fields included (if present):
      - src, dst (IP)
      - proto (string: 'tcp'|'udp'|'icmp'|'other')
      - sport, dport (ints or None)
      - payload_len (payload bytes length)
      - sttl, dttl (ttl observed) -- use same ttl for both directions as approximation
      - swin, dwin, stcpb, dtcpb (if TCP)
      - flags (TCP flags string)
      - ts (timestamp, seconds)
    """
    try:
        ts = pkt.time
        entry = {"ts": ts}
        # IP/IPv6
        if IP in pkt:
            ip = pkt[IP]
            entry["src"] = ip.src
            entry["dst"] = ip.dst
            entry["sttl"] = getattr(ip, "ttl", 0)
            entry["dttl"] = getattr(ip, "ttl", 0)
            proto_layer = ip.proto
        else:
            # fallback: may be IPv6 or non-IP - skip
            logger.debug("Non-IP packet, skipping")
            return None

        # Transport
        if pkt.haslayer(TCP):
            tcp = pkt[TCP]
            entry["proto"] = "tcp"
            entry["sport"] = int(tcp.sport)
            entry["dport"] = int(tcp.dport)
            entry["swin"] = int(tcp.window)
            entry["dwin"] = int(tcp.window)
            entry["stcpb"] = int(tcp.seq)
            entry["dtcpb"] = int(tcp.ack)
            entry["flags"] = str(tcp.flags)
        elif pkt.haslayer(UDP):
            udp = pkt[UDP]
            entry["proto"] = "udp"
            entry["sport"] = int(udp.sport)
            entry["dport"] = int(udp.dport)
        else:
            entry["proto"] = "other"
            entry["sport"] = None
            entry["dport"] = None

        # Payload length
        if pkt.haslayer(Raw):
            entry["payload_len"] = len(pkt[Raw].load)
            entry["res_bdy_len"] = len(pkt[Raw].load)
        else:
            entry["payload_len"] = len(bytes(pkt.payload)) if pkt.payload else 0
            entry["res_bdy_len"] = 0

        return entry
    except Exception as e:
        logger.exception("parse_packet error")
        return None
