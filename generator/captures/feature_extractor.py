import math
import statistics
from collections import Counter

FEATURE_NAMES = [
    "proto","state","sbytes","dbytes","sttl","dttl","sloss","service","Sload",
    "swin","dwin","stcpb","dtcpb","smeansz","dmeansz","res_bdy_len","Sjit",
    "Sintpkt","Dintpkt","tcprtt","synack","ackdat","is_sm_ips_ports",
    "ct_state_ttl","ct_flw_http_mthd","is_ftp_login","ct_ftp_cmd","ct_srv_src",
    "ct_srv_dst","ct_dst_ltm","ct_src_ltm","ct_src_dport_ltm","ct_dst_sport_ltm",
    "ct_dst_src_ltm"
]

def _mean_or_zero(lst):
    return float(statistics.mean(lst)) if lst else 0.0

def _std_or_zero(lst):
    return float(statistics.pstdev(lst)) if len(lst) > 1 else 0.0

def _compute_interarrivals(timestamps, direction):
    # timestamps: list of (ts, dir)
    seq = [ts for ts, d in timestamps if d == direction]
    if len(seq) < 2:
        return 0.0, 0.0  # mean, std
    diffs = [j-i for i,j in zip(seq, seq[1:])]
    return float(statistics.mean(diffs)), float(statistics.pstdev(diffs))

def _compute_jitter(timestamps, direction):
    _, std = _compute_interarrivals(timestamps, direction)
    return std

def flow_to_features(f):
    # f is the flow dict created in flow_tracker.py
    features = {}
    src, dst, sport, dport, proto = f["key"]
    features["proto"] = proto
    # state: best-effort map of flags (string summary)
    # We pick the most common observed TCP flag string or 0 for UDP
    if f["seen_flags"]:
        most = max(f["seen_flags"].items(), key=lambda kv: kv[1])[0]
        features["state"] = most
    else:
        features["state"] = 0

    features["sbytes"] = f.get("sbytes", 0)
    features["dbytes"] = f.get("dbytes", 0)
    features["sttl"] = int(_mean_or_zero(f.get("s_ttls", [])))
    features["dttl"] = int(_mean_or_zero(f.get("d_ttls", [])))
    features["sloss"] = 0  # requires retransmission/ack tracking; placeholder 0

    # service detection by port heuristic
    service = "other"
    known = {80:"http", 443:"https", 21:"ftp", 22:"ssh", 53:"dns"}
    for p in (sport, dport):
        if p in known:
            service = known[p]
    features["service"] = service

    # Sload: src bytes / duration
    duration = max(1e-6, f["last_seen"] - f["first_seen"])
    features["Sload"] = float(f["sbytes"]) / duration
    features["swin"] = int(_mean_or_zero(f.get("s_windows", [])))
    features["dwin"] = int(_mean_or_zero(f.get("d_windows", [])))
    features["stcpb"] = int(f["s_seq"][0]) if f.get("s_seq") else 0
    features["dtcpb"] = int(f["d_seq"][0]) if f.get("d_seq") else 0
    features["smeansz"] = _mean_or_zero(f.get("payload_lens", []))
    features["dmeansz"] = _mean_or_zero([])  # destination mean size; need reverse packets to fill
    features["res_bdy_len"] = 0  # needs HTTP parsing of responses; default 0

    features["Sjit"] = _compute_jitter(f["timestamps"], 's')
    features["Sintpkt"], _ = _compute_interarrivals(f["timestamps"], 's')
    features["Dintpkt"], _ = _compute_interarrivals(f["timestamps"], 'd')

    # tcprtt: approximate using syn -> synack -> ack
    if f.get("syn_time") and f.get("ack_time"):
        features["tcprtt"] = max(0.0, f["ack_time"] - f["syn_time"])
    else:
        features["tcprtt"] = 0.0

    if f.get("syn_time") and f.get("synack_time"):
        features["synack"] = max(0.0, f["synack_time"] - f["syn_time"])
    else:
        features["synack"] = 0.0

    # ackdat: time between data packet and its ack (requires matching packets)
    features["ackdat"] = 0.0

    features["is_sm_ips_ports"] = 1 if src.split(".")[0:2] == dst.split(".")[0:2] else 0
    features["ct_state_ttl"] = int(_mean_or_zero(f.get("s_ttls", [])))

    # HTTP detection: crudely inspect service or port
    features["ct_flw_http_mthd"] = 1 if features["service"] == "http" else 0
    features["is_ftp_login"] = 0
    features["ct_ftp_cmd"] = 0

    # connection trackers - simple counts from flows dict; set to 1 for minimal
    features["ct_srv_src"] = 1
    features["ct_srv_dst"] = 1
    features["ct_dst_ltm"] = 1
    features["ct_src_ltm"] = 1
    features["ct_src_dport_ltm"] = 1
    features["ct_dst_sport_ltm"] = 1
    features["ct_dst_src_ltm"] = 1

    return features
