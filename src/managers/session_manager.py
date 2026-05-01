import uuid
import json
import os
from datetime import datetime
from typing import Dict, Any

class SessionManager:
    def __init__(self, config: Any) -> None:
        self.session_dir: str = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'sessions')
        os.makedirs(self.session_dir, exist_ok=True)
        self.sessions: Dict[str, Dict[str, Any]] = {}

    def create(self) -> str:
        session_id: str = str(uuid.uuid4())
        self.sessions[session_id] = {
            "created_at": datetime.now().isoformat(),
            "active": True
        }
        self._save(session_id)
        return session_id

    def end(self, session_id: str) -> None:
        if session_id in self.sessions:
            self.sessions[session_id]["active"] = False
            self.sessions[session_id]["ended_at"] = datetime.now().isoformat()
            self._save(session_id)

    def is_active(self, session_id: str) -> bool:
        return session_id in self.sessions and self.sessions[session_id].get("active", False)

    def _save(self, session_id: str) -> None:
        filepath: str = os.path.join(self.session_dir, f"{session_id}.json")
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.sessions[session_id], f, indent=2)
