import requests
import json
import os
import time
from typing import Any

class Updater:
    def __init__(self, config: Any) -> None:
        self.github_repo: str = config.get("github.repo", "")
        self.github_branch: str = config.get("github.branch", "main")
        self.current_version: str = self._get_local_version()
        self.latest_version: str | None = None
        self.update_available: bool = False

    def _get_local_version(self) -> str:
        version_file: str = os.path.join(os.path.dirname(__file__), '..', '..', '.version')
        if os.path.exists(version_file):
            with open(version_file, 'r', encoding='utf-8') as f:
                return f.read().strip()
        return "0.0.0"

    def check(self) -> None:
        cache_file: str = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'cache', '.version_cache')
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    data: dict = json.load(f)
                    if time.time() - data.get("timestamp", 0) < 86400:
                        self.latest_version = data.get("version")
                        if self._compare_versions(self.current_version, self.latest_version) < 0:
                            self.update_available = True
                        return
            except:
                pass
        url: str = f"https://raw.githubusercontent.com/{self.github_repo}/{self.github_branch}/.version"
        try:
            r: requests.Response = requests.get(url, timeout=3)
            if r.status_code == 200:
                self.latest_version = r.text.strip()
                os.makedirs(os.path.dirname(cache_file), exist_ok=True)
                with open(cache_file, 'w', encoding='utf-8') as f:
                    json.dump({"version": self.latest_version, "timestamp": time.time()}, f)
                if self._compare_versions(self.current_version, self.latest_version) < 0:
                    self.update_available = True
        except:
            pass

    def _compare_versions(self, v1: str, v2: str | None) -> int:
        if not v2:
            return 0
        try:
            p1: list = [int(x) for x in v1.split(".")]
            p2: list = [int(x) for x in v2.split(".")]
            for i in range(max(len(p1), len(p2))):
                a: int = p1[i] if i < len(p1) else 0
                b: int = p2[i] if i < len(p2) else 0
                if a < b: return -1
                if a > b: return 1
            return 0
        except:
            return 0

    def get_update_command(self) -> str:
        return f"git pull origin {self.github_branch}"