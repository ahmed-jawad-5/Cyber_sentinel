# capture/flow_sniffer.py
from scapy.all import sniff, wrpcap
from capture.packet_parser import parse_packet
from capture.flow_tracker import FlowTracker
from config import IFACE, FILTER, PCAP_FILE
from utils.logger import get_logger

logger = get_logger("FlowSniffer")

class FlowSniffer:
    def __init__(self, iface=IFACE, bpf_filter=FILTER, save_pcap=True):
        self.iface = iface
        self.bpf_filter = bpf_filter
        self.flow_tracker = FlowTracker()
        self.save_pcap = save_pcap
        self.captured_packets = []

    def _process_packet(self, pkt):
        """Called for every sniffed packet"""
        pkt_info = parse_packet(pkt)
        if pkt_info:
            self.flow_tracker.update_flow(pkt_info)
            if self.save_pcap:
                self.captured_packets.append(pkt)

    def start(self):
        """Start sniffing packets"""
        logger.info(f"Starting packet sniffing on interface: {self.iface} with filter: {self.bpf_filter}")
        try:
            sniff(iface=self.iface, filter=self.bpf_filter, prn=self._process_packet, store=False)
        except KeyboardInterrupt:
            logger.info("Stopping sniffing due to keyboard interrupt")
            self.stop()

    def stop(self):
        """Stop sniffing and save pcap if needed"""
        logger.info("Stopping FlowSniffer...")
        self.flow_tracker.stop()
        if self.save_pcap and self.captured_packets:
            wrpcap(PCAP_FILE, self.captured_packets)
            logger.info(f"Saved captured packets to {PCAP_FILE}")
