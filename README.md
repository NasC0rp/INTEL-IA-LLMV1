# Intel CODE

**Assistant IA Terminal — Non censuré — 100% Local**

![Version](https://img.shields.io/badge/version-1.0.0-red)
![License](https://img.shields.io/badge/license-MIT-darkred)
![Python](https://img.shields.io/badge/python-3.8+-black)
![Status](https://img.shields.io/badge/status-active-green)

---

Intel CODE est un assistant IA en ligne de commande qui utilise Ollama avec un modèle abliterated de 4B paramètres. 
Inspiré par Claude Code, il fonctionne entièrement en local, sans cloud, sans API payante, et sans aucune censure.

Développé par **NasCorp** © 2026 — Projet indépendant (pas encore une entreprise certifiée).

---

## Installation

```bash
git clone https://github.com/NasC0rp/intel-code-LLMV1.git
cd intel-code-LLMV1
chmod +x scripts/*.sh
./scripts/setup.sh
./scripts/start.sh
```

## Prérequis

| Composant | Minimum | Recommandé |
|-----------|---------|-------------|
| RAM | 4 Go | 6 Go |
| CPU | 2 cœurs | 3 cœurs |
| Disque | 10 Go | 20 Go SSD |
| Python | 3.8+ | 3.11+ |
| OS | Linux | Ubuntu/Debian |

## Utilisation

```
Intel CODE [free] > votre question ici
```

## Commandes

| Commande | Description |
|----------|-------------|
| help | Affiche l'aide complète |
| mode | Change de mode (cycle) |
| quota | Affiche les messages restants |
| cache | Affiche la taille du cache |
| history | Affiche les derniers échanges |
| models | Liste les modèles disponibles |
| key | Active une clé VIP/Unlimited |
| tier | Affiche le tier actuel |
| clear | Efface l'écran |
| exit | Quitte l'assistant |

## Modes

| Mode | Description |
|------|-------------|
| default | Assistant général équilibré |
| coder | Code et explications techniques uniquement |
| concise | Réponses courtes (3 phrases max) |
| creative | Réponses détaillées et imaginatives |
| teacher | Explications pédagogiques avec exemples |
| hacker | Commandes terminal et astuces avancées |

## Tiers

| Tier | Messages | Fenêtre | Contexte | Threads | Clé requise |
|------|----------|---------|----------|---------|--------------|
| Free | 30 | 12h | 2K | 3 | Non |
| VIP | 50 | 12h | 4K | 3 | INT3LK3Y_V1P-XXXX |
| Unlimited | 999 | 1h | 8K | 3 | INT3LK3Y_ULT1M3-XXXX |

Pour activer une clé : `key` → entrer la clé

## Architecture

```
INTEL-IA-LLMV1/
│
├── 🎯 main.py              → Point d'entrée
├── 📦 requirements.txt     → requests, psutil
├── 🦙 Modelfile            → FROM huihui_ai/qwen3-abliterated:4b
├── 🔢 .version             → 1.0.0
├── 🙈 .gitignore
├── 📖 README.md
│
├── 📁 src/
│   ├── 🐍 __init__.py
│   ├── 📁 core/            → Moteur principal
│   │   ├── 🎮 engine.py        → Boucle de conversation
│   │   ├── ⚙️ config_loader.py → Charge config/limits/prompts/models
│   │   └── 🔄 updater.py       → Vérifie màj GitHub
│   │
│   ├── 📁 api/             → Client Ollama
│   │   ├── 🦙 ollama_client.py  → POST /api/generate, warmup, unload
│   │   ├── 📦 request_builder.py → Construit payloads JSON
│   │   └── ❌ error_handler.py   → 500/404/timeout/connection
│   │
│   ├── 📁 managers/        → Gestionnaires
│   │   ├── 📊 quota_manager.py  → FREE(30msg/12h) VIP(50msg/12h) UNLIMITED(999msg/1h)
│   │   ├── 💾 cache_manager.py  → Cache LRU 100 entrées
│   │   ├── 📜 history_manager.py → Historique par session UUID
│   │   ├── 🆔 session_manager.py → UUID sessions
│   │   ├── 🧠 memory_manager.py  → Garbage collector
│   │   ├── 🔑 key_manager.py     → INT3LK3Y_V1P-XXXX / INT3LK3Y_ULT1M3-XXXX
│   │   └── 📝 logger.py          → data/logs/intel_code.log
│   │
│   ├── 📁 checker/         → Vérification système (parallèle 4 threads)
│   │   ├── 🔍 system_checker.py  → Orchestrateur
│   │   ├── 🖥️ cpu_checker.py     → ≥2 cœurs
│   │   ├── 🧮 ram_checker.py     → ≥4 Go
│   │   ├── 💿 disk_checker.py    → ≥10 Go
│   │   └── 🌐 network_checker.py → Ollama actif
│   │
│   └── 📁 utils/           → Utilitaires
│       ├── 🎨 colors.py        → ANSI colors (RED/GREEN/YELLOW...)
│       ├── 📏 formatter.py     → textwrap 80 colonnes
│       └── 🔧 helpers.py       → timestamp, format_seconds
│
├── 📁 config/              → JSON (à la racine)
│   ├── ⚙️ config.json      → host, model: intel-code, timeout: 120
│   ├── 📊 limits.json      → Tiers + current_tier
│   ├── 💬 prompts.json     → 6 modes
│   ├── 🤖 models.json      → intel-code: 4B, 6Go RAM, 3-8 t/s
│   └── 🔑 keys.json        → VIP: [], unlimited: []
│
├── 📁 data/                → Données (créé auto)
│   ├── 📁 cache/           → .responses, .quota, .version_cache
│   ├── 📁 history/         → {session_id}.json
│   └── 📁 logs/            → intel_code.log
│
└── 📁 scripts/             → Bash
    ├── 🔧 setup.sh         → apt, ollama, pull model, create intel-code
    ├── 🚀 start.sh         → ollama serve + python3 main.py
    ├── 🛠️ dev.sh           → Vérification uniquement
    └── ⬆️ update.sh        → git pull

## Configuration

Fichiers dans `config/` :

| Fichier | Contenu |
|---------|---------|
| config.json | Hôte Ollama, modèle, timeout |
| limits.json | Limites des tiers (messages, fenêtre, contexte) |
| prompts.json | Prompts système pour chaque mode |
| models.json | Modèles disponibles et leurs caractéristiques |
| keys.json | Clés VIP et Unlimited valides |

## Développement

```bash
./scripts/dev.sh    # Vérification système uniquement
./scripts/update.sh # Mise à jour depuis GitHub
```

## Performance

- Cache LRU des réponses fréquentes (100 entrées)
- Warmup automatique du modèle au démarrage
- Vérification système parallèle (4 threads)
- Gestion mémoire avec garbage collector
- Temps de réponse : 3-8 secondes (6 Go RAM)

## FAQ

**Q : Quelle différence avec Claude Code ?**  
R : Intel CODE est 100% local, gratuit, et sans censure. Pas de cloud, pas d'API payante.

**Q : Est-ce que ça tourne sur Windows ?**  
R : Oui, via WSL2 (Windows Subsystem for Linux).

**Q : Comment obtenir une clé VIP ?**  
R : Rejoignez le Discord ou Telegram NasCorp.

**Q : Le modèle est-il vraiment sans censure ?**  
R : Oui, le modèle est "abliterated" — les couches de refus ont été supprimées.

## Liens

- GitHub : [NasC0rp/intel-code-LLMV1](https://github.com/NasC0rp/intel-code-LLMV1)
- Telegram : @IntelIA_NasCorp

## Avertissement

Intel CODE utilise un modèle sans censure. Vous êtes responsable de votre usage.  
L'auteur n'est pas responsable des questions posées ou des réponses générées.

---

NasCorp © 2026 — Projet indépendant. NasCorp n'est pas encore une entreprise certifiée.  
Intel® est une marque déposée d'Intel Corporation. Ce projet n'est pas affilié à Intel.

