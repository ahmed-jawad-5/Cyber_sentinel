# packet_generator.py
import os
import json
import random

FEATURES = [
    'proto', 'state', 'sbytes', 'dbytes', 'sttl', 'dttl', 'sloss', 'service',
    'Sload', 'swin', 'dwin', 'stcpb', 'dtcpb', 'smeansz', 'dmeansz',
    'res_bdy_len', 'Sjit', 'Sintpkt', 'Dintpkt', 'tcprtt', 'synack', 'ackdat',
    'is_sm_ips_ports', 'ct_state_ttl', 'ct_flw_http_mthd', 'is_ftp_login',
    'ct_ftp_cmd', 'ct_srv_src', 'ct_srv_dst', 'ct_dst_ltm', 'ct_src_ltm',
    'ct_src_dport_ltm', 'ct_dst_sport_ltm', 'ct_dst_src_ltm'
]


def generate_packet_bytes():
    packet = {f: random.randint(0, 5000) for f in FEATURES}
    packet["proto"] = random.choice(["tcp", "udp", "icmp"])
    packet["state"] = random.choice(["EST", "INT", "FIN"])
    packet["service"] = random.choice(["http", "ftp", "dns", "ssh", "smtp"])

    js = json.dumps(packet)
    return js.encode("utf-8")
