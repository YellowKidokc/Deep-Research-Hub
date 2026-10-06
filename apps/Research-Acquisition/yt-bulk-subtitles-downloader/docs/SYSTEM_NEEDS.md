# Boot System Notes

This folder is the local boot-up copy for AI-HUB, clipboard sync, and the FastAPI backend.

## Canonical Pieces

- FastAPI backend: `D:\DONT TOUCH BOOT UP\AHK\sync_server.py`
- Clipboard AHK bridge: `D:\DONT TOUCH BOOT UP\AHK\clipsync-bridge\clipsync_bridge.ahk`
- Main AHK entry: `D:\DONT TOUCH BOOT UP\AHK\AI-HUB.ahk`
- Shared config: `D:\DONT TOUCH BOOT UP\AHK\config\bridge.ini`
- Service endpoint config: `D:\DONT TOUCH BOOT UP\AHK\config\services.ini`
- Logs: `D:\DONT TOUCH BOOT UP\AHK\logs`

## What Was Added

- Restored the missing `clipsync-bridge` folder expected by `modules\manifest.ahk`.
- Added a clipboard read retry helper in the bridge so locked clipboard reads do not crash the script.
- Added `tools\start_fastapi.ps1` to start `sync_server.py` on port 3456.
- Added `tools\verify_bootup.ps1` to check files, Python, AutoHotkey, port 3456, and `/health`.
- Added `tools\deploy_to_startup.ps1` to copy this canonical set back to the network startup folder.
- Updated `AI-HUB.ahk` so boot-up starts the local FastAPI server from this folder instead of an external repo path.

## Recommended Rule

Treat this D: folder as the stable boot-up source. Edit here first, verify here, then deploy outward with `tools\deploy_to_startup.ps1`.
