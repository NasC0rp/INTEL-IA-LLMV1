import json
import os
import hashlib
from collections import OrderedDict

class CacheManager:
    def __init__(self, config):
        self.max_size = config.get("system.cache_size", 100)
        self.cache_file = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'cache', '.responses')
        self.cache = OrderedDict()
        self._load()

    def get(self, prompt):
        key = hashlib.md5(prompt.encode()).hexdigest()
        if key in self.cache:
            self.cache.move_to_end(key)
            return self.cache[key]
        return None

    def set(self, prompt, response):
        key = hashlib.md5(prompt.encode()).hexdigest()
        if key in self.cache:
            self.cache.move_to_end(key)
        else:
            if len(self.cache) >= self.max_size:
                self.cache.popitem(last=False)
        self.cache[key] = response
        self._save()

    def size(self):
        return len(self.cache)

    def clear(self):
        self.cache.clear()
        self._save()

    def _load(self):
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r') as f:
                    for k, v in json.load(f).items():
                        self.cache[k] = v
            except:
                pass

    def _save(self):
        os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
        with open(self.cache_file, 'w') as f:
            json.dump(dict(self.cache), f)