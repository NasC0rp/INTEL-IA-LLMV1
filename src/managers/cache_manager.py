import json
import os
import hashlib
from collections import OrderedDict
from typing import Optional, Any

class CacheManager:
    def __init__(self, config: Any) -> None:
        self.max_size: int = config.get("system.cache_size", 100)
        self.cache_file: str = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'cache', '.responses')
        self.cache: OrderedDict = OrderedDict()
        self._load()

    def get(self, prompt: str) -> Optional[str]:
        key: str = hashlib.md5(prompt.encode()).hexdigest()
        if key in self.cache:
            self.cache.move_to_end(key)
            return self.cache[key]
        return None

    def set(self, prompt: str, response: str) -> None:
        key: str = hashlib.md5(prompt.encode()).hexdigest()
        if key in self.cache:
            self.cache.move_to_end(key)
        else:
            if len(self.cache) >= self.max_size:
                self.cache.popitem(last=False)
        self.cache[key] = response
        self._save()

    def size(self) -> int:
        return len(self.cache)

    def clear(self) -> None:
        self.cache.clear()
        self._save()

    def _load(self) -> None:
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    for k, v in json.load(f).items():
                        self.cache[k] = v
            except (json.JSONDecodeError, IOError):
                pass

    def _save(self) -> None:
        os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
        with open(self.cache_file, 'w', encoding='utf-8') as f:
            json.dump(dict(self.cache), f)