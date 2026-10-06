; ============================================================
; MODULE MANIFEST
; Add new modules here. Each module can:
;  - RegisterTab(name, buildFn, order)
;  - Add hotkeys/hotstrings
;  - Add helper functions/classes
; ============================================================

; Utilities: quick toggles (Always On Top, Remember Position) and mini scripts
#include utilities_tab.ahk

; Smooth wheel scrolling disabled: global wheel hooks were interfering with normal work.
; #include smooth_scroll.ahk

; Auto-Clicker: multi-slot coordinate clicker with sequential mode
#include autoclicker.ahk

; Hotkey Menu: Ctrl+Shift+Z prompt menu (select text → AI process)
#include hotkey_menu.ahk

; Research Links: URL repository with categories, search, click-to-open
#include research_links.ahk

; Overnight Operations: Ollama YAML enrichment, batch analytics, knowledge graphs
#include overnight_ops.ahk

; ClipSync Bridge: Dynamic hotkeys, HTML interfaces (Ctrl+Alt+P/L/S)
#include ..\clipsync-bridge\clipsync_bridge.ahk

; BetterTTS: TTS status and controls tab (process runs separately)
#include bettertts_tab.ahk

; Auto-Backup: copies config + data to backup directory on every startup
#include autobackup.ahk

; Config Sync: import from sync dir on startup, export on close + periodic
#include config_sync.ahk

; YouTube Transcript Watcher: pops "Download transcript?" when you watch
; a YouTube video (~4s dwell). Ctrl+Alt+Y = ask now. Saves markdown to
; \\192.168.2.50\Export\YouTube Transcripts via yt_transcript_fetch.py
#include YT_TranscriptWatcher.ahk

; Source-preserved companion tools, launched as isolated AHK v2 processes
#include external_integrations.ahk

; NOTE: Clipboard Manager now lives in .\clipboard\ as a standalone app

; Conversation Exporter: save active browser/AI conversation to E:\Exports
#include conversation_exporter.ahk

; Window Tools: monitor-aware center/resize/snap controls
#include window_tools.ahk

; Unified highlight popup: LLM + Stratum + ExtraClipboard slots, ~2s fade
#include highlight_chooser.ahk

; Clipboard tab: hot slots + synced history from sync_server
#include clipboard_tab.ahk

; Clipboard Bridge: passive OnClipboardChange → sync_server (no OpenClipboard fights)
#include clipboard_bridge.ahk

; AI Chat Copy: Ctrl+Shift+C extracts full conversation from Claude/ChatGPT desktop
#include ai_chat_copy.ahk

