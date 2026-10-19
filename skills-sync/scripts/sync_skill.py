#!/usr/bin/env python3
"""sync_skill.py - publish Claude Code skills to a Git repository (one folder per skill).

Direction is local -> repo. Safety nets, in order:
  1. validation   SKILL.md exists, has a description, `name` matches the folder
  2. secret scan  blocks tokens / private keys / .env-like files before anything is copied
  3. 3-way check  never silently overwrites a newer version that exists in the repo
  4. lock         two Claude sessions cannot run git in the clone at the same time
  5. no prompts   git can never hang waiting for a password (fails with a hint instead)

Exit codes: 0 ok | 1 error | 2 blocked (findings / diverged / repo ahead / needs review)
            3 committed locally but push failed (it will be retried on the next run)
Standard library only.
"""
from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

try:  # POSIX only; on Windows the lock is skipped
    import fcntl
except ImportError:  # pragma: no cover
    fcntl = None

DEFAULTS = {
    "repo_url": "git@github.com:vuillaut/skills.git",
    "repo_dir": None,                      # None -> <state_dir>/repo
    "source_dirs": ["~/.claude/skills"],   # relative entries (e.g. ".claude/skills") resolve against cwd
    "exclude_skills": [],                  # skill names that must never be published
    "extra_deny_patterns": [],             # extra regexes that BLOCK a publish (e.g. internal hostnames)
    "readme_index": False,                 # maintain a skills table in the repo README
    "max_file_mb": 5,
    "push": True,
}

IGNORE_NAMES = [".git", "__pycache__", "*.pyc", ".DS_Store", "node_modules", ".venv", "venv",
                "*-workspace", ".pytest_cache", ".mypy_cache", "*.swp", "*.skill"]

SENSITIVE_FILES = [".env", ".env.*", "*.pem", "*.key", "*.p12", "*.pfx", "id_rsa*", "id_ed25519*",
                   "id_ecdsa*", ".netrc", ".npmrc", ".pypirc", "credentials.json", "*.kdbx"]
ENV_TEMPLATE_SUFFIXES = (".example", ".sample", ".template", ".dist")

SECRET_RX = [
    ("private key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("AWS access key", re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b")),
    ("GitHub token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}\b")),
    ("GitHub fine-grained token", re.compile(r"\bgithub_pat_[A-Za-z0-9_]{22,}\b")),
    ("Slack token", re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}\b")),
    ("Anthropic API key", re.compile(r"\bsk-ant-[A-Za-z0-9_-]{20,}\b")),
    ("OpenAI-style API key", re.compile(r"\bsk-[A-Za-z0-9]{32,}\b")),
    ("Google API key", re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b")),
    ("JWT", re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}")),
    ("URL with embedded credentials", re.compile(r"[a-z][a-z0-9+.-]*://[^/\s:@]+:[^/\s:@]{3,}@[^/\s]+", re.I)),
    ("hard-coded secret", re.compile(
        r"""\b[\w-]*(?:api[_-]?key|secret|token|passwd|password)\b\s*[:=]\s*['"](?P<val>[^'"\s]{12,})['"]""", re.I)),
]
PLACEHOLDER_RX = re.compile(r"^(<.*>|\$\{?\w+\}?|\{\{.*\}\}|x{3,}.*|\*{3,}.*)$|your|example|placeholder|changeme|dummy|redacted",
                            re.I)
HOME_RX = re.compile(r"(?:/home/[A-Za-z_][\w.-]*/|/Users/[\w.-]+/|[A-Za-z]:\\Users\\)")
SAFE_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")

INDEX_START = "<!-- skills-index:start -->"
INDEX_END = "<!-- skills-index:end -->"


class SyncError(Exception):
    pass


# --------------------------------------------------------------------------- paths / config
def state_dir() -> Path:
    return Path(os.environ.get("SKILLS_SYNC_HOME", "~/.claude/skills-sync")).expanduser()


def config_path() -> Path:
    return Path(os.environ.get("SKILLS_SYNC_CONFIG", "~/.claude/skills-sync.json")).expanduser()


def load_config() -> dict:
    cfg = dict(DEFAULTS)
    p = config_path()
    if p.exists():
        try:
            user = json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            raise SyncError(f"invalid JSON in {p}: {e}")
        unknown = set(user) - set(DEFAULTS)
        if unknown:  # a typo like "exclude_skill" would silently disable a safety net
            raise SyncError(f"unknown key(s) in {p}: {sorted(unknown)}; allowed: {sorted(DEFAULTS)}")
        cfg.update(user)
    return cfg


def source_roots(cfg: dict, cwd: str | None = None) -> list[Path]:
    base = Path(cwd or os.getcwd())
    roots = []
    for s in cfg["source_dirs"]:
        p = Path(s).expanduser()
        roots.append(p if p.is_absolute() else base / p)
    return roots


def skill_name_for_path(path: str, cfg: dict, cwd: str | None = None):
    """Map any file/dir path inside a source root to (skill_name, root), else None."""
    p = Path(path).expanduser()
    if not p.is_absolute():
        p = Path(cwd or os.getcwd()) / p
    for root in source_roots(cfg, cwd):
        for cand, base in ((p, root), (p.resolve(), root.resolve())):
            try:
                rel = cand.relative_to(base)
            except ValueError:
                continue
            if rel.parts:
                return rel.parts[0], root
    return None


def find_skill(arg: str, cfg: dict, cwd: str | None = None):
    """Resolve a skill name or a path to (name, source_dir)."""
    hit = None
    if os.sep in arg or arg.startswith(("~", ".")) or Path(arg).expanduser().exists():
        hit = skill_name_for_path(arg, cfg, cwd)
    if hit:
        name, root = hit
        return name, root / name
    for root in source_roots(cfg, cwd):
        if (root / arg / "SKILL.md").is_file():
            return arg, root / arg
    return arg, None


# --------------------------------------------------------------------------- tree hashing
def _ignored(name: str) -> bool:
    return any(fnmatch.fnmatch(name, pat) for pat in IGNORE_NAMES)


def snapshot(root: Path) -> dict:
    """{relpath: ("file", sha256, is_exec) | ("link", target)} honouring IGNORE_NAMES."""
    entries: dict = {}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if not _ignored(d))
        here = Path(dirpath)
        for d in list(dirnames):
            if (here / d).is_symlink():
                entries[(here / d).relative_to(root).as_posix()] = ("link", os.readlink(here / d))
                dirnames.remove(d)
        for f in sorted(filenames):
            if _ignored(f):
                continue
            full = here / f
            rel = full.relative_to(root).as_posix()
            if full.is_symlink():
                entries[rel] = ("link", os.readlink(full))
            elif full.is_file():
                h = hashlib.sha256()
                with open(full, "rb") as fh:
                    for chunk in iter(lambda: fh.read(1 << 20), b""):
                        h.update(chunk)
                entries[rel] = ("file", h.hexdigest(), bool(full.stat().st_mode & 0o111))
    return entries


def tree_hash(entries: dict) -> str:
    return hashlib.sha256(json.dumps(sorted(entries.items())).encode()).hexdigest()


# --------------------------------------------------------------------------- validation / scanning
def parse_frontmatter(text: str):
    m = re.match(r"\A\ufeff?---[ \t]*\n(.*?)\n---[ \t]*(?:\n|\Z)", text, re.S)
    if not m:
        return None
    fm: dict = {}
    lines = m.group(1).splitlines()
    i = 0
    while i < len(lines):
        mm = re.match(r"^([A-Za-z0-9_-]+):[ \t]*(.*)$", lines[i])
        if not mm:
            i += 1
            continue
        key, val = mm.group(1), mm.group(2).strip()
        j, cont = i + 1, []
        while j < len(lines) and (lines[j].startswith((" ", "\t")) or not lines[j].strip()):
            cont.append(lines[j].strip())
            j += 1
        joined = " ".join(c for c in cont if c)
        if val in (">", "|", ">-", "|-", ">+", "|+"):
            val = joined
        elif joined:
            val = f"{val} {joined}".strip()
        if len(val) >= 2 and val[0] == val[-1] and val[0] in "'\"":
            val = val[1:-1]
        fm[key] = val
        i = j
    return fm


def validate_skill(name: str, src: Path):
    """Return (errors, warnings, frontmatter)."""
    errors, warnings = [], []
    if not SAFE_NAME.match(name):
        errors.append(f"unsafe skill folder name {name!r}")
    sm = src / "SKILL.md"
    if not sm.is_file():
        return errors + ["SKILL.md is missing"], warnings, {}
    fm = parse_frontmatter(sm.read_text(encoding="utf-8", errors="replace"))
    if fm is None:
        return errors + ["SKILL.md has no YAML frontmatter (--- block)"], warnings, {}
    if not fm.get("description"):
        errors.append("frontmatter has no `description` (Claude uses it to decide when to trigger the skill)")
    if not fm.get("name"):
        warnings.append("frontmatter has no `name`")
    elif fm["name"] != name:  # legit in practice (folder = slash-command, name = display name): warn only
        warnings.append(f"frontmatter name {fm['name']!r} differs from folder {name!r}")
    return errors, warnings, fm


def scan(root: Path, cfg: dict, entries: dict) -> list:
    """Return [(severity, relpath, line, label)]. Never includes the matched text itself."""
    try:
        deny = [re.compile(p) for p in cfg["extra_deny_patterns"]]
    except re.error as e:
        raise SyncError(f"invalid regex in extra_deny_patterns: {e}")
    max_bytes = int(cfg["max_file_mb"] * 1024 * 1024)
    out = []
    for rel, e in sorted(entries.items()):
        base = rel.rsplit("/", 1)[-1]
        if e[0] == "link":
            out.append(("warn", rel, 0, "symlink (copied as a link; may dangle in the repo)"))
            continue
        env_tpl = base.lower().endswith(ENV_TEMPLATE_SUFFIXES)
        if not env_tpl and any(fnmatch.fnmatch(base, pat) for pat in SENSITIVE_FILES):
            out.append(("block", rel, 0, "sensitive file name"))
            continue
        full = root / rel
        if full.stat().st_size > max_bytes:
            out.append(("block", rel, 0, f"file larger than {cfg['max_file_mb']} MB"))
            continue
        data = full.read_bytes()
        if b"\0" in data[:8192]:
            continue  # binary: size-checked above, not text-scanned
        for n, line in enumerate(data.decode("utf-8", "replace").splitlines(), 1):
            for label, rx in SECRET_RX:
                m = rx.search(line)
                if not m:
                    continue
                val = m.groupdict().get("val")
                if val is not None and PLACEHOLDER_RX.search(val):
                    continue
                out.append(("block", rel, n, label))
            for rx in deny:
                if rx.search(line):
                    out.append(("block", rel, n, "matches extra_deny_patterns"))
            if HOME_RX.search(line):
                out.append(("warn", rel, n, "absolute home path (privacy)"))
    return out


# --------------------------------------------------------------------------- git helpers
class GitError(SyncError):
    pass


def redact(s: str) -> str:
    return re.sub(r"(://)[^/@\s]+@", r"\1***@", s or "")


def _git_env() -> dict:
    env = dict(os.environ)
    env.setdefault("GIT_TERMINAL_PROMPT", "0")      # fail instead of waiting for a password
    env.setdefault("GIT_SSH_COMMAND", "ssh -o BatchMode=yes")
    env.setdefault("GCM_INTERACTIVE", "never")
    return env


def hint_for(stderr: str) -> str:
    s = stderr.lower()
    if any(k in s for k in ("authentication failed", "could not read username", "terminal prompts disabled",
                            "permission denied (publickey)", "invalid username or password", "returned error: 403")):
        return ("authentication failed: check that your SSH key is loaded (`ssh -T git@github.com`) "
                "and has write access to the repo")
    if "tell me who you are" in s or "unable to auto-detect email" in s:
        return "git identity missing: `git config --global user.name ...` and `user.email ...`"
    if any(k in s for k in ("could not resolve host", "unable to access", "connection timed out", "network is unreachable")):
        return "network unreachable"
    return ""


def _git_failure(args, p) -> "GitError":
    err = redact((p.stderr or p.stdout).strip())
    lines = [l for l in err.splitlines() if l.strip()]
    key = next((l for l in lines if l.startswith(("fatal:", "error:", "remote: error", "! [rejected]"))),
               lines[-1] if lines else str(p.returncode))
    h = hint_for(err)
    e = GitError(f"git {' '.join(args[:2])} failed: {key}" + (f" [{h}]" if h else ""))
    e.stderr = err
    return e


def git(repo, *args, check=True, timeout=60):
    try:
        p = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True,
                           env=_git_env(), timeout=timeout)
    except subprocess.TimeoutExpired:
        raise GitError(f"git {args[0]} timed out after {timeout}s")
    except FileNotFoundError:
        raise GitError("git is not installed")
    if check and p.returncode != 0:
        raise _git_failure(args, p)
    return p


def norm_url(u: str) -> str:
    u = u.strip()
    has_scheme = bool(re.match(r"^[a-z+]+://", u))
    u = re.sub(r"^[a-z+]+://", "", u)
    u = re.sub(r"^[^@/]+@", "", u)
    if not has_scheme:
        u = u.replace(":", "/", 1)
    return re.sub(r"\.git$", "", u.rstrip("/")).lower()


def ensure_repo(cfg: dict) -> Path:
    repo = Path(cfg["repo_dir"]).expanduser() if cfg["repo_dir"] else state_dir() / "repo"
    if not (repo / ".git").exists():
        if repo.exists() and any(repo.iterdir()):
            raise SyncError(f"{repo} exists and is not a git clone")
        repo.parent.mkdir(parents=True, exist_ok=True)
        try:
            p = subprocess.run(["git", "clone", cfg["repo_url"], str(repo)], capture_output=True, text=True,
                               env=_git_env(), timeout=120)
        except subprocess.TimeoutExpired:
            raise SyncError("git clone timed out")
        if p.returncode != 0:
            err = redact(p.stderr.strip())
            raise SyncError(f"clone of {redact(cfg['repo_url'])} failed: "
                            f"{err.splitlines()[-1] if err else p.returncode}"
                            + (f" [{hint_for(err)}]" if hint_for(err) else ""))
    origin = git(repo, "remote", "get-url", "origin", check=False).stdout.strip()
    if origin and norm_url(origin) != norm_url(cfg["repo_url"]):
        raise SyncError(f"clone at {repo} points to {redact(origin)} but config repo_url is "
                        f"{redact(cfg['repo_url'])}")
    return repo


def update_repo(repo: Path):
    """Fetch + rebase onto upstream. Returns (net_ok, error_message)."""
    if git(repo, "status", "--porcelain").stdout.strip():
        raise SyncError(f"the clone {repo} has uncommitted changes; inspect it with `git -C {repo} status`")
    if git(repo, "rev-parse", "--abbrev-ref", "HEAD").stdout.strip() == "HEAD":
        raise SyncError(f"the clone {repo} is on a detached HEAD")
    if git(repo, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}", check=False).returncode != 0:
        raise SyncError(f"the clone {repo} has no upstream branch")
    try:
        git(repo, "fetch", "--prune", "origin", timeout=45)
    except GitError as e:
        return False, str(e)  # offline is not fatal: we still commit locally and retry the push later
    p = git(repo, "rebase", "@{u}", check=False)
    if p.returncode != 0:
        git(repo, "rebase", "--abort", check=False)
        raise SyncError("rebase onto the remote failed (conflicting local commits); "
                        f"resolve manually in {repo}")
    return True, ""


def ahead_count(repo: Path) -> int:
    p = git(repo, "rev-list", "--count", "@{u}..HEAD", check=False)
    return int(p.stdout.strip() or 0) if p.returncode == 0 else 0


def rollback(repo: Path, name: str):
    git(repo, "reset", "-q", "HEAD", "--", name, check=False)
    git(repo, "checkout", "--", name, check=False)
    git(repo, "clean", "-fdq", "--", name, check=False)


def push(repo: Path) -> str:
    p = git(repo, "push", check=False, timeout=60)
    if p.returncode != 0:
        if re.search(r"rejected|non-fast-forward|fetch first|failed to push some refs", p.stderr or ""):
            git(repo, "fetch", "origin", timeout=45)        # someone pushed in between: rebase and retry once
            if git(repo, "rebase", "@{u}", check=False).returncode != 0:
                git(repo, "rebase", "--abort", check=False)
                raise SyncError("push rejected and the rebase conflicted; resolve manually")
            git(repo, "push", timeout=60)
        else:
            raise _git_failure(("push",), p)
    return git(repo, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}").stdout.strip()


# --------------------------------------------------------------------------- state (baseline + dirty markers)
def _synced_path() -> Path:
    return state_dir() / "synced.json"


def load_synced() -> dict:
    try:
        return json.loads(_synced_path().read_text())
    except (OSError, json.JSONDecodeError):
        return {}


def save_synced(d: dict):
    p = _synced_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(d, indent=1, sort_keys=True))
    os.replace(tmp, p)


def dirty_dir() -> Path:
    return state_dir() / "dirty"


def mark_dirty(name: str):
    if not SAFE_NAME.match(name):
        return
    d = dirty_dir()
    d.mkdir(parents=True, exist_ok=True)
    f = d / name
    if not f.exists():
        f.write_text(json.dumps({"since": time.time(), "last_attempt": 0}))


def clear_dirty(name: str):
    try:
        (dirty_dir() / name).unlink()
    except OSError:
        pass


def touch_attempt(name: str):
    f = dirty_dir() / name
    try:
        d = json.loads(f.read_text())
        d["last_attempt"] = time.time()
        f.write_text(json.dumps(d))
    except (OSError, json.JSONDecodeError):
        pass


def pending_dirty(retry_after: float = 600.0) -> list[str]:
    out = []
    d = dirty_dir()
    if not d.is_dir():
        return out
    for f in sorted(d.iterdir()):
        try:
            last = json.loads(f.read_text()).get("last_attempt", 0)
        except (OSError, json.JSONDecodeError):
            last = 0
        if time.time() - last >= retry_after:
            out.append(f.name)
    return out


class Lock:
    def __init__(self, timeout=30.0):
        self.timeout, self.fh = timeout, None

    def __enter__(self):
        if fcntl is None:
            return self
        state_dir().mkdir(parents=True, exist_ok=True)
        self.fh = open(state_dir() / "lock", "w")
        end = time.time() + self.timeout
        while True:
            try:
                fcntl.flock(self.fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
                return self
            except OSError:
                if time.time() > end:
                    raise SyncError("another skills-sync run is in progress (lock timeout)")
                time.sleep(0.25)

    def __exit__(self, *a):
        if self.fh:
            self.fh.close()


# --------------------------------------------------------------------------- decision logic (pure)
def decide(local_h, repo_h, base_h, explicit: bool, force_local: bool) -> str:
    """ADD | SAME | UPDATE | REPO_AHEAD | DIVERGED | REVIEW"""
    if repo_h is None:
        return "ADD"
    if local_h == repo_h:
        return "SAME"
    if force_local:
        return "UPDATE"
    if base_h is None:                       # never synced from this machine: who is newer is unknown
        return "UPDATE" if explicit else "REVIEW"
    if base_h == repo_h:                     # only local changed
        return "UPDATE"
    if base_h == local_h:                    # only the repo changed
        return "REPO_AHEAD"
    return "DIVERGED"                        # both changed


# --------------------------------------------------------------------------- report
class Report:
    def __init__(self):
        self.items: list[tuple[str, str, str]] = []
        self.details: list[str] = []
        self.push_status = ""      # "", "pushed ...", "failed: ..."
        self.notes: list[str] = []

    def add(self, name, status, detail=""):
        self.items.append((name, status, detail))

    @property
    def exit_code(self) -> int:
        st = {s for _, s, _ in self.items}
        if "ERROR" in st:
            return 1
        if st & {"BLOCKED", "DIVERGED", "REPO_AHEAD", "REVIEW"}:
            return 2
        if self.push_status.startswith("failed"):
            return 3
        return 0

    def render(self) -> str:
        lines = []
        for name, status, detail in self.items:
            lines.append(f"{status:<14}{name}" + (f"  {detail}" if detail else ""))
        lines += self.details
        lines += self.notes
        if self.push_status:
            kind, _, rest = self.push_status.partition(": ")
            label = {"pushed": "PUSHED", "failed": "PUSH-FAILED", "skipped": "PUSH-SKIPPED"}[kind]
            lines.append(f"{label:<14}{rest}")
        if not lines:
            lines.append("nothing to do")
        return "\n".join(lines)


# --------------------------------------------------------------------------- main operations
def resolve_targets(args_targets, cfg, cwd=None):
    seen, out = set(), []
    for t in args_targets:
        name, src = find_skill(t, cfg, cwd)
        if name in seen:
            continue
        seen.add(name)
        out.append((name, src))
    return out


def build_index(repo: Path) -> str:
    rows = []
    for d in sorted(p for p in repo.iterdir() if p.is_dir() and not p.name.startswith(".")):
        sm = d / "SKILL.md"
        if not sm.is_file():
            continue
        fm = parse_frontmatter(sm.read_text(encoding="utf-8", errors="replace")) or {}
        desc = (fm.get("description") or "").replace("|", "\\|")
        first = re.split(r"(?<=[.!?])\s", desc, maxsplit=1)[0]
        if len(first) > 200:
            first = first[:197] + "..."
        rows.append(f"| [`{d.name}`]({d.name}/SKILL.md) | {first} |")
    return "\n".join([INDEX_START, "## Skills", "", "| Skill | Description |", "|---|---|", *rows, INDEX_END])


def refresh_readme(repo: Path) -> bool:
    readme = repo / "README.md"
    text = readme.read_text(encoding="utf-8") if readme.exists() else "# Skills\n"
    block = build_index(repo)
    if INDEX_START in text and INDEX_END in text:
        new = re.sub(re.escape(INDEX_START) + r".*?" + re.escape(INDEX_END), lambda m: block, text, flags=re.S)
    else:
        new = text.rstrip("\n") + "\n\n" + block + "\n"
    if new == text:
        return False
    readme.write_text(new, encoding="utf-8")
    return True


def run_sync(targets, cfg, *, explicit=True, dry_run=False, no_push=False, ignore_findings=False,
             force_local=False, cwd=None) -> Report:
    rep = Report()
    todo = []
    for name, src in targets:
        if name in cfg["exclude_skills"]:
            rep.add(name, "SKIPPED", "listed in exclude_skills")
        elif src is None:
            where = ", ".join(str(r) for r in source_roots(cfg, cwd))
            rep.add(name, "ERROR", f"skill not found in: {where}")
        else:
            todo.append((name, src))
    if not todo:
        return rep

    try:
        with Lock():
            repo = ensure_repo(cfg)
            net_ok, net_err = (False, "")
            if not dry_run:
                net_ok, net_err = update_repo(repo)
            synced = load_synced()
            commits = 0
            for name, src in todo:
                try:
                    errors, warnings, fm = validate_skill(name, src)
                    if errors:
                        rep.add(name, "ERROR", "; ".join(errors))
                        continue
                    entries = snapshot(src)
                    local_h = tree_hash(entries)
                    dst = repo / name
                    repo_h = tree_hash(snapshot(dst)) if dst.is_dir() else None
                    action = decide(local_h, repo_h, synced.get(name), explicit, force_local)
                    if action == "SAME":
                        synced[name] = local_h
                        clear_dirty(name)
                        rep.add(name, "UNCHANGED")
                        continue
                    if action == "REPO_AHEAD":
                        rep.add(name, "REPO_AHEAD", "the repo has a newer version than this machine; "
                                f"run `sync_skill.py --pull {name}` (or --force-local to overwrite it)")
                        clear_dirty(name)
                        continue
                    if action == "DIVERGED":
                        rep.add(name, "DIVERGED", "changed both locally and in the repo since the last sync; "
                                f"compare `diff -r {src} {dst}` then --force-local or --pull --force-repo")
                        clear_dirty(name)
                        continue
                    if action == "REVIEW":
                        rep.add(name, "REVIEW", "exists in the repo with different content and was never synced "
                                f"from here; run `sync_skill.py {name} --dry-run` and decide")
                        clear_dirty(name)
                        continue
                    findings = scan(src, cfg, entries)
                    blocking = [f for f in findings if f[0] == "block"]
                    if blocking and not ignore_findings:
                        rep.add(name, "BLOCKED", f"{len(blocking)} blocking finding(s), nothing was copied")
                        for sev, rel, line, label in findings:
                            rep.details.append(f"    {sev.upper():<5} {name}/{rel}" + (f":{line}" if line else "")
                                               + f"  {label}")
                        clear_dirty(name)
                        continue
                    for sev, rel, line, label in findings:
                        if sev == "warn" or ignore_findings:
                            rep.details.append(f"    WARN  {name}/{rel}" + (f":{line}" if line else "") + f"  {label}")
                    for w in warnings:
                        rep.details.append(f"    WARN  {name}: {w}")
                    verb = "ADDED" if action == "ADD" else "UPDATED"
                    if dry_run:
                        rep.add(name, f"WOULD-{verb}")
                        continue
                    if dst.exists():
                        shutil.rmtree(dst)
                    shutil.copytree(src, dst, symlinks=True, ignore=shutil.ignore_patterns(*IGNORE_NAMES))
                    git(repo, "add", "-A", "--", name)
                    if git(repo, "diff", "--cached", "--quiet", "--", name, check=False).returncode == 0:
                        rep.add(name, "UNCHANGED")          # only ignored files differed
                        synced[name] = local_h
                        clear_dirty(name)
                        continue
                    subject = f"feat({name}): add skill" if action == "ADD" else f"chore({name}): update skill"
                    body = (fm.get("description") or "")[:200]
                    try:
                        git(repo, "commit", "-q", "-m", subject, *(["-m", body] if body and action == "ADD" else []))
                    except GitError:
                        rollback(repo, name)
                        raise
                    commits += 1
                    synced[name] = local_h
                    clear_dirty(name)
                    rep.add(name, verb, subject)
                except SyncError as e:
                    touch_attempt(name)
                    rep.add(name, "ERROR", str(e))
            if not dry_run:
                save_synced(synced)
                if cfg["readme_index"] and commits:
                    if refresh_readme(repo):
                        git(repo, "add", "--", "README.md")
                        git(repo, "commit", "-q", "-m", "docs: refresh skills index")
                        commits += 1
                pending = ahead_count(repo)
                if no_push or not cfg["push"]:
                    if pending:
                        rep.push_status = f"skipped: {pending} commit(s) not pushed (push disabled)"
                elif pending:
                    if not net_ok:
                        rep.push_status = f"failed: {pending} commit(s) kept locally ({net_err})"
                    else:
                        try:
                            up = push(repo)
                            rep.push_status = f"pushed: {pending} commit(s) to {up}"
                        except SyncError as e:
                            rep.push_status = f"failed: {pending} commit(s) kept locally, retried next run ({e})"
    except SyncError as e:
        rep.add("-", "ERROR", str(e))
    return rep


def drifted_tracked(cfg: dict, cwd=None) -> list[str]:
    """Skills present both locally and in the clone whose content differs (cheap, no network)."""
    repo = Path(cfg["repo_dir"]).expanduser() if cfg["repo_dir"] else state_dir() / "repo"
    if not (repo / ".git").exists():
        return []
    names = []
    for root in source_roots(cfg, cwd):
        if not root.is_dir():
            continue
        for d in sorted(root.iterdir()):
            if (d / "SKILL.md").is_file() and (repo / d.name / "SKILL.md").is_file() and d.name not in names:
                if tree_hash(snapshot(d)) != tree_hash(snapshot(repo / d.name)):
                    names.append(d.name)
    return names


def run_pull(targets, cfg, *, force_repo=False, cwd=None) -> Report:
    rep = Report()
    try:
        with Lock():
            repo = ensure_repo(cfg)
            update_repo(repo)
            synced = load_synced()
            for name, src in targets:
                if not SAFE_NAME.match(name) or not (repo / name / "SKILL.md").is_file():
                    rep.add(name, "ERROR", "not found in the repo")
                    continue
                repo_h = tree_hash(snapshot(repo / name))
                dest = src if src is not None else source_roots(cfg, cwd)[0] / name
                if dest.exists():
                    local_h = tree_hash(snapshot(dest))
                    if local_h == repo_h:
                        rep.add(name, "UNCHANGED")
                        synced[name] = repo_h
                        continue
                    if local_h != synced.get(name) and not force_repo:
                        rep.add(name, "DIVERGED", "local copy has unsynced changes; --force-repo overwrites them")
                        continue
                    shutil.rmtree(dest)
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copytree(repo / name, dest, symlinks=True, ignore=shutil.ignore_patterns(".git"))
                synced[name] = repo_h
                clear_dirty(name)
                rep.add(name, "PULLED", str(dest))
            save_synced(synced)
    except SyncError as e:
        rep.add("-", "ERROR", str(e))
    return rep


def status(cfg: dict, cwd=None) -> str:
    note = ""
    try:
        repo = ensure_repo(cfg)          # clones on first use so NEW / IN-SYNC are accurate
    except SyncError as e:
        repo = Path(cfg["repo_dir"]).expanduser() if cfg["repo_dir"] else state_dir() / "repo"
        note = f"\n(repo unavailable, states below are unreliable: {e})"
    have_repo = (repo / ".git").exists()
    synced = load_synced()
    lines, seen = [], set()
    for root in source_roots(cfg, cwd):
        if not root.is_dir():
            continue
        for d in sorted(root.iterdir()):
            if not (d / "SKILL.md").is_file() or d.name in seen:
                continue
            seen.add(d.name)
            local_h = tree_hash(snapshot(d))
            repo_h = tree_hash(snapshot(repo / d.name)) if have_repo and (repo / d.name).is_dir() else None
            if d.name in cfg["exclude_skills"]:
                state = "EXCLUDED"
            else:
                state = {"ADD": "NEW", "SAME": "IN-SYNC", "UPDATE": "MODIFIED", "REPO_AHEAD": "REPO-AHEAD",
                         "DIVERGED": "DIVERGED", "REVIEW": "NEEDS-REVIEW"}[
                    decide(local_h, repo_h, synced.get(d.name), False, False)]
            lines.append(f"{state:<13}{d.name}")
    if have_repo:
        for d in sorted(p for p in repo.iterdir() if p.is_dir() and (p / "SKILL.md").is_file()):
            if d.name not in seen:
                lines.append(f"{'REPO-ONLY':<13}{d.name}")
    return ("\n".join(lines) or "no skills found in: " + ", ".join(str(r) for r in source_roots(cfg, cwd))) + note


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="sync_skill.py", description=__doc__.split("\n\n")[0])
    ap.add_argument("targets", nargs="*", help="skill names, or paths to a skill folder / a file inside it")
    ap.add_argument("--all-tracked", action="store_true", help="every skill already in the repo whose local copy changed")
    ap.add_argument("--status", action="store_true", help="show NEW / MODIFIED / IN-SYNC per local skill")
    ap.add_argument("--dry-run", action="store_true", help="validate, scan and report; change nothing")
    ap.add_argument("--no-push", action="store_true", help="commit locally only")
    ap.add_argument("--pull", action="store_true", help="repo -> local for the named skills")
    ap.add_argument("--force-local", action="store_true", help="local wins even if the repo has newer/different changes")
    ap.add_argument("--force-repo", action="store_true", help="with --pull: repo wins even over unsynced local changes")
    ap.add_argument("--ignore-findings", action="store_true",
                    help="publish despite blocking scan findings (only after the user has seen them)")
    a = ap.parse_args(argv)
    try:
        cfg = load_config()
        if a.status:
            print(status(cfg))
            return 0
        targets = resolve_targets(a.targets, cfg)
        if a.all_tracked:
            for n in drifted_tracked(cfg):
                if n not in {t[0] for t in targets}:
                    targets.append(find_skill(n, cfg))
        if not targets:
            print("nothing to do (give a skill name/path, or --all-tracked)")
            return 0
        if a.pull:
            rep = run_pull(targets, cfg, force_repo=a.force_repo)
        else:
            rep = run_sync(targets, cfg, explicit=not a.all_tracked, dry_run=a.dry_run, no_push=a.no_push,
                           ignore_findings=a.ignore_findings, force_local=a.force_local)
        print(rep.render())
        return rep.exit_code
    except SyncError as e:
        print(f"ERROR      {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
