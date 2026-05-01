import json
import os
from typing import Any, Dict


class RequestBuilder:
    def __init__(self, config: Any) -> None:
        self.config: Any = config
        self.prompts: Dict[str, str] = {}
        self._load_prompts()

    def _load_prompts(self) -> None:
        prompts_file = os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'prompts.json')
        if os.path.exists(prompts_file):
            try:
                with open(prompts_file, 'r', encoding='utf-8') as f:
                    self.prompts = json.load(f)
            except (json.JSONDecodeError, IOError):
                pass

    def build(self, prompt: str, model: str, mode: str = "default") -> Dict[str, Any]:
        tier = self.config.get_tier_config()
        num_ctx = tier.get("num_ctx", 4096)
        num_predict = tier.get("num_predict", 512)
        num_thread = tier.get("num_thread", 0)
        system_prompt = self.prompts.get(mode, self.prompts.get("default", ""))
        full_prompt = (
            f"{system_prompt}\n\n"
            f"Utilisateur: {prompt}\n"
            "Assistant:"
        )

        options: Dict[str, Any] = {
            "num_ctx": num_ctx,
            "temperature": 0.5,
            "top_p": 0.85,
            "repeat_penalty": 1.15,
            "top_k": 40,
            "num_predict": num_predict,
            "stop": ["\nUtilisateur:", "\nUser:"],
        }
        if num_thread and num_thread > 0:
            options["num_thread"] = num_thread

        return {
            "model": model,
            "prompt": full_prompt,
            "stream": False,
            "keep_alive": self.config.get("ollama.keep_alive", "15m"),
            "options": options,
        }

    def build_retry(self, prompt: str, model: str) -> Dict[str, Any]:
        return {
            "model": model,
            "prompt": f"Reponds en francais, clairement et brievement.\nQuestion: {prompt}\nReponse:",
            "stream": False,
            "keep_alive": self.config.get("ollama.keep_alive", "15m"),
            "options": {
                "num_ctx": 2048,
                "temperature": 0.5,
                "top_p": 0.85,
                "repeat_penalty": 1.1,
                "num_predict": 256,
            },
        }
