# HUB SHELL v0.2 — Tray-Resident Rust Build Prompt
**Date:** 2026-10-22 | **Status:** Approved direction (David, this session) — ready for builder
**Builder:** Claude Code (sole builder on this repo, standing rule)
**Supersedes:** milestone-1 shell scope only. All screen prompts under docs/ remain law.

## Architecture ruling this build implements (decided 2026-10-22)

Three tiers, each pure Rust, split by LIFECYCLE not features:

1. **Utilities** (clipsync, nerve) — separate tiny binaries, always-on, NOT part of this repo.
   Do not absorb them. Do not share a process with them.
2. **Forge** (repo Rust_AI_API) — the ONE AI-call service, always-on, own local port,
   serves its own workbench HTML (Kimi's pages live there).
3. **Hub** (this repo) — the workbench shell. Seven screens. ZERO embedded API-provider
   code: every AI call goes to Forge's local port. No exceptions, no fallback direct calls.

## What to build in this milestone

1. **Tray residence.** The hub runs as a Windows tray app (taskbar icon):
   - left-click → open/raise the hub window (the seven-icon shell from PR #1)
   - right-click menu: Open Hub, each of the seven screens directly, Restart, Quit
   - starts minimized-to-tray on Windows login (registry Run key or Startup shortcut —
     builder's choice, documented in README)
   - closing the window minimizes to tray; Quit is explicit
2. **Forge client module.** One small internal crate/module (`forge_client`) that all
   screens use for AI calls: health check on hub start, clear tray-visible state when
   Forge is unreachable (icon badge or menu line "Forge: down"), retry policy in ONE place.
   If Forge is down, screens still open; AI actions queue or fail loudly — never silently.
3. **Screen spawn hardening.** The shell already spawns one app; make all seven icons
   spawn their screens as child processes or in-window views (keep whatever PR #1 chose),
   with a per-screen "running / stopped" indicator and relaunch on click.
4. **Single-instance guard.** Second launch focuses the existing instance.
5. **Plain black JSX front end stays** (standing rule: all screens look the same;
   simple case default, expanding interface for depth).

## Explicitly OUT of this milestone
- No new screen functionality (screen prompts govern those builds separately).
- No API-provider keys or SDKs anywhere in this repo (Forge owns that).
- No absorption of clipsync/nerve.
- No auto-update mechanism. Code updates = git pull + rebuild (code plane cold).

## Later screen — noted, not specced (David, 2026-10-22)
A canon browser: Wikipedia-like but nicer, reads the canonized documents (Markdown
directly, or rendered to HTML), browse/search on the site David already has partially
built. Treat as screen #8 candidate; spec comes later. Builder: leave a stub icon slot
if trivial, otherwise ignore.

## Acceptance
- Fresh boot → tray icon present → left-click opens shell → each icon launches its
  screen → kill Forge → tray shows Forge down, screens stay alive → restart Forge →
  state clears. Quit exits cleanly, no orphan children.
- Read receipt first: builder restates the three-tier rule and the no-direct-API rule
  in their own words before writing code.
