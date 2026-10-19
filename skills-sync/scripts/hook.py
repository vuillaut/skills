#!/usr/bin/env python3
"""Claude Code hook for skills-sync (deterministic safety net).

  PostToolUse (Write|Edit|MultiEdit): if the edited file lives in a skill folder, mark that skill "dirty".
  Stop (end of Claude's turn):        sync the dirty skills + tracked skills edited through other means
                                      (Bash, cp, another editor), then tell the user what happened.

One commit per turn rather than one per edit. Never blocks Claude, never raises: worst case it
prints a warning. Skills are still only *added* when Claude wrote them in this session or they were
named explicitly; untracked skills that merely appear on disk are never published by the hook.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sync_skill as ss  # noqa: E402

NOTABLE = {"ADDED", "UPDATED", "BLOCKED", "ERROR", "DIVERGED", "REPO_AHEAD", "REVIEW"}


def emit(msg: str):
    print(json.dumps({"systemMessage": msg}))


def on_post_tool_use(data: dict, cfg: dict):
    fp = (data.get("tool_input") or {}).get("file_path")
    if not fp:
        return
    hit = ss.skill_name_for_path(fp, cfg, data.get("cwd"))
    if hit and hit[0] not in cfg["exclude_skills"]:
        ss.mark_dirty(hit[0])


def on_stop(data: dict, cfg: dict):
    cwd = data.get("cwd")
    names = list(ss.pending_dirty())
    for n in ss.drifted_tracked(cfg, cwd):          # edits made via Bash / outside Claude
        if n not in names and n not in cfg["exclude_skills"]:
            names.append(n)
    if not names:
        return
    targets = [ss.find_skill(n, cfg, cwd) for n in names]
    explicit_names = {n for n in names if (ss.dirty_dir() / n).exists()}   # written by Claude this session
    rep_explicit = ss.run_sync([t for t in targets if t[0] in explicit_names], cfg, explicit=True, cwd=cwd)
    rep_auto = ss.run_sync([t for t in targets if t[0] not in explicit_names], cfg, explicit=False, cwd=cwd)
    for rep in (rep_explicit, rep_auto):
        if any(s in NOTABLE for _, s, _ in rep.items) or rep.push_status.startswith("failed"):
            emit("skills-sync:\n" + rep.render())


def main() -> int:
    try:
        data = json.load(sys.stdin)
        cfg = ss.load_config()
        event = data.get("hook_event_name")
        if event == "PostToolUse":
            on_post_tool_use(data, cfg)
        elif event == "Stop":
            on_stop(data, cfg)
    except Exception as e:  # a hook must never break the session
        emit(f"skills-sync hook error: {type(e).__name__}: {e}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
