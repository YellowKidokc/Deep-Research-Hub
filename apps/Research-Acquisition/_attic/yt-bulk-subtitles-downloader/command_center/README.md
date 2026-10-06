# AI-HUB Command Center

Standalone pilot for a manifest-driven Windows command picker.

## Goal

Press `Ctrl+Shift+Alt+W` to open a searchable launcher for local workflows:

- `.bat` / `.cmd`
- `.ps1`
- `.py`
- `.ahk`
- folders
- URLs
- apps
- preference-capture workflows

This starts standalone so it can prove itself before being merged into the main
AI-HUB v2 process.

## Files

```text
command_center.ahk      AutoHotkey v2 hotkey layer
command_picker.py       Tkinter searchable picker GUI
run_command.py          Safe manifest runner
commands.json           Command manifest
scripts/py/             Built-in Python workflows
logs/                   Per-run logs, gitignored by default if added later
data/preferences/       Preference-engine JSONL captures
```

## Launch

Run:

```powershell
AutoHotkey64.exe D:\GitHub\ai-hub-v2\command_center\command_center.ahk
```

Then press:

```text
Ctrl+Shift+Alt+W
```

## Important Hotkey Note

`Ctrl+Alt+W` belongs to AI-HUB **Always On Top** (`hub_core.ahk`).
Command Center uses **`Ctrl+Shift+Alt+W`** so the two do not fight.

## Preference Capture

The sample command `Capture Active Window Preference` records the active window
context plus a like/dislike/neutral decision to:

```text
command_center/data/preferences/window_preferences.jsonl
```

That is the first small backbone for the preference engine.

