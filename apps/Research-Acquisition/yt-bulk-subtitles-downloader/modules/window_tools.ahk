; ============================================================
; Window Tools - AI Hub module
; Monitor-aware center, resize, halves, and quadrants.
; Inspired by Devail1/window-center-resize AHK monitor math.
; ============================================================

if IsSet(HUB_CORE_LOADED)
    RegisterTab("Windows", Build_WindowToolsTab, 78)

global WMT_Status := ""
global WMT_SizeIndex := 0
global WMT_SizePresets := [
    { label: "Focus 70%", w: 70, h: 78 },
    { label: "Large 85%", w: 85, h: 88 },
    { label: "Tall 60%", w: 60, h: 92 },
    { label: "Wide 92%", w: 92, h: 70 }
]

^!+c::WMT_CenterActive()
^!+r::WMT_CycleActiveSize()

Build_WindowToolsTab() {
    global gShell, WMT_Status
    g := gShell.gui

    g.SetFont("s10 cDDDDDD", "Segoe UI")
    g.AddText("xm+15 ym+52 w720", "Window Layout Tools")
    g.SetFont("s8 c888888", "Segoe UI")
    g.AddText("xm+15 y+8 w900", "Use these on the active window. Hotkeys: Ctrl+Alt+Shift+C centers, Ctrl+Alt+Shift+R cycles size presets.")

    g.SetFont("s9 cDDDDDD", "Segoe UI")
    btnCenter := g.AddButton("xm+15 y+22 w150 h34", "Center Active")
    btnCenter.OnEvent("Click", (*) => WMT_CenterActive())
    btnCycle := g.AddButton("x+8 yp w150 h34", "Cycle Size")
    btnCycle.OnEvent("Click", (*) => WMT_CycleActiveSize())
    btnHub := g.AddButton("x+8 yp w150 h34", "Center AI Hub")
    btnHub.OnEvent("Click", (*) => WMT_CenterHub())

    g.AddText("xm+15 y+26 w220 c9FB0C3", "Presets")
    x := 15
    y := 148
    for preset in WMT_SizePresets {
        btn := g.AddButton("x" x " y" y " w138 h32", preset.label)
        btn.OnEvent("Click", WMT_ApplyPreset.Bind(preset))
        x += 148
    }

    g.AddText("xm+15 y+26 w220 c9FB0C3", "Halves")
    y += 78
    btnLeft := g.AddButton("x15 y" y " w138 h32", "Left Half")
    btnLeft.OnEvent("Click", (*) => WMT_SnapActive("left"))
    btnRight := g.AddButton("x+8 yp w138 h32", "Right Half")
    btnRight.OnEvent("Click", (*) => WMT_SnapActive("right"))
    btnTop := g.AddButton("x+8 yp w138 h32", "Top Half")
    btnTop.OnEvent("Click", (*) => WMT_SnapActive("top"))
    btnBottom := g.AddButton("x+8 yp w138 h32", "Bottom Half")
    btnBottom.OnEvent("Click", (*) => WMT_SnapActive("bottom"))

    g.AddText("xm+15 y+26 w220 c9FB0C3", "Quadrants")
    y += 78
    btnNW := g.AddButton("x15 y" y " w138 h32", "Top Left")
    btnNW.OnEvent("Click", (*) => WMT_SnapActive("nw"))
    btnNE := g.AddButton("x+8 yp w138 h32", "Top Right")
    btnNE.OnEvent("Click", (*) => WMT_SnapActive("ne"))
    btnSW := g.AddButton("x+8 yp w138 h32", "Bottom Left")
    btnSW.OnEvent("Click", (*) => WMT_SnapActive("sw"))
    btnSE := g.AddButton("x+8 yp w138 h32", "Bottom Right")
    btnSE.OnEvent("Click", (*) => WMT_SnapActive("se"))

    g.SetFont("s8 c777777", "Segoe UI")
    g.AddText("xm+15 y+32 w900", "Existing XButton2 drag-resize is still active. This tab is for repeatable monitor-aware placement.")

    g.SetFont("s9 c9FB0C3", "Segoe UI")
    WMT_Status := g.AddText("xm+15 y+18 w900 h40", "Ready.")
}

WMT_CenterHub(*) {
    global gShell
    if IsObject(gShell) && IsObject(gShell.gui)
        WMT_CenterWindow(gShell.gui.Hwnd)
}

WMT_CenterActive(*) {
    hwnd := WinExist("A")
    if !hwnd {
        WMT_SetStatus("No active window.")
        return
    }
    WMT_CenterWindow(hwnd)
}

WMT_CycleActiveSize(*) {
    global WMT_SizeIndex, WMT_SizePresets
    hwnd := WinExist("A")
    if !hwnd {
        WMT_SetStatus("No active window.")
        return
    }
    WMT_SizeIndex += 1
    if WMT_SizeIndex > WMT_SizePresets.Length
        WMT_SizeIndex := 1
    preset := WMT_SizePresets[WMT_SizeIndex]
    WMT_ResizeByPercent(hwnd, preset.w, preset.h)
    WMT_SetStatus("Applied " preset.label " to active window.")
}

WMT_ApplyPreset(preset, *) {
    hwnd := WinExist("A")
    if !hwnd {
        WMT_SetStatus("No active window.")
        return
    }
    WMT_ResizeByPercent(hwnd, preset.w, preset.h)
    WMT_SetStatus("Applied " preset.label ".")
}

WMT_CenterWindow(hwnd) {
    try {
        mon := WMT_GetNearestMonitorInfo(hwnd)
        WinGetPos(, , &width, &height, "ahk_id " hwnd)
        x := mon.WALeft + (mon.WAWidth - width) / 2
        y := mon.WATop + (mon.WAHeight - height) / 2
        WinMove(Round(x), Round(y), width, height, "ahk_id " hwnd)
        WMT_SetStatus("Centered active window.")
    } catch as err {
        WMT_SetStatus("Center failed: " err.Message)
    }
}

WMT_ResizeByPercent(hwnd, widthPercent, heightPercent) {
    try {
        mon := WMT_GetNearestMonitorInfo(hwnd)
        newW := Round(mon.WAWidth * widthPercent / 100)
        newH := Round(mon.WAHeight * heightPercent / 100)
        newX := Round(mon.WALeft + (mon.WAWidth - newW) / 2)
        newY := Round(mon.WATop + (mon.WAHeight - newH) / 2)
        WinRestore("ahk_id " hwnd)
        WinMove(newX, newY, newW, newH, "ahk_id " hwnd)
    } catch as err {
        WMT_SetStatus("Resize failed: " err.Message)
    }
}

WMT_SnapActive(region, *) {
    hwnd := WinExist("A")
    if !hwnd {
        WMT_SetStatus("No active window.")
        return
    }
    try {
        mon := WMT_GetNearestMonitorInfo(hwnd)
        left := mon.WALeft
        top := mon.WATop
        halfW := Round(mon.WAWidth / 2)
        halfH := Round(mon.WAHeight / 2)
        fullW := mon.WAWidth
        fullH := mon.WAHeight

        switch region {
        case "left":
            rect := [left, top, halfW, fullH]
        case "right":
            rect := [left + halfW, top, fullW - halfW, fullH]
        case "top":
            rect := [left, top, fullW, halfH]
        case "bottom":
            rect := [left, top + halfH, fullW, fullH - halfH]
        case "nw":
            rect := [left, top, halfW, halfH]
        case "ne":
            rect := [left + halfW, top, fullW - halfW, halfH]
        case "sw":
            rect := [left, top + halfH, halfW, fullH - halfH]
        case "se":
            rect := [left + halfW, top + halfH, fullW - halfW, fullH - halfH]
        default:
            return
        }

        WinRestore("ahk_id " hwnd)
        WinMove(rect[1], rect[2], rect[3], rect[4], "ahk_id " hwnd)
        WMT_SetStatus("Snapped active window: " region ".")
    } catch as err {
        WMT_SetStatus("Snap failed: " err.Message)
    }
}

WMT_GetNearestMonitorInfo(hwnd) {
    static MONITOR_DEFAULTTONEAREST := 0x00000002
    hMonitor := DllCall("MonitorFromWindow", "ptr", hwnd, "uint", MONITOR_DEFAULTTONEAREST, "ptr")
    info := Buffer(104, 0)
    NumPut("uint", 104, info)
    if DllCall("user32\GetMonitorInfo", "ptr", hMonitor, "ptr", info) {
        left := NumGet(info, 4, "int")
        top := NumGet(info, 8, "int")
        right := NumGet(info, 12, "int")
        bottom := NumGet(info, 16, "int")
        waLeft := NumGet(info, 20, "int")
        waTop := NumGet(info, 24, "int")
        waRight := NumGet(info, 28, "int")
        waBottom := NumGet(info, 32, "int")
        return {
            Handle: hMonitor,
            Left: left,
            Top: top,
            Right: right,
            Bottom: bottom,
            WALeft: waLeft,
            WATop: waTop,
            WARight: waRight,
            WABottom: waBottom,
            Width: right - left,
            Height: bottom - top,
            WAWidth: waRight - waLeft,
            WAHeight: waBottom - waTop,
            Primary: NumGet(info, 36, "uint")
        }
    }
    throw Error("GetMonitorInfo failed: " A_LastError)
}

WMT_SetStatus(message) {
    global WMT_Status
    if IsObject(WMT_Status)
        WMT_Status.Text := message
}
