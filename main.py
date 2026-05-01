import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from core.config_loader import ConfigLoader
from core.engine import IntelGPTEngine
from managers.logger import Logger


def main() -> None:
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


if __name__ == "__main__":
    main()
