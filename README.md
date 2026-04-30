
# Intel CODE CX1

**Assistant IA Terminal — Non censuré — 100% Local**

![Version](https://img.shields.io/badge/version-CX1-red) ![License](https://img.shields.io/badge/license-MIT-darkred) ![Python](https://img.shields.io/badge/python-3.8+-black)

---

Intel CODE est un assistant IA en ligne de commande. Modèle Qwen3 4B abliterated via Ollama. 100% local, gratuit, sans censure.

Développé par **NasCorp** © 2026 — Projet indépendant.

---

## Versions

| Version | Statut |
|---------|--------|
| **CX1** | ✅ Actuelle |


---

## Installation

```bash
git clone https://github.com/NasC0rp/INTEL-IA-LLMV1.git
cd INTEL-IA-LLMV1
chmod +x scripts/*.sh
./scripts/setup.sh
./scripts/start.sh
```

## Prérequis

| Composant | Minimum | Recommandé |
|-----------|---------|------------|
| RAM | 4 Go | 6 Go |
| CPU | 2 cœurs | 3 cœurs |
| Disque | 10 Go | 20 Go SSD |
| Python | 3.8+ | 3.11+ |
| OS | Linux | Ubuntu/Debian |

## Utilisation

```
Intel CODE [free] > votre question
```

## Commandes

| Commande | Description |
|----------|-------------|
| `help` | Affiche l'aide |
| `mode` | Change de mode |
| `quota` | Messages restants |
| `models` | Liste les modèles |
| `key` | Active une clé |
| `tier` | Voir le tier actuel |
| `tokens` | Tokens utilisés |
| `clear` | Efface l'écran |
| `exit` | Quitter |

## Modes

| Mode | Description |
|------|-------------|
| `default` | Assistant général |
| `coder` | Code uniquement |
| `concise` | Réponses courtes |
| `creative` | Réponses détaillées |
| `teacher` | Pédagogique |
| `hacker` | Commandes techniques |

## Tiers

| Tier | Messages | Fenêtre | Clé |
|------|----------|---------|-----|
| Free | 30 | 12h | Aucune |
| VIP | 50 | 12h | `INT3LK3Y_V1P-XXXX` |
| Unlimited | 999 | 1h | `INT3LK3Y_ULT1M3-XXXX` |

## Structure

```
INTEL-IA-LLMV1/
├── main.py
├── requirements.txt
├── Modelfile
├── .version
├── .gitignore
├── README.md
├── src/
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── engine.py
│   │   ├── config_loader.py
│   │   └── updater.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── ollama_client.py
│   │   ├── request_builder.py
│   │   └── error_handler.py
│   ├── managers/
│   │   ├── __init__.py
│   │   ├── quota_manager.py
│   │   ├── cache_manager.py
│   │   ├── history_manager.py
│   │   ├── session_manager.py
│   │   ├── memory_manager.py
│   │   ├── key_manager.py
│   │   └── logger.py
│   ├── checker/
│   │   ├── __init__.py
│   │   ├── system_checker.py
│   │   ├── cpu_checker.py
│   │   ├── ram_checker.py
│   │   ├── disk_checker.py
│   │   └── network_checker.py
│   └── utils/
│       ├── __init__.py
│       ├── colors.py
│       ├── formatter.py
│       └── helpers.py
├── config/
│   ├── config.json
│   ├── limits.json
│   ├── prompts.json
│   ├── models.json
│   └── keys.json
├── data/
│   ├── cache/
│   ├── history/
│   └── logs/
└── scripts/
    ├── setup.sh
    ├── start.sh
    ├── dev.sh
    └── update.sh
```

## Liens

- **GitHub** : [NasC0rp/INTEL-IA-LLMV1](https://github.com/NasC0rp/INTEL-IA-LLMV1)
- **Telegram** : [@IntelIA_NasCorp](https://t.me/IntelIA_NasCorp)

## Avertissement

Intel CODE utilise un modèle sans censure. Vous êtes responsable de votre usage.

---

NasCorp © 2026 — Projet indépendant. NasCorp n'est pas encore une entreprise certifiée. Intel® est une marque déposée d'Intel Corporation.
```

