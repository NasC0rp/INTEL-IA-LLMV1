# Intel CODE CX1

Assistant IA en ligne de commande, local, base sur Ollama.

![Version](https://img.shields.io/badge/version-CX1-red)
![License](https://img.shields.io/badge/license-MIT-darkred)
![Python](https://img.shields.io/badge/python-3.10+-black)

> Projet independant NasCorp, non affilie a Intel Corporation.

## Fonctionnalites

- Assistant terminal local via Ollama
- Modes de reponse: default, coder, concise, creative, teacher, hacker
- Gestion de quota par tier: free, vip, unlimited
- Cache local des reponses
- Historique par session
- Verification systeme au demarrage
- Detection de mise a jour GitHub

## Prerequis

| Composant | Minimum | Recommande |
|-----------|---------|------------|
| RAM | 4 Go | 6 Go |
| CPU | 2 coeurs | 3 coeurs |
| Disque | 10 Go | 20 Go SSD |
| Python | 3.10+ | 3.11+ |
| OS | Linux / WSL2 | Ubuntu / Debian |

## Installation

```bash
git clone https://github.com/NasC0rp/INTEL-IA-LLMV1.git
cd INTEL-IA-LLMV1
chmod +x scripts/*.sh
./scripts/setup.sh
./scripts/start.sh
```

## Utilisation

```text
Intel CODE [free] > votre question
```

## Commandes

| Commande | Description |
|----------|-------------|
| `help` | Affiche l'aide |
| `mode` | Change de mode |
| `quota` | Affiche les messages restants |
| `cache` | Affiche la taille du cache |
| `history` | Affiche les derniers echanges |
| `models` | Liste les modeles Ollama disponibles |
| `key` | Active une cle VIP ou Unlimited |
| `tier` | Affiche le tier actuel |
| `tokens` | Affiche l'utilisation de tokens |
| `speed` | Affiche la vitesse de la derniere reponse |
| `clear` | Efface l'ecran |
| `exit` | Quitte l'assistant |

## Modes

| Mode | Description |
|------|-------------|
| `default` | Assistant general |
| `coder` | Code uniquement |
| `concise` | Reponses courtes |
| `creative` | Reponses detaillees |
| `teacher` | Pedagogique |
| `hacker` | Commandes techniques |

## Tiers

| Tier | Messages | Fenetre | Cle |
|------|----------|---------|-----|
| Free | 30 | 12h | Aucune |
| VIP | 50 | 12h | `INT3LK3Y_V1P-XXXX` |
| Unlimited | 999 | 1h | `INT3LK3Y_ULT1M3-XXXX` |

## Configuration des cles

Les cles sensibles ne doivent pas etre commitees.

1. Copiez `config/keys.example.json` vers `config/keys.local.json`.
2. Ajoutez vos cles dans `config/keys.local.json`.
3. Lancez l'application et utilisez la commande `key`.

`config/keys.local.json` est ignore par Git.

## Structure

```text
INTEL-IA-LLMV1/
├── main.py
├── requirements.txt
├── Modelfile
├── README.md
├── config/
│   ├── config.json
│   ├── limits.json
│   ├── prompts.json
│   ├── models.json
│   ├── keys.json
│   └── keys.example.json
├── scripts/
│   ├── setup.sh
│   ├── start.sh
│   ├── dev.sh
│   └── update.sh
└── src/
    ├── api/
    ├── checker/
    ├── core/
    ├── managers/
    └── utils/
```

## Donnees locales

L'application cree automatiquement le dossier `data/` pour stocker le cache, le quota, le tier actif, l'historique et les logs.

Ce dossier est ignore par Git.

## Developpement

```bash
python -m compileall main.py src
./scripts/dev.sh
```

## Liens

- GitHub : [NasC0rp/INTEL-IA-LLMV1](https://github.com/NasC0rp/INTEL-IA-LLMV1)
- Telegram : [@IntelIA_NasCorp](https://t.me/IntelIA_NasCorp)

## Avertissement

Intel CODE execute un modele local via Ollama. L'utilisateur reste responsable de son usage, des prompts envoyes et des reponses generees.
