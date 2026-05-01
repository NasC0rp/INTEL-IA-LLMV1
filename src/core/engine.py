import os
import sys
import time
from typing import Any

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.api.ollama_client import OllamaClient
from src.checker.system_checker import SystemChecker
from src.core.updater import Updater
from src.managers.cache_manager import CacheManager
from src.managers.history_manager import HistoryManager
from src.managers.key_manager import KeyManager
from src.managers.memory_manager import MemoryManager
from src.managers.quota_manager import QuotaManager
from src.managers.session_manager import SessionManager
from src.utils.colors import Colors, clear_screen, print_colored
from src.utils.formatter import Formatter

BANNER = r"""
  ___       _       _    ____ ___  ____  _____
 |_ _|_ __ | |_ ___| |  / ___/ _ \|  _ \| ____|
  | || '_ \| __/ _ \ | | |  | | | | | | |  _|
  | || | | | ||  __/ | | |__| |_| | |_| | |___
 |___|_| |_|\__\___|_|  \____\___/|____/|_____|
"""

COMMANDS = {
    "exit": "Quitter",
    "clear": "Effacer l'ecran",
    "quota": "Messages restants",
    "cache": "Taille du cache",
    "history": "Historique",
    "mode": "Changer de mode",
    "models": "Modeles disponibles",
    "key": "Activer une cle VIP/Unlimited",
    "tier": "Voir le tier actuel",
    "tokens": "Tokens restants",
    "help": "Aide",
}


class IntelGPTEngine:
    def __init__(self, config: Any, logger: Any) -> None:
        self.config: Any = config
        self.logger: Any = logger
        self.ollama: OllamaClient = OllamaClient(config)
        self.quota: QuotaManager = QuotaManager(config)
        self.cache: CacheManager = CacheManager(config)
        self.history: HistoryManager = HistoryManager(config)
        self.session: SessionManager = SessionManager(config)
        self.memory: MemoryManager = MemoryManager(config)
        self.checker: SystemChecker = SystemChecker(config)
        self.updater: Updater = Updater(config)
        self.key_manager: KeyManager = KeyManager()
        self.formatter: Formatter = Formatter()
        self.running: bool = False
        self.current_mode: str = "default"
        self.current_tier: str = self.config.get_tier()
        self.session_id: str = ""
        self._update_tier_config()

    def _update_tier_config(self) -> None:
        self.config.set_tier(self.current_tier)

    def run(self) -> None:
        self.running = True
        self.session_id = self.session.create()
        clear_screen()
        self._show_banner()
        self._quick_check()
        self._check_updates()
        self.ollama.warmup()
        self._chat_loop()

    def _show_banner(self) -> None:
        print_colored(BANNER, Colors.RED)
        print_colored("               Intel CODE CX1 | NasCorp 2026", Colors.YELLOW)
        tier_color: str = Colors.GREEN if self.current_tier == "free" else Colors.MAGENTA if self.current_tier == "vip" else Colors.CYAN
        print_colored(f"               Tier: {self.current_tier.upper()}", tier_color)
        remaining: int = self.quota.get_remaining(self.session_id)
        print_colored(f"               Messages: {remaining}", Colors.GRAY)
        print_colored("               'help' pour les commandes\n", Colors.GRAY)

    def _quick_check(self) -> None:
        ok, results = self.checker.check_all()
        print_colored("=== VERIFICATION ===", Colors.CYAN)
        for status, msg in results:
            tag = "[OK]" if status else "[FAIL]"
            color = Colors.GREEN if status else Colors.RED
            print_colored(f"  {tag} {msg}", color)
        if not ok:
            print_colored("Attention: certains checks ont echoue.", Colors.YELLOW)
        print()
        self.memory.optimize()

    def _check_updates(self) -> None:
        self.updater.check()
        if self.updater.update_available:
            print_colored(f"Nouvelle version disponible: v{self.updater.latest_version}", Colors.YELLOW)
            print_colored(f"   -> {self.updater.get_update_command()}\n", Colors.GRAY)

    def _chat_loop(self) -> None:
        while self.running:
            try:
                remaining: int = self.quota.get_remaining(self.session_id)
                if remaining <= 0:
                    tier_config = self.config.get_tier_config()
                    hours = tier_config.get("window_hours", 12)
                    print_colored(f"\n[QUOTA] 0 messages restants. Renouvellement dans {hours}h.\n", Colors.YELLOW)
                    input("Appuyez sur Entree pour verifier...")
                    continue

                prompt: str = input(f"{Colors.RED}Intel CODE [{self.current_tier}] > {Colors.NC}")

                if prompt.lower() in COMMANDS:
                    self._handle_command(prompt.lower())
                    continue

                if not prompt.strip():
                    continue

                cached: str | None = self.cache.get(prompt)
                if cached:
                    print_colored(f"\n{cached}\n", Colors.WHITE)
                    self.quota.use(self.session_id)
                    continue

                print_colored("\nReflexion...", Colors.GRAY)
                start_time: float = time.time()
                response: str = self.ollama.generate(prompt, self.current_mode)
                elapsed: float = time.time() - start_time

                if response and not response.startswith("Erreur"):
                    formatted: str = self.formatter.format(response)
                    print_colored(f"\n{formatted}\n", Colors.WHITE)
                    self.cache.set(prompt, response)
                    self.history.add(self.session_id, prompt, response)
                    self.quota.use(self.session_id)
                    remaining = self.quota.get_remaining(self.session_id)
                    print_colored(f"[{elapsed:.1f}s] [messages:{remaining}] [mode:{self.current_mode}] [tier:{self.current_tier}]", Colors.GRAY)
                else:
                    print_colored(f"\n{response or '[ERREUR] Verifiez qu Ollama est lance.'}\n", Colors.RED)

            except KeyboardInterrupt:
                self.running = False
            except Exception as e:
                self.logger.error(f"Erreur: {e}")
                print_colored(f"\n[ERREUR] {e}\n", Colors.RED)

        self._shutdown()

    def _activate_key(self) -> None:
        print_colored("\n=== ACTIVATION CLE ===", Colors.CYAN)
        print_colored("Formats: INT3LK3Y_V1P-XXXX ou INT3LK3Y_ULT1M3-XXXX", Colors.GRAY)
        key: str = input(f"{Colors.YELLOW}Cle > {Colors.NC}").strip()
        if not key:
            return
        tier: str | None = self.key_manager.validate_key(key)
        if tier == "vip":
            self.current_tier = "vip"
            self._update_tier_config()
            print_colored("Cle VIP activee. 50 messages/12h debloques.", Colors.GREEN)
        elif tier == "unlimited":
            self.current_tier = "unlimited"
            self._update_tier_config()
            print_colored("Cle UNLIMITED activee. Quota eleve debloque.", Colors.CYAN)
        else:
            print_colored("Cle invalide.", Colors.RED)

    def _handle_command(self, cmd: str) -> None:
        if cmd == "exit":
            self.running = False
        elif cmd == "clear":
            clear_screen()
            self._show_banner()
        elif cmd == "quota":
            remaining = self.quota.get_remaining(self.session_id)
            print_colored(f"Messages restants : {remaining}", Colors.YELLOW)
        elif cmd == "cache":
            print_colored(f"Cache : {self.cache.size()} entrees", Colors.YELLOW)
        elif cmd == "history":
            entries: list = self.history.get(self.session_id)
            print_colored(f"Historique : {len(entries)} entrees", Colors.YELLOW)
            for entry in entries[-3:]:
                print_colored(f"  Q: {entry['prompt'][:40]}...", Colors.GRAY)
        elif cmd == "mode":
            modes = ["default", "coder", "concise", "creative", "teacher", "hacker"]
            idx = modes.index(self.current_mode) if self.current_mode in modes else 0
            self.current_mode = modes[(idx + 1) % len(modes)]
            print_colored(f"Mode : {self.current_mode}", Colors.GREEN)
        elif cmd == "models":
            print_colored("Modeles disponibles :", Colors.CYAN)
            for model in self.ollama.get_available_models():
                print_colored(f"  - {model}", Colors.GRAY)
        elif cmd == "key":
            self._activate_key()
        elif cmd == "tier":
            print_colored(f"Tier actuel : {self.current_tier.upper()}", Colors.YELLOW)
        elif cmd == "tokens":
            max_tokens = self.config.get_tier_config().get("num_predict", 512)
            used = self.ollama.get_last_eval_count()
            remaining = max(0, max_tokens - used)
            bar_len = 20
            filled = int((used / max_tokens) * bar_len) if max_tokens > 0 else 0
            filled = min(filled, bar_len)
            bar = "|" + "#" * filled + "-" * (bar_len - filled) + "|"
            print_colored(f"Tokens : {bar} {used}/{max_tokens} utilises ({remaining} restants)", Colors.CYAN)
        elif cmd == "help":
            print_colored("\nCommandes :", Colors.CYAN)
            for command, description in COMMANDS.items():
                print_colored(f"  {command:10} -> {description}", Colors.GRAY)
            print_colored("\nTiers disponibles :", Colors.CYAN)
            print_colored("  FREE      -> 30 msg/12h (gratuit)", Colors.GREEN)
            print_colored("  VIP       -> 50 msg/12h (cle INT3LK3Y_V1P-XXXX)", Colors.MAGENTA)
            print_colored("  UNLIMITED -> 999 msg/h  (cle INT3LK3Y_ULT1M3-XXXX)", Colors.CYAN)
            print()

    def _shutdown(self) -> None:
        self.session.end(self.session_id)
        self.memory.cleanup()
        self.ollama.unload()
        print_colored("\n=== Session terminee ===\n", Colors.RED)
