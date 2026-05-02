import json
import logging
import os
from urllib.parse import urlparse
from typing import Any, Dict

_log = logging.getLogger(__name__)


class ConfigLoader:
    def __init__(self, config_path: str) -> None:
        self.config_path: str = config_path
        self.config_dir: str = os.path.dirname(config_path)
        self.state_path: str = os.path.join(self.config_dir, "..", "data", "cache", "state.json")
        self.data: Dict[str, Any] = {}
        self._limits: Dict[str, Any] = {}
        self._models: Dict[str, Any] = {}
        self._prompts: Dict[str, str] = {}
        self._state: Dict[str, Any] = {}
        self._load_all()

    def _load_all(self) -> None:
        self._load_main()
        self._load_limits()
        self._load_models()
        self._load_prompts()
        self._load_state()

    def _load_main(self) -> None:
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Fichier introuvable: {self.config_path}")
        with open(self.config_path, "r", encoding="utf-8") as f:
            self.data = json.load(f)

    def _load_limits(self) -> None:
        path: str = os.path.join(self.config_dir, "limits.json")
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    self._limits = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                _log.warning("Impossible de lire %s: %s", path, e)

    def _load_models(self) -> None:
        path: str = os.path.join(self.config_dir, "models.json")
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    self._models = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                _log.warning("Impossible de lire %s: %s", path, e)

    def _load_prompts(self) -> None:
        path: str = os.path.join(self.config_dir, "prompts.json")
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    self._prompts = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                _log.warning("Impossible de lire %s: %s", path, e)

    def _load_state(self) -> None:
        if os.path.exists(self.state_path):
            try:
                with open(self.state_path, "r", encoding="utf-8") as f:
                    self._state = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                _log.warning("Impossible de lire %s: %s", self.state_path, e)
                self._state = {}

    def _save_state(self) -> None:
        os.makedirs(os.path.dirname(self.state_path), exist_ok=True)
        with open(self.state_path, "w", encoding="utf-8") as f:
            json.dump(self._state, f, indent=2)

    def get(self, key_path: str, default: Any = None) -> Any:
        keys: list = key_path.split(".")
        value: Any = self.data
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value

    def get_tier(self) -> str:
        return self._state.get("current_tier") or self._limits.get("current_tier", "free")

    def set_tier(self, tier: str) -> None:
        if tier not in self._limits.get("tiers", {}):
            raise ValueError(f"Tier inconnu: {tier}")
        self._state["current_tier"] = tier
        self._save_state()

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
            host = self.data["ollama"].get("host")
            model = self.data["ollama"].get("model")
            timeout = self.data["ollama"].get("timeout")
            if not host:
                errors.append("Cle 'ollama.host' manquante")
            elif urlparse(host).scheme not in {"http", "https"}:
                errors.append("Cle 'ollama.host' doit etre une URL http(s)")
            if not model:
                errors.append("Cle 'ollama.model' manquante")
            if timeout is not None and (not isinstance(timeout, int) or timeout <= 0):
                errors.append("Cle 'ollama.timeout' doit etre un entier positif")

        max_history = self.get("system.max_history")
        if max_history is not None and (not isinstance(max_history, int) or max_history <= 0):
            errors.append("Cle 'system.max_history' doit etre un entier positif")

        tiers = self._limits.get("tiers", {})
        if not isinstance(tiers, dict) or not tiers:
            errors.append("Section 'tiers' manquante dans config/limits.json")
        for tier_name, tier_config in tiers.items():
            for key in ("max_messages", "window_hours", "num_ctx", "num_predict"):
                value = tier_config.get(key)
                if not isinstance(value, int) or value <= 0:
                    errors.append(f"Tier '{tier_name}': '{key}' doit etre un entier positif")
            mtw = tier_config.get("max_tokens_window")
            if mtw is not None and (not isinstance(mtw, int) or mtw <= 0):
                errors.append(
                    f"Tier '{tier_name}': 'max_tokens_window' doit etre un entier positif ou omis"
                )

        if errors:
            raise ValueError("\n".join(errors))
        return True
