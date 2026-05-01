import requests

class ErrorHandler:
    def __init__(self) -> None:
        self.error_count: int = 0

    def handle(self, exception: requests.exceptions.RequestException, prompt: str) -> str:
        self.error_count += 1
        msg: str = str(exception)
        if "timeout" in msg.lower():
            return "Delai depasse. Reessayez."
        if "connection" in msg.lower():
            return "Ollama non lance. Faites: ollama serve"
        return f"Erreur API: {msg[:200]}"

    def reset(self) -> None:
        self.error_count = 0