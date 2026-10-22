"""Subscriber registry: issue-form opt-in, encrypted at rest (AES-256-CBC via openssl).

Privacy hard rules (repo 红线):
- data/subscribers.enc never contains plaintext; key only in repo secret SUBSCRIBER_KEY.
- issue titles/bodies are auto-redacted by the subscribe workflow right after parsing.
"""
import os
import re
import subprocess
import sys
from pathlib import Path

ENC_PATH = Path(__file__).resolve().parent.parent / "data" / "subscribers.enc"
EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")


def _key() -> str:
    key = os.environ.get("SUBSCRIBER_KEY")
    if not key:
        print("SUBSCRIBER_KEY missing", file=sys.stderr)
        sys.exit(2)
    return key


def _openssl(args: list[str], input_bytes: bytes) -> bytes:
    env = dict(os.environ, SK=_key())
    r = subprocess.run(["openssl"] + args, input=input_bytes, capture_output=True, env=env, check=True)
    return r.stdout


def _decrypt() -> list[tuple[str, str]]:
    if not os.path.exists(ENC_PATH):
        return []
    blob = ENC_PATH.read_bytes()
    if not blob.strip():
        return []
    text = _openssl(["enc", "-d", "-aes-256-cbc", "-pbkdf2", "-pass", "env:SK"], blob).decode("utf-8")
    out = []
    for line in text.splitlines():
        line = line.strip()
        if "," in line and EMAIL_RE.match(line.split(",")[0]):
            email, freq = line.split(",", 1)
            out.append((email.lower(), freq if freq in ("daily", "weekly") else "weekly"))
    return out


def _encrypt(pairs: list[tuple[str, str]]) -> None:
    text = "\n".join(f"{e},{f}" for e, f in pairs) + "\n"
    blob = _openssl(["enc", "-aes-256-cbc", "-pbkdf2", "-pass", "env:SK"], text.encode("utf-8"))
    ENC_PATH.write_bytes(blob)


def add(email: str, freq: str) -> str:
    email = email.strip().lower()
    if not EMAIL_RE.match(email):
        return "invalid"
    freq = freq if freq in ("daily", "weekly") else "weekly"
    pairs = _decrypt()
    for i, (e, f) in enumerate(pairs):
        if e == email:
            if f == freq:
                return "exists"
            pairs[i] = (email, freq)
            _encrypt(pairs)
            return f"updated:{freq}"
    pairs.append((email, freq))
    _encrypt(pairs)
    return f"subscribed:{freq}"


def remove(email: str) -> str:
    email = email.strip().lower()
    before = _decrypt()
    pairs = [p for p in before if p[0] != email]
    if len(pairs) == len(before):
        return "not_found"
    _encrypt(pairs)
    return "removed"


def sendable(today=None) -> list[tuple[str, str]]:
    """Weekly job: 直发全体名单（freq 字段保留，未来加 daily 细分）。"""
    return _decrypt()
