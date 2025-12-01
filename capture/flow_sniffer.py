# capture/flow_sniffer.py

import json
import os
from scapy.all import sniff

from .packet_parser import parse_packet
from utils.logger import get_logger

logger = get_logger("FLOW_SNIFFER")


class FlowSnifferRunner:
    """Sniffer that converts each captured packet into a feature dict.

    The feature dict uses the column names defined in capture/feature_schema.json
    so that the server receives exactly those columns.
    """

    def __init__(self, interface="wlan0"):
        self.interface = interface

        # Load desired feature names from schema
        schema_path = os.path.join(os.path.dirname(__file__), "feature_schema.json")
        with open(schema_path, "r") as f:
            schema = json.load(f)
        self.feature_names = schema["features"]

    def start(self, callback):
        """Start sniffing indefinitely and invoke callback for each packet.

        callback is called as callback(flow_id, feature_dict). For now we don't
        track flow IDs, so flow_id is always None.
        """
        logger.info(f"[Sniffer] Starting sniffing on {self.interface}...")
        sniff(iface=self.interface, prn=lambda pkt: self.handle(pkt, callback), store=False)

    def handle(self, packet, callback):
        parsed = parse_packet(packet)
        if not parsed:
            return

        features = self._packet_to_features(parsed)
        callback(None, features)

    def _packet_to_features(self, p: dict) -> dict:
        """Map a parsed packet dict to the schema-defined feature dict.

        Many of the original dataset features are flow-level or multi-flow
        statistics. Here we fill what we can directly from a single packet and
        default the rest to 0. This still guarantees the server sees the exact
        schema columns.
        """
        feats = {name: 0 for name in self.feature_names}

        # proto: encode TCP/UDP/other as integers (simple mapping)
        proto_str = p.get("proto", "other")
        if proto_str == "tcp":
            feats["proto"] = 6
        elif proto_str == "udp":
            feats["proto"] = 17
        else:
            feats["proto"] = 0

        # Basic TTL and TCP header fields
        feats["sttl"] = p.get("sttl", 0)
        feats["dttl"] = p.get("dttl", 0)
        feats["swin"] = p.get("swin", 0)
        feats["dwin"] = p.get("dwin", 0)
        feats["stcpb"] = p.get("stcpb", 0)
        feats["dtcpb"] = p.get("dtcpb", 0)
        feats["res_bdy_len"] = p.get("res_bdy_len", 0)

        # Directional bytes (simplified: this packet is from source only)
        payload_len = p.get("payload_len", 0)
        feats["sbytes"] = payload_len
        feats["dbytes"] = 0

        # state: encode TCP flags string or default
        flags = str(p.get("flags", "")) if proto_str == "tcp" else ""
        feats["state"] = {
            "S": 1,      # SYN
            "SA": 2,     # SYN-ACK
            "FA": 3,     # FIN-ACK
            "R": 4,      # RST
        }.get(flags, 0)

        # service: basic mapping from destination port
        dport = p.get("dport")
        if dport in (80, 8080):
            service = 1  # http
        elif dport == 443:
            service = 2  # https
        elif dport in (20, 21):
            service = 3  # ftp
        else:
            service = 0  # other/unknown
        feats["service"] = service

        # is_sm_ips_ports: 1 if src/dst IP and ports are the same
        src = p.get("src")
        dst = p.get("dst")
        sport = p.get("sport")
        dport = p.get("dport")
        feats["is_sm_ips_ports"] = int(src == dst and sport == dport)

        # All remaining schema features (sloss, Sload, Sjit, Sintpkt, Dintpkt,
        # tcprtt, synack, ackdat, ct_* etc.) are left as 0 for now. Implementing
        # their exact semantics requires a more elaborate flow tracker.

        return feats

    def run_sniffer(self):
        """Generator version kept for completeness (not used currently)."""
        results = []

        def callback(flow_id, features):
            results.append((flow_id, features))

        sniff(iface=self.interface, prn=lambda pkt: self.handle(pkt, callback), store=False)

        while results:
            yield results.pop(0)
