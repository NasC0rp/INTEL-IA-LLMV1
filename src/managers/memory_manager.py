
import gc
import os

class MemoryManager:
    def __init__(self, config):
        self.max_ram_mb = config.get("system.max_ram_mb", 4096)

    def optimize(self):
        gc.collect()

    def cleanup(self):
        gc.collect()

    def get_usage(self):
        try:
            import psutil
            return psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024)
        except:
            return 0