import json
import os
from typing import Dict, Any

class ConfigLoader:
    def __init__(self, config_path: str) -> None:
        self.config_path = config_path
        self.config_dir = os.path.dirname(config_path)
        self.data = {}
        self._limits = {}
        self._prompts = {}
        self._load()

    def _load(self) -> None:
        with open(self.config_path, 'r', encoding='utf-8') as f:
            self.data = json.load(f)
        limits_path = os.path.join(self.config_dir, "limits.json")
        if os.path.exists(limits_path):
            with open(limits_path, 'r', encoding='utf-8') as f:
                self._limits = json.load(f)
        prompts_path = os.path.join(self.config_dir, "prompts.json")
        if os.path.exists(prompts_path):
            with open(prompts_path, 'r', encoding='utf-8') as f:
                self._prompts = json.load(f)

    def get(self, key_path: str, default: Any = None) -> Any:
        keys = key_path.split('.')
        value = self.data
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value

    def get_tier_config(self) -> Dict[str, Any]:
        tier = self._limits.get("current_tier", "free")
        return self._limits.get("tiers", {}).get(tier, {})

    def get_prompt(self, mode: str = "default") -> str:
        return self._prompts.get(mode, "")

    def validate(self) -> bool:
        return True