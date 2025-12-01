# capture/flow_tracker.py
from utils_capture import get_5tuple
from utils.logger import get_logger

logger = get_logger("FLOW_TRACKER")

class FlowTracker:
    def __init__(self):
        self.active_flows = {}
        self.TIMEOUT = 3  # seconds without packets → flow ends

    def add_packet(self, pkt):
        flow_key = get_5tuple(pkt)

        if flow_key not in self.active_flows:
            self.active_flows[flow_key] = {
                "packets": [],
                "last_ts": pkt.time
            }

        flow = self.active_flows[flow_key]
        flow["packets"].append(pkt)
        flow["last_ts"] = pkt.time

        # finalize flow if timeout
        return self._check_timeouts(), None

    def _check_timeouts(self):
        finished = []

        now = time.time()
        for key, flow in list(self.active_flows.items()):
            if now - flow["last_ts"] > self.TIMEOUT:
                finished.append((key, flow))
                del self.active_flows[key]

        return finished
