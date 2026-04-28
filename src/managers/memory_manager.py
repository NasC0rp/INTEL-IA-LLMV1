import gc
import os
from typing import Any

class MemoryManager:
    def __init__(self, config: Any) -> None:
        self.max_ram_mb: int = config.get("system.max_ram_mb", 4096)

    def optimize(self) -> None:
        gc.collect()

    def cleanup(self) -> None:
        gc.collect()

    def get_usage(self) -> float:
        try:
            import psutil
            return psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024)
        except ImportError:
            return 0.0