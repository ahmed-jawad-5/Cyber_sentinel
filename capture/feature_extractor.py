# capture/feature_extractor.py
import math
import statistics
from utils.logger import get_logger

logger = get_logger("FeatureExtractor")

FEATURE_ORDER = [
    'proto','state','sbytes','dbytes','sttl','dttl','sloss','service',
    'Sload','swin','dwin','stcpb','dtcpb','smeansz','dmeansz','res_bdy_len',
    'Sjit','Sintpkt','Dintpkt','tcprtt','synack','ackdat','is_sm_ips_ports',
    'ct_state_ttl','ct_flw_http_mthd','is_ftp_login','ct_ftp_cmd','ct_srv_src',
    'ct_srv_dst','ct_dst_ltm','ct_src_ltm','ct_src_dport_ltm','ct_dst_sport_ltm',
    'ct_dst_src_ltm'
]

def extract_features(flow_key, packets):
    """
    flow_key: 5-tuple
    packets: list of packet dicts from packet_parser
    returns: dict with keys as in FEATURE_ORDER
    """
    if not packets:
        return None

    proto = packets[0].get("proto", "other")
    service = packets[0].get("dport", 0)  # use dst port as service proxy

    # byte counters in forward direction approximation (sum payload_len)
    sbytes = sum(p.get("payload_len",0) for p in packets)
    dbytes = sum(p.get("res_bdy_len",0) for p in packets)

    sttls = [p.get("sttl",0) for p in packets if p.get("sttl") is not None]
    dttls = [p.get("dttl",0) for p in packets if p.get("dttl") is not None]

    sttl = int(statistics.mean(sttls)) if sttls else 0
    dttl = int(statistics.mean(dttls)) if dttls else 0

    payloads = [p.get("payload_len",0) for p in packets]
    smeansz = int(statistics.mean(payloads)) if payloads else 0
    dmeansz = smeansz

    res_bdy_len = sum(p.get("res_bdy_len",0) for p in packets)

    # inter-packet times
    times = [p.get("ts",0) for p in packets]
    ipd = [t2 - t1 for t1,t2 in zip(times, times[1:])] if len(times)>=2 else [0]
    Sintpkt = float(statistics.mean(ipd)) if ipd else 0.0
    Dintpkt = Sintpkt
    Sjit = float(statistics.pstdev(ipd)) if len(ipd)>=2 else 0.0

    swin_vals = [p.get("swin",0) for p in packets if p.get("swin") is not None]
    dwin_vals = [p.get("dwin",0) for p in packets if p.get("dwin") is not None]
    swin = int(statistics.mean(swin_vals)) if swin_vals else 0
    dwin = int(statistics.mean(dwin_vals)) if dwin_vals else 0

    stcpb_vals = [p.get("stcpb",0) for p in packets if p.get("stcpb") is not None]
    dtcpb_vals = [p.get("dtcpb",0) for p in packets if p.get("dtcpb") is not None]
    stcpb = int(stcpb_vals[-1]) if stcpb_vals else 0
    dtcpb = int(dtcpb_vals[-1]) if dtcpb_vals else 0

    # simple approximations for RTT, synack, ackdat: not computed reliably without timestamps of SYN/SYN-ACK
    tcprtt = 0.0
    synack = 0.0
    ackdat = 0.0

    # derived/placeholder features
    sloss = 0
    is_sm_ips_ports = 1
    state = 0  # placeholder numeric state

    # basic connection tracking counters approximated
    ct_state_ttl = len(set(sttls))
    ct_flw_http_mthd = 0
    is_ftp_login = 0
    ct_ftp_cmd = 0
    ct_srv_src = 1
    ct_srv_dst = 1
    ct_dst_ltm = 1
    ct_src_ltm = 1
    ct_src_dport_ltm = 1
    ct_dst_sport_ltm = 1
    ct_dst_src_ltm = 1

    # compute Sload as bytes/sec approximation: total bytes / duration
    duration = times[-1] - times[0] if times[-1] > times[0] else 1e-6
    Sload = sbytes / duration if duration > 0 else sbytes

    features = {
        "proto": proto,
        "state": state,
        "sbytes": sbytes,
        "dbytes": dbytes,
        "sttl": sttl,
        "dttl": dttl,
        "sloss": sloss,
        "service": service,
        "Sload": round(Sload,3),
        "swin": swin,
        "dwin": dwin,
        "stcpb": stcpb,
        "dtcpb": dtcpb,
        "smeansz": smeansz,
        "dmeansz": dmeansz,
        "res_bdy_len": res_bdy_len,
        "Sjit": round(Sjit,6),
        "Sintpkt": round(Sintpkt,6),
        "Dintpkt": round(Dintpkt,6),
        "tcprtt": round(tcprtt,6),
        "synack": synack,
        "ackdat": ackdat,
        "is_sm_ips_ports": is_sm_ips_ports,
        "ct_state_ttl": ct_state_ttl,
        "ct_flw_http_mthd": ct_flw_http_mthd,
        "is_ftp_login": is_ftp_login,
        "ct_ftp_cmd": ct_ftp_cmd,
        "ct_srv_src": ct_srv_src,
        "ct_srv_dst": ct_srv_dst,
        "ct_dst_ltm": ct_dst_ltm,
        "ct_src_ltm": ct_src_ltm,
        "ct_src_dport_ltm": ct_src_dport_ltm,
        "ct_dst_sport_ltm": ct_dst_sport_ltm,
        "ct_dst_src_ltm": ct_dst_src_ltm
    }
    return features
