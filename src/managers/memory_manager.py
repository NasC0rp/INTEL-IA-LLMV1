import gc
import os
from typing import Any

import psutil


class MemoryManager:
    def __init__(self, config: Any) -> None:
        self.max_ram_mb: int = config.get("system.max_ram_mb", 4096)
        self.process = psutil.Process(os.getpid())

    def optimize(self) -> None:
        gc.collect()
        if self.get_usage() > self.max_ram_mb:
            self.process.rlimit(psutil.RLIMIT_AS, (self.max_ram_mb * 1024 * 1024,))

    def cleanup(self) -> None:
        gc.collect()

    def get_usage(self) -> float:
        return self.process.memory_info().rss / (1024 * 1024)

    def is_over_limit(self) -> bool:
        return self.get_usage() > self.max_ram_mb