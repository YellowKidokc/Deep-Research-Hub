#Requires AutoHotkey v2.0+
#SingleInstance Force
#Warn
#UseHook

; ============================================================
; AI-HUB v2 — Entry Point
; ============================================================
; Three processes, three tray icons:
;   1. AI-HUB (this)     — main GUI with tabs [shell32 icon]
;   2. ClipSync Bridge    — clipboard + hotkeys [notepad icon]
;   3. BetterTTS          — TTS with normalizer [GHOSTY icon]
;
; On startup also launches:
;   - Theophysics_HUB FastAPI server (serves HTML panels)
;   - Prompt Picker HTML
;   - Research Links HTML
; ============================================================

#include .\hub_core.ahk
#include .\modules\manifest.ahk

; Boot the application (defined in hub_core.ahk)
Hub_Boot()
AIH_IntegrationsBoot()
SetTimer(EnsureHubVisibleAfterBoot, -1200)

EnsureHubVisibleAfterBoot() {
    ; Surface the main hub once after boot so startup does not silently succeed
    ; while leaving the GUI hidden behind the panel launches.
    try ShowGui()
}

; Hardcode always-on-top + remember-pos ON (INI already saves these but apply them directly)
SetTimer(TTS_ForceWindowBehavior, -1500)
TTS_ForceWindowBehavior() {
    global gShell, gAlwaysOnTop, gRememberPos
    gAlwaysOnTop := true
    gRememberPos := true
    try WinSetAlwaysOnTop(1, "ahk_id " gShell.gui.Hwnd)
    try {
        gShell.chkAlwaysOnTop.Value := 1
        gShell.chkAlwaysOnTop.Text  := "ON"
        gShell.chkRememberPos.Value := 1
        gShell.chkRememberPos.Text  := "ON"
    }
}

; --- SUBPROCESS 1: Local FastAPI server ---
; Keep boot-up self-contained in D:\DONT TOUCH BOOT UP\AHK.
try {
    ps := A_WinDir "\System32\WindowsPowerShell\v1.0\powershell.exe"
    fastApiStart := A_ScriptDir "\tools\start_fastapi.ps1"
    if FileExist(fastApiStart)
        Run('"' ps '" -ExecutionPolicy Bypass -File "' fastApiStart '"', A_ScriptDir, "Hide")
}

; --- SUBPROCESS 2: ClipSync hotkeys/UI bridge (AHK) ---
; Disabled here because the bridge is already loaded through modules\manifest.ahk.
; Running it again creates duplicate timers/hotkeys and extra tray noise.
; try Run(A_ScriptDir "\clipsync-bridge\clipsync_bridge.ahk")

; --- SUBPROCESS 3: BetterTTS (AHK, own tray icon) ---
; DISABLED - TTS now embedded in hub TTS tab
; try Run(A_ScriptDir "\BetterTTS\BetterTTS.ahk")

; --- SUBPROCESS 4: Clipboard Manager ---
; DISABLED — Clipboard.ahk does not exist in clipboard\ folder
; try Run(A_ScriptDir "\clipboard\Clipboard.ahk")

; YouTube transcript watcher runs inside modules\YT_TranscriptWatcher.ahk.
; Shortcut: Ctrl+Alt+Shift+Y asks against the active YouTube tab.

; --- HTML PANELS: Launch after server has time to start ---
SetTimer(LaunchStartupPanels, -6000)

StartupPanelEnabled(key, default := "1") {
    global CONFIG_FILE
    try return IniRead(CONFIG_FILE, "StartupPanels", key, default) = "1"
    catch
        return default = "1"
}

LaunchStartupPanels() {
    ; FastAPI is started locally by tools\start_fastapi.ps1.
    if StartupPanelEnabled("clipboard")
        LaunchHtmlPanel("http://127.0.0.1:3456/clipboard3", "POF-Clipboard")
    if StartupPanelEnabled("prompts")
        LaunchHtmlPanel("http://127.0.0.1:3456/prompts", "POF-Prompts")
    if StartupPanelEnabled("links")
        LaunchHtmlPanel("http://127.0.0.1:3456/links", "POF-Links")
    if StartupPanelEnabled("calendar")
        LaunchHtmlPanel("http://127.0.0.1:3456/calendar", "POF-Calendar")
    if StartupPanelEnabled("deepcrawl")
        LaunchHtmlPanel("https://deepcrawl-ui.dlowehomelab.com", "POF-Deepcrawl")
    if StartupPanelEnabled("n8n")
        LaunchHtmlPanel("https://n8n.dlowehomelab.com", "POF-n8n")
    if StartupPanelEnabled("search")
        LaunchHtmlPanel("https://search.dlowehomelab.com", "POF-Search")
}

; Clipboard ingestion now lives in the current Theophysics_HUB Python server.
; Keep AHK focused on GUI, hotkeys, and OS-level actions.
