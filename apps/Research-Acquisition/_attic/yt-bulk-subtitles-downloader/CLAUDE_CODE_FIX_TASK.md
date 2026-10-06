# AI-HUB FIX — Claude Code Task
## POF 2828 | July 2026

You are fixing an AHK v2 application that keeps crashing on startup. The hub loads briefly then dies — sometimes within seconds, sometimes after a few minutes. The user can never keep it running.

## The Problem

The main script is `AI-HUB.ahk` which `#include`s `hub_core.ahk` (2900+ lines) and `modules\manifest.ahk` (which includes 15+ module files). One or more of these modules is throwing an unhandled error that kills the entire AHK process. AHK v2 with `#Warn` is unforgiving — one error anywhere and the whole thing dies.

## File Locations

- Entry point: `\\192.168.2.50\h_hp\Desktop\AI HUB DAVID\AHK\AI-HUB.ahk`
- Core: `\\192.168.2.50\h_hp\Desktop\AI HUB DAVID\AHK\hub_core.ahk`
- Module manifest: `\\192.168.2.50\h_hp\Desktop\AI HUB DAVID\AHK\modules\manifest.ahk`
- All modules are in: `\\192.168.2.50\h_hp\Desktop\AI HUB DAVID\AHK\modules\`
- Config: `\\192.168.2.50\h_hp\Desktop\AI HUB DAVID\AHK\config\`
- AHK v2 exe: `C:\Program Files\AutoHotkey\v2\AutoHotkey64.exe`
- Python: `C:\Users\David\AppData\Local\Programs\Python\Python312\python.exe`

## Your Task (in order)

### Step 1: Diagnose
1. Read `AI-HUB.ahk`, `hub_core.ahk`, and `modules\manifest.ahk`
2. Read every module file listed in manifest.ahk
3. Look for:
   - Missing file references (paths that don't exist)
   - Unhandled exceptions (function calls without try/catch)
   - Global variable conflicts between modules
   - Timer callbacks that reference destroyed GUIs
   - Network calls without timeouts (hanging connections that freeze AHK)
   - `#Warn` violations (unset variables, local-same-as-global)
   - Modules that depend on external processes (FastAPI server, Python scripts) that may not be running

### Step 2: Fix
For each issue found:
- Wrap dangerous calls in try/catch
- Add OnError handler to AI-HUB.ahk that logs crashes instead of dying:
```autohotkey
OnError(LogError)
LogError(exception, mode) {
    logFile := A_ScriptDir "\logs\hub_crash.log"
    FileAppend(FormatTime(A_Now, "yyyy-MM-dd HH:mm:ss") " | " exception.Message " | " exception.File ":" exception.Line "`n", logFile)
    return -1  ; suppress the error, keep running
}
```
- Fix or disable modules that reference missing files/servers
- Make all network calls (API calls, localhost server checks) non-blocking with timeouts
- Make sure SetTimer callbacks are wrapped in try/catch
- Make the FastAPI server launch failure non-fatal (the hub should work without it)

### Step 3: Add Resilience
- Add the OnError crash logger as the FIRST line after #Requires
- Add a heartbeat log: every 60 seconds, append a timestamp to `logs\hub_heartbeat.log` so David can see when it died
- Make every `#include` in manifest.ahk load through a wrapper that catches failures and logs them without killing the hub
- If a module fails to load, log it and continue — don't take down the whole hub

### Step 4: Also fix Ctrl+Space
The `SmartFixActiveWindow()` function at line ~2668 of hub_core.ahk calls `CallAI()` which uses OpenAI or Claude. Add DeepSeek as a third provider option:
- Add "DeepSeek" to the provider dropdown in BuildSettingsTab
- Add a DeepSeek API key field and model field (default: `deepseek-chat`)
- Add `CallDeepSeek()` function matching the pattern of `CallOpenAI()` and `CallClaude()`
- DeepSeek endpoint: `https://api.deepseek.com/chat/completions`
- DeepSeek uses the same request format as OpenAI (Authorization: Bearer)
- Wire it into `CallAI()` so when provider is "DeepSeek" it routes there

### Step 5: Verify
- Run the hub with the fixes
- Confirm it stays alive for at least 5 minutes
- Confirm Ctrl+Space works with DeepSeek
- Confirm the crash log captures any errors instead of dying

## Rules
- Do NOT rewrite the whole hub. Fix what's broken, leave what works.
- Do NOT strip features. Every module should still load if possible.
- If a module is unfixable, disable it with a log message, don't delete it.
- Keep the dark mode theme intact.
- Test after each major change.
- Write a summary of everything you fixed to `\\192.168.2.50\h_hp\Desktop\AI HUB DAVID\AHK\FIX_LOG.md`
