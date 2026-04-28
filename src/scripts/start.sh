#!/bin/bash
# scripts/start.sh
set -e
clear
if ! pgrep -f "ollama serve" > /dev/null; then
    ollama serve > /dev/null 2>&1 &
    sleep 3
fi
if ! ollama list | grep -q "intel-gpt"; then
    ollama create intel-gpt -f Modelfile
fi
python3 main.py