import json
import os
from typing import Dict, Any, Optional

class ConfigLoader:
    def __init__(self, config_path: str) -> None:
        self.config_path: str = config_path
        self.config_dir: str = os.path.dirname(config_path)
        self.data: Dict[str, Any] = {}
        self._limits: Dict[str, Any] = {}
        self._models: Dict[str, Any] = {}
        self._prompts: Dict[str, str] = {}
        self._load_all()

    def _load_all(self) -> None:
        self._load_main()
        self._load_limits()
        self._load_models()
        self._load_prompts()

    def _load_main(self) -> None:
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Fichier introuvable: {self.config_path}")
        with open(self.config_path, 'r', encoding='utf-8') as f:
            self.data = json.load(f)

    def _load_limits(self) -> None:
        path: str = os.path.join(self.config_dir, "limits.json")
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    self._limits = json.load(f)
            except (json.JSONDecodeError, IOError):
                pass

    def _load_models(self) -> None:
        path: str = os.path.join(self.config_dir, "models.json")
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    self._models = json.load(f)
            except (json.JSONDecodeError, IOError):
                pass

    def _load_prompts(self) -> None:
        path: str = os.path.join(self.config_dir, "prompts.json")
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    self._prompts = json.load(f)
            except (json.JSONDecodeError, IOError):
                pass

    def get(self, key_path: str, default: Any = None) -> Any:
        keys: list = key_path.split('.')
        value: Any = self.data
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value

    def get_tier(self) -> str:
        return self._limits.get("current_tier", "free")

    def get_tier_config(self) -> Dict[str, Any]:
        tier: str = self.get_tier()
        return self._limits.get("tiers", {}).get(tier, {})

    def get_prompt(self, mode: str = "default") -> str:
        return self._prompts.get(mode, self._prompts.get("default", ""))

    def validate(self) -> bool:
        errors: list = []
        if "ollama" not in self.data:
            errors.append("Section 'ollama' manquante")
        else:
            if "host" not in self.data["ollama"]:
                errors.append("Clé 'ollama.host' manquante")
            if "model" not in self.data["ollama"]:
                errors.append("Clé 'ollama.model' manquante")
        if errors:
            raise ValueError("\n".join(errors))
        return True