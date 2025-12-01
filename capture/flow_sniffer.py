# capture/flow_sniffer.py
from scapy.all import sniff
from .flow_tracker import FlowTracker
from .feature_extractor import FeatureExtractor
from utils.logger import get_logger

logger = get_logger("FLOW_SNIFFER")

class FlowSnifferRunner:
    def __init__(self):
        self.tracker = FlowTracker()
        self.extractor = FeatureExtractor()

    def _process_packet(self, packet):
        flow_key, flow_complete = self.tracker.add_packet(packet)

        if flow_complete:
            # Extract features (34)
            features = self.extractor.extract(flow_complete)
            logger.info(f"[FLOW COMPLETED] {flow_key} | 34 features extracted.")
            return features

        return None

    def run_sniffer(self):
        """Generator yields completed flow feature dictionaries."""
        def callback(pkt):
            result = self._process_packet(pkt)
            if result:
                yield_result.append(result)

        yield_result = []

        sniff(prn=lambda pkt: callback(pkt), store=False)

        while yield_result:
            yield yield_result.pop(0)
