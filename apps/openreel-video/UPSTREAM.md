# OpenReel Video — Upstream Record

**Source:** https://github.com/Augani/openreel-video.git  
**Imported:** 2026-10-29  
**License:** MIT (see LICENSE)

## Local changes for Deep Research Hub integration

- Removed the upstream `.git` folder so this is a plain subtree of files inside `apps/openreel-video`.
- Added `START_OPENREEL_WEB.bat` so the hub (and the standalone batch menu) can start the browser-based editor.
- Added to `hub/launch.json` as app `openreel-video`.
- Added to `START_HUB.bat` as menu option `[6]`.
- Added OpenReel checks to `TROUBLESHOOT_HUB.bat`.

Everything else is unchanged from upstream.
