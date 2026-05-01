import psutil


class RamChecker:
    def check(self):
        gb = psutil.virtual_memory().total / (1024 ** 3)
        if gb >= 6:
            return True, f"RAM: {gb:.1f} Go - Optimal"
        if gb >= 4:
            return True, f"RAM: {gb:.1f} Go - OK"
        return False, f"RAM: {gb:.1f} Go - Insuffisant"