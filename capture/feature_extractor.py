import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# capture/feature_extractor.py
import json
import numpy as np
from utils.logger import get_logger

logger = get_logger("FEATURE_EXTRACTOR")

class FeatureExtractor:
    def __init__(self):
        with open("capture/feature_schema.json") as f:
            self.schema = json.load(f)

    def extract(self, flow):
        packets = flow["packets"]
        key = flow["key"]

        features = {}

        # Example extraction
        features["src_ip"] = key[0]
        features["dst_ip"] = key[1]
        features["src_port"] = key[2]
        features["dst_port"] = key[3]
        features["protocol"] = key[4]

        # Add all features defined in schema
        for f in self.schema:
            features[f["name"]] = self._compute_feature(f["name"], packets)

        return features

    def _compute_feature(self, name, packets):
        # Placeholder for your real logic
        if name == "packet_count":
            return len(packets)
        if name == "byte_count":
            return sum(len(p) for p in packets)

        return 0
