import os
from datetime import datetime

class Logger:
    def __init__(self, name: str = "IntelCODE", logs_dir: str = "data/logs") -> None:
        self.log_file: str = os.path.join(logs_dir, "intel_code.log")
        os.makedirs(logs_dir, exist_ok=True)

    def _log(self, level: str, message: str) -> None:
        timestamp: str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp}] [{level}] {message}\n")

    def info(self, msg: str) -> None: self._log("INFO", msg)
    def warning(self, msg: str) -> None: self._log("WARNING", msg)
    def error(self, msg: str) -> None: self._log("ERROR", msg)
    def debug(self, msg: str) -> None: self._log("DEBUG", msg)