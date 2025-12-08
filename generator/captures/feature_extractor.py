# generator/captures/feature_extractor.py
import statistics
from collections import OrderedDict
from .feature_schema import FEATURE_ORDER, validate_and_fill

def _mean_or_zero(lst):
    try:
        return float(statistics.mean(lst)) if lst else 0.0
    except Exception:
        return 0.0

def _std_or_zero(lst):
    try:
        return float(statistics.pstdev(lst)) if len(lst) > 1 else 0.0
    except Exception:
        return 0.0

def _compute_interarrivals(timestamps, direction):
    """
    timestamps: list of (ts, 's'|'d')
    returns: (mean_interarrival, std_interarrival)
    """
    try:
        seq = [ts for ts, d in timestamps if d == direction]
        if len(seq) < 2:
            return 0.0, 0.0
        diffs = [j - i for i, j in zip(seq, seq[1:])]
        return float(statistics.mean(diffs)), float(statistics.pstdev(diffs)) if len(diffs) > 1 else 0.0
    except Exception:
        return 0.0, 0.0

def _compute_jitter(timestamps, direction):
    _, std = _compute_interarrivals(timestamps, direction)
    return std

def flow_to_features(f):
    """
    Convert a raw flow dict (from flow_tracker) into an 18-feature dict.
    Features are taken from FEATURE_ORDER (single source of truth).
    All outputs are numeric (int/float) with safe defaults.
    """
    features = {}

    # safe getters
    key = f.get("key", (None, None, 0, 0, 0))
    src, dst, sport, dport, proto = key

    # 1. dur: duration of flow (last_seen - first_seen)
    first = float(f.get("first_seen") or 0.0)
    last = float(f.get("last_seen") or first)
    dur = max(0.0, last - first)
    features["dur"] = dur

    # 2/3. sbytes, dbytes
    sbytes = int(f.get("sbytes", 0) or 0)
    dbytes = int(f.get("dbytes", 0) or 0)
    features["sbytes"] = sbytes
    features["dbytes"] = dbytes

    # 4. Sload (bytes/sec) - guard against tiny durations and cap outliers
    Sload = float(sbytes) / max(1e-6, dur)
    # clamp to reasonable max to avoid blowing up model (adjust if needed)
    if Sload != Sload:  # NaN guard
        Sload = 0.0
    Sload = min(Sload, 1e8)
    features["Sload"] = Sload

    # 5. swin (mean source TCP window)
    features["swin"] = int(_mean_or_zero(f.get("s_windows", [])))

    # 6. stcpb: first seen source seq or 0
    s_seq = f.get("s_seq") or []
    features["stcpb"] = int(s_seq[0]) if len(s_seq) > 0 else 0

    # 7. smeansz: mean source payload size (use payload_lens collected)
    features["smeansz"] = _mean_or_zero(f.get("payload_lens", []))

    # 8. Sjit: jitter for source direction
    timestamps = f.get("timestamps", [])
    features["Sjit"] = float(_compute_jitter(timestamps, 's'))

    # 9. Djit: jitter for dest direction
    features["Djit"] = float(_compute_jitter(timestamps, 'd'))

    # 10. Stime: use flow start time relative to epoch (float seconds)
    # Note: If your model expects something else, change accordingly.
    features["Stime"] = float(first)

    # 11. Sintpkt: mean inter-arrival time for source direction
    features["Sintpkt"], _ = _compute_interarrivals(timestamps, 's')

    # 12. tcprtt: ack_time - syn_time (safe)
    syn_time = f.get("syn_time") or 0.0
    ack_time = f.get("ack_time") or 0.0
    try:
        tcprtt = max(0.0, float(ack_time) - float(syn_time))
    except Exception:
        tcprtt = 0.0
    features["tcprtt"] = tcprtt

    # 13. synack: synack_time - syn_time
    synack_time = f.get("synack_time") or 0.0
    try:
        synack = max(0.0, float(synack_time) - float(syn_time))
    except Exception:
        synack = 0.0
    features["synack"] = synack

    # 14/15/16/17/18: connection trackers (best-effort approximations)
    # We do simple, defensible computations based on available flow dict:
    # ct_srv_src: number of distinct service ports observed in this flow (as proxy)
    service_ports = f.get("service_ports") or set()
    try:
        ct_srv_src = len(service_ports)
    except Exception:
        ct_srv_src = 0
    features["ct_srv_src"] = ct_srv_src if ct_srv_src >= 0 else 0

    # ct_srv_dst: number of distinct src IPs seen for this dst in short-term window
    # We don't have global state here, so approximate with 1 (self) or length of d_seq as proxy
    try:
        ct_srv_dst = max(1, len(f.get("d_seq") or []))
    except Exception:
        ct_srv_dst = 1
    features["ct_srv_dst"] = ct_srv_dst

    # ct_dst_ltm, ct_src_ltm, ct_dst_src_ltm: long-term counters are not available
    # Provide reasonable defaults or proxies:
    features["ct_dst_ltm"] = int(f.get("ct_dst_ltm", 1) or 1)
    features["ct_src_ltm"] = int(f.get("ct_src_ltm", 1) or 1)
    features["ct_dst_src_ltm"] = int(f.get("ct_dst_src_ltm", 1) or 1)

    # build final dict in the FEATURE_ORDER
    out = {}
    for k in FEATURE_ORDER:
        out[k] = features.get(k, 0)

    # validate and return OrderedDict
    return validate_and_fill(out)
