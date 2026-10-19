# Setup

## Install
Copy this folder to `~/.claude/skills/skills-sync/`. Run once: `python3 ~/.claude/skills/skills-sync/scripts/sync_skill.py --status` (clones the repo into `~/.claude/skills-sync/repo`).

The repo is cloned over SSH (`git@github.com:vuillaut/skills.git`), so an SSH key with write access must be loaded
(`ssh -T git@github.com` should greet you by name). If a clone already exists over HTTPS, switch it with
`git -C ~/.claude/skills-sync/repo remote set-url origin git@github.com:vuillaut/skills.git`
(the HTTPS and SSH URLs are treated as the same repo, so no re-clone is needed).

## Config (optional): `~/.claude/skills-sync.json`
```json
{
  "repo_url": "git@github.com:vuillaut/skills.git",
  "source_dirs": ["~/.claude/skills", ".claude/skills"],
  "exclude_skills": [],
  "extra_deny_patterns": ["internal\\.hostname\\.example"],
  "readme_index": false,
  "max_file_mb": 5,
  "push": true
}
```
Relative `source_dirs` resolve against the current directory (project skills). Unknown keys are rejected (typo guard). `extra_deny_patterns` are regexes that block a publish. `readme_index: true` maintains a skills table in the repo README.

## Hook (optional safety net)
Skills trigger on Claude's judgment and can be missed. The hook is deterministic: `PostToolUse` marks edited skills, `Stop` (end of turn) syncs them, so you get one commit per turn. At `Stop` it also catches edits of already-tracked skills made via Bash, and never auto-publishes brand-new untracked skills it did not see Claude write.

Add to `~/.claude/settings.json` (merge with existing `hooks`), then restart Claude Code (hooks are read at session start):
```json
{
  "hooks": {
    "PostToolUse": [
      { "matcher": "Write|Edit|MultiEdit",
        "hooks": [{ "type": "command", "command": "python3 \"$HOME/.claude/skills/skills-sync/scripts/hook.py\"", "timeout": 10 }] }
    ],
    "Stop": [
      { "hooks": [{ "type": "command", "command": "python3 \"$HOME/.claude/skills/skills-sync/scripts/hook.py\"", "timeout": 90 }] }
    ]
  }
}
```
The hook only prints a message when something notable happens (added, updated, blocked, error).

## Safety nets in the engine
Secret scan (tokens, private keys, `.env`/`*.pem` files, big files) before any copy; refuses to overwrite a newer repo version (3-way check via a baseline in `~/.claude/skills-sync/synced.json`); lock against concurrent runs; git never prompts for a password; one retry if someone pushed in between.

Known limits: first sync of a skill that already exists in the repo with different content treats local as truth when explicit (use `--dry-run` first); renames create a new folder and leave the old one.

## Tests
`cd ~/.claude/skills/skills-sync && python3 -m unittest discover -s tests -v` (uses a local fake remote, never touches GitHub).
