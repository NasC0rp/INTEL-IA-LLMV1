#!/bin/bash
# scripts/setup.sh
set -e

echo "=== INTEL CODE - Installation ==="

sudo apt update && sudo apt install -y python3 python3-pip
python3 -m pip install -r requirements.txt

if ! command -v ollama &> /dev/null; then
    curl -fsSL https://ollama.com/install.sh | sh
fi

ollama serve > /dev/null 2>&1 &
sleep 3

ollama pull huihui_ai/qwen3-abliterated:4b
ollama create intel-code -f Modelfile

echo "=== Installation terminee ==="
