; ============================================================
; MODULE: Unified Highlight Popup
; ------------------------------------------------------------
; Drag-select text -> one small popup with:
;   LLM  |  Stratum  |  Copy
;   ExtraClipboard slots 1-9
;
; Idle fade-out ~2 seconds if unused.
; Toggle: Ctrl+Alt+H  (also tray "Highlight Chooser")
; ============================================================

; Highlight strip OFF — was stealing focus from terminals / paste.
; Re-enable later with Ctrl+Alt+H only if needed (hooks stay registered but gated).
global gHCEnabled        := false
global gHCPosition       := "cursor"
global gHCDragThreshold  := 30
global gHCMinHoldMs      := 120
global gHCDownX          := 0
global gHCDownY          := 0
global gHCDownTick       := 0
global gHCLastText       := ""
global gHCPopup          := ""
global gHCOpenedAt       := 0
global gHCIdleMs         := 2000
global gHCFadeStartMs    := 1400
global gHCDragHwnds      := Map()
global gHCFadeLevel      := 255

OnMessage(0x0201, HC_OnLButtonDown)  ; WM_LBUTTONDOWN — drag chrome

HC_MakeDraggable(guiObj) {
    global gHCDragHwnds
    try gHCDragHwnds[guiObj.Hwnd] := true
}

HC_OnLButtonDown(wParam, lParam, msg, hwnd) {
    global gHCDragHwnds, gHCOpenedAt
    if gHCDragHwnds.Has(hwnd) {
        gHCOpenedAt := A_TickCount  ; touching chrome cancels idle close
        try PostMessage(0xA1, 2, 0, , "ahk_id " hwnd)
        return 0
    }
}

if IsSet(HUB_CORE_LOADED) {
    try A_TrayMenu.Add("Highlight Chooser", HC_ToggleFromTray)
    try (gHCEnabled ? A_TrayMenu.Check("Highlight Chooser") : A_TrayMenu.UnCheck("Highlight Chooser"))
    try A_TrayMenu.Add("Popup Position: cursor", HC_CyclePosition)
}

HC_CyclePosition(*) {
    global gHCPosition
    gHCPosition := (gHCPosition = "cursor") ? "left"
                 : (gHCPosition = "left")   ? "right"
                 : "cursor"
    try A_TrayMenu.Rename("Popup Position: cursor", "Popup Position: " gHCPosition)
    try A_TrayMenu.Rename("Popup Position: left",   "Popup Position: " gHCPosition)
    try A_TrayMenu.Rename("Popup Position: right",  "Popup Position: " gHCPosition)
    ToolTip("Highlight popup: " gHCPosition)
    SetTimer(() => ToolTip(), -1200)
}

HC_ToggleFromTray(*) {
    HC_Toggle()
}

HC_Toggle(*) {
    global gHCEnabled
    gHCEnabled := !gHCEnabled
    try (gHCEnabled ? A_TrayMenu.Check("Highlight Chooser") : A_TrayMenu.UnCheck("Highlight Chooser"))
    ToolTip("Highlight Chooser " (gHCEnabled ? "ON" : "OFF"))
    SetTimer(() => ToolTip(), -1200)
}

^!h::HC_Toggle()

; Drag detection REMOVED 2026-07-30 — highlight popup was interfering with
; terminals and paste. Use Ctrl+Alt+H + manual tray if we reintroduce it.
; ~LButton::HC_MouseDown()
; ~LButton Up::HC_MouseUp()

HC_MouseDown() {
    global gHCDownX, gHCDownY, gHCDownTick
    try {
        CoordMode("Mouse", "Screen")
        MouseGetPos(&x, &y)
        gHCDownX := x, gHCDownY := y
        gHCDownTick := A_TickCount
    }
}

HC_MouseUp() {
    global gHCEnabled, gHCDownX, gHCDownY, gHCDownTick, gHCDragThreshold, gHCMinHoldMs
    if !gHCEnabled
        return
    try {
        CoordMode("Mouse", "Screen")
        MouseGetPos(&x, &y)
        dist := Abs(x - gHCDownX) + Abs(y - gHCDownY)
        held := A_TickCount - gHCDownTick
        if (dist < gHCDragThreshold || held < gHCMinHoldMs)
            return
        ; Let the app finish selecting; avoid racing Ditto/ExtraClipboard.
        SetTimer(HC_TryShow, -180)
    }
}

HC_TryShow() {
    global gHCLastText, gSelectedText, gHCPopup
    try {
        if (gHCPopup != "" && WinActive("ahk_id " gHCPopup.Hwnd))
            return

        sel := CaptureSelectedText(0.45)
        sel := Trim(sel, " `t`r`n")
        if (sel = "")
            return

        gSelectedText := sel
        gHCLastText := sel
        HC_ShowChooser(sel)
    }
}

HC_ShowChooser(sel) {
    global gHCPopup, gHCOpenedAt, gHCIdleMs, gHCFadeStartMs, gHCFadeLevel

    try (gHCPopup != "" && gHCPopup.Destroy())
    gHCPopup := ""
    gHCFadeLevel := 255

    CoordMode("Mouse", "Screen")
    MouseGetPos(&mx, &my)

    g := Gui("+AlwaysOnTop -Caption +ToolWindow +Border", "Highlight")
    g.BackColor := "111115"
    g.MarginX := 8
    g.MarginY := 8
    g.SetFont("s8 c888888", "Segoe UI")

    if (VerCompare(A_OSVersion, "10.0.17763") >= 0) {
        attr := (VerCompare(A_OSVersion, "10.0.18985") >= 0) ? 20 : 19
        try DllCall("dwmapi\DwmSetWindowAttribute", "Ptr", g.hWnd, "Int", attr, "Int*", true, "Int", 4)
    }

    preview := StrReplace(SubStr(sel, 1, 52), "`n", " ")
    if (StrLen(sel) > 52)
        preview .= "..."
    g.Add("Text", "xm w248", "SELECTED:  " preview)

    g.SetFont("s10 Bold cFFFFFF", "Segoe UI")
    btnLLM := g.Add("Button", "xm w80 h32", "LLM")
    btnLLM.OnEvent("Click", (*) => HC_Pick(g, "llm"))
    try DllCall("uxtheme\SetWindowTheme", "Ptr", btnLLM.hWnd, "Str", "DarkMode_Explorer", "Ptr", 0)

    btnStratum := g.Add("Button", "x+4 yp w100 h32", "Stratum")
    btnStratum.OnEvent("Click", (*) => HC_Pick(g, "stratum"))
    try DllCall("uxtheme\SetWindowTheme", "Ptr", btnStratum.hWnd, "Str", "DarkMode_Explorer", "Ptr", 0)

    btnCopy := g.Add("Button", "x+4 yp w60 h32", "Copy")
    btnCopy.OnEvent("Click", (*) => HC_Pick(g, "copy"))
    try DllCall("uxtheme\SetWindowTheme", "Ptr", btnCopy.hWnd, "Str", "DarkMode_Explorer", "Ptr", 0)

    g.SetFont("s8 c888888", "Segoe UI")
    g.Add("Text", "xm w248 y+8", "ExtraClipboard slots")
    g.SetFont("s10 Bold cFFFFFF", "Segoe UI")
    loop 9 {
        slotId := A_Index
        opts := (slotId = 1) ? "xm w24 h26" : "x+3 yp w24 h26"
        btn := g.Add("Button", opts, slotId)
        btn.OnEvent("Click", HC_SaveSlot.Bind(g, slotId))
        try DllCall("uxtheme\SetWindowTheme", "Ptr", btn.hWnd, "Str", "DarkMode_Explorer", "Ptr", 0)
    }

    g.SetFont("s8 c666666", "Segoe UI")
    g.Add("Text", "xm w248 y+6", "Fades in 2s if unused · Esc")

    g.OnEvent("Escape", (*) => HC_Close(g))
    HC_MakeDraggable(g)

    g.Show("x-4000 y-4000 AutoSize NoActivate")
    g.GetPos(, , &gw, &gh)
    HC_PlacePopup(g, mx, my, gw, gh)
    gHCPopup := g
    gHCOpenedAt := A_TickCount
    openedAt := gHCOpenedAt
    SetTimer(() => HC_BeginFade(g, openedAt), -gHCFadeStartMs)
    SetTimer(() => HC_IdleClose(g, openedAt), -gHCIdleMs)
}

HC_BeginFade(g, openedAt) {
    global gHCPopup, gHCOpenedAt, gHCFadeLevel
    if (gHCPopup != g || gHCOpenedAt != openedAt)
        return
    gHCFadeLevel := 255
    SetTimer(() => HC_FadeStep(g, openedAt), 40)
}

HC_FadeStep(g, openedAt) {
    global gHCPopup, gHCOpenedAt, gHCFadeLevel
    if (gHCPopup != g || gHCOpenedAt != openedAt) {
        SetTimer(() => HC_FadeStep(g, openedAt), 0)
        return
    }
    gHCFadeLevel := Max(40, gHCFadeLevel - 30)
    try WinSetTransparent(gHCFadeLevel, "ahk_id " g.Hwnd)
    if gHCFadeLevel <= 40
        SetTimer(() => HC_FadeStep(g, openedAt), 0)
}

HC_IdleClose(g, openedAt) {
    global gHCPopup, gHCOpenedAt
    if (gHCPopup != g || gHCOpenedAt != openedAt)
        return
    HC_Close(g)
}

HC_PlacePopup(g, mx, my, gw, gh) {
    global gHCPosition
    L := 0, T := 0, R := A_ScreenWidth, B := A_ScreenHeight
    try {
        mon := HC_MonitorFromPoint(mx, my)
        MonitorGetWorkArea(mon, &L, &T, &R, &B)
    }
    margin := 10
    if (gHCPosition = "left") {
        px := L + margin
        py := my - (gh // 2)
    } else if (gHCPosition = "right") {
        px := R - gw - margin
        py := my - (gh // 2)
    } else {
        px := mx - (gw // 2)
        py := my - gh - 100
    }
    if (px + gw > R)
        px := R - gw - margin
    if (px < L)
        px := L + margin
    if (py + gh > B)
        py := B - gh - margin
    if (py < T)
        py := T + margin
    g.Move(px, py)
    g.Show("NoActivate")
}

HC_MonitorFromPoint(x, y) {
    Loop MonitorGetCount() {
        MonitorGet(A_Index, &ml, &mt, &mr, &mb)
        if (x >= ml && x < mr && y >= mt && y < mb)
            return A_Index
    }
    return MonitorGetPrimary()
}

HC_BumpIdle(*) {
    global gHCOpenedAt
    gHCOpenedAt := A_TickCount
}

HC_SaveSlot(g, slotId, *) {
    global gHCLastText
    HC_BumpIdle()
    text := gHCLastText
    if Trim(text) = "" {
        ToolTip("Nothing to save")
        SetTimer(() => ToolTip(), -1000)
        return
    }
    pendingDir := A_ScriptDir "\ExtraClipboard\data"
    try DirCreate(pendingDir)
    pendingPath := pendingDir "\pending_slot_" slotId ".txt"
    try FileDelete(pendingPath)
    FileAppend(text, pendingPath, "UTF-8")
    HC_Close(g)
    ToolTip("Saving to ExtraClipboard slot " slotId "...")
    SetTimer(() => ToolTip(), -1200)
}

HC_Pick(g, which) {
    global gSelectedText, gHCLastText
    HC_Close(g)
    if (which = "llm") {
        ; Quick-actions sheet (prompts + defaults) — LLM half of the old trio.
        try ShowQuickActionPopup()
    } else if (which = "stratum") {
        try HC_LaunchStratum(gHCLastText)
    } else if (which = "copy") {
        A_Clipboard := gHCLastText
        ToolTip("Copied")
        SetTimer(() => ToolTip(), -1000)
    }
}

HC_LaunchStratum(selection := "") {
    global gSelectedText
    if selection = ""
        selection := gSelectedText

    rootDir := A_ScriptDir "\integrations\stratum pop up"
    popupScript := rootDir "\03_ui_python\action_popup.py"
    pythonExe := "C:\Users\David\AppData\Local\Programs\Python\Python312\pythonw.exe"

    if !FileExist(popupScript) {
        ; Fallback to DONT TOUCH copy
        rootDir := "D:\DONT TOUCH BOOT UP\stratum pop up"
        popupScript := rootDir "\03_ui_python\action_popup.py"
    }
    if !FileExist(popupScript) {
        MsgBox("Stratum popup not found.", "Highlight", "Icon!")
        return
    }
    if !FileExist(pythonExe) {
        MsgBox("Python not found:`n" pythonExe, "Highlight", "Icon!")
        return
    }

    selFile := A_Temp "\stratum_selection.txt"
    try FileDelete(selFile)
    if selection != ""
        FileAppend(selection, selFile, "UTF-8")

    sourceApp := ""
    try sourceApp := WinGetProcessName("A")
    Run('"' pythonExe '" "' popupScript '" --selection-file "' selFile '" --source-app "' sourceApp '"', rootDir, "Hide")
}

HC_Close(g) {
    global gHCPopup
    SetTimer(() => HC_FadeStep(g, 0), 0)
    try g.Destroy()
    if (gHCPopup = g)
        gHCPopup := ""
}
