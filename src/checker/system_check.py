import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from src.checker.cpu_checker import CpuChecker
from src.checker.ram_checker import RamChecker
from src.checker.disk_checker import DiskChecker
from src.checker.network_checker import NetworkChecker
from concurrent.futures import ThreadPoolExecutor, as_completed

class SystemChecker:
    def __init__(self, config):
        self.checks = [
            CpuChecker(),
            RamChecker(),
            DiskChecker(),
            NetworkChecker(config),
        ]

    def check_all(self):
        results = []
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {executor.submit(c.check): c for c in self.checks}
            for future in as_completed(futures):
                try:
                    results.append(future.result())
                except Exception as e:
                    results.append((False, f"Erreur: {str(e)[:50]}"))
        return all(r[0] for r in results), results