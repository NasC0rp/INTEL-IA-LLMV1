import json
import os
from typing import Dict, Any

class RequestBuilder:
    def __init__(self, config: Any) -> None:
        self.config: Any = config
        self.prompts: Dict[str, str] = {}
        self._load_prompts()

    def _load_prompts(self) -> None:
        prompts_file: str = os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'prompts.json')
        if os.path.exists(prompts_file):
            try:
                with open(prompts_file, 'r', encoding='utf-8') as f:
                    self.prompts = json.load(f)
            except (json.JSONDecodeError, IOError):
                pass

    def build(self, prompt: str, model: str, mode: str = "default") -> Dict[str, Any]:
        tier: Dict[str, Any] = self.config.get_tier_config()
        num_ctx: int = tier.get("num_ctx", 2048)
        num_predict: int = tier.get("num_predict", 512)
        num_thread: int = tier.get("num_thread", 3)
        temperature: float = 0.8

        system_prompt: str = self.prompts.get(mode, self.prompts.get("default", ""))
        full_prompt: str = f"{system_prompt}\n\nQuestion: {prompt}\n\nRéponse:"

        return {
            "model": model,
            "prompt": full_prompt,
            "stream": False,
            "options": {
                "num_ctx": num_ctx,
                "temperature": temperature,
                "num_predict": num_predict,
                "num_thread": num_thread
            }
        }