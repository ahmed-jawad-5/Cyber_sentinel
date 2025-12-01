# capture/flow_sniffer.py
import csv
import time
from capture.feature_extractor import FeatureExtractor
from capture.flow_tracker import FlowTracker
from server.anomaly_detector import AnomalyDetector

class FlowSnifferRunner:
    def __init__(self):
        self.flow_tracker = FlowTracker()
        self.feature_extractor = FeatureExtractor()
        self.detector = AnomalyDetector(model_path="models/xg_boost.pkl",
                                        scaler_path="models/scaler.pkl")
        self.csv_file = "output/captured_flows.csv"

        # Write header if file empty
        with open(self.csv_file, "a", newline="") as f:
            writer = csv.writer(f)
            header = ["timestamp", "src_ip", "dst_ip", "src_port", "dst_port"] + \
                     self.detector.selected_features + ["label"]
            writer.writerow(header)

    def process_flow(self, raw_flow):
        """
        Called for each raw flow (dict with packet info)
        """
        # Extract 34 features
        features = self.feature_extractor.extract(raw_flow)

        # Predict anomaly/normal
        label = self.detector.predict(features)

        # Add timestamp and src/dst info
        timestamp = time.time()
        src_ip = raw_flow.get("src_ip", "0.0.0.0")
        dst_ip = raw_flow.get("dst_ip", "0.0.0.0")
        src_port = raw_flow.get("src_port", 0)
        dst_port = raw_flow.get("dst_port", 0)

        # Save to CSV
        with open(self.csv_file, "a", newline="") as f:
            writer = csv.writer(f)
            row = [timestamp, src_ip, dst_ip, src_port, dst_port] + \
                  [features[f] for f in self.detector.selected_features] + [label]
            writer.writerow(row)

    def run(self):
        """
        Main loop: get flows from FlowTracker and process them
        """
        for raw_flow in self.flow_tracker.get_flows():  # your existing flow source
            self.process_flow(raw_flow)
