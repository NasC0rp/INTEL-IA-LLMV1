import json
import os

class ConfigLoader:
    def __init__(self, config_path):
        self.config_path = config_path
        self.config_dir = os.path.dirname(config_path)
        self.data = {}
        self._limits = {}
        self._models = {}
        self._prompts = {}
        self._load_all()

    def _load_all(self):
        self._load_main()
        self._load_limits()
        self._load_models()
        self._load_prompts()

    def _load_main(self):
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Fichier introuvable: {self.config_path}")
        with open(self.config_path, 'r', encoding='utf-8') as f:
            self.data = json.load(f)

    def _load_limits(self):
        path = os.path.join(self.config_dir, "limits.json")
        if os.path.exists(path):
            with open(path, 'r') as f:
                self._limits = json.load(f)

    def _load_models(self):
        path = os.path.join(self.config_dir, "models.json")
        if os.path.exists(path):
            with open(path, 'r') as f:
                self._models = json.load(f)

    def _load_prompts(self):
        path = os.path.join(self.config_dir, "prompts.json")
        if os.path.exists(path):
            with open(path, 'r') as f:
                self._prompts = json.load(f)

    def get(self, key_path, default=None):
        keys = key_path.split('.')
        value = self.data
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value

    def get_tier(self):
        return self._limits.get("current_tier", "free")

    def get_tier_config(self):
        tier = self.get_tier()
        return self._limits.get("tiers", {}).get(tier, {})

    def get_prompt(self, mode="default"):
        return self._prompts.get(mode, self._prompts.get("default", ""))

    def validate(self):
        if "ollama" not in self.data:
            raise ValueError("Section 'ollama' manquante")
        if "host" not in self.data["ollama"]:
            raise ValueError("Clé 'ollama.host' manquante")
        if "model" not in self.data["ollama"]:
            raise ValueError("Clé 'ollama.model' manquante")
        return True
