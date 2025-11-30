# config/settings.py

# Network interface for sniffing
IFACE = "eth0"  # change to your active interface, e.g., "en0" on Mac

# Sniff filter (BPF style)
FILTER = "ip"

# Flow timeout in seconds (after which a flow is considered complete)
FLOW_TIMEOUT = 10

# Output CSV file paths
CAPTURED_FLOWS_CSV = "output/captured_flows.csv"
ANOMALIES_CSV = "output/anomalies.csv"

# PCAP file for optional raw capture
PCAP_FILE = "output/packets.pcap"

# Maximum number of packets to store in memory (before writing to CSV)
MAX_BUFFER_SIZE = 1000
