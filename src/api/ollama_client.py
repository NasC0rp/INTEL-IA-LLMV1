import requests
import threading
from typing import Optional, Dict, Any
from src.api.request_builder import RequestBuilder
from src.api.error_handler import ErrorHandler

class OllamaClient:
    def __init__(self, config: Any) -> None:
        self.host: str = config.get("ollama.host", "http://localhost:11434/api/generate")
        self.model: str = config.get("ollama.model", "intel-code")
        self.timeout: int = config.get("ollama.timeout", 120)
        self.builder: RequestBuilder = RequestBuilder(config)
        self.error_handler: ErrorHandler = ErrorHandler()
        self._warmed: bool = False
        self._lock: threading.Lock = threading.Lock()

    def generate(self, prompt: str, mode: str = "default") -> str:
        if not self._warmed:
            self.warmup()
        payload: Dict[str, Any] = self.builder.build(prompt, self.model, mode)
        try:
            response: requests.Response = requests.post(self.host, json=payload, timeout=self.timeout)
            response.raise_for_status()
            data: Dict[str, Any] = response.json()
            self.error_handler.reset()
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
                "http://localhost:11434/api/generate",
                json={"model": self.model, "prompt": "", "keep_alive": 0},
                timeout=5
            )
        except requests.exceptions.RequestException:
            pass

    def is_alive(self) -> bool:
        try:
            r: requests.Response = requests.get("http://localhost:11434/api/tags", timeout=3)
            if r.ok:
                models: list = [m["name"] for m in r.json().get("models", [])]
                return self.model in models or f"{self.model}:latest" in models
        except requests.exceptions.RequestException:
            pass
        return False

    def get_available_models(self) -> list:
        try:
            r: requests.Response = requests.get("http://localhost:11434/api/tags", timeout=3)
            if r.ok:
                return [m["name"] for m in r.json().get("models", [])]
        except requests.exceptions.RequestException:
            pass
        return []