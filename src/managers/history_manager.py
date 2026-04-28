import json
import os
from datetime import datetime

class HistoryManager:
    def __init__(self, config):
        self.max_history = config.get("system.max_history", 20)
        self.history_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'history')

    def add(self, session_id, prompt, response):
        filepath = os.path.join(self.history_dir, f"{session_id}.json")
        os.makedirs(self.history_dir, exist_ok=True)
        history = []
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r') as f:
                    history = json.load(f)
            except:
                pass
        history.append({
            "timestamp": datetime.now().isoformat(),
            "prompt": prompt,
            "response": response[:500]
        })
        if len(history) > self.max_history:
            history = history[-self.max_history:]
        with open(filepath, 'w') as f:
            json.dump(history, f, indent=2, ensure_ascii=False)

    def get(self, session_id):
        filepath = os.path.join(self.history_dir, f"{session_id}.json")
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r') as f:
                    return json.load(f)
            except:
                pass
        return []

    def clear(self, session_id):
        filepath = os.path.join(self.history_dir, f"{session_id}.json")
        if os.path.exists(filepath):
            os.remove(filepath)