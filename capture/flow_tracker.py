# capture/flow_tracker.py

from datetime import datetime
from .utils_capture import get_5tuple


class FlowTracker:

    def __init__(self):
        self.flows = {}  # 5-tuple → stats dict

    def update_flow(self, packet):
        flow_id = get_5tuple(packet)
        if flow_id is None:
            return None, None

        timestamp = datetime.now().timestamp()
        packet_len = len(packet)

        if flow_id not in self.flows:
            self.flows[flow_id] = {
                "first_ts": timestamp,
                "last_ts": timestamp,
                "total_pkts": 0,
                "total_bytes": 0,
                "pkt_sizes": [],
                "iat_list": [],
                "last_pkt_ts": None
            }

        flow = self.flows[flow_id]

        # Update stats
        flow["total_pkts"] += 1
        flow["total_bytes"] += packet_len
        flow["pkt_sizes"].append(packet_len)

        if flow["last_pkt_ts"] is not None:
            flow["iat_list"].append(timestamp - flow["last_pkt_ts"])

        flow["last_pkt_ts"] = timestamp
        flow["last_ts"] = timestamp

        # Extract 34 features
        features = self.extract_34_features(flow)

        return flow_id, features

    def extract_34_features(self, f):
        import numpy as np

        pkt_sizes = np.array(f["pkt_sizes"])
        iat = np.array(f["iat_list"]) if len(f["iat_list"]) else np.array([0])

        return [
            f["total_pkts"],                   # 1
            f["total_bytes"],                  # 2
            pkt_sizes.mean(),                  # 3
            pkt_sizes.std(),                   # 4
            pkt_sizes.max(),                   # 5
            pkt_sizes.min(),                   # 6
            pkt_sizes.sum(),                   # 7
            len(iat),                           # 8
            iat.mean(),                         # 9
            iat.std(),                          # 10
            iat.max(),                          # 11
            iat.min(),                          # 12
            f["last_ts"] - f["first_ts"],      # 13
            np.percentile(pkt_sizes, 10),      # 14
            np.percentile(pkt_sizes, 20),      # 15
            np.percentile(pkt_sizes, 30),      # 16
            np.percentile(pkt_sizes, 40),      # 17
            np.percentile(pkt_sizes, 50),      # 18
            np.percentile(pkt_sizes, 60),      # 19
            np.percentile(pkt_sizes, 70),      # 20
            np.percentile(pkt_sizes, 80),      # 21
            np.percentile(pkt_sizes, 90),      # 22
            pkt_sizes.var(),                    # 23
            iat.var(),                          # 24
            float(pkt_sizes[-1]),               # 25 last packet size
            float(iat[-1]) if len(iat) else 0,  # 26 last IAT
            f["total_bytes"] / max(f["total_pkts"], 1),  # 27 avg bytes/packet
            pkt_sizes.mean() ** 2,             # 28 some engineered feature
            iat.mean() ** 2,                   # 29
            pkt_sizes.std() ** 2,              # 30
            iat.std() ** 2,                    # 31
            f["total_pkts"] / max((f["last_ts"] - f["first_ts"]), 1e-6),  # 32 packet rate
            f["total_bytes"] / max((f["last_ts"] - f["first_ts"]), 1e-6), # 33 byte rate
            len(pkt_sizes)                     # 34
        ]
