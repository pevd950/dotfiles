#!/usr/bin/env python3
"""Build <repo>/.env.op from <repo>/.env: op:// references for credentials, literals for config.
Values never leave this process; only variable names and references are printed.

Usage: build-env-op.py --repo PATH --project SLUG --vault "Project Dev" [--vault "Agent Tools Dev" ...]
                       [--secret NAME ...] [--config NAME ...] [--env-file .env] [--out .env.op]
Credential detection: names matching KEY|SECRET|TOKEN|PASSWORD|PASSWD|PRIVATE|CREDENTIAL|DSN|_URL with user:pass@,
plus any --secret names; --config names are forced literal.
"""
import argparse, hashlib, json, os, re, subprocess, sys, datetime

ap = argparse.ArgumentParser()
ap.add_argument("--repo", required=True); ap.add_argument("--project", required=True)
ap.add_argument("--vault", action="append", required=True, help="first vault is where new items are created")
ap.add_argument("--secret", action="append", default=[]); ap.add_argument("--config", action="append", default=[])
ap.add_argument("--env-file", default=".env"); ap.add_argument("--out", default=".env.op")
ap.add_argument("--dry-run", action="store_true", help="do not create items or write files")
a = ap.parse_args()
repo = os.path.expanduser(a.repo); env_path = os.path.join(repo, a.env_file); out_path = os.path.join(repo, a.out)
create_vault = a.vault[0]
SECRET_RE = re.compile(r"(KEY|SECRET|TOKEN|PASSWORD|PASSWD|PRIVATE|CREDENTIAL|DSN)", re.I)

def op(*args):
    r = subprocess.run(["op", *args], capture_output=True, text=True, stdin=subprocess.DEVNULL)
    if r.returncode: sys.exit("op failed: " + r.stderr.strip()[:160])
    return r.stdout
def h(v): return hashlib.sha256(v.encode()).hexdigest()[:16]
def is_secret(name, value):
    if name in a.config: return False
    if name in a.secret or SECRET_RE.search(name): return True
    return bool(re.match(r"^[a-z][a-z0-9+.-]*://[^/@\s]+:[^/@\s]+@", value))  # DSN with credentials

order, vals = [], {}
for line in open(env_path):
    s = line.strip()
    if not s or s.startswith("#") or "=" not in s: continue
    k, v = s.split("=", 1); v = v.strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'": v = v[1:-1]
    if k not in vals: order.append(k)
    vals[k] = v

index = {}
for vault in a.vault:
    for it in json.loads(op("item", "list", "--vault", vault, "--format", "json")):
        if it["category"] not in ("API_CREDENTIAL", "PASSWORD", "LOGIN", "DATABASE"): continue
        full = json.loads(op("item", "get", it["id"], "--vault", vault, "--format", "json"))
        for f in full.get("fields", []):
            v = f.get("value"); lab = f.get("label") or f.get("id")
            if not v or "\n" in v or len(v) < 4 or f.get("purpose") == "NOTES": continue
            sec = f["section"]["label"] if f.get("section") and f["section"].get("label") else None
            index.setdefault(h(v), f"op://{vault}/{full['title']}/{sec + '/' if sec else ''}{lab}")

refs, created = {}, []
for k in order:
    if is_secret(k, vals[k]) and vals[k]:
        hit = index.get(h(vals[k]))
        if hit: refs[k] = hit
for k in order:
    if is_secret(k, vals[k]) and vals[k] and k not in refs:
        title = f"{a.project} local {k}"
        if not a.dry_run:
            op("item", "create", "--category", "API Credential", "--vault", create_vault, "--title", title,
               "--tags", f"project:{a.project},env:local", f"credential={vals[k]}",
               f"notesPlain=Local-dev value of {k} imported from {a.env_file} on {datetime.date.today()} by onepassword-project-setup.")
        refs[k] = f"op://{create_vault}/{title}/credential"; created.append(title)

lines = [f"# {a.project} local environment, 1Password reference edition. Generated {datetime.date.today()} from {a.env_file}.",
         "# Usage: op run --env-file .env.op -- <command>   (OP_SERVICE_ACCOUNT_TOKEN from .envrc, or desktop-app auth)",
         "# Credentials are op:// references; non-secret config is literal. No secret values live in this file.", ""]
for k in order:
    lines.append(f'{k}="{refs[k]}"' if k in refs else f"{k}={vals[k]}")
if not a.dry_run:
    open(out_path, "w").write("\n".join(lines) + "\n"); os.chmod(out_path, 0o600)
    excl = os.path.join(repo, ".git", "info", "exclude")
    if os.path.isdir(os.path.dirname(excl)):
        have = open(excl).read().splitlines() if os.path.exists(excl) else []
        with open(excl, "a") as fh:
            for p in (a.out, ".envrc"):
                if p not in have: fh.write(p + "\n")
print(("DRY RUN: " if a.dry_run else "") + f"{out_path}: {len(refs)} references, {len(order) - len(refs)} literals")
for k in order: print(f"  {k:34s} {refs[k] if k in refs else '(literal)'}")
if created: print("created items:", created)
