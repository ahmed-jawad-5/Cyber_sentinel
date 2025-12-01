# capture/flow_sniffer.py

from scapy.all import sniff
from .flow_tracker import FlowTracker
from utils.logger import get_logger

logger = get_logger("FLOW_SNIFFER")

class FlowSnifferRunner:

    def __init__(self, interface="wlan0"):
        self.interface = interface
        self.tracker = FlowTracker()

    def start(self, callback):
        """Start sniffing indefinitely"""
        logger.info(f"[Sniffer] Starting sniffing on {self.interface}...")
        sniff(iface=self.interface, prn=lambda pkt: self.handle(pkt, callback), store=False)

    def handle(self, packet, callback):
        flow_id, features = self.tracker.update_flow(packet)
        if features is not None:
            callback(flow_id, features)

    def run_sniffer(self):
        """
        Generator version: yields (flow_id, features) for each new flow update.
        """
        results = []

        def callback(flow_id, features):
            results.append((flow_id, features))

        sniff(iface=self.interface, prn=lambda pkt: self.handle(pkt, callback), store=False)

        while results:
            yield results.pop(0)
