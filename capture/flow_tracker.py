# capture/flow_tracker.py
import time
import threading
from collections import defaultdict
from utils.logger import get_logger
from config.settings import FLOW_TIMEOUT

logger = get_logger("FlowTracker")

class FlowTracker:
    def __init__(self, on_flow_complete=None):
        """
        on_flow_complete(flow_key, packets_list) -> called when a flow times out
        packets_list is a list of packet dicts (as from packet_parser)
        """
        self.flows = {}  # key -> {packets: [...], first_ts, last_ts}
        self.lock = threading.Lock()
        self.on_flow_complete = on_flow_complete
        self.running = True
        self._thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self._thread.start()

    def _make_key(self, pkt):
        # 5-tuple key: src,dst,sport,dport,proto
        return (pkt.get("src"), pkt.get("dst"), pkt.get("sport"), pkt.get("dport"), pkt.get("proto"))

    def update(self, pkt):
        if pkt is None:
            return
        key = self._make_key(pkt)
        now = pkt.get("ts", time.time())
        with self.lock:
            f = self.flows.get(key)
            if f is None:
                f = {"packets": [], "first_ts": now, "last_ts": now}
                self.flows[key] = f
            f["packets"].append(pkt)
            f["last_ts"] = now

    def _cleanup_loop(self):
        while self.running:
            now = time.time()
            remove = []
            with self.lock:
                for key, f in list(self.flows.items()):
                    idle = now - f["last_ts"]
                    if idle >= FLOW_TIMEOUT:
                        packets = f["packets"]
                        # call callback (outside lock)
                        try:
                            if self.on_flow_complete:
                                # deliver a shallow copy
                                self.on_flow_complete(key, list(packets))
                        except Exception:
                            logger.exception("on_flow_complete error")
                        remove.append(key)
                for k in remove:
                    del self.flows[k]
            time.sleep(1.0)

    def stop(self):
        self.running = False
        self._thread.join(timeout=2.0)
