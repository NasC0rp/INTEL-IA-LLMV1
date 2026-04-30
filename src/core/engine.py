import sys
import os
import time
import json
from typing import Any
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from src.api.ollama_client import OllamaClient
from src.managers.quota_manager import QuotaManager
from src.managers.cache_manager import CacheManager
from src.managers.history_manager import HistoryManager
from src.managers.session_manager import SessionManager
from src.managers.memory_manager import MemoryManager
from src.managers.key_manager import KeyManager
from src.checker.system_checker import SystemChecker
from src.utils.colors import Colors, print_colored, clear_screen
from src.utils.formatter import Formatter
from src.core.updater import Updater

BANNER = """
██╗      ██╗███╗   ██╗████████╗███████╗██╗          ██████╗ ██████╗ ██████╗ ███████╗
╚██╗     ██║████╗  ██║╚══██╔══╝██╔════╝██║         ██╔════╝██╔═══██╗██╔══██╗██╔════╝
 ╚██╗    ██║██╔██╗ ██║   ██║   █████╗  ██║         ██║     ██║   ██║██║  ██║█████╗  
 ██╔╝    ██║██║╚██╗██║   ██║   ██╔══╝  ██║         ██║     ██║   ██║██║  ██║██╔══╝  
██╔╝     ██║██║ ╚████║   ██║   ███████╗███████╗    ╚██████╗╚██████╔╝██████╔╝███████╗
╚═╝      ╚═╝╚═╝  ╚═══╝   ╚═╝   ╚══════╝╚══════╝     ╚═════╝ ╚═════╝ ╚═════╝ ╚══════╝
"""

COMMANDS = {
    "exit": "Quitter",
    "clear": "Effacer l'ecran",
    "quota": "Messages restants",
    "mode": "Changer de mode",
    "models": "Modeles disponibles",
    "key": "Activer une cle VIP/Unlimited",
    "tier": "Voir le tier actuel",
    "tokens": "Tokens restants",
    "help": "Aide"
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
        self.current_tier: str = "free"
        self.session_id: str = ""
        self._update_tier_config()

    def _update_tier_config(self) -> None:
        limits_file: str = os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'limits.json')
        if os.path.exists(limits_file):
            with open(limits_file, 'r', encoding='utf-8') as f:
                limits: dict = json.load(f)
            limits["current_tier"] = self.current_tier
            with open(limits_file, 'w', encoding='utf-8') as f:
                json.dump(limits, f, indent=2)

    def run(self) -> None:
        self.running = True
        self.session_id = self.session.create()
        clear_screen()
        self._show_banner()
        self._quick_check()
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
        print()

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
                    print_colored(f"[{elapsed:.1f}s] [messages:{remaining}] [mode:{self.current_mode}]", Colors.GRAY)
                else:
                    print_colored(f"\n{response}\n", Colors.RED)

            except KeyboardInterrupt:
                self.running = False
            except Exception as e:
                self.logger.error(f"Erreur: {e}")
                print_colored(f"\n[ERREUR] {e}\n", Colors.RED)

        self._shutdown()

    def _activate_key(self) -> None:
        print_colored("\n=== ACTIVATION CLE ===", Colors.CYAN)
        key: str = input(f"{Colors.YELLOW}Cle > {Colors.NC}").strip()
        if not key:
            return
        tier: str | None = self.key_manager.validate_key(key)
        if tier == "vip":
            self.current_tier = "vip"
            self._update_tier_config()
            print_colored("Cle VIP activee !", Colors.GREEN)
        elif tier == "unlimited":
            self.current_tier = "unlimited"
            self._update_tier_config()
            print_colored("Cle UNLIMITED activee !", Colors.CYAN)
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
        elif cmd == "mode":
            modes = ["default", "coder", "concise", "creative", "teacher", "hacker"]
            idx = modes.index(self.current_mode) if self.current_mode in modes else 0
            self.current_mode = modes[(idx + 1) % len(modes)]
            print_colored(f"Mode : {self.current_mode}", Colors.GREEN)
        elif cmd == "models":
            print_colored("Modeles disponibles :", Colors.CYAN)
            for m in self.ollama.get_available_models():
                print_colored(f"  * {m}", Colors.GRAY)
        elif cmd == "key":
            self._activate_key()
        elif cmd == "tier":
            print_colored(f"Tier actuel : {self.current_tier.upper()}", Colors.YELLOW)
        elif cmd == "tokens":
            max_tokens = self.config.get_tier_config().get("num_predict", 512)
            used = self.ollama.get_last_eval_count()
            bar_len = 20
            filled = int((used / max_tokens) * bar_len) if max_tokens > 0 else 0
            filled = min(filled, bar_len)
            bar = "|" + "#" * filled + "-" * (bar_len - filled) + "|"
            print_colored(f"Tokens : {bar} {used}/{max_tokens}", Colors.CYAN)
        elif cmd == "help":
            print_colored("\nCommandes :", Colors.CYAN)
            for c, d in COMMANDS.items():
                print_colored(f"  {c:10} -> {d}", Colors.GRAY)
            print()

    def _shutdown(self) -> None:
        self.session.end(self.session_id)
        self.memory.cleanup()
        self.ollama.unload()
        print_colored("\n=== Session terminee ===\n", Colors.RED)