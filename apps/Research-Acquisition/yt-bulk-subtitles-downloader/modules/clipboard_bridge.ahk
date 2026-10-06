; ============================================================
; MODULE: Clipboard → Sync Server Bridge
; ------------------------------------------------------------
; Passive listener: OnClipboardChange fires AFTER whatever app
; (ExtraClipboard, Ditto, etc.) finishes its clipboard work.
; No OpenClipboard calls. No polling. No fights.
; Posts text clips to sync_server at 127.0.0.1:3456/api/clips.
; ============================================================

global gClipBridgeUrl := "http://127.0.0.1:3456/api/clips"
global gClipBridgeLastText := ""
global gClipBridgeDebounceTimer := 0

ClipBridge_Boot() {
    OnClipboardChange(ClipBridge_OnChange)
}

ClipBridge_OnChange(dataType) {
    ; dataType 1 = text, 2 = non-text (image/file). Only capture text.
    if dataType != 1
        return
    ; Debounce: some apps fire multiple clipboard changes in rapid succession.
    ; Wait 300ms for things to settle before reading.
    global gClipBridgeDebounceTimer
    if gClipBridgeDebounceTimer
        SetTimer(gClipBridgeDebounceTimer, 0)
    gClipBridgeDebounceTimer := ClipBridge_Capture.Bind()
    SetTimer(gClipBridgeDebounceTimer, -300)
}

ClipBridge_Capture() {
    global gClipBridgeLastText, gClipBridgeUrl
    text := ""
    try text := A_Clipboard ""
    text := Trim(text)
    if text = ""
        return
    if text = gClipBridgeLastText
        return
    ; Skip very short clips (single chars, accidental selections)
    if StrLen(text) < 3
        return
    gClipBridgeLastText := text

    title := ""
    for line in StrSplit(text, "`n", "`r") {
        title := Trim(line)
        if title != ""
            break
    }
    if StrLen(title) > 80
        title := SubStr(title, 1, 80)

    ClipBridge_Post(text, title)
}

ClipBridge_Post(content, title) {
    global gClipBridgeUrl
    body := '{"content":"' ClipBridge_JsonEscape(content)
        . '","title":"' ClipBridge_JsonEscape(title)
        . '","category":"clipboard"'
        . ',"tags":["history","bridge"]}'
    try {
        req := ComObject("WinHttp.WinHttpRequest.5.1")
        req.Open("POST", gClipBridgeUrl, true)  ; async = true so we never block clipboard
        req.SetTimeouts(1000, 1000, 2000, 2000)
        req.SetRequestHeader("Content-Type", "application/json")
        req.Send(body)
        ; Fire and forget — don't wait for response
    } catch {
        ; Server might be down. That's fine — clip is still in ExtraClipboard.
    }
}

ClipBridge_JsonEscape(str) {
    s := str ""
    s := StrReplace(s, "\", "\\")
    s := StrReplace(s, '"', '\"')
    s := StrReplace(s, "`r", "\r")
    s := StrReplace(s, "`n", "\n")
    s := StrReplace(s, "`t", "\t")
    return s
}

; Auto-boot if loaded as part of AI-HUB
if IsSet(HUB_CORE_LOADED)
    ClipBridge_Boot()
