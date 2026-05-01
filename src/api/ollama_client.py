import time
import threading
from typing import Any, Callable, Dict, Iterator, Optional

import requests


class OllamaClient:
    def __init__(self, config: Any, logger: Any = None) -> None:
        self.host: str = config.get("ollama.host", "http://localhost:11434/api/generate")
        self.base_url: str = self.host.removesuffix("/api/generate").rstrip("/")
        self.model: str = config.get("ollama.model", "intel-code")
        self.timeout: int = config.get("ollama.timeout", 180)
        self.logger: Any = logger
        from src.api.error_handler import ErrorHandler
        from src.api.request_builder import RequestBuilder
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
        text = self._generate_with_retry(payload)
        if text and not text.startswith("Erreur"):
            return text
        if self.logger:
            self.logger.warning(f"Reponse vide ou erreur en mode {mode}. Retry fallback.")
        retry_payload = self.builder.build_retry(prompt, self.model)
        return self._generate_with_retry(retry_payload)

    def generate_streaming(self, prompt: str, mode: str = "default", on_token: Optional[Callable[[str], None]] = None) -> str:
        if not self._warmed:
            self.warmup()
        payload: Dict[str, Any] = self.builder.build(prompt, self.model, mode)
        payload["stream"] = True
        text = self._generate_with_retry(payload, on_token=on_token)
        if text and not text.startswith("Erreur"):
            return text
        if self.logger:
            self.logger.warning(f"Streaming failed, fallback to non-streaming.")
        payload["stream"] = False
        return self._generate_with_retry(payload)

    def _generate_with_retry(self, payload: Dict[str, Any], max_retries: int = 2, on_token: Optional[Callable[[str], None]] = None) -> str:
        last_error: str = ""
        for attempt in range(1, max_retries + 1):
            self._last_attempts = attempt
            try:
                text = self._generate_payload(payload, on_token=on_token)
                if text and not text.startswith("Erreur"):
                    return text
                last_error = "empty_response"
            except requests.exceptions.RequestException as e:
                last_error = str(e)
                self._last_error = last_error
                if attempt < max_retries:
                    time.sleep(0.5 * attempt)
                    continue
                return self.error_handler.handle(e, payload.get("prompt", ""))
        if self.logger:
            self.logger.warning(f"All {max_retries} attempts failed. Last error: {last_error}")
        self._last_error = last_error
        return f"Erreur: {last_error[:200]}"

    def _generate_payload(self, payload: Dict[str, Any], on_token: Optional[Callable[[str], None]] = None) -> str:
        is_stream = payload.get("stream", False)
        if is_stream:
            return self._stream_response(on_token)
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

    def _stream_response(self, on_token: Optional[Callable[[str], None]] = None) -> str:
        full_text: list = []
        start_time: float = time.time()
        try:
            with requests.post(self.host, json={"stream": True}, timeout=self.timeout, stream=True) as response:
                if response.status_code != 200:
                    self._last_error = f"HTTP {response.status_code}: {response.text[:200]}"
                    return f"Erreur {response.status_code}"
                total_duration_ns: int = 0
                eval_count: int = 0
                for line in response.iter_lines():
                    if not line:
                        continue
                    try:
                        chunk: Dict[str, Any] = __import__("json").loads(line.decode("utf-8"))
                    except __import__("json").JSONDecodeError:
                        continue
                    token: str = chunk.get("response", "")
                    if token:
                        full_text.append(token)
                        if on_token:
                            on_token(token)
                    eval_count = chunk.get("eval_count", 0)
                    total_duration_ns = chunk.get("total_duration", 0)
                    if chunk.get("done", False):
                        break
            self.error_handler.reset()
            self._last_eval_count = eval_count
            self._last_eval_seconds = chunk.get("eval_duration", 0) / 1_000_000_000
            self._last_total_seconds = total_duration_ns / 1_000_000_000
            text = "".join(full_text).strip()
            if not text:
                self._last_error = "empty_response"
            return text
        except requests.exceptions.RequestException as e:
            self._last_error = str(e)
            raise

    def warmup(self) -> None:
        with self._lock:
            if self._warmed:
                return
            payload: Dict[str, Any] = {
                "model": self.model,
                "prompt": "ping",
                "stream": False,
                "options": {"num_predict": 1, "num_ctx": 128, "temperature": 0.1},
            }
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
