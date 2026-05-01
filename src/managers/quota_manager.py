import json
import os
import atexit
from datetime import datetime, timedelta
from typing import Dict, Any


class QuotaManager:
    def __init__(self, config: Any) -> None:
        self.quota_file: str = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'cache', '.quota')
        os.makedirs(os.path.dirname(self.quota_file), exist_ok=True)
        self.config: Any = config
        self._cache: Dict[str, Any] = {}
        self._dirty: bool = False
        atexit.register(self._save_if_dirty)

    def _get_tier_config(self) -> Dict[str, int]:
        tier: Dict[str, Any] = self.config.get_tier_config()
        return {
            "max_messages": tier.get("max_messages", 30),
            "window_hours": tier.get("window_hours", 12)
        }

    def _quota_key(self, session_id: str) -> str:
        return f"tier:{self.config.get_tier()}"

    def get_remaining(self, session_id: str) -> int:
        cfg: Dict[str, int] = self._get_tier_config()
        data: Dict[str, Any] = self._load()
        key: str = self._quota_key(session_id)
        if key not in data:
            data[key] = {"count": 0, "start": datetime.now().isoformat()}
            self._save_immediate(data)
            return cfg["max_messages"]
        entry: Dict[str, Any] = data[key]
        start: datetime = datetime.fromisoformat(entry["start"])
        if datetime.now() - start > timedelta(hours=cfg["window_hours"]):
            data[key] = {"count": 0, "start": datetime.now().isoformat()}
            self._save_immediate(data)
            return cfg["max_messages"]
        return max(0, cfg["max_messages"] - entry["count"])

    def use(self, session_id: str) -> None:
        cfg: Dict[str, int] = self._get_tier_config()
        data: Dict[str, Any] = self._load()
        key: str = self._quota_key(session_id)
        now: datetime = datetime.now()
        if key not in data:
            data[key] = {"count": 1, "start": now.isoformat()}
        else:
            entry: Dict[str, Any] = data[key]
            start: datetime = datetime.fromisoformat(entry["start"])
            if now - start > timedelta(hours=cfg["window_hours"]):
                data[key] = {"count": 1, "start": now.isoformat()}
            else:
                data[key]["count"] += 1
        self._save_immediate(data)

    def _load(self) -> Dict[str, Any]:
        if os.path.exists(self.quota_file):
            try:
                with open(self.quota_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError, KeyError, ValueError):
                pass
        return {}

    def _save_immediate(self, data: Dict[str, Any]) -> None:
        try:
            with open(self.quota_file, 'w', encoding='utf-8') as f:
                json.dump(data, f)
            self._dirty = False
        except IOError:
            pass

    def _save_if_dirty(self) -> None:
        if self._dirty:
            self._cache.clear()
            self._dirty = False
