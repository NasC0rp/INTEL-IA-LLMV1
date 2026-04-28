import uuid
from datetime import datetime

class SessionManager:
    def __init__(self, config):
        self.sessions = {}

    def create(self):
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = {
            "created_at": datetime.now().isoformat(),
            "active": True
        }
        return session_id

    def end(self, session_id):
        if session_id in self.sessions:
            self.sessions[session_id]["active"] = False
            self.sessions[session_id]["ended_at"] = datetime.now().isoformat()

    def is_active(self, session_id):
        return session_id in self.sessions and self.sessions[session_id].get("active", False)