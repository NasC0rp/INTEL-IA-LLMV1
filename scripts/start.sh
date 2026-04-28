#!/bin/bash
# scripts/start.sh
set -e
clear
if ! pgrep -f "ollama serve" > /dev/null; then
    ollama serve > /dev/null 2>&1 &
    sleep 3
fi
if ! ollama list | grep -q "intel-code"; then
    ollama create intel-code -f Modelfile
fi
python3 main.py