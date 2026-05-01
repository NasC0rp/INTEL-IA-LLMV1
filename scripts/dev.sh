#!/bin/bash
# scripts/dev.sh
set -e

ollama serve > /dev/null 2>&1 &
sleep 2

python3 -c "
from src.core.config_loader import ConfigLoader
from src.checker.system_checker import SystemChecker

c = ConfigLoader('config/config.json')
s = SystemChecker(c)
ok, r = s.check_all()

for status, msg in r:
    print(f'  [{\"OK\" if status else \"KO\"}] {msg}')
"
