#!/usr/bin/env python3
"""Match the secret-looking variables a shell env file exports to the 1Password items that already hold
the same value. Prints names, item references and NO 1PASSWORD ITEM; values never leave this process.

Usage: match-env-to-items.py [ENV_FILE] [--vault NAME ...]
  ENV_FILE defaults to ~/.zshenv.local; --vault limits the search (default: every vault you can read).
Matches are exact (SHA-256 of the value); a stale or rotated value shows as NO 1PASSWORD ITEM.
"""
import argparse, hashlib, json, os, re, subprocess, sys

SECRET = re.compile(r"(KEY|TOKEN|SECRET|PASSWORD|PASSWD|CREDENTIAL|DSN|CLIENT_ID)$")
ap = argparse.ArgumentParser()
ap.add_argument("env_file", nargs="?", default=os.path.expanduser("~/.zshenv.local"))
ap.add_argument("--vault", action="append")
a = ap.parse_args()

def op(*args):
    r = subprocess.run(["op", *args], capture_output=True, text=True, stdin=subprocess.DEVNULL)
    if r.returncode: sys.exit("op failed: " + r.stderr.strip()[:160])
    return json.loads(r.stdout or "null")

# Evaluate the file in a clean bash so command substitutions and quoting resolve as the shell would.
r = subprocess.run(["env", "-i", "HOME=" + os.environ["HOME"], "PATH=/usr/bin:/bin", "ENV_FILE=" + a.env_file,
                    "bash", "-c", 'set -a; . "$ENV_FILE" >/dev/null 2>&1; env -0'], capture_output=True)
env = dict(kv.split("=", 1) for kv in r.stdout.decode(errors="replace").split("\0") if "=" in kv)
names = sorted(n for n in env if SECRET.search(n) and env[n])
digest = lambda v: hashlib.sha256(v.encode()).hexdigest()
wanted = {}
for n in names: wanted.setdefault(digest(env[n]), []).append(n)
hits = {n: [] for n in names}
vaults = a.vault or [v["name"] for v in op("vault", "list", "--format", "json")]
for vault in vaults:
    for item in op("item", "list", "--vault", vault, "--format", "json") or []:
        if item["category"] in ("DOCUMENT", "SSH_KEY"): continue
        full = op("item", "get", item["id"], "--vault", vault, "--format", "json")
        for f in full.get("fields", []):
            v = f.get("value")
            if isinstance(v, str) and v and digest(v) in wanted:
                for n in wanted[digest(v)]:
                    hits[n].append(f'op://{vault}/{item["id"]}/{f.get("label") or f["id"]}  # {full["title"]}')
for n in names:
    print(f"{n}=" + (hits[n][0] if hits[n] else "NO 1PASSWORD ITEM") + (f"  (+{len(hits[n]) - 1} more)" if len(hits[n]) > 1 else ""))
