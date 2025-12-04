import statistics
from collections import OrderedDict
from generator.captures.feature_schema import FEATURE_ORDER, validate_and_fill

def _mean_or_zero(lst):
    try:
        return float(statistics.mean(lst)) if lst else 0.0
    except:
        return 0.0

def _std_or_zero(lst):
    try:
        return float(statistics.pstdev(lst)) if len(lst) > 1 else 0.0
    except:
        return 0.0

def _compute_interarrivals(timestamps, direction):
    try:
        seq = [ts for ts, d in timestamps if d == direction]
        if len(seq) < 2:
            return 0.0, 0.0
        diffs = [j - i for i, j in zip(seq, seq[1:])]
        return float(statistics.mean(diffs)), float(statistics.pstdev(diffs))
    except:
        return 0.0, 0.0

def _compute_jitter(timestamps, direction):
    _, std = _compute_interarrivals(timestamps, direction)
    return std

# Map TCP flags to numeric codes
TCP_FLAG_MAP = {"S": 1, "SA": 2, "A": 3, "F": 4, "R": 5, "P": 6, "": 0, None: 0}

def flow_to_features(f):
    """
    Convert a raw flow dict to 34 numeric features for the model.
    """
    features = {}

    key = f.get("key", (0,0,0,0,0))
    src, dst, sport, dport, proto = key

    # Protocol
    features["proto"] = int(proto) if proto else 0

    # State: map most common TCP flag to numeric
    seen_flags = f.get("seen_flags", {})
    if seen_flags:
        most = max(seen_flags.items(), key=lambda kv: kv[1])[0]
        features["state"] = TCP_FLAG_MAP.get(most, 0)
    else:
        features["state"] = 0

    # Bytes
    features["sbytes"] = int(f.get("sbytes", 0) or 0)
    features["dbytes"] = int(f.get("dbytes", 0) or 0)

    # TTL
    features["sttl"] = int(_mean_or_zero(f.get("s_ttls", [])))
    features["dttl"] = int(_mean_or_zero(f.get("d_ttls", [])))

    features["sloss"] = 0
    features["service"] = 0  # numeric placeholder

    # Sload
    duration = max(1e-6, (f.get("last_seen", 0.0) or 0.0) - (f.get("first_seen", 0.0) or 0.0))
    features["Sload"] = float(f.get("sbytes",0) or 0) / duration

    # Window sizes
    features["swin"] = int(_mean_or_zero(f.get("s_windows", [])))
    features["dwin"] = int(_mean_or_zero(f.get("d_windows", [])))

    # TCP sequence numbers (safely)
    s_seq = f.get("s_seq") or []
    features["stcpb"] = int(s_seq[0]) if len(s_seq) > 0 else 0

    d_seq = f.get("d_seq") or []
    features["dtcpb"] = int(d_seq[0]) if len(d_seq) > 0 else 0

    # Payload sizes
    features["smeansz"] = _mean_or_zero(f.get("payload_lens", []))
    features["dmeansz"] = 0.0
    features["res_bdy_len"] = 0.0

    # Jitter and inter-packet times
    timestamps = f.get("timestamps", [])
    features["Sjit"] = _compute_jitter(timestamps, 's')
    features["Sintpkt"], _ = _compute_interarrivals(timestamps, 's')
    features["Dintpkt"], _ = _compute_interarrivals(timestamps, 'd')

    # TCP RTTs safely
    syn_time = f.get("syn_time") or 0.0
    ack_time = f.get("ack_time") or 0.0
    synack_time = f.get("synack_time") or 0.0
    features["tcprtt"] = max(0.0, ack_time - syn_time)
    features["synack"] = max(0.0, synack_time - syn_time)
    features["ackdat"] = 0.0

    # Same subnet check
    try:
        features["is_sm_ips_ports"] = 1 if src.split(".")[0:2] == dst.split(".")[0:2] else 0
    except:
        features["is_sm_ips_ports"] = 0

    # TTL for connection state
    features["ct_state_ttl"] = int(_mean_or_zero(f.get("s_ttls", [])))

    # HTTP/FTP placeholders
    features["ct_flw_http_mthd"] = 0
    features["is_ftp_login"] = 0
    features["ct_ftp_cmd"] = 0

    # Connection trackers
    features["ct_srv_src"] = 1
    features["ct_srv_dst"] = 1
    features["ct_dst_ltm"] = 1
    features["ct_src_ltm"] = 1
    features["ct_src_dport_ltm"] = 1
    features["ct_dst_sport_ltm"] = 1
    features["ct_dst_src_ltm"] = 1

    # Return OrderedDict with proper feature order
    return validate_and_fill(features)
