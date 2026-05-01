import threading
from typing import Any, Dict

import requests

from src.api.error_handler import ErrorHandler
from src.api.request_builder import RequestBuilder


class OllamaClient:
    def __init__(self, config: Any) -> None:
        self.host: str = config.get("ollama.host", "http://localhost:11434/api/generate")
        self.base_url: str = self.host.removesuffix("/api/generate").rstrip("/")
        self.model: str = config.get("ollama.model", "intel-code")
        self.timeout: int = config.get("ollama.timeout", 120)
        self.builder: RequestBuilder = RequestBuilder(config)
        self.error_handler: ErrorHandler = ErrorHandler()
        self._warmed: bool = False
        self._lock: threading.Lock = threading.Lock()
        self._last_eval_count: int = 0

    def generate(self, prompt: str, mode: str = "default") -> str:
        if not self._warmed:
            self.warmup()
        payload: Dict[str, Any] = self.builder.build(prompt, self.model, mode)
        try:
            response: requests.Response = requests.post(self.host, json=payload, timeout=self.timeout)
            if response.status_code != 200:
                return f"Erreur {response.status_code}: {response.text[:200]}"
            data: Dict[str, Any] = response.json()
            self.error_handler.reset()
            self._last_eval_count = data.get("eval_count", 0)
            return data.get("response", "").strip()
        except requests.exceptions.RequestException as e:
            return self.error_handler.handle(e, prompt)

    def warmup(self) -> None:
        with self._lock:
            if self._warmed:
                return
            payload: Dict[str, Any] = self.builder.build("ping", self.model, "concise")
            payload["options"]["num_predict"] = 1
            payload["options"]["num_ctx"] = 128
            try:
                requests.post(self.host, json=payload, timeout=10)
            except requests.exceptions.RequestException:
                pass
            self._warmed = True

    def unload(self) -> None:
        try:
            requests.post(
                f"{self.base_url}/api/generate",
                json={"model": self.model, "prompt": "", "keep_alive": 0},
                timeout=5,
            )
        except requests.exceptions.RequestException:
            pass

    def is_alive(self) -> bool:
        try:
            r: requests.Response = requests.get(f"{self.base_url}/api/tags", timeout=3)
            if r.ok:
                models = [m["name"] for m in r.json().get("models", [])]
                return self.model in models or f"{self.model}:latest" in models
        except requests.exceptions.RequestException:
            pass
        return False

    def get_available_models(self) -> list:
        try:
            r: requests.Response = requests.get(f"{self.base_url}/api/tags", timeout=3)
            if r.ok:
                return [m["name"] for m in r.json().get("models", [])]
        except requests.exceptions.RequestException:
            pass
        return []

    def get_last_eval_count(self) -> int:
        return self._last_eval_count
