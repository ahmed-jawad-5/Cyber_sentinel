# generator/captures/feature_schema.py
from collections import OrderedDict

# === single source-of-truth list (18 features) ===
FEATURE_SCHEMA = [
    "dur",
    "sbytes",
    "dbytes",
    "Sload",
    "swin",
    "stcpb",
    "smeansz",
    "Sjit",
    "Djit",
    "Stime",
    "Sintpkt",
    "tcprtt",
    "synack",
    "ct_srv_src",
    "ct_srv_dst",
    "ct_dst_ltm",
    "ct_src_ltm",
    "ct_dst_src_ltm"
]

# keep old name available for compatibility
FEATURE_ORDER = FEATURE_SCHEMA

def validate_and_fill(features_dict):
    """
    Return an OrderedDict with FEATURE_ORDER as keys. For missing keys, fill with zeros
    or reasonable defaults. Ensures numeric values where possible.
    """
    out = OrderedDict()
    for key in FEATURE_ORDER:
        if key in features_dict:
            val = features_dict[key]
            # ensure numeric where appropriate
            try:
                # If value is bool or int-like/float-like, convert to float/int as appropriate.
                if isinstance(val, (int, float)):
                    out[key] = val
                else:
                    # attempt numeric conversion
                    out[key] = float(val)
            except Exception:
                # fallback: keep as-is for non-numeric (rare) or set 0
                out[key] = 0
        else:
            # missing -> default 0 (safe numeric)
            out[key] = 0
    return out
