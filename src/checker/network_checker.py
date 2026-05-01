import requests

class NetworkChecker:
    def __init__(self, config):
        self.model = config.get("ollama.model", "intel-code")
        self.base_url = config.get("ollama.host", "http://localhost:11434/api/generate").removesuffix("/api/generate").rstrip("/")

    def check(self):
        try:
            r = requests.get(f"{self.base_url}/api/tags", timeout=3)
            if r.ok:
                models = [m["name"] for m in r.json().get("models", [])]
                if self.model in models or f"{self.model}:latest" in models:
                    return True, f"Ollama: Actif - {self.model}"
                return False, f"Ollama: Actif - {self.model} absent"
            return False, "Ollama: Ne répond pas"
        except:
            return False, "Ollama: Non lancé"
