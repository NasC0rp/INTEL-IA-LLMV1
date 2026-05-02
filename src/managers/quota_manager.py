import json
import os
import atexit
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Tuple


class QuotaManager:
    def __init__(self, config: Any) -> None:
        self.quota_file: str = os.path.join(os.path.dirname(__file__), "..", "..", "data", "cache", ".quota")
        os.makedirs(os.path.dirname(self.quota_file), exist_ok=True)
        self.config: Any = config
        self._cache: Dict[str, Any] = {}
        self._dirty: bool = False
        atexit.register(self._save_if_dirty)

    def _get_tier_config(self) -> Dict[str, int]:
        tier: Dict[str, Any] = self.config.get_tier_config()
        return {
            "max_messages": tier.get("max_messages", 30),
            "window_hours": tier.get("window_hours", 12),
        }

    def _quota_key(self, session_id: str) -> str:
        return f"tier:{self.config.get_tier()}"

    def _load(self) -> Dict[str, Any]:
        if os.path.exists(self.quota_file):
            try:
                with open(self.quota_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError, KeyError, ValueError):
                pass
        return {}

    def _window_end(self, start_iso: str, window_hours: int) -> datetime:
        start = datetime.fromisoformat(start_iso)
        return start + timedelta(hours=window_hours)

    def get_remaining(self, session_id: str) -> int:
        """Messages restants. La fenetre de quota ne demarre qu'au premier message compte (use)."""
        cfg: Dict[str, int] = self._get_tier_config()
        data: Dict[str, Any] = self._load()
        key: str = self._quota_key(session_id)
        now: datetime = datetime.now()

        if key not in data:
            return cfg["max_messages"]

        entry: Dict[str, Any] = data[key]
        start: datetime = datetime.fromisoformat(entry["start"])
        if now - start > timedelta(hours=cfg["window_hours"]):
            del data[key]
            self._save_immediate(data)
            return cfg["max_messages"]

        return max(0, cfg["max_messages"] - entry["count"])

    def get_wait_until_renewal(self, session_id: str) -> Optional[Tuple[datetime, float]]:
        """
        Si le quota est epuise (0 messages restants) dans la fenetre courante,
        retourne (instant de renouvellement, secondes restantes). Sinon None.
        """
        cfg: Dict[str, int] = self._get_tier_config()
        data: Dict[str, Any] = self._load()
        key: str = self._quota_key(session_id)
        now: datetime = datetime.now()

        if key not in data:
            return None

        entry: Dict[str, Any] = data[key]
        start: datetime = datetime.fromisoformat(entry["start"])
        if now - start > timedelta(hours=cfg["window_hours"]):
            return None

        remaining_msgs: int = cfg["max_messages"] - entry["count"]
        if remaining_msgs > 0:
            return None

        end: datetime = self._window_end(entry["start"], cfg["window_hours"])
        seconds: float = max(0.0, (end - now).total_seconds())
        return (end, seconds)

    @staticmethod
    def format_wait_message(end: datetime, seconds: float) -> str:
        total_m: int = int(seconds // 60)
        h: int = total_m // 60
        m: int = total_m % 60
        end_str: str = end.strftime("%H:%M")
        if h > 0:
            duree: str = f"{h} h {m} min"
        else:
            duree: str = f"{m} min"
        return (
            f"Vous avez atteint votre limite de messages pour cette periode. "
            f"Attendez encore environ {duree} (renouvellement vers {end_str})."
        )

    def use(self, session_id: str) -> None:
        cfg: Dict[str, int] = self._get_tier_config()
        data: Dict[str, Any] = self._load()
        key: str = self._quota_key(session_id)
        now: datetime = datetime.now()

        if key not in data:
            data[key] = {"count": 1, "start": now.isoformat()}
            self._save_immediate(data)
            return

        entry: Dict[str, Any] = data[key]
        start: datetime = datetime.fromisoformat(entry["start"])
        if now - start > timedelta(hours=cfg["window_hours"]):
            data[key] = {"count": 1, "start": now.isoformat()}
        else:
            data[key]["count"] += 1
        self._save_immediate(data)

    def _save_immediate(self, data: Dict[str, Any]) -> None:
        try:
            with open(self.quota_file, "w", encoding="utf-8") as f:
                json.dump(data, f)
            self._dirty = False
        except IOError:
            pass

    def _save_if_dirty(self) -> None:
        if self._dirty:
            self._cache.clear()
            self._dirty = False
