class ErrorHandler:
    def __init__(self):
        self.error_count = 0

    def handle(self, exception, prompt):
        self.error_count += 1
        msg = str(exception)
        if "500" in msg:
            return "Erreur serveur Ollama. Réessayez."
        elif "404" in msg:
            return "Modèle introuvable. Lancez: ollama pull"
        elif "timeout" in msg.lower():
            return "Délai dépassé. Réessayez."
        elif "connection" in msg.lower():
            return "Ollama non lancé. Faites: ollama serve"
        return f"Erreur: {msg[:100]}"

    def reset(self):
        self.error_count = 0