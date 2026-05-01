import json
import os
import atexit
from datetime import datetime
from typing import Any, List, Dict


class HistoryManager:
    def __init__(self, config: Any) -> None:
        self.max_history: int = config.get("system.max_history", 20)
        self.history_dir: str = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'history')
        os.makedirs(self.history_dir, exist_ok=True)
        self._cache: Dict[str, List[Dict[str, str]]] = {}
        self._dirty: Dict[str, bool] = {}
        atexit.register(self.flush_all)

    def add(self, session_id: str, prompt: str, response: str) -> None:
        if session_id not in self._cache:
            self._cache[session_id] = self._load_from_disk(session_id)
        self._cache[session_id].append({
            "timestamp": datetime.now().isoformat(),
            "prompt": prompt,
            "response": response[:500]
        })
        if len(self._cache[session_id]) > self.max_history:
            self._cache[session_id] = self._cache[session_id][-self.max_history:]
        self._dirty[session_id] = True

    def get(self, session_id: str) -> List[Dict[str, str]]:
        if session_id in self._cache:
            return self._cache[session_id]
        return self._load_from_disk(session_id)

    def clear(self, session_id: str) -> None:
        filepath: str = os.path.join(self.history_dir, f"{session_id}.json")
        if os.path.exists(filepath):
            os.remove(filepath)
        self._cache.pop(session_id, None)
        self._dirty.pop(session_id, None)

    def flush_all(self) -> None:
        for session_id in list(self._dirty.keys()):
            if self._dirty[session_id] and session_id in self._cache:
                self._save_to_disk(session_id, self._cache[session_id])
                self._dirty[session_id] = False

    def _load_from_disk(self, session_id: str) -> List[Dict[str, str]]:
        filepath: str = os.path.join(self.history_dir, f"{session_id}.json")
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return []

    def _save_to_disk(self, session_id: str, history: List[Dict[str, str]]) -> None:
        filepath: str = os.path.join(self.history_dir, f"{session_id}.json")
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(history, f, indent=2, ensure_ascii=False)
        except IOError:
            pass
