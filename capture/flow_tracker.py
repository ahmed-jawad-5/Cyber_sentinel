# capture/flow_tracker.py
import time
from threading import Lock, Thread
from capture.feature_extractor import extract_features
from capture.utils_capture import write_flow_csv
from config import FLOW_TIMEOUT
from utils.logger import get_logger

logger = get_logger("FlowTracker")

class FlowTracker:
    def __init__(self):
        # key = (src, sport, dst, dport, proto)
        self.flows = {}
        self.lock = Lock()
        self.running = True

        # background thread to clean up timed-out flows
        self.cleanup_thread = Thread(target=self._cleanup_loop, daemon=True)
        self.cleanup_thread.start()

    def update_flow(self, pkt_info: dict):
        """Add packet to flow table or create a new flow."""
        key = (
            pkt_info.get("src"),
            pkt_info.get("sport"),
            pkt_info.get("dst"),
            pkt_info.get("dport"),
            pkt_info.get("proto")
        )

        with self.lock:
            flow = self.flows.get(key)
            now = time.time()
            if flow is None:
                # initialize new flow
                flow = {
                    "packets": [],
                    "first_ts": now,
                    "last_ts": now
                }
                self.flows[key] = flow

            # append packet info
            pkt_entry =_
