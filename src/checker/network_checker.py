import requests

class NetworkChecker:
    def __init__(self, config):
        self.model = config.get("ollama.model", "intel-code")

    def check(self):
        try:
            r = requests.get("http://localhost:11434/api/tags", timeout=3)
            if r.ok:
                models = [m["name"] for m in r.json().get("models", [])]
                if self.model in models or f"{self.model}:latest" in models:
                    return True, f"Ollama: Actif - {self.model}"
                return False, "Ollama: Actif - modele absent"
            return False, "Ollama: Ne repond pas"
        except:
            return False, "Ollama: Non lance"