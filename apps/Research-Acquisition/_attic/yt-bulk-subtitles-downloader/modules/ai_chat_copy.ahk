; ============================================================
; MODULE: AI Chat Full-Copy Override
; ------------------------------------------------------------
; Detects Claude Desktop / ChatGPT Desktop windows.
; Ctrl+Shift+C → extract full conversation via Python helper
;   (uses CDP if available, falls back to scroll+copy)
; Regular Ctrl+C still works for selected text.
; ============================================================

global gAICopyScript := A_ScriptDir "\modules\ai_chat_extract.py"

AICopy_IsAIChat() {
    try {
        proc := WinGetProcessName("A")
        if InStr(proc, "claude") || InStr(proc, "Claude")
            return true
        if InStr(proc, "chatgpt") || InStr(proc, "ChatGPT")
            return true
    }
    return false
}

; Ctrl+Shift+C = full conversation extract (only in AI apps)
^+c::{
    if !AICopy_IsAIChat() {
        Send("^+c")  ; passthrough
        return
    }
    AICopy_Extract(false)
}

; Ctrl+Shift+Alt+S = full extract + save to file
^+!s::{
    if !AICopy_IsAIChat() {
        Send("^+!s")
        return
    }
    AICopy_Extract(true)
}

AICopy_Extract(saveFile := false) {
    py := AICopy_FindPython()
    if py = "" {
        ToolTip("Python not found")
        SetTimer(() => ToolTip(), -2000)
        return
    }
    if !FileExist(gAICopyScript) {
        ToolTip("ai_chat_extract.py not found")
        SetTimer(() => ToolTip(), -2000)
        return
    }

    ToolTip("Extracting conversation...")
    args := saveFile ? " --file" : ""
    RunWait('"' py '" "' gAICopyScript '"' args, A_ScriptDir, "Hide")
    ToolTip("Conversation copied!")
    SetTimer(() => ToolTip(), -1500)
}

AICopy_FindPython() {
    candidates := [
        "C:\Users\David\AppData\Local\Programs\Python\Python312\python.exe",
        "C:\Users\David\AppData\Local\Programs\Python\Python311\python.exe",
        "python.exe"
    ]
    for c in candidates {
        if InStr(c, "\") {
            if FileExist(c)
                return c
        } else {
            return c
        }
    }
    return ""
}

if IsSet(HUB_CORE_LOADED)
    ; nothing to register — hotkeys are global
    {}
