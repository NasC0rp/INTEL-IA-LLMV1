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
    "cache": "Taille du cache",
    "history": "Historique",
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
        clear_screen()
        self._show_banner()
        self._quick_check()
        self._check_updates()
        self.ollama.warmup()
        self._chat_loop()

    def _show_banner(self) -> None:
        print_colored(BANNER, Colors.RED)
        print_colored("                     Projet NasCorp © 2026", Colors.YELLOW)
        tier_color: str = Colors.GREEN if self.current_tier == "free" else Colors.MAGENTA if self.current_tier == "vip" else Colors.CYAN
        print_colored(f"                     Tier: {self.current_tier.upper()}", tier_color)
        print_colored("                     'help' pour les commandes\n", Colors.GRAY)

    def _quick_check(self) -> None:
        ok: bool
        results: list
        ok, results = self.checker.check_all()
        print_colored("═══ VERIFICATION ═══", Colors.CYAN)
        for status, msg in results:
            tag: str = "[✓]" if status else "[✗]"
            color: str = Colors.GREEN if status else Colors.RED
            print_colored(f"  {tag} {msg}", color)
        print_colored("════════════════════\n", Colors.CYAN)
        if not ok:
            print_colored("⚠️  Certains checks ont echoue.\n", Colors.YELLOW)
        self.memory.optimize()

    def _check_updates(self) -> None:
        self.updater.check()
        if self.updater.update_available:
            print_colored(f"⬆️  Nouvelle version dispo : v{self.updater.latest_version}", Colors.YELLOW)
            print_colored(f"   → {self.updater.get_update_command()}\n", Colors.GRAY)

    def _chat_loop(self) -> None:
        session_id: str = self.session.create()
        remaining: int = self.quota.get_remaining(session_id)

        while self.running:
            try:
                prompt: str = input(f"{Colors.RED}Intel CODE [{self.current_tier}] > {Colors.NC}")

                if prompt.lower() in COMMANDS:
                    self._handle_command(prompt.lower(), session_id)
                    continue

                if not prompt.strip():
                    continue

                if remaining <= 0:
                    print_colored("\n[QUOTA] Limite atteinte. Passez VIP avec 'key'.\n", Colors.YELLOW)
                    continue

                cached: str | None = self.cache.get(prompt)
                if cached:
                    print_colored(f"\n{cached}\n", Colors.WHITE)
                    self.quota.use(session_id)
                    remaining = self.quota.get_remaining(session_id)
                    continue

                print_colored("\nReflexion...", Colors.GRAY)
                start_time: float = time.time()
                response: str = self.ollama.generate(prompt, self.current_mode)
                elapsed: float = time.time() - start_time

                if response:
                    formatted: str = self.formatter.format(response)
                    print_colored(f"\n{formatted}\n", Colors.WHITE)
                    self.cache.set(prompt, response)
                    self.history.add(session_id, prompt, response)
                    self.quota.use(session_id)
                    remaining = self.quota.get_remaining(session_id)
                    print_colored(f"[{elapsed:.1f}s] [quota:{remaining}] [mode:{self.current_mode}] [tier:{self.current_tier}]", Colors.GRAY)
                else:
                    print_colored("\n[ERREUR] Verifiez qu'Ollama est lance.\n", Colors.RED)

            except KeyboardInterrupt:
                self.running = False
            except Exception as e:
                self.logger.error(f"Erreur: {e}")
                print_colored(f"\n[ERREUR] {e}\n", Colors.RED)

        self._shutdown(session_id)

    def _activate_key(self) -> None:
        print_colored("\n═══ ACTIVATION CLE ═══", Colors.CYAN)
        print_colored("Formats: INT3LK3Y_V1P-XXXX ou INT3LK3Y_ULT1M3-XXXX", Colors.GRAY)
        key: str = input(f"{Colors.YELLOW}Cle > {Colors.NC}").strip()

        if not key:
            print_colored("Aucune cle entree.", Colors.RED)
            return

        tier: str | None = self.key_manager.validate_key(key)
        if tier == "vip":
            self.current_tier = "vip"
            self._update_tier_config()
            print_colored("✅ Cle VIP activee ! 50 messages/12h debloques.", Colors.GREEN)
        elif tier == "unlimited":
            self.current_tier = "unlimited"
            self._update_tier_config()
            print_colored("✅ Cle UNLIMITED activee ! Quota illimite.", Colors.CYAN)
        else:
            print_colored("❌ Cle invalide.", Colors.RED)

    def _handle_command(self, cmd: str, session_id: str) -> None:
        if cmd == "exit":
            self.running = False
        elif cmd == "clear":
            clear_screen()
            self._show_banner()
        elif cmd == "quota":
            r: int = self.quota.get_remaining(session_id)
            print_colored(f"Messages restants : {r}", Colors.YELLOW)
        elif cmd == "cache":
            s: int = self.cache.size()
            print_colored(f"Cache : {s} entrees", Colors.YELLOW)
        elif cmd == "history":
            entries: list = self.history.get(session_id)
            print_colored(f"Historique : {len(entries)} entrees", Colors.YELLOW)
            for e in entries[-3:]:
                print_colored(f"  Q: {e['prompt'][:40]}...", Colors.GRAY)
        elif cmd == "mode":
            modes: list = ["default", "coder", "concise", "creative", "teacher", "hacker"]
            idx: int = modes.index(self.current_mode) if self.current_mode in modes else 0
            self.current_mode = modes[(idx + 1) % len(modes)]
            print_colored(f"Mode : {self.current_mode}", Colors.GREEN)
        elif cmd == "models":
            models: list = self.ollama.get_available_models()
            print_colored("Modeles disponibles :", Colors.CYAN)
            for m in models:
                print_colored(f"  • {m}", Colors.GRAY)
        elif cmd == "key":
            self._activate_key()
        elif cmd == "tier":
            print_colored(f"Tier actuel : {self.current_tier.upper()}", Colors.YELLOW)
        elif cmd == "tokens":
            tier_config: dict = self.config.get_tier_config()
            max_tokens: int = tier_config.get("num_predict", 512)
            used: int = self.ollama.get_last_eval_count()
            remaining: int = max(0, max_tokens - used)
            bar_length: int = 20
            filled: int = int((used / max_tokens) * bar_length) if max_tokens > 0 else 0
            filled = min(filled, bar_length)
            bar: str = "|" + "█" * filled + "░" * (bar_length - filled) + "|"
            print_colored(f"Tokens : {bar} {used}/{max_tokens} utilises ({remaining} restants)", Colors.CYAN)
        elif cmd == "help":
            print_colored("\nCommandes :", Colors.CYAN)
            for c, d in COMMANDS.items():
                print_colored(f"  {c:10} → {d}", Colors.GRAY)
            print_colored("\nTiers disponibles :", Colors.CYAN)
            print_colored("  FREE      → 30 msg/12h (gratuit)", Colors.GREEN)
            print_colored("  VIP       → 50 msg/12h (cle INT3LK3Y_V1P-XXXX)", Colors.MAGENTA)
            print_colored("  UNLIMITED → 999 msg/h  (cle INT3LK3Y_ULT1M3-XXXX)", Colors.CYAN)
            print()

    def _shutdown(self, session_id: str) -> None:
        self.session.end(session_id)
        self.memory.cleanup()
        self.ollama.unload()
        print_colored("\n╚═══ Session terminee ═══╝\n", Colors.RED)