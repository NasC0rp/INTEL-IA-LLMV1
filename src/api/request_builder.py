import json
import os

class RequestBuilder:
    def __init__(self, config):
        self.config = config
        self.prompts = {}
        self._load_prompts()

    def _load_prompts(self):
        prompts_file = os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'prompts.json')
        if os.path.exists(prompts_file):
            try:
                with open(prompts_file, 'r') as f:
                    self.prompts = json.load(f)
            except:
                pass

    def build(self, prompt, model, mode="default"):
        tier = self.config.get_tier_config()
        num_ctx = tier.get("num_ctx", 2048)
        num_predict = tier.get("num_predict", 512)
        num_thread = tier.get("num_thread", 3)
        temperature = 0.8

        system_prompt = self.prompts.get(mode, self.prompts.get("default", ""))
        full_prompt = f"{system_prompt}\n\nQuestion: {prompt}\n\nRéponse:"

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