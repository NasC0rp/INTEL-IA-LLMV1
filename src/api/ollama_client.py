import threading
from typing import Any, Dict

import requests

from src.api.error_handler import ErrorHandler
from src.api.request_builder import RequestBuilder


class OllamaClient:
    def __init__(self, config: Any, logger: Any = None) -> None:
        self.host: str = config.get("ollama.host", "http://localhost:11434/api/generate")
        self.base_url: str = self.host.removesuffix("/api/generate").rstrip("/")
        self.model: str = config.get("ollama.model", "intel-code")
        self.timeout: int = config.get("ollama.timeout", 120)
        self.logger: Any = logger
        self.builder: RequestBuilder = RequestBuilder(config)
        self.error_handler: ErrorHandler = ErrorHandler()
        self._warmed: bool = False
        self._lock: threading.Lock = threading.Lock()
        self._last_eval_count: int = 0
        self._last_eval_seconds: float = 0.0
        self._last_total_seconds: float = 0.0
        self._last_attempts: int = 0
        self._last_error: str = ""

    def generate(self, prompt: str, mode: str = "default") -> str:
        if not self._warmed:
            self.warmup()
        payload: Dict[str, Any] = self.builder.build(prompt, self.model, mode)
        try:
            self._last_attempts = 1
            self._last_error = ""
            text = self._generate_payload(payload)
            if text and not text.startswith("Erreur"):
                return text
            if self.logger:
                self.logger.warning(f"Reponse vide ou erreur en mode {mode}. Retry fallback.")
            retry_payload = self.builder.build_retry(prompt, self.model)
            self._last_attempts = 2
            return self._generate_payload(retry_payload)
        except requests.exceptions.RequestException as e:
            self._last_error = str(e)
            return self.error_handler.handle(e, prompt)

    def _generate_payload(self, payload: Dict[str, Any]) -> str:
        response: requests.Response = requests.post(self.host, json=payload, timeout=self.timeout)
        if response.status_code != 200:
            self._last_error = f"HTTP {response.status_code}: {response.text[:200]}"
            if self.logger:
                self.logger.error(f"Ollama error: {self._last_error}")
            return f"Erreur {response.status_code}: {response.text[:200]}"
        data: Dict[str, Any] = response.json()
        self.error_handler.reset()
        self._last_eval_count = data.get("eval_count", 0)
        self._last_eval_seconds = data.get("eval_duration", 0) / 1_000_000_000
        self._last_total_seconds = data.get("total_duration", 0) / 1_000_000_000
        text = data.get("response", "").strip()
        if not text:
            self._last_error = "empty_response"
            if self.logger:
                self.logger.warning(f"Ollama empty response with payload options: {payload.get('options', {})}")
        return text

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

    def get_last_tokens_per_second(self) -> float:
        if self._last_eval_seconds <= 0:
            return 0.0
        return self._last_eval_count / self._last_eval_seconds

    def get_last_total_seconds(self) -> float:
        return self._last_total_seconds

    def get_last_attempts(self) -> int:
        return self._last_attempts

    def get_last_error(self) -> str:
        return self._last_error
