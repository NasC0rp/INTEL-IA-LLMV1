import sys
import os
import time
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
    "clear": "Effacer l'écran",
    "quota": "Messages restants",
    "cache": "Taille du cache",
    "history": "Historique",
    "mode": "Changer de mode",
    "models": "Modèles disponibles",
    "key": "Activer une clé VIP/Unlimited",
    "tier": "Voir le tier actuel",
    "help": "Aide"
}

class IntelGPTEngine:
    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        self.ollama = OllamaClient(config)
        self.quota = QuotaManager(config)
        self.cache = CacheManager(config)
        self.history = HistoryManager(config)
        self.session = SessionManager(config)
        self.memory = MemoryManager(config)
        self.checker = SystemChecker(config)
        self.updater = Updater(config)
        self.key_manager = KeyManager()
        self.formatter = Formatter()
        self.running = False
        self.current_mode = "default"
        self.current_tier = "free"
        self._update_tier_config()

    def _update_tier_config(self):
        limits_file = os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'limits.json')
        if os.path.exists(limits_file):
            import json
            with open(limits_file, 'r') as f:
                limits = json.load(f)
            limits["current_tier"] = self.current_tier
            with open(limits_file, 'w') as f:
                json.dump(limits, f, indent=2)

    def run(self):
        self.running = True
        clear_screen()
        self._show_banner()
        self._quick_check()
        self._check_updates()
        self.ollama.warmup()
        self._chat_loop()

    def _show_banner(self):
        print_colored(BANNER, Colors.RED)
        print_colored("                     Projet NasCorp © 2026", Colors.YELLOW)
        tier_color = Colors.GREEN if self.current_tier == "free" else Colors.MAGENTA if self.current_tier == "vip" else Colors.CYAN
        print_colored(f"                     Tier: {self.current_tier.upper()}", tier_color)
        print_colored("                     'help' pour les commandes\n", Colors.GRAY)

    def _quick_check(self):
        ok, results = self.checker.check_all()
        print_colored("═══ VÉRIFICATION ═══", Colors.CYAN)
        for status, msg in results:
            tag = "[✓]" if status else "[✗]"
            color = Colors.GREEN if status else Colors.RED
            print_colored(f"  {tag} {msg}", color)
        print_colored("════════════════════\n", Colors.CYAN)
        if not ok:
            print_colored("⚠️  Certains checks ont échoué.\n", Colors.YELLOW)
        self.memory.optimize()

    def _check_updates(self):
        self.updater.check()
        if self.updater.update_available:
            print_colored(f"⬆️  Nouvelle version dispo : v{self.updater.latest_version}", Colors.YELLOW)
            print_colored(f"   → {self.updater.get_update_command()}\n", Colors.GRAY)

    def _chat_loop(self):
        session_id = self.session.create()
        remaining = self.quota.get_remaining(session_id)
        
        while self.running:
            try:
                prompt = input(f"{Colors.RED}Intel CODE [{self.current_tier}] > {Colors.NC}")
                
                if prompt.lower() in COMMANDS:
                    self._handle_command(prompt.lower(), session_id)
                    continue
                
                if not prompt.strip():
                    continue
                    
                if remaining <= 0:
                    print_colored("\n[QUOTA] Limite atteinte. Passez VIP avec 'key'.\n", Colors.YELLOW)
                    continue

                cached = self.cache.get(prompt)
                if cached:
                    print_colored(f"\n{cached}\n", Colors.WHITE)
                    self.quota.use(session_id)
                    remaining = self.quota.get_remaining(session_id)
                    continue

                print_colored("\nRéflexion...", Colors.GRAY)
                start_time = time.time()
                response = self.ollama.generate(prompt, self.current_mode)
                elapsed = time.time() - start_time

                if response:
                    formatted = self.formatter.format(response)
                    print_colored(f"\n{formatted}\n", Colors.WHITE)
                    self.cache.set(prompt, response)
                    self.history.add(session_id, prompt, response)
                    self.quota.use(session_id)
                    remaining = self.quota.get_remaining(session_id)
                    print_colored(f"[{elapsed:.1f}s] [quota:{remaining}] [mode:{self.current_mode}] [tier:{self.current_tier}]", Colors.GRAY)
                else:
                    print_colored("\n[ERREUR] Vérifiez qu'Ollama est lancé.\n", Colors.RED)

            except KeyboardInterrupt:
                self.running = False
            except Exception as e:
                self.logger.error(f"Erreur: {e}")
                print_colored(f"\n[ERREUR] {e}\n", Colors.RED)

        self._shutdown(session_id)

    def _activate_key(self):
        print_colored("\n═══ ACTIVATION CLÉ ═══", Colors.CYAN)
        print_colored("Formats: INT3LK3Y_V1P-XXXX ou INT3LK3Y_ULT1M3-XXXX", Colors.GRAY)
        key = input(f"{Colors.YELLOW}Clé > {Colors.NC}").strip()
        
        if not key:
            print_colored("Aucune clé entrée.", Colors.RED)
            return
        
        tier = self.key_manager.validate_key(key)
        if tier == "vip":
            self.current_tier = "vip"
            self._update_tier_config()
            print_colored("✅ Clé VIP activée ! 50 messages/12h débloqués.", Colors.GREEN)
        elif tier == "unlimited":
            self.current_tier = "unlimited"
            self._update_tier_config()
            print_colored("✅ Clé UNLIMITED activée ! Quota illimité.", Colors.CYAN)
        else:
            print_colored("❌ Clé invalide. Obtenez une clé sur le Discord NasCorp.", Colors.RED)

    def _handle_command(self, cmd, session_id):
        if cmd == "exit":
            self.running = False
        elif cmd == "clear":
            clear_screen()
            self._show_banner()
        elif cmd == "quota":
            r = self.quota.get_remaining(session_id)
            print_colored(f"Messages restants : {r}", Colors.YELLOW)
        elif cmd == "cache":
            s = self.cache.size()
            print_colored(f"Cache : {s} entrées", Colors.YELLOW)
        elif cmd == "history":
            entries = self.history.get(session_id)
            print_colored(f"Historique : {len(entries)} entrées", Colors.YELLOW)
            for e in entries[-3:]:
                print_colored(f"  Q: {e['prompt'][:40]}...", Colors.GRAY)
        elif cmd == "mode":
            modes = ["default", "coder", "concise", "creative", "teacher", "hacker"]
            idx = modes.index(self.current_mode) if self.current_mode in modes else 0
            self.current_mode = modes[(idx + 1) % len(modes)]
            print_colored(f"Mode : {self.current_mode}", Colors.GREEN)
        elif cmd == "models":
            models = self.ollama.get_available_models()
            print_colored("Modèles disponibles :", Colors.CYAN)
            for m in models:
                print_colored(f"  • {m}", Colors.GRAY)
        elif cmd == "key":
            self._activate_key()
        elif cmd == "tier":
            print_colored(f"Tier actuel : {self.current_tier.upper()}", Colors.YELLOW)
            print_colored("Tapez 'key' pour activer une clé VIP/Unlimited.", Colors.GRAY)
        elif cmd == "help":
            print_colored("\nCommandes :", Colors.CYAN)
            for c, d in COMMANDS.items():
                print_colored(f"  {c:10} → {d}", Colors.GRAY)
            print_colored(f"\nTiers disponibles :", Colors.CYAN)
            print_colored(f"  FREE      → 30 msg/12h (gratuit)", Colors.GREEN)
            print_colored(f"  VIP       → 50 msg/12h (clé INT3LK3Y_V1P-XXXX)", Colors.MAGENTA)
            print_colored(f"  UNLIMITED → 999 msg/h  (clé INT3LK3Y_ULT1M3-XXXX)", Colors.CYAN)
            print()

    def _shutdown(self, session_id):
        self.session.end(session_id)
        self.memory.cleanup()
        self.ollama.unload()
        print_colored("\n╚═══ Session terminée ═══╝\n", Colors.RED)