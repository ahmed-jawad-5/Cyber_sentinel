import random
import json

FEATURES = [
    'proto', 'state', 'sbytes', 'dbytes', 'sttl', 'dttl', 'sloss', 'service', 
    'Sload', 'swin', 'dwin', 'stcpb', 'dtcpb', 'smeansz', 'dmeansz', 
    'res_bdy_len', 'Sjit', 'Sintpkt', 'Dintpkt', 'tcprtt', 'synack', 'ackdat',
    'is_sm_ips_ports', 'ct_state_ttl', 'ct_flw_http_mthd', 'is_ftp_login',
    'ct_ftp_cmd', 'ct_srv_src', 'ct_srv_dst', 'ct_dst_ltm', 'ct_src_ltm',
    'ct_src_dport_ltm', 'ct_dst_sport_ltm', 'ct_dst_src_ltm'
]

PROTO_LIST = ["tcp", "udp", "icmp"]
STATE_LIST = ["ESTABLISHED", "RETRANSMIT", "FIN", "S0", "S1", "S2"]
SERVICE_LIST = ["http", "ftp", "dns", "smtp", "ssh", "unknown"]


def generate_packet():
    """Generate a synthetic network packet with all 34 features."""
    packet = {
        "proto": random.choice(PROTO_LIST),
        "state": random.choice(STATE_LIST),
        "sbytes": random.randint(0, 20000),
        "dbytes": random.randint(0, 20000),
        "sttl": random.randint(0, 255),
        "dttl": random.randint(0, 255),
        "sloss": random.randint(0, 10),
        "service": random.choice(SERVICE_LIST),
        "Sload": random.uniform(0, 2000),
        "swin": random.randint(0, 65535),
        "dwin": random.randint(0, 65535),
        "stcpb": random.randint(0, 2**32),
        "dtcpb": random.randint(0, 2**32),
        "smeansz": random.randint(0, 1500),
        "dmeansz": random.randint(0, 1500),
        "res_bdy_len": random.randint(0, 50000),
        "Sjit": random.uniform(0, 50),
        "Sintpkt": random.uniform(0, 2),
        "Dintpkt": random.uniform(0, 2),
        "tcprtt": random.uniform(0, 500),
        "synack": random.uniform(0, 500),
        "ackdat": random.uniform(0, 500),

        "is_sm_ips_ports": random.randint(0, 1),
        "ct_state_ttl": random.randint(0, 50),
        "ct_flw_http_mthd": random.randint(0, 10),
        "is_ftp_login": random.randint(0, 1),
        "ct_ftp_cmd": random.randint(0, 10),
        "ct_srv_src": random.randint(0, 200),
        "ct_srv_dst": random.randint(0, 200),
        "ct_dst_ltm": random.randint(0, 200),
        "ct_src_ltm": random.randint(0, 200),
        "ct_src_dport_ltm": random.randint(0, 200),
        "ct_dst_sport_ltm": random.randint(0, 200),
        "ct_dst_src_ltm": random.randint(0, 200),
    }

    return packet


def generate_packet_bytes():
    """Return the generated packet encoded as bytes for sending."""
    pkt = generate_packet()
    json_str = json.dumps(pkt)
    return json_str.encode("utf-8")
