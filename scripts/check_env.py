"""Check a developer machine for the FDE program: a ✅/❌ checklist with a fix for every ❌.

    python3.12 scripts/check_env.py      # works before the venv exists (standard library only)
    make check                           # the same, with the venv's python

Checks: Python 3.11+, an active virtual environment with the requirements installed,
git with a commit identity, the VS Code `code` command, a running Docker daemon,
a git-ignored .env, an NVIDIA API key (masked, never printed) and one live model call.
Exit code 0 only when every check passes.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MIN_PY = (3, 11)
COLOR = sys.stdout.isatty() and os.getenv("NO_COLOR") is None


def paint(s: str, code: str) -> str:
    return f"\033[{code}m{s}\033[0m" if COLOR else s


def run(cmd: list[str], timeout: float = 20) -> tuple[int, str]:
    """Run a command; return (exit code, first line of stdout). Missing command -> 127."""
    if shutil.which(cmd[0]) is None:
        return 127, ""
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, cwd=ROOT)
    except (OSError, subprocess.TimeoutExpired):
        return 1, ""
    lines = [ln for ln in p.stdout.splitlines() if ln.strip()]
    return p.returncode, lines[0].strip() if lines else ""


def read_env() -> dict[str, str]:
    """Values from .env (simple KEY=value lines); real environment variables win."""
    vals: dict[str, str] = {}
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                vals[k.strip()] = v.strip().strip('"').strip("'")
    for k in ("NVIDIA_API_KEY", "NVIDIA_BASE_URL", "CHAT_MODEL"):
        if os.getenv(k):
            vals[k] = os.environ[k]
    return vals


def mask(key: str) -> str:
    """Never show any of the secret part: only the public prefix and the length."""
    return f"nvapi-****…**** ({len(key)} chars)"


# Each check returns (ok, detail). detail is what we found, or how to fix it.
def check_python() -> tuple[bool, str]:
    v = sys.version_info
    found = f"{v.major}.{v.minor}.{v.micro}"
    if v[:2] >= MIN_PY:
        return True, f"{found} (need 3.11+)"
    return False, f"{found} is too old → install 3.12, then run with python3.12"


def check_venv() -> tuple[bool, str]:
    if sys.prefix == sys.base_prefix:
        return False, "not active → python3.12 -m venv .venv && source .venv/bin/activate"
    missing = []
    for mod in ("openai", "dotenv"):
        try:
            __import__(mod)
        except ImportError:
            missing.append(mod)
    name = Path(sys.prefix).name
    if missing:
        return False, f"{name} active, missing {', '.join(missing)} → pip install -r requirements.txt"
    return True, f"{name} active, requirements installed"


def check_git() -> tuple[bool, str]:
    code, ver = run(["git", "--version"])
    if code != 0:
        return False, "not installed → see README: Install git"
    ver = ver.replace("git version ", "").split(" ")[0]
    _, name = run(["git", "config", "user.name"])
    _, email = run(["git", "config", "user.email"])
    if not (name and email):
        return False, f"{ver}, no identity → git config --global user.name / user.email"
    return True, f"{ver}, commits as {name} <{email}>"


def check_code() -> tuple[bool, str]:
    code, ver = run(["code", "--version"])
    if code != 0 or not ver:
        return False, "`code` not on PATH → VS Code: Shell Command: Install 'code' command"
    return True, f"`code` {ver}"


def check_docker() -> tuple[bool, str]:
    if shutil.which("docker") is None:
        return False, "not installed → Docker Desktop (macOS, Windows) or Docker Engine (Linux)"
    code, server = run(["docker", "version", "--format", "{{.Server.Version}}"])
    if code != 0 or not server:
        return False, "daemon not running → start Docker Desktop (or: sudo systemctl start docker)"
    return True, f"engine {server}, daemon running"


def check_dotenv() -> tuple[bool, str]:
    if not (ROOT / ".env").exists():
        return False, "missing → cp .env.example .env, then paste your key"
    code, _ = run(["git", "check-ignore", "-q", ".env"])
    if code != 0:
        return False, "present but NOT git-ignored → add .env to .gitignore"
    return True, "present and git-ignored"


def check_key(vals: dict[str, str]) -> tuple[bool, str]:
    key = vals.get("NVIDIA_API_KEY", "")
    if not key:
        return False, "not set → paste it into .env (build.nvidia.com → Get API Key)"
    if not key.startswith("nvapi-") or "your-key" in key:
        return False, "still the placeholder → paste your real key into .env"
    return True, mask(key)


def check_live(vals: dict[str, str]) -> tuple[bool, str]:
    key = vals.get("NVIDIA_API_KEY", "")
    if not key.startswith("nvapi-") or "your-key" in key:
        return False, "skipped: no key yet"
    base = vals.get("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1").rstrip("/")
    model = vals.get("CHAT_MODEL", "openai/gpt-oss-20b")
    body = {"model": model, "messages": [{"role": "user", "content": "Reply with one word: ready"}], "max_tokens": 200}
    req = urllib.request.Request(f"{base}/chat/completions", data=json.dumps(body).encode(),
                                 headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            data = json.load(r)
    except urllib.error.HTTPError as e:
        hint = {401: "key rejected → create a new key", 403: "no access to this model", 429: "rate limited → wait, retry"}
        return False, f"HTTP {e.code} → {hint.get(e.code, 'see README: Troubleshooting')}"
    except (urllib.error.URLError, TimeoutError) as e:
        return False, f"no connection ({getattr(e, 'reason', e)}) → proxy or firewall? see README"
    if not data.get("choices"):
        return False, "unexpected reply → see README: Troubleshooting"
    return True, f"key valid, {model} answered in {time.perf_counter() - t0:.1f} s"


def main() -> int:
    vals = read_env()
    checks = [
        ("Python", check_python),
        ("Virtual env", check_venv),
        ("Git", check_git),
        ("VS Code", check_code),
        ("Docker", check_docker),
        (".env file", check_dotenv),
        ("NVIDIA key", lambda: check_key(vals)),
        ("NVIDIA API", lambda: check_live(vals)),
    ]
    print(paint("FDE starter · environment check", "1"))
    passed = 0
    for label, fn in checks:
        ok, detail = fn()
        passed += ok
        mark = "✅" if ok else "❌"
        print(f"  {mark} {label:<12} {paint(detail, '32' if ok else '33')}")
    total = len(checks)
    if passed == total:
        print(paint(f"{passed}/{total} checks passed. You're ready.", "1;32"))
        return 0
    print(paint(f"{passed}/{total} checks passed. Fix the ❌ lines and run again.", "1;33"))
    return 1


if __name__ == "__main__":
    sys.exit(main())
