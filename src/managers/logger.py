import os
from datetime import datetime

class Logger:
    def __init__(self, name="IntelCODE", logs_dir="data/logs"):
        self.log_file = os.path.join(logs_dir, "intel_code.log")
        os.makedirs(logs_dir, exist_ok=True)

    def _log(self, level, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp}] [{level}] {message}\n")

    def info(self, msg): self._log("INFO", msg)
    def warning(self, msg): self._log("WARNING", msg)
    def error(self, msg): self._log("ERROR", msg)
    def debug(self, msg): self._log("DEBUG", msg)