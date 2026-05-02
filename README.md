# Intel CODE CX1.2

Assistant IA en ligne de commande, local, base sur Ollama.

**CX1.2 est la version la plus stable publiee a ce jour.**

Elle se concentre sur la fiabilite et une experience CLI propre :
- **Quota fiable** : le compteur ne se reinitialise pas au redemarrage et la fenetre demarre au premier message compte.
- **Quota tokens periode** : total de tokens de sortie cumule dans la meme fenetre que les messages (config `max_tokens_window`).
- **Limite atteinte = message clair** : attente indiquee si quota messages et/ou tokens atteint.
- **Ollama plus robuste** : utilisation de `/api/chat`, retry, et streaming cote API (affichage uniquement quand la reponse est complete).
- **Windows OK** : checks RAM via `psutil` et dossiers de donnees geres automatiquement.

![Version](https://img.shields.io/badge/version-CX1.2-red)
![License](https://img.shields.io/badge/license-MIT-darkred)
![Python](https://img.shields.io/badge/python-3.10+-black)

> Projet independant NasCorp, non affilie a Intel Corporation.

## Sommaire

- [Nouveautes](#nouveautes-cx12)
- [Fonctionnalites](#fonctionnalites)
- [Prerequis](#prerequis)
- [Installation](#installation)
- [Utilisation](#utilisation)
- [Commandes](#commandes)
- [Modes](#modes)
- [Tiers et quotas](#tiers-et-quotas)
- [Configuration des cles](#configuration-des-cles)
- [Modele Ollama](#modele-ollama)
- [Donnees locales](#donnees-locales)
- [Structure](#structure)
- [Developpement](#developpement)
- [Liens](#liens)
- [Avertissement](#avertissement)
- [Bugs connus](#bugs-connus)

## Nouveautes CX1.2

- API `/api/chat` au lieu de `/api/generate` (reponses stables sans corruption)
- Streaming cote API Ollama avec affichage de la reponse une fois complete
- Optimisation des ecritures disque (batch saves avec flush a la fermeture)
- Compatibilite Windows corrigee (RamChecker via psutil)
- Retry avec exponential backoff en cas d'erreur Ollama
- Prompt systeme ameliore avec instruction "reponds en francais uniquement"
- Parametres par defaut optimises (temperature 0.4, repeat_penalty 1.2)

## Fonctionnalites

- Assistant terminal local via Ollama
- Reponses affichees uniquement quand elles sont completes (pas de tokens partiels avant le contenu utile)
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
| OS | Windows / Linux | Windows 10+ / Ubuntu |

## Installation

### Windows

```powershell
git clone https://github.com/NasC0rp/INTEL-IA-LLMV1.git
cd INTEL-IA-LLMV1
pip install -r requirements.txt
ollama pull intel-code
python main.py
```

### Linux

```bash
git clone https://github.com/NasC0rp/INTEL-IA-LLMV1.git
cd INTEL-IA-LLMV1
chmod +x scripts/*.sh
./scripts/setup.sh
./scripts/start.sh
```

## Utilisation

Lancement depuis la racine du depot:

```powershell
python main.py
```

Alternative : `python -m src`.

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
| `tokens` | Quota tokens sur la periode + derniere generation vs `num_predict` (stats memorisees) |
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

## Tiers et quotas

### Limites par tier

| Tier | num_ctx | num_predict | max_tokens_window (periode) |
|------|---------|-------------|------------------------------|
| Free | 2048 | 256 | 7680 |
| VIP | 8048 | 2024 | 101200 |
| Unlimited | 9096 | 4024 | 4019976 |

`max_tokens_window` est le **total de tokens de sortie** (compteur Ollama `eval_count`) cumule sur la **meme fenetre** que le quota de messages. Reglable dans `config/limits.json`. Si la cle est omise pour un tier, le quota tokens periode est desactive.

### Renouvellement quota et tokens

Le quota de messages se renouvelle automatiquement selon la fenetre du tier actif:

- Free: 30 messages toutes les 12 heures
- VIP: 50 messages toutes les 12 heures
- Unlimited: 999 messages toutes les 1 heure

La fenetre commence au premier message compte dans le cycle courant. Exemple: si le quota Free commence a 14h00, les messages se renouvellent a 02h00.

En parallele, le **quota tokens periode** compte la somme des tokens generes sur la periode. Quand il est a 0 restant, les nouvelles questions vers Ollama sont bloquees (le cache peut encore repondre sans consommer de tokens). Le renouvellement est le meme instant que pour les messages.

`num_predict` reste un **plafond technique par generation** (une seule reponse ne depasse pas ce plafond). Si une reponse atteint ce plafond, elle s'arrete ; vous pouvez envoyer un autre message si vous avez encore du **quota messages** et du **quota tokens periode** (`quota` / `tokens`).

## Configuration des cles

Les cles sensibles ne doivent pas etre commitees.

1. Copiez `config/keys.example.json` vers `config/keys.local.json`.
2. Ajoutez vos cles dans `config/keys.local.json`.
3. Lancez l'application et utilisez la commande `key`.

`config/keys.local.json` est ignore par Git.

En option, vous pouvez creer localement `config/keys.json` (non versionne) comme fichier de secours. Ces fichiers sensibles sont listes dans `.gitignore`.

## Modele Ollama

Si tu as une ancienne version du modele, recree-le:

```powershell
ollama rm intel-code
ollama create intel-code -f Modelfile
```

## Donnees locales

L'application cree automatiquement le dossier `data/` pour stocker le cache, le quota, le tier actif, l'historique, les dernieres mesures tokens Ollama (fichier `data/cache/token_stats.json`) et les logs.

Ce dossier est ignore par Git.

## Structure

```text
INTEL-IA-LLMV1/
|-- main.py
|-- pyproject.toml
|-- requirements.txt
|-- Modelfile
|-- README.md
|-- tests/
|-- config/
|   |-- config.json
|   |-- limits.json
|   |-- prompts.json
|   |-- models.json
|   `-- keys.example.json
|-- scripts/
|   |-- setup.sh
|   |-- start.sh
|   |-- dev.sh
|   `-- update.sh
`-- src/
    |-- api/
    |-- checker/
    |-- core/
    |-- managers/
    `-- utils/
```

## Developpement

```bash
pip install -e ".[dev]"
python -m pytest tests/ -q
python -m compileall main.py src
./scripts/dev.sh
```

## Liens

- GitHub : [NasC0rp/INTEL-IA-LLMV1](https://github.com/NasC0rp/INTEL-IA-LLMV1)
- Telegram : [@IntelIA_NasCorp](https://t.me/IntelIA_NasCorp)

## Avertissement

Intel CODE execute un modele local via Ollama. L'utilisateur reste responsable de son usage, des prompts envoyes et des reponses generees.

## Bugs connus
- **Vitesse de generation lente** : Sur les machines a 3 coeurs / 6 Go RAM, la vitesse peut tomber a 1-2 tok/s, ce qui rend les reponses longues (~150-300s pour 256 tokens).
- **Prompts sensibles** : Certains sujets declenchent des refus silencieux du modele (reponse vide). Le retry automatique reformule le prompt, mais sans garantie.

