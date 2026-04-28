import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from core.engine import IntelGPTEngine
from core.config_loader import ConfigLoader
from managers.logger import Logger

def main():
    logger = Logger("IntelCODE", logs_dir="data/logs")
    logger.info("INTEL CODE - Démarrage")
    
    try:
        config = ConfigLoader("config/config.json")
        config.validate()
        logger.info("Configuration chargée")
    except Exception as e:
        logger.error(f"Erreur configuration: {e}")
        print(f"\nErreur: {e}")
        sys.exit(1)
    
    try:
        engine = IntelGPTEngine(config, logger)
        engine.run()
    except KeyboardInterrupt:
        logger.info("Arrêt utilisateur")
    except Exception as e:
        logger.error(f"Erreur fatale: {e}")
        print(f"\nErreur: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()