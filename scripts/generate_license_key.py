"""
Generateur de cle de licence (cote admin).

Usage (exemple):
  python scripts/generate_license_key.py --private-key config/license_private_key.pem --tier vip --exp 2026-12-31

La cle privee NE doit jamais etre commit.
"""

import argparse
import base64
import json

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey


def b64u(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--private-key", required=True, help="Chemin vers la cle privee Ed25519 (PEM)")
    p.add_argument("--tier", required=True, choices=["vip", "unlimited"])
    p.add_argument("--exp", required=False, help="Expiration YYYY-MM-DD (optionnel)")
    args = p.parse_args()

    with open(args.private_key, "rb") as f:
        priv = serialization.load_pem_private_key(f.read(), password=None)
    if not isinstance(priv, Ed25519PrivateKey):
        raise SystemExit("Cle privee invalide (attendu Ed25519).")

    payload = {"tier": args.tier}
    if args.exp:
        payload["exp"] = args.exp

    payload_bytes = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    sig = priv.sign(payload_bytes)

    print(f"LIC.{b64u(payload_bytes)}.{b64u(sig)}")


if __name__ == "__main__":
    main()

