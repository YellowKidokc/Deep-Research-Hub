; ============================================================
; SmartFix.ahk — STANDALONE Ctrl+Space text fixer
; POF 2828 | AHK v2 | Uses DeepSeek API directly
;
; SELECT TEXT → Ctrl+Space → fixed text replaces it
; No server needed. No hub needed. Just this file + API key.
;
; SETUP: Edit the API key below, then double-click to run.
; ============================================================
#Requires AutoHotkey v2.0
#SingleInstance Force

; ============ CONFIG — EDIT THIS ============
Global API_KEY := "sk-65f60f714a2842ffb638f1443f456858"
Global API_URL := "https://api.deepseek.com/chat/completions"
Global MODEL   := "deepseek-v4-flash"
; ============================================

TrayTip "SmartFix", "Ctrl+Space to fix selected text", 3

^Space:: {
    global API_KEY, API_URL, MODEL

    ; Grab selected text (NOT select-all — just what's highlighted)
    savedClip := ClipboardAll()
    A_Clipboard := ""
    Send "^c"
    if !ClipWait(1.5) {
        ; Nothing selected — try select-all as fallback
        Send "^a"
        Sleep 80
        Send "^c"
        if !ClipWait(1.5) {
            A_Clipboard := savedClip
            ToolTip "No text found"
            SetTimer(() => ToolTip(), -1500)
            return
        }
    }

    rawText := A_Clipboard
    A_Clipboard := savedClip

    if StrLen(Trim(rawText)) < 3 {
        ToolTip "Text too short"
        SetTimer(() => ToolTip(), -1500)
        return
    }

    ToolTip "Fixing..."

    ; Build JSON payload
    sysMsg := "This is rough voice-to-text from a speaker who thinks in connected systems. "
    sysMsg .= "The transmission is noisy but the signal is coherent. "
    sysMsg .= "Find the coherent structure underneath the incoherent delivery. "
    sysMsg .= "Sentences that repeat are one sentence trying to form — find its final shape. "
    sysMsg .= "The speaker often delivers the conclusion before the setup — restructure so the reader gets setup then conclusion. "
    sysMsg .= "Never add ideas the speaker didn't say. Never soften claims. Never hedge what was stated plainly. "
    sysMsg .= "Keep the same register — casual stays casual, intense stays intense. "
    sysMsg .= "Aim for half the original length. "
    sysMsg .= "Return ONLY the cleaned text. No explanations, no markdown, no quotes."

    payload := '{"model":"' MODEL '","temperature":0.1,"max_tokens":16384,"messages":['
    payload .= '{"role":"system","content":"' EscJSON(sysMsg) '"},'
    payload .= '{"role":"user","content":"' EscJSON(rawText) '"}'
    payload .= ']}'

    ; Call DeepSeek API
    try {
        whr := ComObject("WinHttp.WinHttpRequest.5.1")
        whr.SetTimeouts(3000, 8000, 8000, 120000)
        whr.Open("POST", API_URL, false)
        whr.SetRequestHeader("Content-Type", "application/json")
        whr.SetRequestHeader("Authorization", "Bearer " API_KEY)
        whr.Send(payload)

        if whr.Status != 200 {
            ToolTip "API error: " whr.Status
            SetTimer(() => ToolTip(), -3000)
            return
        }

        resp := whr.ResponseText

        ; Extract content from response
        if RegExMatch(resp, '"content"\s*:\s*"((?:[^"\\]|\\.)*)"', &m) {
            cleaned := m[1]
            ; Unescape JSON
            cleaned := StrReplace(cleaned, "\n", "`n")
            cleaned := StrReplace(cleaned, "\r", "`r")
            cleaned := StrReplace(cleaned, "\t", "`t")
            cleaned := StrReplace(cleaned, '\"', '"')
            cleaned := StrReplace(cleaned, "\\", "\")

            ; Strip markdown fences if model wraps them
            fence := Chr(96) Chr(96) Chr(96)
            if SubStr(cleaned, 1, 3) = fence {
                cleaned := RegExReplace(cleaned, "s)^" fence "[a-zA-Z0-9_-]*\R?", "")
                cleaned := RegExReplace(cleaned, "s)\R?" fence "$", "")
                cleaned := Trim(cleaned)
            }

            ; Paste result
            A_Clipboard := cleaned
            ClipWait(1)
            Send "^v"
            Sleep 100

            ; Restore clipboard
            SetTimer(() => (A_Clipboard := savedClip), -1500)

            ToolTip "Fixed! (Ctrl+Z to undo)"
            SetTimer(() => ToolTip(), -2000)
        } else {
            ToolTip "Couldn't parse response"
            SetTimer(() => ToolTip(), -3000)
        }
    } catch as e {
        ToolTip "Error: " e.Message
        SetTimer(() => ToolTip(), -3000)
    }
}

EscJSON(str) {
    str := StrReplace(str, "\", "\\")
    str := StrReplace(str, '"', '\"')
    str := StrReplace(str, "`n", "\n")
    str := StrReplace(str, "`r", "\r")
    str := StrReplace(str, "`t", "\t")
    return str
}
