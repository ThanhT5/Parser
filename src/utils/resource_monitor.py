import time
import psutil
import threading
from contextlib import contextmanager


class ResourceMonitor:
    """Monitor system resources and implement throttling."""
    def __init__(self, cpu_threshold=70, memory_threshold=80):
        self.cpu_threshold = cpu_threshold
        self.memory_threshold = memory_threshold
        self._lock = threading.Lock()
       
    def check_resources(self) -> bool:
        """Check if resource usage is below thresholds."""
        cpu_percent = psutil.cpu_percent(interval=1)
        memory_percent = psutil.virtual_memory().percent
        return cpu_percent < self.cpu_threshold and memory_percent < self.memory_threshold
   
    @contextmanager
    def throttle_if_needed(self, check_interval=2):
        """Context manager to throttle processing if resources are constrained."""
        while not self.check_resources():
            time.sleep(check_interval)
        yield