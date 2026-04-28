import shutil
import os

class DiskChecker:
    def check(self):
        gb = None
        for path in [os.path.expanduser("~"), "/", "."]:
            try:
                gb = shutil.disk_usage(path).free / (1024**3)
                break
            except:
                continue
        if gb is None:
            return True, "Disque: Inconnu"
        if gb >= 10:
            return True, f"Disque: {gb:.1f} Go libres - OK"
        return False, f"Disque: {gb:.1f} Go libres - Insuffisant"