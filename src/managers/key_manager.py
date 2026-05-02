import json
import logging
import os
from typing import Dict, List, Optional

_log = logging.getLogger(__name__)


class KeyManager:
    def __init__(self) -> None:
        config_dir: str = os.path.join(os.path.dirname(__file__), '..', '..', 'config')
        self.keys_file: str = os.path.join(config_dir, 'keys.local.json')
        fallback_file: str = os.path.join(config_dir, 'keys.json')
        self.valid_keys: Dict[str, set] = {"vip": set(), "unlimited": set()}
        keys_file: str = self.keys_file if os.path.exists(self.keys_file) else fallback_file
        if os.path.exists(keys_file):
            try:
                with open(keys_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for tier in data:
                        if tier in self.valid_keys:
                            self.valid_keys[tier] = set(data[tier])
            except (json.JSONDecodeError, IOError):
                pass

    def validate_key(self, key: str) -> Optional[str]:
        if key in self.valid_keys["unlimited"]:
            return "unlimited"
        if key in self.valid_keys["vip"]:
            return "vip"
        return None

    def add_key(self, tier: str, key: str) -> bool:
        if tier in self.valid_keys:
            if key not in self.valid_keys[tier]:
                self.valid_keys[tier].add(key)
                self._save()
                return True
        return False

    def remove_key(self, key: str) -> bool:
        for tier in self.valid_keys:
            if key in self.valid_keys[tier]:
                self.valid_keys[tier].discard(key)
                self._save()
                return True
        return False

    def list_keys(self, tier: Optional[str] = None) -> Dict[str, List[str]]:
        if tier:
            return {tier: list(self.valid_keys.get(tier, set()))}
        return {t: list(keys) for t, keys in self.valid_keys.items()}

    def _save(self) -> None:
        try:
            os.makedirs(os.path.dirname(self.keys_file), exist_ok=True)
            with open(self.keys_file, "w", encoding="utf-8") as f:
                json.dump({t: list(keys) for t, keys in self.valid_keys.items()}, f, indent=2)
        except OSError as e:
            _log.warning("Impossible d'enregistrer les cles: %s", e)
