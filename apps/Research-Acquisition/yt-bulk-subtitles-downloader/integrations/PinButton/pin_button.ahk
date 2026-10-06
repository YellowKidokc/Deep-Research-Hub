#Requires AutoHotkey v2.0
#SingleInstance Force
#Warn LocalSameAsGlobal, Off
#Warn VarUnset, Off

; ============================================================
; PIN BUTTON — visual Always-On-Top toggle  (AI HUB, dark)
; ============================================================
; A small blacked-out pin button rides the top-right of the
; ACTIVE window, just left of the min / max / close buttons.
;   click  -> pin window ON TOP   (button turns RED)
;   click  -> unpin               (button goes GRAY)
; Follows the window as you move/resize it. No hotkey needed.
; Exit via the tray icon.
; ============================================================

; ---------- tunables ----------
global SIZE     := 26        ; button width/height, px
global OFFSET_X := 168       ; px left of the window's RIGHT edge (clears the 3 caption buttons)
global OFFSET_Y := 8         ; px down from the window's TOP edge
global TICK_MS  := 200       ; how often we re-check the active window

; ---------- colors (blacked out) ----------
global BG_OFF := "1c1c1c"    ; floating (not on top)
global BG_ON  := "8a1f1f"    ; pinned on top (red)

; ---------- state ----------
global gTarget      := 0
global gPinned      := false
global gPinnedPrev  := -1
global gVisible     := false

; ---------- build the gadget ----------
; -Caption   = no frame/titlebar
; +ToolWindow / E0x80    = keep off taskbar + alt-tab
; +E0x08000000 (NOACTIVATE) = clicking it never steals focus from the target window
global gPin := Gui("+AlwaysOnTop -Caption +ToolWindow +E0x08000000 +E0x00000080 +LastFound")
gPin.BackColor := BG_OFF
gPin.MarginX := 0
gPin.MarginY := 0
gPin.SetFont("s13", "Segoe UI Emoji")
global gLbl := gPin.Add("Text", Format("w{1} h{2} Center 0x200 BackgroundTrans", SIZE, SIZE), "📌")
gLbl.OnEvent("Click", TogglePin)

; ---------- tray ----------
A_IconTip := "Pin Button — visual Always-On-Top"
try TraySetIcon("shell32.dll", 264)
A_TrayMenu.Delete()
A_TrayMenu.Add("Pin / Unpin active window", (*) => TogglePin())
A_TrayMenu.Add()
A_TrayMenu.Add("Exit", (*) => ExitApp())
A_TrayMenu.Default := "Pin / Unpin active window"

SetTimer(Track, TICK_MS)
Track()  ; first paint now

; ============================================================
Track() {
    global gPin, gLbl, gTarget, gPinned, gPinnedPrev, gVisible
    global SIZE, OFFSET_X, OFFSET_Y, BG_OFF, BG_ON

    fw := DllCall("GetForegroundWindow", "Ptr")
    ; keep showing over our own gadget interactions
    if (fw = gPin.Hwnd)
        return

    if !fw || !IsTargetable(fw) {
        if gVisible {
            gPin.Hide()
            gVisible := false
            gPinnedPrev := -1
        }
        return
    }

    gTarget := fw
    gPinned := (WinGetExStyle("ahk_id " fw) & 0x8) ? true : false

    if !WinGetPos(&x, &y, &w, &h, "ahk_id " fw)
        return
    if (w <= 0 || h <= 0)
        return
    px := x + w - OFFSET_X
    py := y + OFFSET_Y

    ; recolor only when the pinned state actually changes (avoids flicker)
    if (gPinned != gPinnedPrev) {
        gPin.BackColor := gPinned ? BG_ON : BG_OFF
        gPinnedPrev := gPinned
    }

    if !gVisible {
        gPin.Show(Format("x{1} y{2} w{3} h{4} NoActivate", px, py, SIZE, SIZE))
        gVisible := true
    } else {
        ; move + re-assert topmost without stealing focus
        ; SetWindowPos(hwnd, HWND_TOPMOST=-1, x,y,w,h, SWP_NOACTIVATE=0x10)
        DllCall("SetWindowPos", "Ptr", gPin.Hwnd, "Ptr", -1,
            "Int", px, "Int", py, "Int", SIZE, "Int", SIZE, "UInt", 0x10)
    }
}

TogglePin(*) {
    global gTarget, gPinned, gPinnedPrev
    if !gTarget || !WinExist("ahk_id " gTarget)
        return
    isTop := WinGetExStyle("ahk_id " gTarget) & 0x8
    try WinSetAlwaysOnTop(isTop ? 0 : 1, "ahk_id " gTarget)
    gPinned := !isTop
    gPinnedPrev := -1  ; force recolor next tick
    ToolTip(gPinned ? "📌  Pinned on top" : "Unpinned")
    SetTimer(() => ToolTip(), -1100)
}

; Which windows should the pin ride? Real, visible, uncloaked top-level app
; windows — not the desktop, taskbar, or our own gadget.
IsTargetable(hwnd) {
    global gPin
    if (hwnd = gPin.Hwnd)
        return false
    if !DllCall("IsWindowVisible", "Ptr", hwnd)
        return false

    ; skip DWM-cloaked windows (ghost UWP, background virtual-desktop apps)
    cloaked := 0
    try DllCall("dwmapi\DwmGetWindowAttribute", "Ptr", hwnd, "UInt", 14, "Int*", &cloaked, "UInt", 4)
    if cloaked
        return false

    cls := ""
    try cls := WinGetClass("ahk_id " hwnd)
    for , skip in ["Progman", "WorkerW", "Shell_TrayWnd", "Shell_SecondaryTrayWnd", "TaskManagerWindow"] {
        if (cls = skip)
            return false
    }
    return true
}
