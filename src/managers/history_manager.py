import json
import os
from datetime import datetime
from typing import Any, List, Dict

class HistoryManager:
    def __init__(self, config: Any) -> None:
        self.max_history: int = config.get("system.max_history", 20)
        self.history_dir: str = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'history')
        os.makedirs(self.history_dir, exist_ok=True)

    def add(self, session_id: str, prompt: str, response: str) -> None:
        filepath: str = os.path.join(self.history_dir, f"{session_id}.json")
        os.makedirs(self.history_dir, exist_ok=True)
        history: List[Dict[str, str]] = []
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    history = json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        history.append({
            "timestamp": datetime.now().isoformat(),
            "prompt": prompt,
            "response": response[:500]
        })
        if len(history) > self.max_history:
            history = history[-self.max_history:]
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2, ensure_ascii=False)

    def get(self, session_id: str) -> List[Dict[str, str]]:
        filepath: str = os.path.join(self.history_dir, f"{session_id}.json")
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return []

    def clear(self, session_id: str) -> None:
        filepath: str = os.path.join(self.history_dir, f"{session_id}.json")
        if os.path.exists(filepath):
            os.remove(filepath)
