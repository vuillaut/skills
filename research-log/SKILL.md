---
name: research-log
description: Document a research or computational science session so the next agent or human can pick up the project without re-deriving context. Use at the end of a research session that involved trying approaches, running computations, or making decisions, and whenever the user asks to log, write up, or document a session, record findings, track tasks, or update the project's status.
---

# Research log

A research session produces three different kinds of memory, and collapsing them into one growing document is how projects end up with a wall of text nobody rereads. This skill keeps them in three files:

- `RESEARCH_LOG.md` — append-only. One dated entry per session. Never edited except to fix a factual error, and the correction is noted as a correction, not folded silently into the original text.
- `TODO.md` — a live checklist. Ticked off, added to, or struck through every session as the work actually moves.
- `STATE.md` — overwritten each session. The project's current status in one page: what's settled, what's open, where to look next. This is what a new agent or a collaborator reads first.

## Step 1: find or start the project's log

Check the project root and any `docs/` folder for `STATE.md`, `RESEARCH_LOG.md`, and `TODO.md`. Also check `AGENTS.md`, `CLAUDE.md`, or the README for a pointer to any of these under a different name (`NOTES.md`, `JOURNAL.md`, `TASKS.md`) — if one exists, that is the file for this project. Use it instead of creating a second one.

If the files exist, read all of them before writing anything. You need the current state and open tasks to know what changed this session, and you need the log's own conventions to match rather than starting a new style halfway through.

If none exist, this is the project's first recorded session. Create all three at the project root. Open `RESEARCH_LOG.md` with a short project header before the first entry: project name, the objective in one line, and the start date. `STATE.md` gets the same objective line. `TODO.md` starts with whatever tasks this first session actually surfaces.

Done when: you know which files are this project's source of truth for history, tasks, and status, and you've read whichever already existed.

## Step 2: reconstruct the session

Work back through the conversation, the code changes, and any commands or jobs that ran, and fill in every field below. If a field genuinely has nothing for this session, write "none" rather than dropping it. A missing field looks like an oversight to whoever reads this next; an explicit "none" looks like a decision.

- **Goal.** What this session set out to do, as it was understood at the time. Don't retroactively rewrite this in light of what you later found out.
- **Tried.** Every approach or method attempted, however briefly, with the immediate result.
- **Worked.** What held up, and the evidence for it: a number, a plot, a test that passed, a benchmark. "It worked" without the evidence is a claim someone else will have to re-verify from scratch.
- **Discarded.** Every approach that was tried and dropped, or considered and never tried, with the actual reason it didn't survive: wrong hypothesis, a bug, too slow, numerically unstable, out of scope for now. This field is the one people skip and the one that saves the most time later. A project's real cost is redoing work someone already ruled out, because nobody wrote down why.
- **Decisions.** Each choice made this session, the reasoning behind it, and the alternative(s) it was chosen over. If a decision reverses something in the current `STATE.md` or closes out a task in `TODO.md`, say so explicitly.
- **Artifacts.** Commands run, config or data versions, commit hashes, job IDs, output paths, plot files. Link to these rather than re-describing their contents in prose — a linked file stays accurate as the project moves; a paraphrase of it goes stale the moment the file changes.
- **Open questions / next steps.** What's unresolved, and what the next session should pick up. This is the raw material for this session's `TODO.md` update.

If you're not sure whether something counts as discarded or just paused, say so in the entry instead of picking one. A false "discarded" buries a live idea; a false "paused" leaves a dead one looking open. Guessing either way costs someone real time later.

Done when: every field above has real content or an explicit "none," and no decision that overturns something in the current `STATE.md` or `TODO.md` has gone unmentioned.

## Step 3: append the log entry

Add the entry to the end of `RESEARCH_LOG.md`, dated, using this shape:

```
## YYYY-MM-DD — <one-line session focus>

**Goal:** ...

**Tried:**
- ...

**Worked:**
- ...

**Discarded:**
- approach — reason

**Decisions:**
- decision — rationale — alternative(s) considered

**Artifacts:**
- commands / versions / commit / job IDs / output paths

**Open questions / next steps:**
- ...
```

Match whatever section names the file already used if this isn't the first entry — consistency across entries matters more than this exact template.

Done when: the entry is appended and no earlier entry's text has changed.

## Step 4: update the task list

Edit `TODO.md` so it reflects what actually happened this session, using this shape:

```
## Open
- [ ] task

## Done
- [x] task — YYYY-MM-DD

## Not pursuing
- [ ] ~~task~~ — not pursuing since YYYY-MM-DD, see that day's log entry
```

Three moves, all driven by what you found in Step 2, not invented fresh here:

- Tick anything this session's Worked or Decisions fields closed out, and move it under Done with the date.
- Add anything this session's Open questions / next steps surfaced that isn't already on the list.
- Strike anything this session's Discarded field ruled out, and move it under Not pursuing with a one-line pointer to the log entry rather than repeating the full reasoning there.

Never delete a task outright. A deleted line looks like it was never considered; a struck line under Not pursuing shows someone thought about it and made a call. If Done grows long across many sessions, it's fine to trim older completed items — the log entry that closed them already preserves the record, so `TODO.md` doesn't need to carry it twice.

Done when: every task ticked, added, or struck this session traces back to something in Step 2, and nothing was silently removed.

## Step 5: update the snapshot

Rewrite `STATE.md` so it describes the project as it stands after this session, not as a running history. Anything this session settled, reversed, or closed gets updated or removed from the old text, not appended alongside it. A snapshot that accumulates instead of updating stops being useful the same way a single merged log file does.

Keep it short: objective, current status, what's settled (with a pointer to the log entry for the full reasoning behind each), open questions, and pointers to where the code, data, results, and `TODO.md` actually live. Don't restate the task list here — point at `TODO.md` instead, so there's one place tasks live rather than two that can drift apart.

Done when: `STATE.md` contains no claim that this session's `RESEARCH_LOG.md` entry or the updated `TODO.md` contradicts.

## Step 6: check before closing

Show the user the log entry, the task list changes, and the updated state. Research memory is only as good as its accuracy, and you were working from a conversation, not from ground truth — ask the user to confirm or correct anything you inferred rather than were told directly, especially in Discarded, Decisions, and Not pursuing. Only treat the session as documented once they've had a chance to fix anything.
