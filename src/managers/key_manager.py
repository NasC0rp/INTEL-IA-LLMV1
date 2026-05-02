import json
import logging
import os
import base64
from typing import Dict, List, Optional

_log = logging.getLogger(__name__)


class KeyManager:
    def __init__(self, public_key_path: str = "config/license_public_key.pem") -> None:
        config_dir: str = os.path.join(os.path.dirname(__file__), '..', '..', 'config')
        self.keys_file: str = os.path.join(config_dir, 'keys.local.json')
        fallback_file: str = os.path.join(config_dir, 'keys.json')
        self.valid_keys: Dict[str, set] = {"vip": set(), "unlimited": set()}
        self.public_key_path: str = public_key_path
        keys_file: str = self.keys_file if os.path.exists(self.keys_file) else fallback_file
        if os.path.exists(keys_file):
            try:
                with open(keys_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for tier in data:
                        if tier in self.valid_keys:
                            self.valid_keys[tier] = set(data[tier])
            except (json.JSONDecodeError, IOError) as e:
                _log.warning("Impossible de lire les cles (%s): %s", keys_file, e)

    def _load_public_key(self) -> Optional[bytes]:
        # Import ici pour ne pas forcer la dep si l'utilisateur n'utilise pas les licences signees
        try:
            from cryptography.hazmat.primitives import serialization
        except Exception as e:
            _log.warning("cryptography indisponible: %s", e)
            return None
        try:
            with open(self.public_key_path, "rb") as f:
                raw = f.read()
            pub = serialization.load_pem_public_key(raw)
            # Ed25519 only
            return raw if pub is not None else None
        except OSError:
            return None
        except Exception as e:
            _log.warning("Cle publique invalide: %s", e)
            return None

    def _verify_signed_license(self, key: str) -> Optional[str]:
        """
        Format: LIC.<base64url(payload_json)>.<base64url(signature)>

        payload exemple:
        {"tier":"vip","exp":"2026-12-31","kid":"default"}
        """
        if not key.startswith("LIC."):
            return None

        parts = key.split(".")
        if len(parts) != 3:
            return None

        _, payload_b64, sig_b64 = parts
        try:
            payload_bytes = base64.urlsafe_b64decode(payload_b64 + "===")
            sig = base64.urlsafe_b64decode(sig_b64 + "===")
        except Exception:
            return None

        pub_pem = self._load_public_key()
        if not pub_pem:
            return None

        try:
            from cryptography.hazmat.primitives import serialization
            from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
        except Exception:
            return None

        try:
            pub = serialization.load_pem_public_key(pub_pem)
            if not isinstance(pub, Ed25519PublicKey):
                return None
            pub.verify(sig, payload_bytes)
        except Exception:
            return None

        try:
            payload = json.loads(payload_bytes.decode("utf-8"))
        except Exception:
            return None

        tier = payload.get("tier")
        if tier not in {"vip", "unlimited"}:
            return None

        exp = payload.get("exp")
        if exp:
            # date ISO YYYY-MM-DD
            try:
                from datetime import date
                y, m, d = [int(x) for x in exp.split("-")]
                if date.today() > date(y, m, d):
                    return None
            except Exception:
                return None

        return tier

    def validate_key(self, key: str) -> Optional[str]:
        tier = self._verify_signed_license(key)
        if tier:
            return tier
        if key in self.valid_keys["unlimited"]:
            return "unlimited"
        if key in self.valid_keys["vip"]:
            return "vip"
        return None

    def add_key(self, tier: str, key: str) -> bool:
        if tier in self.valid_keys:
            if key not in self.valid_keys[tier]:
                self.valid_keys[tier].add(key)
                self._save()
                return True
        return False

    def remove_key(self, key: str) -> bool:
        for tier in self.valid_keys:
            if key in self.valid_keys[tier]:
                self.valid_keys[tier].discard(key)
                self._save()
                return True
        return False

    def list_keys(self, tier: Optional[str] = None) -> Dict[str, List[str]]:
        if tier:
            return {tier: list(self.valid_keys.get(tier, set()))}
        return {t: list(keys) for t, keys in self.valid_keys.items()}

    def _save(self) -> None:
        try:
            os.makedirs(os.path.dirname(self.keys_file), exist_ok=True)
            with open(self.keys_file, "w", encoding="utf-8") as f:
                json.dump({t: list(keys) for t, keys in self.valid_keys.items()}, f, indent=2)
        except OSError as e:
            _log.warning("Impossible d'enregistrer les cles: %s", e)
