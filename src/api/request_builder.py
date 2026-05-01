import json
import os
from typing import Dict, Any

class RequestBuilder:
    def __init__(self, config: Any) -> None:
        self.config: Any = config
        self.prompts: Dict[str, str] = {}
        self._load_prompts()

    def _load_prompts(self) -> None:
        p = os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'prompts.json')
        if os.path.exists(p):
            try:
                with open(p, 'r', encoding='utf-8') as f:
                    self.prompts = json.load(f)
            except:
                pass

    def build(self, prompt: str, model: str, mode: str = "default") -> Dict[str, Any]:
        tier = self.config.get_tier_config()
        num_ctx = tier.get("num_ctx", 2048)
        num_predict = tier.get("num_predict", 512)
        num_thread = tier.get("num_thread", 3)
        system_prompt = self.prompts.get(mode, self.prompts.get("default", ""))
        full_prompt = f"{system_prompt}\n\nQuestion: {prompt}\n\nReponse:"
        return {
            "model": model,
            "prompt": full_prompt,
            "stream": False,
            "options": {
                "num_ctx": num_ctx,
                "temperature": 0.8,
                "num_predict": num_predict,
                "num_thread": num_thread
            }
        }