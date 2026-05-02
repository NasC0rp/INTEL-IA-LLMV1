"""Point d'entrée commun pour `python main.py` et `python -m src`."""

import logging
import sys

from src.core.config_loader import ConfigLoader
from src.core.engine import IntelGPTEngine
from src.managers.logger import Logger


def main() -> None:
    logging.basicConfig(level=logging.WARNING, format="[%(levelname)s] %(message)s")
    logger: Logger = Logger("IntelCODE", logs_dir="data/logs")
    logger.info("INTEL CODE - Demarrage")

    try:
        config: ConfigLoader = ConfigLoader("config/config.json")
        config.validate()
        logger.info("Configuration chargee")
    except (FileNotFoundError, ValueError) as e:
        logger.error(f"Erreur configuration: {e}")
        print(f"\nErreur: {e}")
        sys.exit(1)

    try:
        engine: IntelGPTEngine = IntelGPTEngine(config, logger)
        engine.run()
    except KeyboardInterrupt:
        logger.info("Arret utilisateur")
    except Exception as e:
        logger.error(f"Erreur fatale: {e}")
        print(f"\nErreur: {e}")
        sys.exit(1)
