#Requires AutoHotkey v2.0+
#SingleInstance Force
global SERVICES_INI := FileExist(A_ScriptDir "\..\config\services.ini")
    ? A_ScriptDir "\..\config\services.ini"
    : A_ScriptDir "\config\services.ini"
global BRIDGE_INI := FileExist(A_ScriptDir "\..\config\bridge.ini")
    ? A_ScriptDir "\..\config\bridge.ini"
    : A_ScriptDir "\config\bridge.ini"
global LOG_DIR := A_ScriptDir "\..\logs"
global LOG_FILE := LOG_DIR "\clipsync_bridge.log"
global LAST_CLIP := ""
global READ_RETRIES := Integer(IniRead(BRIDGE_INI, "clipboard", "read_retries", "5"))
global READ_RETRY_MS := Integer(IniRead(BRIDGE_INI, "clipboard", "read_retry_ms", "50"))
global POLL_MS := Integer(IniRead(BRIDGE_INI, "clipboard", "poll_ms", "800"))

DirCreate(LOG_DIR)
LAST_CLIP := ReadClipboardText()
Log("bridge start | services=" SERVICES_INI " | poll_ms=" POLL_MS)
OnClipboardChange(ClipChanged)

ClipChanged(*) {
    CaptureClipboard("event")
}

PollClipboard() {
    CaptureClipboard("poll")
}

CaptureClipboard(source) {
    global LAST_CLIP
    txt := ReadClipboardText()
    if !IsSet(txt) || txt = "" || txt = LAST_CLIP
        return
    LAST_CLIP := txt
    PostClip(txt, source)
}

ReadClipboardText(retries := "", delayMs := "") {
    retries := retries = "" ? READ_RETRIES : retries
    delayMs := delayMs = "" ? READ_RETRY_MS : delayMs
    Loop retries {
        try {
            return A_Clipboard
        } catch {
            if A_Index = retries
                return ""
            Sleep(delayMs)
        }
    }
    return ""
}

PostClip(content, source := "manual") {
    endpointKey := IniRead(SERVICES_INI, "CLIPBOARD", "active", "local")
    baseUrl := IniRead(SERVICES_INI, "CLIPBOARD", endpointKey, "http://localhost:3456")
    title := ClipTitle(content)
    payload := Format('{{"content":{1},"title":{2},"category":"clipboard","tags":["history"],"ts":"{3}"}}', JsonStr(content), JsonStr(title), FormatTime(A_NowUTC, "yyyy-MM-ddTHH:mm:ssZ"))
    http := ComObject("WinHttp.WinHttpRequest.5.1")
    try {
        http.Open("POST", baseUrl "/api/clips", false)
        http.SetRequestHeader("Content-Type", "application/json")
        http.Send(payload)
        Log("post ok | source=" source " | status=" http.Status " | title=" title)
    } catch Error as err {
        Log("post fail | source=" source " | message=" err.Message)
    }
}
ClipTitle(s) {
    for line in StrSplit(s, "`n", "`r") {
        line := Trim(line)
        if line != ""
            return SubStr(line, 1, 80)
    }
    return "Clipboard"
}
JsonStr(s) => '"' StrReplace(StrReplace(StrReplace(StrReplace(StrReplace(s, "\", "\\"), '"', '\"'), "`r", "\r"), "`n", "\n"), "`t", "\t") '"'

Log(message) {
    global LOG_FILE
    try FileAppend(FormatTime(A_Now, "yyyy-MM-dd HH:mm:ss") " | " message "`n", LOG_FILE, "UTF-8")
}

^!s:: {
    txt := ReadClipboardText()
    if txt != ""
        PostClip(txt, "hotkey")
}

; Poll via timer — MUST NOT use a blocking Loop here.
; This file is #included by modules\manifest.ahk; a top-level infinite
; loop blocks AI-HUB's auto-execute thread and Hub_Boot() never runs
; (no GUI, no tray). Timer preserves polling in both standalone and
; included modes.
SetTimer(PollClipboard, POLL_MS)
