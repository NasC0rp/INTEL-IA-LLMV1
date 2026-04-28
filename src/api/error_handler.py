import requests

class ErrorHandler:
    def __init__(self) -> None:
        self.error_count: int = 0

    def handle(self, exception: requests.exceptions.RequestException, prompt: str) -> str:
        self.error_count += 1
        msg: str = str(exception)
        if "500" in msg:
            return "Erreur serveur Ollama. Réessayez."
        if "404" in msg:
            return "Modèle introuvable. Lancez: ollama pull"
        if "timeout" in msg.lower():
            return "Délai dépassé. Réessayez."
        if "connection" in msg.lower():
            return "Ollama non lancé. Faites: ollama serve"
        return f"Erreur: {msg[:100]}"

    def reset(self) -> None:
        self.error_count = 0