#Requires AutoHotkey v2.0
#SingleInstance Force
#Include ElementPicker.ahk

; AI-HUB companion integration for D:\GitHub\window-capture-router.
; Python owns profile storage, UIA picking, OCR, and routing behavior.

global WCR_MUTEX := DllCall("CreateMutex", "Ptr", 0, "Int", false, "Str", "Global\WindowCaptureRouterHotkeys", "Ptr")
if (DllCall("GetLastError") = 183)
    ExitApp

TraySetIcon("shell32.dll", 167)
A_IconTip := "Window Capture Router"

RouterRepo := "D:\GitHub\window-capture-router"
VenvRouter := RouterRepo "\.venv\Scripts\window-router.exe"
RouterCommand := FileExist(VenvRouter) ? '"' VenvRouter '"' : "window-router"

^!Space::{
    WCR_ShowActionTip("Copying selected text, then opening the routing picker...")
    Send "^c"
    Sleep 150
    Run RouterCommand " gui"
}

^!e::{
    WCR_ShowActionTip("Element picker: move over a pane/message until it outlines, then left-click.")
    LaunchElementPicker(RouterCommand)
}
^!i::Run RouterCommand " inspect-active"
+F5::{
    WCR_ShowActionTip("Learn source: name the pane, then click it when the outline is correct.")
    Run A_ComSpec ' /k "' RouterCommand ' learn-source"'
}
+F6::{
    WCR_ShowActionTip("Capturing saved source: Claude artifacts.")
    Run A_ComSpec ' /k "' RouterCommand ' capture-source ""Claude artifacts"""'
}
^+q::WCR_ShowTips()

; Ctrl+Alt+R belongs to AI-HUB Research Links, so region OCR uses Ctrl+Alt+O.
^!o::{
    WCR_ShowActionTip("OCR region: drag a rectangle around the text/image area.")
    LaunchRegionPicker(RouterCommand)
}

WCR_ShowActionTip(message) {
    ToolTip(message, 24, 24)
    SetTimer(() => ToolTip(), -2400)
}

WCR_ShowTips() {
    text := "Window Capture Router tips`n"
        . "Ctrl+Alt+Space  copy selected text -> routing GUI`n"
        . "Ctrl+Alt+E      outline UI element/pane -> click to capture`n"
        . "Ctrl+Alt+O      draw OCR rectangle -> routing GUI`n"
        . "Shift+F5        learn a named source pane, like Claude artifacts`n"
        . "Shift+F6        capture saved Claude artifacts pane`n"
        . "Ctrl+Shift+Q    show these tips`n`n"
        . "Flow: learn once with Shift+F5, then reuse with Shift+F6."
    ToolTip(text, 24, 24)
    SetTimer(() => ToolTip(), -12000)
}

; Repo:
;   D:\GitHub\window-capture-router
