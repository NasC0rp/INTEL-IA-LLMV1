import os
import platform


class CpuChecker:
    def check(self):
        cores = os.cpu_count()
        if cores is None:
            return True, "CPU: Inconnu"
        arch = platform.processor() or platform.machine()
        if cores >= 3:
            return True, f"CPU: {cores} coeurs ({arch}) - Optimal"
        if cores >= 2:
            return True, f"CPU: {cores} coeurs ({arch}) - OK"
        return False, f"CPU: {cores} coeurs - Insuffisant"
