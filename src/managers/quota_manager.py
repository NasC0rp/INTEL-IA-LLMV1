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

    def _get_tier_config(self) -> Dict[str, Any]:
        tier: Dict[str, Any] = self.config.get_tier_config()
        max_ttok = tier.get("max_tokens_window")
        return {
            "max_messages": int(tier.get("max_messages", 30)),
            "window_hours": int(tier.get("window_hours", 12)),
            "max_tokens_window": int(max_ttok) if isinstance(max_ttok, int) and max_ttok > 0 else None,
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
        """Messages restants. La fenetre ne demarre qu'au premier message compte (use)."""
        cfg: Dict[str, Any] = self._get_tier_config()
        data: Dict[str, Any] = self._load()
        key: str = self._quota_key(session_id)
        now: datetime = datetime.now()

        if key not in data:
            return int(cfg["max_messages"])

        entry: Dict[str, Any] = data[key]
        start: datetime = datetime.fromisoformat(entry["start"])
        if now - start > timedelta(hours=int(cfg["window_hours"])):
            del data[key]
            self._save_immediate(data)
            return int(cfg["max_messages"])

        return max(0, int(cfg["max_messages"]) - int(entry["count"]))

    def get_remaining_tokens(self, session_id: str) -> Optional[int]:
        """
        Tokens sortie generateur cumules restants dans la meme fenetre (None = quota tokens desactive pour ce tier).
        """
        cfg: Dict[str, Any] = self._get_tier_config()
        cap: Optional[int] = cfg["max_tokens_window"]
        if cap is None:
            return None

        data: Dict[str, Any] = self._load()
        key: str = self._quota_key(session_id)
        now: datetime = datetime.now()

        if key not in data:
            return cap

        entry: Dict[str, Any] = data[key]
        start: datetime = datetime.fromisoformat(entry["start"])
        if now - start > timedelta(hours=int(cfg["window_hours"])):
            return cap

        used: int = int(entry.get("tokens", 0))
        return max(0, cap - used)

    def get_tokens_used_this_window(self, session_id: str) -> int:
        cfg: Dict[str, Any] = self._get_tier_config()
        if cfg["max_tokens_window"] is None:
            return 0
        data: Dict[str, Any] = self._load()
        key: str = self._quota_key(session_id)
        now: datetime = datetime.now()
        if key not in data:
            return 0
        entry = data[key]
        start: datetime = datetime.fromisoformat(entry["start"])
        if now - start > timedelta(hours=int(cfg["window_hours"])):
            return 0
        return int(entry.get("tokens", 0))

    def get_max_tokens_window(self, session_id: str) -> Optional[int]:
        return self._get_tier_config()["max_tokens_window"]

    def get_wait_until_renewal(self, session_id: str) -> Optional[Tuple[datetime, float, BlockReason]]:
        """
        Si blocage dans la fenetre (messages OU tokens selon tier), renvoie la fin de fenetre,
        les secondes restantes, et la raison: 'messages', 'tokens', ou 'both'.
        """
        cfg: Dict[str, Any] = self._get_tier_config()
        data: Dict[str, Any] = self._load()
        key: str = self._quota_key(session_id)
        now: datetime = datetime.now()

        if key not in data:
            return None

        entry: Dict[str, Any] = data[key]
        start: datetime = datetime.fromisoformat(entry["start"])
        if now - start > timedelta(hours=int(cfg["window_hours"])):
            return None

        remaining_msgs: int = int(cfg["max_messages"]) - int(entry["count"])
        cap_tokens: Optional[int] = cfg["max_tokens_window"]
        used_tokens: int = int(entry.get("tokens", 0))
        remaining_tok: Optional[int] = None if cap_tokens is None else max(0, cap_tokens - used_tokens)

        bad_msg: bool = remaining_msgs <= 0
        bad_tok: bool = cap_tokens is not None and remaining_tok is not None and remaining_tok <= 0

        if not bad_msg and not bad_tok:
            return None

        if bad_msg and bad_tok:
            reason: str = "both"
        elif bad_tok:
            reason = "tokens"
        else:
            reason = "messages"

        end: datetime = self._window_end(entry["start"], int(cfg["window_hours"]))
        seconds: float = max(0.0, (end - now).total_seconds())
        return (end, seconds, reason)

    @staticmethod
    def format_wait_message(end: datetime, seconds: float, reason: str = "messages") -> str:
        total_m: int = int(seconds // 60)
        h: int = total_m // 60
        m: int = total_m % 60
        end_str: str = end.strftime("%H:%M")
        if h > 0:
            duree: str = f"{h} h {m} min"
        else:
            duree = f"{m} min"

        if reason == "tokens":
            return (
                f"Vous avez atteint votre quota de tokens (generation Ollama) pour cette periode. "
                f"Attendez encore environ {duree} (renouvellement vers {end_str})."
            )
        if reason == "both":
            return (
                f"Vous avez atteint la limite de messages ET le quota de tokens pour cette periode. "
                f"Attendez encore environ {duree} (renouvellement vers {end_str})."
            )
        return (
            f"Vous avez atteint votre limite de messages pour cette periode. "
            f"Attendez encore environ {duree} (renouvellement vers {end_str})."
        )

    def use(self, session_id: str, tokens_output: int = 0) -> None:
        """Compte un message utilise + tokens generateur reels (eval_count). Cache = 0 tokens."""
        cfg: Dict[str, Any] = self._get_tier_config()
        data: Dict[str, Any] = self._load()
        key: str = self._quota_key(session_id)
        now: datetime = datetime.now()
        to_add: int = max(0, int(tokens_output))

        if key not in data:
            data[key] = {"count": 1, "tokens": to_add, "start": now.isoformat()}
            self._save_immediate(data)
            return

        entry: Dict[str, Any] = data[key]
        start: datetime = datetime.fromisoformat(entry["start"])
        if now - start > timedelta(hours=int(cfg["window_hours"])):
            data[key] = {"count": 1, "tokens": to_add, "start": now.isoformat()}
            self._save_immediate(data)
            return

        entry["count"] = int(entry["count"]) + 1
        entry["tokens"] = int(entry.get("tokens", 0)) + to_add
        data[key] = entry
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
