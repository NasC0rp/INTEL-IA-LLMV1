# Intel CODE

Assistant IA en ligne de commande, local, base sur Ollama.

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
Intel CODE [free] > votre question ici
```

## Commandes

| Commande | Description |
|----------|-------------|
| help | Affiche l'aide |
| mode | Change de mode |
| quota | Affiche les messages restants |
| cache | Affiche la taille du cache |
| history | Affiche les derniers echanges |
| models | Liste les modeles Ollama disponibles |
| key | Active une cle VIP ou Unlimited |
| tier | Affiche le tier actuel |
| tokens | Affiche l'utilisation de tokens de la derniere reponse |
| clear | Efface l'ecran |
| exit | Quitte l'assistant |

## Configuration des cles

Les cles sensibles ne doivent pas etre commitees.

1. Copiez `config/keys.example.json` vers `config/keys.local.json`.
2. Ajoutez vos cles dans `config/keys.local.json`.
3. Lancez l'application et utilisez la commande `key`.

`config/keys.local.json` est ignore par Git.

## Fichiers importants

```text
main.py                  Point d'entree
config/config.json       Configuration Ollama et systeme
config/limits.json       Definition des tiers
config/prompts.json      Prompts systeme des modes
config/keys.example.json Exemple de fichier de cles
src/core/engine.py       Boucle principale
src/api/ollama_client.py Client Ollama
src/managers/            Cache, quota, historique, sessions, cles
scripts/setup.sh         Installation Linux / WSL2
scripts/start.sh         Demarrage
```

## Donnees locales

L'application cree automatiquement le dossier `data/` pour stocker:

- cache des reponses
- quota local
- tier actif
- historique
- logs

Ce dossier est ignore par Git.

## Developpement

```bash
python -m compileall main.py src
./scripts/dev.sh
```

## Avertissement

Intel CODE execute un modele local via Ollama. L'utilisateur reste responsable de son usage, des prompts envoyes et des reponses generees.
