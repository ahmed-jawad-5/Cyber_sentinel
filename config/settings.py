# config/settings.py

# Sniffer network interface used by client (Scapy)
IFACE = "wlan0"     # change to your actual interface, e.g. "eth0", "en0", or interface index on Windows

# BPF filter for sniffing (capture what you want; 'ip' captures all IPv4)
BPF_FILTER = "ip"

# Flow timeout (seconds) — flow is considered finished after this idle time
FLOW_TIMEOUT = 10.0

# TCP server to which the client will send feature JSONs
# On the client side set SERVER_IP to the server laptop IP (change before running)
SERVER_IP = "10.5.40.102"
SERVER_PORT = 9000

# Server CSV output (path relative to server script)
OUTPUT_CSV = "output/captured_flows.csv"
