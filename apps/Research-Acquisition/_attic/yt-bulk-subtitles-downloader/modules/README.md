# Personal Dashboard Data Spine

This folder is the physical storage spine for the local dashboard.

Purpose:
- keep the four dashboard modules attached to real folders
- make later phone/desktop/cloud transfer straightforward
- give publishing, research, prompts, clipboard, and time state a stable home

Folders:
- `Clipboard` — captured snippets, exports, mobile handoff
- `Prompts` — prompt packs, chains, reusable command sets
- `Research` — bookmarks, source bundles, ingest staging
- `Theophysics` — master-equation outputs, reports, canonical artifacts
- `Transfer` — shuttle lane for phone/desktop/cloud movement
- `Time` — task exports, schedules, command-state snapshots
- `Publishing` — page outputs, forum drafts, deploy-ready material

Operating intent:
- Desktop now
- Cloud-sync later
- Same structure on every machine

Launch pattern:
- every main folder now includes `LAUNCH_HERE.bat`
- those wrappers call `C:\Users\lowes\Desktop\Personal dashboard\EngineRoom\engine_room.ps1`
- use `C:\Users\lowes\Desktop\Personal dashboard\EngineRoom\START_CORE_STACK.bat` to start the main local stack

Recommended next move:
- put `C:\Users\lowes\Desktop\Personal dashboard\Data` inside a synced location when ready
- keep the HTML apps in place, but point exports and generated outputs into these folders
