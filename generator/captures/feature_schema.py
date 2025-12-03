
from collections import OrderedDict

FEATURE_ORDER = [
    "proto","state","sbytes","dbytes","sttl","dttl","sloss","service","Sload",
    "swin","dwin","stcpb","dtcpb","smeansz","dmeansz","res_bdy_len","Sjit",
    "Sintpkt","Dintpkt","tcprtt","synack","ackdat","is_sm_ips_ports",
    "ct_state_ttl","ct_flw_http_mthd","is_ftp_login","ct_ftp_cmd","ct_srv_src",
    "ct_srv_dst","ct_dst_ltm","ct_src_ltm","ct_src_dport_ltm","ct_dst_sport_ltm",
    "ct_dst_src_ltm"
]

def validate_and_fill(features_dict):
    """
    Return an OrderedDict with FEATURE_ORDER as keys. For missing keys, fill with 0 or sensible default.
    """
    out = OrderedDict()
    for key in FEATURE_ORDER:
        if key in features_dict:
            out[key] = features_dict[key]
        else:
            # default for service should be "other"
            if key == "service":
                out[key] = "other"
            else:
                out[key] = 0 if not key.endswith("_mthd") else 0
    return out
