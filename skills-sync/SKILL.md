---
name: skills-sync
description: Publish new or modified Claude Code skills to the user's GitHub repo https://github.com/vuillaut/skills. Use this right after creating or editing any skill (SKILL.md or files in a skill folder, e.g. via skill-creator), and whenever the user says sync, publish, push, save or back up a skill, or "update my skills repo", even if they don't mention GitHub.
---

# skills-sync

Keeps vuillaut/skills on GitHub, cloned over SSH (`git@github.com:vuillaut/skills.git`; one folder per skill at the repo root) in sync with the user's local skills. The engine is `scripts/sync_skill.py`; it validates, scans for secrets, copies, commits and pushes.

## Procedure

1. Identify the skill(s) just created or changed (usually `~/.claude/skills/<name>/`). Only sync skills the user authored; skip plugin or downloaded skills, and ask if unsure.
2. Run (path is relative to this skill's folder, normally `~/.claude/skills/skills-sync/`):
   ```bash
   python3 ~/.claude/skills/skills-sync/scripts/sync_skill.py <name> [<name2> ...]
   ```
   Useful variants: `--dry-run` (change nothing), `--status` (NEW / MODIFIED / IN-SYNC per skill), `--all-tracked`, `--pull <name>` (repo -> local).
3. Report the outcome in one or two lines.

## Reading the output

| Status | Meaning | What to do |
|---|---|---|
| ADDED / UPDATED / UNCHANGED | done | report; `PUSHED` line confirms the push |
| BLOCKED | secret, `.env`-like file or oversized file found; nothing was copied | show file:line and label, ask the user to fix. Never use `--ignore-findings` unless the user has seen the findings and says so |
| REPO_AHEAD | repo has a newer version than this machine | offer `--pull <name>`; never overwrite silently |
| DIVERGED / REVIEW | both sides changed, or the skill exists in the repo and was never synced from here | show `diff -r`, ask. `--force-local` only on explicit user decision |
| PUSH-FAILED (exit 3) | committed locally, push failed | say so plainly; it is retried on the next run. For auth errors suggest checking the SSH key (`ssh -T git@github.com`) |
| ERROR | invalid skill (no SKILL.md or description), git problem | relay the message |

## Rules

- Never force-push, never edit the clone (`~/.claude/skills-sync/repo`) by hand.
- Deleting a skill locally never deletes it from the repo; do that manually if wanted.
- Config, optional hook and tests: see `references/setup.md`.
