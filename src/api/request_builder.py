from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, List

from src.core.config_loader import ConfigLoader

_log = logging.getLogger(__name__)


class RequestBuilder:
    def __init__(self, config: ConfigLoader) -> None:
        self.config: ConfigLoader = config
        self.prompts: Dict[str, str] = {}
        self._load_prompts()

    def _load_prompts(self) -> None:
        prompts_file = os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'prompts.json')
        if os.path.exists(prompts_file):
            try:
                with open(prompts_file, 'r', encoding='utf-8') as f:
                    self.prompts = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                _log.warning("Impossible de lire prompts.json: %s", e)

    def _build_system(self, mode: str) -> str:
        base = self.prompts.get(mode, self.prompts.get("default", ""))
        return f"Reponds uniquement en francais. {base}"

    def build(self, prompt: str, model: str, mode: str = "default") -> Dict[str, Any]:
        tier = self.config.get_tier_config()
        num_ctx = tier.get("num_ctx", 2048)
        num_predict_base = tier.get("num_predict", 256)
        num_thread = tier.get("num_thread", 0)
        system_prompt = self._build_system(mode)

        model_opts = self.config.get_model_options()
        scale = model_opts.get("num_predict_scale", 1.0)
        try:
            scale_f = float(scale)
        except Exception:
            scale_f = 1.0
        num_predict = int(max(1, round(int(num_predict_base) * max(0.1, min(2.0, scale_f)))))

        messages: List[Dict[str, str]] = [
            {"role": "user", "content": f"{system_prompt}\n\n{prompt}"},
        ]

        options: Dict[str, Any] = {
            "num_ctx": num_ctx,
            "temperature": model_opts.get("temperature", 0.5),
            "top_p": model_opts.get("top_p", 0.85),
            "repeat_penalty": model_opts.get("repeat_penalty", 1.15),
            "top_k": model_opts.get("top_k", 40),
            "num_predict": num_predict,
        }
        if num_thread and num_thread > 0:
            options["num_thread"] = num_thread

        return {
            "model": model,
            "messages": messages,
            "stream": False,
            "keep_alive": self.config.get("ollama.keep_alive", "15m"),
            "options": options,
        }

    def build_retry(self, prompt: str, model: str) -> Dict[str, Any]:
        system_text = self._build_system("default")
        return {
            "model": model,
            "messages": [
                {"role": "user", "content": f"{system_text}\n\nExplique comment fonctionne ce concept en detail technique: {prompt}"},
            ],
            "stream": False,
            "keep_alive": self.config.get("ollama.keep_alive", "15m"),
            "options": {
                "num_ctx": 2048,
                "temperature": 0.3,
                "top_p": 0.9,
                "repeat_penalty": 1.0,
                "num_predict": 256,
            },
        }
