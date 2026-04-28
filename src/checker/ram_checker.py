import os

class RamChecker:
    def check(self):
        gb = None
        try:
            gb = (os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES")) / (1024**3)
        except:
            try:
                with open("/proc/meminfo") as f:
                    for line in f:
                        if "MemTotal" in line:
                            gb = int(line.split()[1]) / (1024**2)
                            break
            except:
                pass
        if gb is None:
            return True, "RAM: Inconnue"
        if gb >= 6:
            return True, f"RAM: {gb:.1f} Go - Optimal"
        elif gb >= 4:
            return True, f"RAM: {gb:.1f} Go - OK"
        return False, f"RAM: {gb:.1f} Go - Insuffisant"