import threading
import time
from collections import defaultdict, deque
from scapy.all import sniff, IP, TCP, UDP
from .feature_extractor import flow_to_features
from .feature_schema import validate_and_fill

# Flow timeout in seconds: if no packet seen for a flow in this many seconds, expire it.
FLOW_TIMEOUT = 2.0
CLEANUP_INTERVAL = 1.0

# Keyed by 5-tuple: (src, dst, sport, dport, proto)
flows = {}
flows_lock = threading.Lock()

def _make_key(pkt):
    if IP not in pkt:
        return None
    ip = pkt[IP]
    proto = ip.proto
    sport = 0; dport = 0
    if TCP in pkt:
        sport = pkt[TCP].sport; dport = pkt[TCP].dport
    elif UDP in pkt:
        sport = pkt[UDP].sport; dport = pkt[UDP].dport
    return (ip.src, ip.dst, sport, dport, proto)

def _now():
    return time.time()

def process_packet(pkt):
    key = _make_key(pkt)
    if key is None:
        return

    with flows_lock:
        f = flows.get(key)
        t = _now()
        if f is None:
            f = {
                "key": key,
                "first_seen": t,
                "last_seen": t,
                "pkts": 0,
                "sbytes": 0,       # bytes from src to dst
                "dbytes": 0,       # bytes from dst to src (if reverse packets observed)
                "s_ttls": [],      # source-side TTLs
                "d_ttls": [],      # dest-side TTLs
                "s_windows": [],   # source-side TCP windows
                "d_windows": [],   # dest-side TCP windows
                "s_seq": [],       # seq numbers seen (src->dst)
                "d_seq": [],       # seq numbers seen (dst->src)
                "timestamps": [],  # list of (timestamp, direction) where direction = 's' or 'd'
                "payload_lens": [],# payload lengths observed (per packet)
                "service_ports": set(),
                # handshake timing
                "syn_time": None,
                "synack_time": None,
                "ack_time": None,
                # counts & derived
                "seen_flags": defaultdict(int)
            }
            flows[key] = f

        f["pkts"] += 1
        f["last_seen"] = t

        ip = pkt[IP]
        proto = ip.proto

        # direction: 's' if packet is from flow.src -> flow.dst, else 'd'
        src, dst, sport, dport, _ = key
        if ip.src == src and ip.dst == dst:
            direction = 's'
        elif ip.src == dst and ip.dst == src:
            direction = 'd'
        else:
            # unusual; treat as s
            direction = 's'

        if TCP in pkt:
            payload_len = len(bytes(pkt[TCP].payload))
        else:
            payload_len = 0

        f["payload_lens"].append(payload_len)

        f["timestamps"].append((t, direction))

        if direction == 's':
            f["sbytes"] += l
            if TCP in pkt:
                f["s_windows"].append(pkt[TCP].window)
                f["s_seq"].append(pkt[TCP].seq)
                flags = pkt[TCP].flags
                f["seen_flags"][str(flags)] += 1
                # handshake detection
                if flags & 0x02:  # SYN
                    f["syn_time"] = f["syn_time"] or t
            f["s_ttls"].append(ip.ttl)
        else:
            f["dbytes"] += l
            if TCP in pkt:
                f["d_windows"].append(pkt[TCP].window)
                f["d_seq"].append(pkt[TCP].seq)
                flags = pkt[TCP].flags
                f["seen_flags"][str(flags)] += 1
                if flags & 0x12:  # SYN+ACK (0x10=ACK,0x02=SYN -> 0x12)
                    f["synack_time"] = f["synack_time"] or t
                if flags & 0x10:  # ACK
                    f["ack_time"] = f["ack_time"] or t
            f["d_ttls"].append(ip.ttl)

        # record service port suggestion
        if sport:
            f["service_ports"].add(sport)
        if dport:
            f["service_ports"].add(dport)

def _expire_flow(key):
    """Handle expiration: compute features and remove flow from flows dict."""
    with flows_lock:
        f = flows.pop(key, None)
    if not f:
        return
    features = flow_to_features(f)
    ordered = validate_and_fill(features)
    # For demo we will print; in real setup we push to client queue
    print("Completed flow -> features:")
    for k,v in ordered.items():
        print(f" {k}: {v}")
    # append to outbound queue for client to send (optional)
    # send_to_client(ordered)

def _cleanup_loop():
    while True:
        now = _now()
        expired = []
        with flows_lock:
            for key, f in list(flows.items()):
                if now - f["last_seen"] > FLOW_TIMEOUT:
                    expired.append(key)
        for k in expired:
            _expire_flow(k)
        time.sleep(CLEANUP_INTERVAL)

def start_sniff(iface=None, filter=None):
    t = threading.Thread(target=_cleanup_loop, daemon=True)
    t.start()
    sniff(iface=iface, prn=process_packet, store=False, filter=filter)

if __name__ == "__main__":
    # Example: start sniffing on default interface. Run as root.
    print("Starting flow tracker (sniffing)...")
    start_sniff()
