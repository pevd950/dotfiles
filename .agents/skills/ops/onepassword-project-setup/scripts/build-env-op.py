#!/usr/bin/env python3
"""Build <repo>/.env.op from <repo>/.env: op:// references for credentials, literals for config.
Values never leave this process; only variable names and references are printed.

Usage: build-env-op.py --repo PATH --project SLUG --vault "Project Dev" [--vault "Agent Tools Dev" ...]
                       [--secret NAME ...] [--config NAME ...] [--env-file .env] [--out .env.op]
Credential detection: names matching KEY|SECRET|TOKEN|PASSWORD|PASSWD|PRIVATE|CREDENTIAL|DSN, or any URL carrying a password,
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
    return bool(re.match(r"^[a-z][a-z0-9+.-]*://[^/@\s]*:[^/@\s]+@", value))  # URL with a password, username may be empty

# Quoted literals, optional inline comment after the closing quote, may span lines. Double quotes allow
# backslash escapes (\" \\ \n \r \t \$), single quotes are verbatim: the same rules dotenv loaders apply.
DQ_RE = re.compile(r'^"((?:[^"\\]|\\.)*)"[ \t]*(#.*)?$', re.S)
SQ_RE = re.compile(r"^'([^']*)'[ \t]*(#.*)?$", re.S)
DQ_ESCAPES = {"n": "\n", "r": "\r", "t": "\t"}
def quoted_match(raw): return DQ_RE.match(raw) if raw[:1] == '"' else SQ_RE.match(raw) if raw[:1] == "'" else None

def parse_dotenv_value(raw):
    """Return the value a dotenv loader would see: quoted literals with their quotes removed and, for double
    quotes, escapes decoded (newlines kept); unquoted values cut at the first ' #' inline comment and trimmed."""
    raw = raw.strip()
    q = quoted_match(raw)
    if q:
        body = q.group(1)
        # Only the supported escapes decode; any other backslash sequence is kept as written.
        return re.sub(r'\\(["\\nrt$])', lambda m: DQ_ESCAPES.get(m.group(1), m.group(1)), body) if raw[0] == '"' else body
    m = re.match(r"^(.*?)(\s+#.*)?$", raw)
    return m.group(1).strip()

def read_dotenv(path):
    """Yield (name, raw_value) per assignment. A quoted value that does not close on its line continues
    on the following lines until the closing quote, so multiline keys and certificates stay whole."""
    lines = open(path).read().split("\n"); i = 0
    while i < len(lines):
        s = lines[i].strip(); i += 1
        if not s or s.startswith("#") or "=" not in s: continue
        if s.startswith("export "): s = s[7:]
        k, v = s.split("=", 1); k, v = k.strip(), v.strip()
        if v[:1] in ("\"", "'") and not quoted_match(v):
            while i < len(lines) and not quoted_match(v):
                v += "\n" + lines[i].rstrip("\r"); i += 1
            if not quoted_match(v): sys.exit(f"{path}: unterminated quoted value for {k}")
        yield k, v

order, vals, raw = [], {}, {}
for k, v in read_dotenv(env_path):
    if k not in vals: order.append(k)
    raw[k] = v; vals[k] = parse_dotenv_value(v)

index = {}
for vault in a.vault:
    for it in json.loads(op("item", "list", "--vault", vault, "--format", "json")):
        if it["category"] in ("DOCUMENT", "SSH_KEY", "SECURE_NOTE", "SOFTWARE_LICENSE", "IDENTITY", "CREDIT_CARD"): continue
        # Every other category (API Credential, Login, Password, Database, Server, custom...) may hold a credential field.
        full = json.loads(op("item", "get", it["id"], "--vault", vault, "--format", "json"))
        for f in full.get("fields", []):
            v = f.get("value"); lab = f.get("label") or f.get("id")
            if not v or "\n" in v or len(v) < 4 or f.get("purpose") == "NOTES" or f.get("type") not in ("CONCEALED", "STRING", "URL"): continue
            # Prefer the reference the CLI supplies; it uses IDs where a title, section or label
            # contains characters a secret reference cannot carry. Skip fields with neither.
            ref = f.get("reference")
            if not ref:
                sec = f["section"]["label"] if f.get("section") and f["section"].get("label") else None
                parts = [vault, full["title"], sec, lab]
                if any(part and re.search(r"[/()\[\]{}·]", part) for part in parts): continue
                ref = f"op://{vault}/{full['title']}/{sec + '/' if sec else ''}{lab}"
            index.setdefault(h(v), ref)

refs, created = {}, []
for k in order:
    if is_secret(k, vals[k]) and vals[k]:
        hit = index.get(h(vals[k]))
        if hit: refs[k] = hit
for k in order:
    if is_secret(k, vals[k]) and vals[k] and k not in refs:
        title = f"{a.project} local {k}"
        if not a.dry_run:
            # JSON on stdin keeps the value out of process arguments (visible to other processes via ps).
            item = {"title": title, "category": "API_CREDENTIAL", "tags": [f"project:{a.project}", "env:local"], "fields": [
                {"id": "credential", "type": "CONCEALED", "label": "credential", "value": vals[k]},
                {"id": "notesPlain", "type": "STRING", "purpose": "NOTES", "label": "notesPlain",
                 "value": f"Local-dev value of {k} imported from {a.env_file} on {datetime.date.today()} by onepassword-project-setup."}]}
            r = subprocess.run(["op", "item", "create", "-", "--vault", create_vault], input=json.dumps(item), capture_output=True, text=True)
            if r.returncode: sys.exit("op item create failed: " + r.stderr.strip()[:160])
        refs[k] = f"op://{create_vault}/{title}/credential"; created.append(title)

lines = [f"# {a.project} local environment, 1Password reference edition. Generated {datetime.date.today()} from {a.env_file}.",
         "# Usage: op run --env-file .env.op -- <command>   (OP_SERVICE_ACCOUNT_TOKEN from .envrc, or desktop-app auth)",
         "# Credentials are op:// references; non-secret config is literal. No secret values live in this file.", ""]
for k in order:
    lines.append(f'{k}="{refs[k]}"' if k in refs else f"{k}={raw[k]}")  # literals keep their original quoting and comments
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
