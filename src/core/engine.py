import os
import time
from pathlib import Path
from src.api.ollama_client import OllamaClient
from src.core.config_loader import ConfigLoader
from src.checker.system_checker import SystemChecker
from src.core.updater import Updater
from src.managers.cache_manager import CacheManager
from src.managers.history_manager import HistoryManager
from src.managers.key_manager import KeyManager
from src.managers.memory_manager import MemoryManager
from src.managers.quota_manager import QuotaManager
from src.managers.session_manager import SessionManager
from src.utils.colors import Colors, clear_screen, print_colored
from src.managers.logger import Logger
from src.utils.formatter import Formatter

BANNER = """
██╗      ██╗███╗   ██╗████████╗███████╗██╗         ██╗ █████╗ 
╚██╗     ██║████╗  ██║╚══██╔══╝██╔════╝██║         ██║██╔══██╗
 ╚██╗    ██║██╔██╗ ██║   ██║   █████╗  ██║         ██║███████║
 ██╔╝    ██║██║╚██╗██║   ██║   ██╔══╝  ██║         ██║██╔══██║
██╔╝     ██║██║ ╚████║   ██║   ███████╗███████╗    ██║██║  ██║
╚═╝      ╚═╝╚═╝  ╚═══╝   ╚═╝   ╚══════╝╚══════╝    ╚═╝╚═╝  ╚═╝
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
    "tokens": "Quota tokens periode + derniere generation (num_predict)",
    "speed": "Vitesse derniere reponse",
    "help": "Aide",
}


class IntelGPTEngine:
    def __init__(self, config: ConfigLoader, logger: Logger) -> None:
        self._ensure_directories()
        self.config: ConfigLoader = config
        self.logger: Logger = logger
        self.ollama: OllamaClient = OllamaClient(config, logger)
        self.quota: QuotaManager = QuotaManager(config)
        self.cache: CacheManager = CacheManager(config)
        self.history: HistoryManager = HistoryManager(config)
        self.session: SessionManager = SessionManager(config)
        self.memory: MemoryManager = MemoryManager(config)
        self.checker: SystemChecker = SystemChecker(config)
        self.updater: Updater = Updater(config)
        pub_path = self.config.get("license.public_key_path", "config/license_public_key.pem")
        self.key_manager: KeyManager = KeyManager(public_key_path=pub_path)
        self.formatter: Formatter = Formatter()
        self.running: bool = False
        self.current_mode: str = "default"
        self.current_tier: str = self.config.get_tier()
        self.session_id: str = ""
        self._update_tier_config()

    def _ensure_directories(self) -> None:
        for directory in ("data/cache", "data/history", "data/logs", "data/sessions"):
            Path(directory).mkdir(parents=True, exist_ok=True)

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
        print_colored("               Intel CODE CX1.2 | NasCorp 2026", Colors.YELLOW)
        tier_color: str = Colors.GREEN if self.current_tier == "free" else Colors.MAGENTA if self.current_tier == "vip" else Colors.CYAN
        print_colored(f"               Tier: {self.current_tier.upper()}", tier_color)
        remaining: int = self.quota.get_remaining(self.session_id)
        print_colored(f"               Messages: {remaining}", Colors.GRAY)
        cap_tok: int | None = self.quota.get_max_tokens_window(self.session_id)
        if cap_tok is not None:
            tr: int | None = self.quota.get_remaining_tokens(self.session_id)
            if tr is not None:
                print_colored(f"               Tokens (periode): {tr} / {cap_tok} restants", Colors.GRAY)
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

    def _print_quota_blocked(self) -> None:
        info = self.quota.get_wait_until_renewal(self.session_id)
        if info:
            end, seconds, reason = info
            print_colored(f"\n{QuotaManager.format_wait_message(end, seconds, reason)}\n", Colors.YELLOW)
            return
        hrs = self.config.get_tier_config().get("window_hours", 12)
        print_colored(
            f"\nQuota atteint (messages ou tokens). Renouvellement sous environ {hrs} h apres le debut de votre periode.\n",
            Colors.YELLOW,
        )

    def _chat_loop(self) -> None:
        while self.running:
            try:
                prompt: str = input(f"{Colors.RED}Intel CODE [{self.current_tier}] > {Colors.NC}")
                line: str = prompt.strip()
                cmd_key: str = line.lower()

                if cmd_key in COMMANDS:
                    self._handle_command(cmd_key)
                    continue

                if not line:
                    continue

                remaining: int = self.quota.get_remaining(self.session_id)
                if remaining <= 0:
                    self._print_quota_blocked()
                    continue

                cached: str | None = self.cache.get(line)
                if cached:
                    print_colored(f"\n{cached}\n", Colors.WHITE)
                    self.quota.use(self.session_id, 0)
                    continue

                tok_period: int | None = self.quota.get_remaining_tokens(self.session_id)
                if tok_period is not None and tok_period <= 0:
                    self._print_quota_blocked()
                    continue

                start_time: float = time.time()
                # Streaming API Ollama (robuste), mais affichage seulement quand la reponse est complete
                response: str = self.ollama.generate_streaming(line, self.current_mode, on_token=None)
                elapsed: float = time.time() - start_time

                if response and not response.startswith("Erreur"):
                    formatted: str = self.formatter.format(response)
                    print_colored(f"\n{formatted}\n", Colors.WHITE)
                    self.cache.set(line, response)
                    self.history.add(self.session_id, line, response)
                    self.quota.use(self.session_id, self.ollama.get_last_eval_count())
                    remaining = self.quota.get_remaining(self.session_id)
                    tokens_per_second = self.ollama.get_last_tokens_per_second()
                    tok_rem: int | None = self.quota.get_remaining_tokens(self.session_id)
                    tok_seg: str = ""
                    if tok_rem is not None:
                        cap_t: int | None = self.quota.get_max_tokens_window(self.session_id)
                        if cap_t is not None:
                            tok_seg = f" [tokens periode:{tok_rem}/{cap_t}]"
                    print_colored(
                        f"[{elapsed:.1f}s] [{tokens_per_second:.1f} tok/s] [messages:{remaining}]{tok_seg} [mode:{self.current_mode}] [tier:{self.current_tier}]",
                        Colors.GRAY,
                    )
                else:
                    self._show_generation_error(response)

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

    def _show_generation_error(self, response: str) -> None:
        if response and not response.startswith("Erreur: empty"):
            print_colored(f"\n[ERREUR OLLAMA] {response}\n", Colors.RED)
            return

        attempts = self.ollama.get_last_attempts()
        last_error = self.ollama.get_last_error() or "empty_response"
        print_colored("\n[ERREUR] Le modele n'a pas produit de texte.", Colors.RED)
        print_colored(f"Tentatives: {attempts} | Diagnostic: {last_error}", Colors.GRAY)
        print_colored("Causes possibles: requete refusee par le modele, prompt trop ambigu, ou ressources insuffisantes.", Colors.YELLOW)
        print_colored("Solution: reformule la question ou essaie un autre mode (commande 'mode').\n", Colors.GRAY)

    def _handle_command(self, cmd: str) -> None:
        if cmd == "exit":
            self.running = False
        elif cmd == "clear":
            clear_screen()
            self._show_banner()
        elif cmd == "quota":
            remaining = self.quota.get_remaining(self.session_id)
            wait = self.quota.get_wait_until_renewal(self.session_id)
            if wait is not None:
                print_colored(QuotaManager.format_wait_message(wait[0], wait[1], wait[2]), Colors.YELLOW)
            print_colored(f"Messages restants : {remaining}", Colors.YELLOW)
            cap_tw = self.quota.get_max_tokens_window(self.session_id)
            if cap_tw is not None:
                used_tw = self.quota.get_tokens_used_this_window(self.session_id)
                rem_tw = self.quota.get_remaining_tokens(self.session_id)
                print_colored(
                    f"Quota tokens (sortie modele) sur la periode : {used_tw} utilises, {rem_tw} restants (plafond {cap_tw})",
                    Colors.YELLOW,
                )
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
            models = self.ollama.get_available_models()
            if not models:
                print_colored("Aucun modele trouve. Verifiez qu'Ollama est lance.", Colors.YELLOW)
                return
            print_colored("Modeles disponibles :", Colors.CYAN)
            for index, model in enumerate(models, 1):
                marker = " (actif)" if model == self.ollama.model or model == f"{self.ollama.model}:latest" else ""
                print_colored(f"  {index}. {model}{marker}", Colors.GRAY)
        elif cmd == "key":
            self._activate_key()
        elif cmd == "tier":
            print_colored(f"Tier actuel : {self.current_tier.upper()}", Colors.YELLOW)
        elif cmd == "tokens":
            max_tokens = self.config.get_tier_config().get("num_predict", 512)
            cap_tw = self.quota.get_max_tokens_window(self.session_id)
            if cap_tw is not None:
                utw = self.quota.get_tokens_used_this_window(self.session_id)
                rtw = self.quota.get_remaining_tokens(self.session_id)
                print_colored(
                    f"Quota TOKENS periode (cumul sortie modele, meme fenetre que les messages): "
                    f"{utw} utilises, {rtw} restants, plafond {cap_tw}.",
                    Colors.CYAN,
                )
            used = self.ollama.get_last_eval_count()
            speed = self.ollama.get_last_tokens_per_second()
            if used <= 0:
                print_colored(
                    "Pas encore de derniere reponse enregistree (0 token). Posez une question pour remplir cette mesure.",
                    Colors.YELLOW,
                )
                print_colored(
                    f"Par message, le modele est limite par num_predict = {max_tokens} tokens max par generation.",
                    Colors.GRAY,
                )
            else:
                bar_len = 20
                filled = int((used / max_tokens) * bar_len) if max_tokens > 0 else 0
                filled = min(filled, bar_len)
                bar = "|" + "#" * filled + "-" * (bar_len - filled) + "|"
                print_colored(
                    f"Derniere reponse: {used} tokens generes (plafond technique par message num_predict: {max_tokens}).",
                    Colors.CYAN,
                )
                print_colored(
                    f"Taux d'utilisation du plafond sur cette reponse: {bar} {used}/{max_tokens}",
                    Colors.CYAN,
                )
                print_colored(
                    "num_predict limite une seule generation ; le quota TOKENS periode limite le total sur la fenetre.",
                    Colors.GRAY,
                )
                print_colored(f"Vitesse derniere reponse: {speed:.1f} tok/s", Colors.GRAY)
        elif cmd == "speed":
            tokens_per_second = self.ollama.get_last_tokens_per_second()
            total_seconds = self.ollama.get_last_total_seconds()
            print_colored(f"Vitesse derniere reponse : {tokens_per_second:.1f} tok/s, total Ollama {total_seconds:.1f}s", Colors.CYAN)
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
