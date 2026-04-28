import requests
import json
import os
import time

class Updater:
    def __init__(self, config):
        self.github_repo = config.get("github.repo", "")
        self.github_branch = config.get("github.branch", "main")
        self.current_version = self._get_local_version()
        self.latest_version = None
        self.update_available = False

    def _get_local_version(self):
        version_file = os.path.join(os.path.dirname(__file__), '..', '..', '.version')
        if os.path.exists(version_file):
            with open(version_file, 'r') as f:
                return f.read().strip()
        return "0.0.0"

    def check(self):
        cache_file = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'cache', '.version_cache')
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                    if time.time() - data.get("timestamp", 0) < 86400:
                        self.latest_version = data.get("version")
                        if self._compare_versions(self.current_version, self.latest_version) < 0:
                            self.update_available = True
                        return
            except:
                pass
        url = f"https://raw.githubusercontent.com/{self.github_repo}/{self.github_branch}/.version"
        try:
            r = requests.get(url, timeout=3)
            if r.status_code == 200:
                self.latest_version = r.text.strip()
                os.makedirs(os.path.dirname(cache_file), exist_ok=True)
                with open(cache_file, 'w') as f:
                    json.dump({"version": self.latest_version, "timestamp": time.time()}, f)
                if self._compare_versions(self.current_version, self.latest_version) < 0:
                    self.update_available = True
        except:
            pass

    def _compare_versions(self, v1, v2):
        try:
            p1 = [int(x) for x in v1.split(".")]
            p2 = [int(x) for x in v2.split(".")]
            for i in range(max(len(p1), len(p2))):
                a = p1[i] if i < len(p1) else 0
                b = p2[i] if i < len(p2) else 0
                if a < b: return -1
                if a > b: return 1
            return 0
        except:
            return 0

    def get_update_command(self):
        return f"git pull origin {self.github_branch}"
python
# src/api/__init__.py
python
# src/api/ollama_client.py
import requests
import sys
import os
import threading
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from src.api.request_builder import RequestBuilder
from src.api.error_handler import ErrorHandler

class OllamaClient:
    def __init__(self, config):
        self.host = config.get("ollama.host", "http://localhost:11434/api/generate")
        self.model = config.get("ollama.model", "intel-code")
        self.timeout = config.get("ollama.timeout", 120)
        self.builder = RequestBuilder(config)
        self.error_handler = ErrorHandler()
        self._warmed = False
        self._lock = threading.Lock()

    def generate(self, prompt, mode="default"):
        if not self._warmed:
            self.warmup()
        payload = self.builder.build(prompt, self.model, mode)
        try:
            response = requests.post(self.host, json=payload, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            self.error_handler.reset()
            return data.get("response", "").strip()
        except requests.exceptions.RequestException as e:
            return self.error_handler.handle(e, prompt)

    def warmup(self):
        with self._lock:
            if self._warmed:
                return
            payload = self.builder.build("ping", self.model, "concise")
            payload["options"]["num_predict"] = 1
            payload["options"]["num_ctx"] = 128
            try:
                requests.post(self.host, json=payload, timeout=10)
            except:
                pass
            self._warmed = True

    def unload(self):
        try:
            requests.post(
                "http://localhost:11434/api/generate",
                json={"model": self.model, "prompt": "", "keep_alive": 0},
                timeout=5
            )
        except:
            pass

    def is_alive(self):
        try:
            r = requests.get("http://localhost:11434/api/tags", timeout=3)
            if r.ok:
                models = [m["name"] for m in r.json().get("models", [])]
                return self.model in models or f"{self.model}:latest" in models
        except:
            pass
        return False

    def get_available_models(self):
        try:
            r = requests.get("http://localhost:11434/api/tags", timeout=3)
            if r.ok:
                return [m["name"] for m in r.json().get("models", [])]
        except:
            pass
        return []