# Intel CODE CX1.2

Assistant IA en ligne de commande, local, base sur Ollama.

![Version](https://img.shields.io/badge/version-CX1.2-red)
![License](https://img.shields.io/badge/license-MIT-darkred)
![Python](https://img.shields.io/badge/python-3.10+-black)

> Projet independant NasCorp, non affilie a Intel Corporation.

## Nouveautes CX1.2

- API `/api/chat` au lieu de `/api/generate` (reponses stables sans corruption)
- Streaming en temps reel (tokens affiches au fur et a mesure)
- Optimisation des ecritures disque (batch saves avec flush a la fermeture)
- Compatibilite Windows corrigee (RamChecker via psutil)
- Retry avec exponential backoff en cas d'erreur Ollama
- Prompt systeme ameliore avec instruction "reponds en francais uniquement"
- Parametres par defaut optimises (temperature 0.4, repeat_penalty 1.2)

## Fonctionnalites

- Assistant terminal local via Ollama
- Streaming en temps reel des reponses
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

## Limites par tier

| Tier | num_ctx | num_predict |
|------|---------|-------------|
| Free | 2048 | 256 |
| VIP | 8048 | 2024 |
| Unlimited | 9096 | 4024 |

## Renouvellement quota et tokens

Le quota de messages se renouvelle automatiquement selon la fenetre du tier actif:

- Free: 30 messages toutes les 12 heures
- VIP: 50 messages toutes les 12 heures
- Unlimited: 999 messages toutes les 1 heure

La fenetre commence au premier message compte dans le cycle courant. Exemple: si le quota Free commence a 14h00, les messages se renouvellent a 02h00.

La limite de tokens n'est pas un quota qui se renouvelle. C'est une limite par reponse: si une reponse atteint la limite de tokens, elle s'arrete, mais l'utilisateur peut envoyer un autre message tant qu'il lui reste du quota messages.

## Configuration des cles

Les cles sensibles ne doivent pas etre commitees.

1. Copiez `config/keys.example.json` vers `config/keys.local.json`.
2. Ajoutez vos cles dans `config/keys.local.json`.
3. Lancez l'application et utilisez la commande `key`.

`config/keys.local.json` est ignore par Git.

## Recree le modele Ollama

Si tu as une ancienne version du modele, recree-le:

```powershell
ollama rm intel-code
ollama create intel-code -f Modelfile
```

## Structure

```text
INTEL-IA-LLMV1/
|-- main.py
|-- requirements.txt
|-- Modelfile
|-- README.md
|-- config/
|   |-- config.json
|   |-- limits.json
|   |-- prompts.json
|   |-- models.json
|   |-- keys.json
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

## Bugs connus

- **Modele 4B instable** : Le modele `huihui_ai/qwen3-abliterated:4b` est leger et peut produire des reponses vides ou incoherentes sur des sujets sensibles (reverse shell, etc.). C'est un comportement du modele, pas de l'app.
- **Vitesse de generation lente** : Sur les machines a 3 coeurs / 6 Go RAM, la vitesse peut tomber a 1-2 tok/s, ce qui rend les reponses longues (~150-300s pour 256 tokens).
- **Prompts sensibles** : Certains sujets declenchent des refus silencieux du modele (reponse vide). Le retry automatique reformule le prompt, mais sans garantie.

Pour ameliorer la qualite, utilise un modele plus robuste :
```powershell
ollama pull dolphin3-mistral:7b
```
Puis change `"model": "intel-code"` vers `"model": "dolphin3-mistral:7b"` dans `config/config.json`.
