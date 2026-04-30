import requests
import os

class Updater:
    def __init__(self, config):
        self.github_repo = config.get("github.repo", "")
        self.github_branch = config.get("github.branch", "main")
        self.current_version = self._get_local()
        self.latest_version = None
        self.update_available = False

    def _get_local(self):
        vf = os.path.join(os.path.dirname(__file__), '..', '..', '.version')
        if os.path.exists(vf):
            with open(vf, 'r') as f:
                return f.read().strip()
        return "0.0.0"

    def check(self):
        try:
            url = f"https://raw.githubusercontent.com/{self.github_repo}/{self.github_branch}/.version"
            r = requests.get(url, timeout=3)
            if r.status_code == 200:
                self.latest_version = r.text.strip()
                if self._cmp(self.current_version, self.latest_version) < 0:
                    self.update_available = True
        except:
            pass

    def _cmp(self, v1, v2):
        try:
            p1 = [int(x) for x in v1.split(".")]
            p2 = [int(x) for x in v2.split(".")]
            for i in range(max(len(p1), len(p2))):
                a = p1[i] if i < len(p1) else 0
                b = p2[i] if i < len(p2) else 0
                if a < b: return -1
                if a > b: return 1
            return 0
        except:
            return 0

    def get_update_command(self):
        return f"git pull origin {self.github_branch}"