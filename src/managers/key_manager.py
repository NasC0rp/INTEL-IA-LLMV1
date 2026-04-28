# src/managers/key_manager.py
import json
import os

class KeyManager:
    def __init__(self):
        keys_file = os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'keys.json')
        self.valid_keys = {"vip": [], "unlimited": []}
        if os.path.exists(keys_file):
            try:
                with open(keys_file, 'r') as f:
                    self.valid_keys = json.load(f)
            except:
                pass

    def validate_key(self, key):
        if key in self.valid_keys.get("unlimited", []):
            return "unlimited"
        if key in self.valid_keys.get("vip", []):
            return "vip"
        return None

    def add_key(self, tier, key):
        if tier in self.valid_keys:
            if key not in self.valid_keys[tier]:
                self.valid_keys[tier].append(key)
                self._save()
                return True
        return False

    def remove_key(self, key):
        for tier in self.valid_keys:
            if key in self.valid_keys[tier]:
                self.valid_keys[tier].remove(key)
                self._save()
                return True
        return False

    def list_keys(self, tier=None):
        if tier:
            return self.valid_keys.get(tier, [])
        return self.valid_keys

    def _save(self):
        keys_file = os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'keys.json')
        os.makedirs(os.path.dirname(keys_file), exist_ok=True)
        with open(keys_file, 'w') as f:
            json.dump(self.valid_keys, f, indent=2)