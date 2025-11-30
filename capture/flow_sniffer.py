# capture/flow_sniffer.py
from scapy.all import sniff
from capture.packet_parser import parse_packet
from capture.flow_tracker import FlowTracker
from capture.feature_extractor import extract_features
from utils.logger import get_logger
from config.settings import IFACE, BPF_FILTER

logger = get_logger("FlowSniffer")

class FlowSnifferRunner:
    def __init__(self, on_feature_ready):
        """
        on_feature_ready(features_dict) -> called when a flow is complete and features are extracted.
        """
        self.on_feature_ready = on_feature_ready
        self.tracker = FlowTracker(on_flow_complete=self._on_flow_complete)

    def _on_flow_complete(self, flow_key, packets):
        try:
            features = extract_features(flow_key, packets)
            if features:
                # attach basic flow_key info optionally
                features["_flow_key"] = {
                    "src": flow_key[0],
                    "dst": flow_key[1],
                    "sport": flow_key[2],
                    "dport": flow_key[3],
                    "proto": flow_key[4]
                }
                # call external callback to send features (client) or store
                self.on_feature_ready(features)
        except Exception:
            logger.exception("Feature extraction error")

    def _process(self, pkt):
        parsed = parse_packet(pkt)
        if parsed:
            self.tracker.update(parsed)

    def start(self, iface=IFACE, bpf_filter=BPF_FILTER):
        logger.info(f"Starting sniff on iface={iface} filter={bpf_filter}")
        sniff(iface=iface, filter=bpf_filter, prn=self._process, store=False)

    def stop(self):
        self.tracker.stop()
