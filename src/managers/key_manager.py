import json
import os
from typing import Dict, List, Optional

class KeyManager:
    def __init__(self) -> None:
        keys_file: str = os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'keys.json')
        self.valid_keys: Dict[str, List[str]] = {"vip": [], "unlimited": []}
        if os.path.exists(keys_file):
            try:
                with open(keys_file, 'r', encoding='utf-8') as f:
                    self.valid_keys = json.load(f)
            except (json.JSONDecodeError, IOError):
                pass

    def validate_key(self, key: str) -> Optional[str]:
        if key in self.valid_keys.get("unlimited", []):
            return "unlimited"
        if key in self.valid_keys.get("vip", []):
            return "vip"
        return None

    def add_key(self, tier: str, key: str) -> bool:
        if tier in self.valid_keys:
            if key not in self.valid_keys[tier]:
                self.valid_keys[tier].append(key)
                self._save()
                return True
        return False

    def remove_key(self, key: str) -> bool:
        for tier in self.valid_keys:
            if key in self.valid_keys[tier]:
                self.valid_keys[tier].remove(key)
                self._save()
                return True
        return False

    def list_keys(self, tier: Optional[str] = None) -> Dict[str, List[str]]:
        if tier:
            return {tier: self.valid_keys.get(tier, [])}
        return self.valid_keys

    def _save(self) -> None:
        keys_file: str = os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'keys.json')
        os.makedirs(os.path.dirname(keys_file), exist_ok=True)
        with open(keys_file, 'w', encoding='utf-8') as f:
            json.dump(self.valid_keys, f, indent=2)