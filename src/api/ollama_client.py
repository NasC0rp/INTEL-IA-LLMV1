import json
import os
import time
import threading
from datetime import datetime
from typing import Any, Callable, Dict, Optional

import requests

from src.api.error_handler import ErrorHandler
from src.api.request_builder import RequestBuilder
from src.core.config_loader import ConfigLoader
from src.managers.logger import Logger


class OllamaClient:
    def __init__(self, config: ConfigLoader, logger: Optional[Logger] = None) -> None:
        self.base_url: str = config.get("ollama.host", "http://localhost:11434/api/generate").removesuffix("/api/generate").rstrip("/")
        self.chat_url: str = f"{self.base_url}/api/chat"
        self._config: ConfigLoader = config
        self.model: str = config.get_model_source(config.get_model_id())
        self.timeout: int = config.get("ollama.timeout", 180)
        self.logger: Optional[Logger] = logger
        self.builder: RequestBuilder = RequestBuilder(config)
        self.error_handler: ErrorHandler = ErrorHandler()
        self._warmed: bool = False
        self._lock: threading.Lock = threading.Lock()
        self._last_eval_count: int = 0
        self._last_eval_seconds: float = 0.0
        self._last_total_seconds: float = 0.0
        self._last_attempts: int = 0
        self._last_error: str = ""
        self._stats_file: str = os.path.join(
            os.path.dirname(__file__), "..", "..", "data", "cache", "token_stats.json"
        )
        self._load_persistent_stats()

    def set_model(self, model_id: str) -> None:
        self._config.set_model_id(model_id)
        self.model = self._config.get_model_source(self._config.get_model_id())
        # reset warmup so next request is fast & consistent
        self._warmed = False
        # reset stats cache if switching profile/model
        self._load_persistent_stats()

    def _load_persistent_stats(self) -> None:
        if not os.path.exists(self._stats_file):
            return
        try:
            with open(self._stats_file, "r", encoding="utf-8") as f:
                raw: Dict[str, Any] = json.load(f)
        except (json.JSONDecodeError, OSError):
            return
        if raw.get("model") != self.model:
            return
        self._last_eval_count = int(raw.get("eval_count") or 0)
        self._last_eval_seconds = float(raw.get("eval_seconds") or 0)
        self._last_total_seconds = float(raw.get("total_duration_seconds") or 0)

    def _persist_persistent_stats(self) -> None:
        try:
            os.makedirs(os.path.dirname(self._stats_file), exist_ok=True)
            payload: Dict[str, Any] = {
                "model": self.model,
                "eval_count": self._last_eval_count,
                "eval_seconds": self._last_eval_seconds,
                "total_duration_seconds": self._last_total_seconds,
                "saved_at": datetime.now().isoformat(timespec="seconds"),
            }
            with open(self._stats_file, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2)
        except OSError:
            pass

    def _apply_usage_from_ollama(self, chunk: Dict[str, Any]) -> None:
        self._last_eval_count = int(chunk.get("eval_count") or 0)
        self._last_eval_seconds = float(chunk.get("eval_duration") or 0) / 1_000_000_000
        self._last_total_seconds = float(chunk.get("total_duration") or 0) / 1_000_000_000
        self._persist_persistent_stats()

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
                user_prompt = payload.get("messages", [{"content": ""}])[-1].get("content", "")
                return self.error_handler.handle(e, user_prompt)
        if self.logger:
            self.logger.warning(f"All {max_retries} attempts failed. Last error: {last_error}")
        self._last_error = last_error
        return f"Erreur: {last_error[:200]}"

    def _generate_payload(self, payload: Dict[str, Any], on_token: Optional[Callable[[str], None]] = None) -> str:
        is_stream = payload.get("stream", False)
        if is_stream:
            return self._stream_response(payload, on_token)
        response = requests.post(self.chat_url, json=payload, timeout=self.timeout)
        if response.status_code != 200:
            self._last_error = f"HTTP {response.status_code}: {response.text[:200]}"
            if self.logger:
                self.logger.error(f"Ollama error: {self._last_error}")
            return f"Erreur {response.status_code}: {response.text[:200]}"
        data: Dict[str, Any] = response.json()
        self.error_handler.reset()
        self._apply_usage_from_ollama(data)
        text = data.get("message", {}).get("content", "").strip()
        if not text:
            self._last_error = "empty_response"
            if self.logger:
                self.logger.warning(f"Ollama empty response. Full reply: {str(data)[:300]}")
        return text

    def _stream_response(self, payload: Dict[str, Any], on_token: Optional[Callable[[str], None]] = None) -> str:
        full_text: list = []
        last_chunk: Dict[str, Any] = {}
        try:
            response = requests.post(self.chat_url, json=payload, timeout=self.timeout, stream=True)
            if response.status_code != 200:
                self._last_error = f"HTTP {response.status_code}: {response.text[:200]}"
                return f"Erreur {response.status_code}"
            for line in response.iter_lines():
                if not line:
                    continue
                try:
                    chunk: Dict[str, Any] = json.loads(line.decode("utf-8"))
                except json.JSONDecodeError:
                    continue
                last_chunk = chunk
                token: str = chunk.get("message", {}).get("content", "")
                if token:
                    full_text.append(token)
                    if on_token:
                        on_token(token)
                if chunk.get("done", False):
                    break
            response.close()
            self.error_handler.reset()
            if last_chunk:
                self._apply_usage_from_ollama(last_chunk)
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
                "messages": [{"role": "user", "content": "ping"}],
                "stream": False,
                "options": {"num_predict": 1, "num_ctx": 128, "temperature": 0.1},
            }
            try:
                requests.post(self.chat_url, json=payload, timeout=10)
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
