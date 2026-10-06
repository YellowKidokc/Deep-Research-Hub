; ============================================================
; AI Chat Controller v3 — AutoHotkey v2
; Two-tab design: [CONTROLS] [CONFIG]
; Functional-first. Resizable. Bind + test sequence.
;
; BIND: finds window → clicks input area → types space →
;       deletes it → confirms BOUND+TESTED or shows failure
;
; HOTKEYS (Ctrl+Alt+Shift+):
;   V = Paste+Send   Enter = Send   B = Bind
;   A = AutoScroll   M = Mic        Q = Quit
;   1-6 = Switch profile
; ============================================================

#Requires AutoHotkey v2.0
#SingleInstance Force
Persistent

; ── CONFIG ──────────────────────────────────────────────────
FILE_DROP_URL := "http://localhost:8100/file-drop"
HUB_BASE_URL  := EnvGet("FIHUB_BASE_URL")
if (HUB_BASE_URL = "")
    HUB_BASE_URL := "http://127.0.0.1:10000"
HUB_TOKEN     := EnvGet("FIHUB_TOKEN")

FOLLOW_MS  := 80
SCROLL_MS  := 80
scrollSpeed := 3
isScrolling := false
isAnchored  := false
anchorHwnd  := 0
activeIdx   := 1
activeTab   := "controls"   ; "controls" or "config"

; ── PROFILES ────────────────────────────────────────────────
; [name, proc, titleMatch, offR, offB, inpH, apiKey]
global profiles := [
    ["Claude",     "chrome.exe",  "Claude",     420, 220, 50,  ""],
    ["ChatGPT",    "chrome.exe",  "ChatGPT",    420, 220, 50,  ""],
    ["Kimi",       "kimi.exe",    "Kimi",       420, 220, 50,  ""],
    ["Codex",      "Codex.exe",   "Codex",      420, 200, 110, ""],
    ["TypingMind", "chrome.exe",  "TypingMind", 420, 220, 50,  ""],
    ["Gemini",     "chrome.exe",  "Gemini",     420, 220, 50,  ""],
]

P() {
    global activeIdx
    return profiles[activeIdx]
}

; ── GUI ─────────────────────────────────────────────────────
g := Gui("+AlwaysOnTop +ToolWindow -Caption +Resize +MinSize460x170")
g.BackColor := "111111"
g.MarginX := 6
g.MarginY := 4
g.SetFont("s8", "Segoe UI")

; ── TAB STRIP (manual — two buttons acting as tabs) ─────────
btnTabCtrl := g.Add("Button", "x4 y3 w90 h22", "CONTROLS")
btnTabCfg  := g.Add("Button", "x97 y3 w80 h22", "CONFIG")
g.SetFont("s7", "Consolas")
lblStatus := g.Add("Text", "x182 y7 w200 h16 cSilver", "Ready.")
g.SetFont("s8", "Segoe UI")
btnQuit := g.Add("Button", "xp+240 y3 w36 h22", "✕")

g.Add("Text", "x0 y27 w800 h1 Background333333", "")   ; divider

; ══════════════════════════════════════════════════════════════
;  CONTROLS TAB
; ══════════════════════════════════════════════════════════════

; Profile row
g.SetFont("s7 Bold", "Consolas")
g.Add("Text", "x4 y33 w28 h16 cSilver", "APP:")
g.SetFont("s8", "Segoe UI")
profileBtns := []
xp := 34
for i, prof in profiles {
    b := g.Add("Button", "x" xp " y31 w70 h20", prof[1])
    b.OnEvent("Click", MakeProfileSwitcher(i))
    profileBtns.Push(b)
    xp += 73
}

; Anchor row
g.SetFont("s7", "Consolas")
anchorLabel := g.Add("Text", "x4 y55 w340 h16 cSilver", "Not bound — click BIND or Ctrl+Alt+Shift+B")
btnBind := g.Add("Button", "x348 y52 w80 h22", "⊕  BIND")

; Action row 1
btnPaste  := g.Add("Button", "x4   y80 w100 h28", "PASTE + SEND")
btnSend   := g.Add("Button", "x107 y80 w70  h28", "SEND ↵")
btnMic    := g.Add("Button", "x180 y80 w46  h28", "🎤 MIC")
btnScroll := g.Add("Button", "x229 y80 w90  h28", "⏬ SCROLL")
g.SetFont("s7", "Consolas")
g.Add("Text", "x323 y88 w26 h14 cSilver", "Spd:")
speedCtrl := g.Add("Edit", "x350 y85 w32 h18 Number Center", String(scrollSpeed))
g.SetFont("s8", "Segoe UI")

; Action row 2
btnPull   := g.Add("Button", "x4   y111 w70  h24", "📥 PULL")
btnPush   := g.Add("Button", "x77  y111 w70  h24", "📤 PUSH")
btnMem    := g.Add("Button", "x150 y111 w86  h24", "💾 MEMORY")
btnHub    := g.Add("Button", "x239 y111 w60  h24", "HUB")
btnEndAll := g.Add("Button", "x302 y111 w76  h24", "⛔ END ALL")

; Command line
g.SetFont("s7 Bold", "Consolas")
g.Add("Text", "x4 y140 w10 h18 cYellow", ">")
g.SetFont("s8", "Consolas")
cmdInput := g.Add("Edit", "x16 y139 w370 h20", "")
btnRun   := g.Add("Button", "x389 y139 w36 h20", "↵")

; Controls tab controls — collect for show/hide
ctrlTabCtrls := [
    anchorLabel, btnBind,
    btnPaste, btnSend, btnMic, btnScroll, speedCtrl,
    btnPull, btnPush, btnMem, btnHub, btnEndAll,
    cmdInput, btnRun
]
for b in profileBtns
    ctrlTabCtrls.Push(b)

; ══════════════════════════════════════════════════════════════
;  CONFIG TAB
; ══════════════════════════════════════════════════════════════
g.SetFont("s7 Bold", "Consolas")
cfgHdr   := g.Add("Text",   "x4 y33 w80 h16 cYellow", "API KEYS")
cfgHdr2  := g.Add("Text",   "x4 y33 w500 h16 cGray",  "One key per profile. Stored in memory only — not saved to disk.")

g.SetFont("s7", "Consolas")
keyEdits := []
keyLabels := []
yy := 52
for i, prof in profiles {
    lbl := g.Add("Text",   "x4  y" yy " w70  h16 cSilver", prof[1] ":")
    ed  := g.Add("Edit",   "x78 y" (yy-1) " w300 h18 Password", prof[7])
    ed.SetFont("s8", "Consolas")
    ed.OnEvent("Change", MakeKeySaver(i, ed))
    keyLabels.Push(lbl)
    keyEdits.Push(ed)
    yy += 20
}

g.SetFont("s8", "Segoe UI")
btnShowKeys := g.Add("Button", "x4 y" (yy+4) " w100 h22", "👁 Show Keys")
btnShowKeys.OnEvent("Click", DoToggleShowKeys)

g.SetFont("s7 Bold", "Consolas")
fdLabel := g.Add("Text", "x4 y" (yy+32) " w100 h16 cYellow", "FILE DROP URL:")
g.SetFont("s8", "Consolas")
dropEdit := g.Add("Edit", "x4 y" (yy+48) " w374 h20", FILE_DROP_URL)
dropEdit.OnEvent("Change", (*) => (FILE_DROP_URL := dropEdit.Value))

; Config tab controls — collect for show/hide
cfgTabCtrls := [cfgHdr, cfgHdr2, btnShowKeys, fdLabel, dropEdit]
for c in keyLabels
    cfgTabCtrls.Push(c)
for c in keyEdits
    cfgTabCtrls.Push(c)

; ── WIRE EVENTS ─────────────────────────────────────────────
btnTabCtrl.OnEvent("Click", (*) => ShowTab("controls"))
btnTabCfg.OnEvent("Click",  (*) => ShowTab("config"))
btnQuit.OnEvent("Click",    DoQuit)
btnBind.OnEvent("Click",    DoBind)
btnPaste.OnEvent("Click",   DoPasteSend)
btnSend.OnEvent("Click",    DoSend)
btnMic.OnEvent("Click",     DoVoice)
btnScroll.OnEvent("Click",  DoToggleScroll)
btnPull.OnEvent("Click",    DoPullFile)
btnPush.OnEvent("Click",    DoPushClip)
btnMem.OnEvent("Click",     DoSaveMemory)
btnHub.OnEvent("Click",     DoHubStats)
btnEndAll.OnEvent("Click",  DoEndAll)
btnRun.OnEvent("Click",     DoRunCmd)
speedCtrl.OnEvent("Change", DoSpeedChange)
g.OnEvent("Size",  DoGuiSize)
g.OnEvent("Close", DoQuit)

; Enter key in cmdInput
OnMessage(0x0100, OnKeyDown)
OnKeyDown(wParam, lParam, msg, hwnd) {
    if (hwnd = cmdInput.Hwnd && wParam = 13) {
        DoRunCmd()
        return 0
    }
}

; Draggable
OnMessage(0x0201, WM_LBUTTONDOWN)
WM_LBUTTONDOWN(wParam, lParam, msg, hwnd) {
    if (hwnd = g.Hwnd)
        PostMessage(0xA1, 2, 0, , g.Hwnd)
}

; ── HOTKEYS ─────────────────────────────────────────────────
Hotkey("^!+v",     DoPasteSend,   "On")
Hotkey("^!+Enter", DoSend,        "On")
Hotkey("^!+b",     DoBind,        "On")
Hotkey("^!+a",     DoToggleScroll,"On")
Hotkey("^!+m",     DoVoice,       "On")
Hotkey("^!+p",     DoPushClip,    "On")
Hotkey("^!+r",     DoPullFile,    "On")
Hotkey("^!+q",     DoQuit,        "On")
Loop 6
    Hotkey("^!+" A_Index, MakeProfileSwitcher(A_Index), "On")

; ── TIMERS ──────────────────────────────────────────────────
SetTimer(FollowTarget, FOLLOW_MS)

; ── INITIAL STATE ───────────────────────────────────────────
ShowTab("controls")
UpdateProfileHighlight()
g.Show("w434 h170 x100 y100")

; ============================================================
;  TAB SWITCHING
; ============================================================
ShowTab(tabName) {
    global activeTab
    activeTab := tabName
    if (tabName = "controls") {
        for c in ctrlTabCtrls
            c.Opt("+Visible")
        for c in cfgTabCtrls
            c.Opt("-Visible")
        btnTabCtrl.Opt("Default")
    } else {
        for c in ctrlTabCtrls
            c.Opt("-Visible")
        for c in cfgTabCtrls
            c.Opt("+Visible")
    }
}

; ============================================================
;  PROFILE SWITCHING
; ============================================================
MakeProfileSwitcher(idx) {
    return (*) => SwitchProfile(idx)
}

SwitchProfile(idx) {
    global activeIdx
    if (idx < 1 || idx > profiles.Length)
        return
    activeIdx := idx
    isAnchored := false
    anchorHwnd := 0
    anchorLabel.Text := "Not bound — click BIND"
    anchorLabel.SetFont("s7 c" "Silver", "Consolas")
    UpdateProfileHighlight()
    SetStatus(P()[1] " selected.")
}

UpdateProfileHighlight() {
    for i, b in profileBtns {
        if (i = activeIdx)
            b.Opt("Default")
        else
            b.Opt("-Default")
    }
}

; ============================================================
;  BIND + TEST SEQUENCE
; ============================================================
DoBind(*) {
    global isAnchored, anchorHwnd
    prof := P()
    SetStatus("Searching for " prof[1] "...")
    hwnd := 0
    try hwnd := WinExist(prof[3])
    if (!hwnd)
        try hwnd := WinExist("ahk_exe " prof[2])
    if (!hwnd) {
        anchorLabel.Text := "⚠  " prof[1] " not found — is it open?"
        anchorLabel.SetFont("s7 cRed", "Consolas")
        SetStatus("Bind failed.")
        isAnchored := false
        return
    }
    anchorHwnd := hwnd
    isAnchored := true
    WinGetPos(&wx, &wy, &ww, &wh, "ahk_id " hwnd)
    anchorLabel.Text := "Testing " prof[1] " (" ww "x" wh ")..."
    anchorLabel.SetFont("s7 cYellow", "Consolas")
    Sleep(200)
    try {
        WinActivate("ahk_id " anchorHwnd)
        Sleep(250)
        ClickInputArea()
        Sleep(150)
        Send(" ")
        Sleep(100)
        Send("{BackSpace}")
        Sleep(100)
        anchorLabel.Text := "✓  BOUND + TESTED — " prof[1] " (" ww "x" wh ")"
        anchorLabel.SetFont("s7 cLime", "Consolas")
        SetStatus("Ready.")
    } catch as e {
        anchorLabel.Text := "⚠  Bound but test click failed — " e.Message
        anchorLabel.SetFont("s7 cYellow", "Consolas")
        SetStatus("Bound. Test failed — adjust inpH offset if needed.")
    }
}

; ============================================================
;  FOLLOW / ANCHOR
; ============================================================
FollowTarget() {
    global isAnchored, anchorHwnd
    if !isAnchored
        return
    if !WinExist("ahk_id " anchorHwnd) {
        isAnchored := false
        anchorLabel.Text := "⚠  Window closed"
        anchorLabel.SetFont("s7 cRed", "Consolas")
        return
    }
    try {
        prof := P()
        WinGetPos(&wx, &wy, &ww, &wh, "ahk_id " anchorHwnd)
        g.Move(wx + ww - prof[4], wy + wh - prof[5])
    }
}

; ============================================================
;  CORE ACTIONS
; ============================================================
ActivateTarget() {
    global anchorHwnd, isAnchored
    if isAnchored && WinExist("ahk_id " anchorHwnd) {
        WinActivate("ahk_id " anchorHwnd)
        Sleep(150)
    }
}

ClickInputArea() {
    global anchorHwnd
    if !anchorHwnd
        return
    prof := P()
    WinGetPos(&wx, &wy, &ww, &wh, "ahk_id " anchorHwnd)
    Click(wx + (ww // 2), wy + wh - (prof[6] + 30))
    Sleep(100)
}

DoPasteSend(*) {
    SetStatus("Pasting + sending...")
    ActivateTarget()
    ClickInputArea()
    Send("^v")
    Sleep(300)
    Send("{Enter}")
    SetStatus("Sent.")
}

DoSend(*) {
    ActivateTarget()
    Send("{Enter}")
    SetStatus("Sent ↵")
}

DoVoice(*) {
    global anchorHwnd
    ActivateTarget()
    if !anchorHwnd
        return
    WinGetPos(&wx, &wy, &ww, &wh, "ahk_id " anchorHwnd)
    Click(wx + ww - 60, wy + wh - 45)
    SetStatus("Clicked mic.")
}

DoToggleScroll(*) {
    global isScrolling
    isScrolling := !isScrolling
    if isScrolling {
        SetTimer(DoAutoScroll, SCROLL_MS)
        btnScroll.Text := "⏸ STOP SCROLL"
        SetStatus("Auto-scroll ON (speed " scrollSpeed ")")
    } else {
        SetTimer(DoAutoScroll, 0)
        btnScroll.Text := "⏬ SCROLL"
        SetStatus("Auto-scroll OFF")
    }
}

DoAutoScroll() {
    global isScrolling, scrollSpeed, anchorHwnd, isAnchored
    if !isScrolling
        return
    if isAnchored && WinExist("ahk_id " anchorHwnd) {
        try WinActivate("ahk_id " anchorHwnd)
        loop scrollSpeed
            Send("{WheelDown}")
    }
}

DoSpeedChange(*) {
    global scrollSpeed
    val := speedCtrl.Value
    if (val != "" && IsInteger(val) && Integer(val) > 0 && Integer(val) <= 20)
        scrollSpeed := Integer(val)
}

; ============================================================
;  FILE DROP / HUB
; ============================================================
DoPullFile(*) {
    SetStatus("Pulling...")
    try {
        whr := ComObject("WinHttp.WinHttpRequest.5.1")
        whr.Open("GET", FILE_DROP_URL "/list?limit=1", false)
        whr.Send()
        if RegExMatch(whr.ResponseText, '"path"\s*:\s*"([^"]+)"', &m) {
            whr2 := ComObject("WinHttp.WinHttpRequest.5.1")
            whr2.Open("POST", FILE_DROP_URL "/read", false)
            whr2.SetRequestHeader("Content-Type", "application/json")
            whr2.Send('{"path":"' m[1] '"}')
            A_Clipboard := whr2.ResponseText
            SetStatus("📥 " m[1] " → clipboard")
        } else
            SetStatus("No files in drop.")
    } catch as e {
        SetStatus("Pull failed: " e.Message)
    }
}

DoPushClip(*) {
    content := A_Clipboard
    if (content = "") {
        SetStatus("Clipboard empty.")
        return
    }
    DoAPIPush(content, "clip_" FormatTime(, "yyyyMMdd_HHmmss") ".md")
}

DoAPIPush(content, filename) {
    content := StrReplace(content, "\",  "\\")
    content := StrReplace(content, '"',  '\"')
    content := StrReplace(content, "`n", "\n")
    content := StrReplace(content, "`r", "")
    content := StrReplace(content, "`t", "\t")
    whr := ComObject("WinHttp.WinHttpRequest.5.1")
    whr.Open("POST", FILE_DROP_URL "/create", false)
    whr.SetRequestHeader("Content-Type", "application/json")
    whr.Send('{"filename":"' filename '","content":"' content '","source":"ahk-v3"}')
    SetStatus("📤 " filename)
}

DoSaveMemory(*) {
    content := A_Clipboard
    if (content = "") {
        SetStatus("Clipboard empty.")
        return
    }
    src := ""
    try src := WinGetTitle("A")
    body := "{`"body`":`"" JE(content) "`",`"kind`":`"text`",`"source_app`":`"ahk-v3`",`"source_window`":`"" JE(src) "`",`"folder`":`"AI Chat`",`"tags`":`"ahk`",`"pinned`":false}"
    SetStatus("Saving...")
    try {
        HubPost("/clipboard/save", body)
        SetStatus("Memory saved.")
    } catch as e {
        SetStatus("Memory failed: " e.Message)
    }
}

DoEndAll(*) {
    try {
        HubPost("/top-of-mind/controls/end-all", "{}")
        SetStatus("End All sent.")
    } catch as e {
        SetStatus("End All failed: " e.Message)
    }
}

DoHubStats(*) {
    try {
        resp := HubGet("/jobs/stats")
        A_Clipboard := resp
        SetStatus("Hub OK → clipboard.")
    } catch as e {
        SetStatus("Hub: " e.Message)
    }
}

; ============================================================
;  CONFIG ACTIONS
; ============================================================
MakeKeySaver(idx, editCtrl) {
    return (*) => (profiles[idx][7] := editCtrl.Value)
}

keysVisible := false
DoToggleShowKeys(*) {
    global keysVisible
    keysVisible := !keysVisible
    for ed in keyEdits
        ed.Opt(keysVisible ? "-Password" : "+Password")
    btnShowKeys.Text := keysVisible ? "🙈 Hide Keys" : "👁 Show Keys"
}

; ============================================================
;  COMMAND LINE
; ============================================================
DoRunCmd(*) {
    raw := Trim(cmdInput.Value)
    if (raw = "")
        return
    cmdInput.Value := ""
    if (SubStr(raw, 1, 1) != "/") {
        A_Clipboard := raw
        DoPasteSend()
        return
    }
    parts := StrSplit(raw, " ", , 2)
    cmd := StrLower(parts[1])
    arg := (parts.Length > 1) ? parts[2] : ""
    switch cmd {
        case "/send":
            if (arg != "") {
                A_Clipboard := arg
                DoPasteSend()
            } else
                DoSend()
        case "/paste":   DoPasteSend()
        case "/pull":    DoPullFile()
        case "/push":
            if (arg != "")
                DoAPIPush(arg, "cmd_" FormatTime(,"yyyyMMdd_HHmmss") ".md")
            else
                DoPushClip()
        case "/scroll":  DoToggleScroll()
        case "/speed":
            if (arg != "" && IsInteger(arg)) {
                scrollSpeed := Integer(arg)
                speedCtrl.Value := arg
            }
        case "/bind":    DoBind()
        case "/mic":     DoVoice()
        case "/hub":     DoHubStats()
        case "/memory":  DoSaveMemory()
        case "/endall":  DoEndAll()
        case "/profile":
            if (arg != "" && IsInteger(arg))
                SwitchProfile(Integer(arg))
        case "/shell":
            if (arg != "") {
                try {
                    sh := ComObject("WScript.Shell")
                    ex := sh.Exec("cmd.exe /c " arg)
                    out := ex.StdOut.ReadAll()
                    A_Clipboard := out
                    SetStatus("Shell → clipboard (" StrLen(out) "c)")
                } catch as e
                    SetStatus("Shell: " e.Message)
            }
        case "/key":
            kp := StrSplit(arg, " ", , 2)
            if (kp.Length = 2) {
                for i, prof in profiles {
                    if (StrLower(prof[1]) = StrLower(kp[1])) {
                        profiles[i][7] := kp[2]
                        keyEdits[i].Value := kp[2]
                        SetStatus("Key set: " prof[1])
                        break
                    }
                }
            }
        case "/help":
            SetStatus("/send /paste /pull /push /scroll /speed /bind /mic /hub /memory /endall /profile /shell /key /quit")
        case "/quit":    DoQuit()
        default:         SetStatus("Unknown: " cmd)
    }
}

; ============================================================
;  RESIZE
; ============================================================
DoGuiSize(guiObj, minMax, width, height) {
    ; Title strip
    lblStatus.Move(182, 7, width - 232, 16)
    btnQuit.Move(width - 40, 3, 36, 22)
    ; Anchor label (controls tab)
    anchorLabel.Move(4, 55, width - 92, 16)
    btnBind.Move(width - 88, 52, 80, 22)
    ; Command input (controls tab)
    cmdInput.Move(16, height - 31, width - 60, 20)
    btnRun.Move(width - 40, height - 31, 36, 20)
    ; Status label
    lblStatus.Move(182, 7, Max(60, width - 240), 16)
}

; ============================================================
;  UTILITIES
; ============================================================
SetStatus(msg) {
    lblStatus.Text := SubStr(msg, 1, 80)
}

JE(v) {   ; JSON escape
    v := StrReplace(v, "\",  "\\")
    v := StrReplace(v, '"',  '\"')
    v := StrReplace(v, "`r", "\r")
    v := StrReplace(v, "`n", "\n")
    v := StrReplace(v, "`t", "\t")
    return v
}

HubRequest(method, path, body := "") {
    whr := ComObject("WinHttp.WinHttpRequest.5.1")
    whr.SetTimeouts(2000, 2000, 5000, 5000)
    whr.Open(method, RTrim(HUB_BASE_URL, "/") path, false)
    if (HUB_TOKEN != "")
        whr.SetRequestHeader("X-FIHUB-Token", HUB_TOKEN)
    if (body != "")
        whr.SetRequestHeader("Content-Type", "application/json")
    whr.Send(body)
    if (whr.Status < 200 || whr.Status >= 300)
        throw Error("HTTP " whr.Status)
    return whr.ResponseText
}

HubGet(path) {
    return HubRequest("GET", path)
}
HubPost(path, body) {
    return HubRequest("POST", path, body)
}

DoQuit(*) {
    ExitApp()
}
