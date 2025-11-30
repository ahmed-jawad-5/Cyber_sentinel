# capture/feature_extractor.py
import numpy as np
from utils.logger import get_logger

logger = get_logger("FeatureExtractor")

def extract_features(packets: list) -> dict:
    """
    Extract 34 network + transport + application features from a flow.
    packets: list of packet dictionaries with keys from packet_parser
    Returns a dict ready to write to CSV.
    """
    if not packets:
        return {}

    # Initialize feature dict
    features = {f: 0 for f in [
        'proto', 'state', 'sbytes', 'dbytes', 'sttl', 'dttl', 'sloss', 'service',
        'Sload', 'swin', 'dwin', 'stcpb', 'dtcpb', 'smeansz', 'dmeansz', 'res_bdy_len',
        'Sjit', 'Sintpkt', 'Dintpkt', 'tcprtt', 'synack', 'ackdat', 'is_sm_ips_ports',
        'ct_state_ttl', 'ct_flw_http_mthd', 'is_ftp_login', 'ct_ftp_cmd', 'ct_srv_src',
        'ct_srv_dst', 'ct_dst_ltm', 'ct_src_ ltm', 'ct_src_dport_ltm', 'ct_dst_sport_ltm',
        'ct_dst_src_ltm'
    ]}

    # Basic packet info
    features['proto'] = packets[0].get('proto', 0)
    features['service'] = packets[0].get('dport', 0)

    # Byte counts
    sbytes = sum(pkt.get('payload_len', 0) for pkt in packets)
    dbytes = sum(pkt.get('res_bdy_len', 0) for pkt in packets)
    features['sbytes'] = sbytes
    features['dbytes'] = dbytes

    # TTLs
    features['sttl'] = np.mean([pkt.get('sttl', 0) for pkt in packets])
    features['dttl'] = np.mean([pkt.get('dttl', 0) for pkt in packets])

    # TCP window sizes
    swin_values = [pkt.get('swin', 0) for pkt in packets if 'swin' in pkt]
    dwin_values = [pkt.get('dwin', 0) for pkt in packets if 'dwin' in pkt]
    features['swin'] = np.mean(swin_values) if swin_values else 0
    features['dwin'] = np.mean(dwin_values) if dwin_values else 0

    # TCP sequence numbers
    stcpb_values = [pkt.get('stcpb', 0) for pkt in packets if 'stcpb' in pkt]
    dtcpb_values = [pkt.get('dtcpb', 0) for pkt in packets if 'dtcpb' in pkt]
    features['stcpb'] = stcpb_values[-1] if stcpb_values else 0
    features['dtcpb'] = dtcpb_values[-1] if dtcpb_values else 0

    # Packet sizes
    payload_sizes = [pkt.get('payload_len', 0) for pkt in packets]
    features['smeansz'] = np.mean(payload_sizes) if payload_sizes else 0
    features['dmeansz'] = np.mean(payload_sizes) if payload_sizes else 0

    # Response body length
    features['res_bdy_len'] = np.sum([pkt.get('res_bdy_len', 0) for pkt in packets])

    # Inter-packet times
    timestamps = [pkt['ts'] for pkt in packets]
    ipkt_diffs = np.diff(timestamps) if len(timestamps) > 1 else [0]
    features['Sintpkt'] = np.mean(ipkt_diffs) if ipkt_diffs.any() else 0
    features['Dintpkt'] = np.mean(ipkt_diffs) if ipkt_diffs.any() else 0

    # Jitter
    features['Sjit'] = np.std(ipkt_diffs) if ipkt_diffs.any() else 0

    # RTT and SYN/ACK/ACK times — simple approximation for offline capture
    features['tcprtt'] = 0
    features['synack'] = 0
    features['ackdat'] = 0

    # Placeholder booleans
    features['is_sm_ips_ports'] = 1  # assume same flow
    features['state'] = 1             # placeholder for flow state
    features['sloss'] = 0             # placeholder packet loss

    # Connection tracking counters (placeholders)
    features['ct_state_ttl'] = len(set([pkt.get('sttl', 0) for pkt in packets]))
    features['ct_flw_http_mthd'] = 0
    features['is_ftp_login'] = 0
    features['ct_ftp_cmd'] = 0
    features['ct_srv_src'] = 1
    features['ct_srv_dst'] = 1
    features['ct_dst_ltm'] = 1
    features['ct_src_ ltm'] = 1
    features['ct_src_dport_ltm'] = 1
    features['ct_dst_sport_ltm'] = 1
    features['ct_dst_src_ltm'] = 1

    return features
