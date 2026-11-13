#!/usr/bin/env python3
"""Commonhold signed records: the reference check (spec/records.md), in plain Python.

    python tools/records.py verify spec/vectors/records/mesh-vector.json

The rules every implementation follows (Leyline's launcher and host kit do today):
  * canonical JSON: sorted keys, no spaces, UTF-8 (not ASCII-escaped);
  * signature: Ed25519 over  context + "\\n" + canonical(document), hex encoded;
  * id of a key: base32(sha256(public key)), lower case, first 16 characters.
Needs the `cryptography` package.
"""
from __future__ import annotations

import base64
import hashlib
import json
import sys

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.hazmat.primitives import serialization

CONTEXTS = {
    "realm": "wu-listing-heartbeat-v1",
    "endpoint": "leyline-mesh-endpoint-v1",
    "relay": "leyline-mesh-node-v1",
    "block": "leyline-mesh-block-v1",
    "profile": "leyline-profile-v1",
    "friendship": "leyline-friendship-v1",
}


def canonical(doc) -> bytes:
    return json.dumps(doc, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def key_id(public: bytes) -> str:
    return base64.b32encode(hashlib.sha256(public).digest()).decode().lower()[:16]


def sign(seed: bytes, doc: dict, context: str) -> str:
    return Ed25519PrivateKey.from_private_bytes(seed).sign(context.encode() + b"\n" + canonical(doc)).hex()


def public_of(seed: bytes) -> bytes:
    return Ed25519PrivateKey.from_private_bytes(seed).public_key().public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw)


def verify(public_hex: str, doc: dict, context: str, sig_hex: str) -> bool:
    try:
        Ed25519PublicKey.from_public_bytes(bytes.fromhex(public_hex)).verify(
            bytes.fromhex(sig_hex), context.encode() + b"\n" + canonical(doc))
        return True
    except (InvalidSignature, ValueError, TypeError):
        return False


def check_record(rec: dict) -> list[str]:
    """Problems with one network record (empty: it checks out)."""
    kind, out = rec.get("kind"), []
    if kind == "realm":
        b = rec.get("beat", {})
        if not verify(b.get("pubkey", ""), b, CONTEXTS["realm"], rec.get("sig", "")):
            out.append("realm: bad signature")
        if b.get("pubkey") and key_id(bytes.fromhex(b["pubkey"])) != b.get("realm_id"):
            out.append("realm: realm_id isn't its key's id")
        for e in rec.get("endpoints", []):
            att = e.get("att", {})
            if not verify(att.get("node", ""), att, CONTEXTS["endpoint"], e.get("sig", "")):
                out.append("endpoint: bad signature")
    elif kind == "relay":
        n = rec.get("node", {})
        if not verify(n.get("pubkey", ""), n, CONTEXTS["relay"], rec.get("sig", "")):
            out.append("relay: bad signature")
    else:
        out.append(f"unknown kind {kind!r}")
    return out


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    if len(argv) != 2 or argv[0] != "verify":
        print(__doc__)
        return 2
    recs = json.load(open(argv[1], encoding="utf-8"))["records"]
    bad = 0
    for i, r in enumerate(recs):
        p = check_record(r)
        print(f"{i}: {r.get('kind')}: " + ("OK" if not p else "; ".join(p)))
        bad += bool(p)
    print("ALL OK" if not bad else f"{bad} record(s) failed")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
