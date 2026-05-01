from src.checker.cpu_checker import CpuChecker
from src.checker.ram_checker import RamChecker
from src.checker.disk_checker import DiskChecker
from src.checker.network_checker import NetworkChecker
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

class SystemChecker:
    def __init__(self, config: Any) -> None:
        self.checks: list = [
            CpuChecker(),
            RamChecker(),
            DiskChecker(),
            NetworkChecker(config),
        ]

    def check_all(self) -> tuple:
        results: list = []
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures: dict = {executor.submit(c.check): c for c in self.checks}
            for future in as_completed(futures):
                try:
                    results.append(future.result())
                except Exception as e:
                    results.append((False, f"Erreur: {str(e)[:50]}"))
        return all(r[0] for r in results), results