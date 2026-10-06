; ============================================================
; TextCleanup.ahk — Ctrl+Space to clean selected text
; POF 2828 | AHK v2
;
; Select text -> Ctrl+Space -> cleaned text replaces selection
; Requires: text_cleanup_server.py running on port 10790
; ============================================================
#Requires AutoHotkey v2.0
#SingleInstance Force

Global CleanupURL := "http://127.0.0.1:10790/clean"

TrayTip "Text Cleanup", "Ctrl+Space to clean selected text", 3

; ============================================================
; Ctrl+Space — clean selected text
; ============================================================
^Space:: {
    global CleanupURL

    ; Save clipboard
    clipSave := ClipboardAll()
    A_Clipboard := ""

    ; Copy selection
    Send "^c"
    if !ClipWait(1.5) {
        A_Clipboard := clipSave
        TrayTip "Text Cleanup", "No text selected", 3
        return
    }

    rawText := A_Clipboard

    if (StrLen(Trim(rawText)) < 2) {
        A_Clipboard := clipSave
        return
    }

    ; Show working indicator
    ToolTip "Cleaning..."

    ; Call server
    try {
        whr := ComObject("WinHttp.WinHttpRequest.5.1")
        whr.Open("POST", CleanupURL, false)
        whr.SetRequestHeader("Content-Type", "text/plain; charset=utf-8")
        whr.SetTimeouts(2000, 5000, 5000, 120000)
        whr.Send(rawText)
        whr.WaitForResponse()

        if (whr.Status = 200) {
            cleaned := whr.ResponseText

            ; Paste cleaned text
            A_Clipboard := cleaned
            Send "^v"
            Sleep 100
        } else {
            TrayTip "Text Cleanup", "Server error: " whr.Status, 3
        }
    } catch as e {
        TrayTip "Text Cleanup", "Connection failed — is the server running?", 3
    }

    ; Restore clipboard after short delay
    SetTimer () => (A_Clipboard := clipSave), -1500

    ToolTip
}
