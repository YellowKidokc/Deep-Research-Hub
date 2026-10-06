#Requires AutoHotkey v2.0
#SingleInstance Force
; MX Master 3 button detector.
; Run this, then press each thumb button (Back, Forward, and the gesture button
; under the thumb rest). The tooltip shows what AHK actually receives.
;
; If a button shows NOTHING when pressed, Logi Options+ is swallowing it —
; open Options+ and set that button to "Disabled" or a keystroke, then retest.
; Whatever DOES register here is what we bind the AI-hub gestures to.
;
; Press Esc to quit.

show(name) {
    ToolTip("AHK sees: " name "`n(press each thumb button; Esc to quit)")
    SetTimer(() => ToolTip(), -1500)
}

LButton::   { show("LButton (left)")        ; Send("{LButton}") }
RButton::   { show("RButton (right)") }
MButton::   { show("MButton (wheel click)") }
XButton1::  { show("XButton1 (thumb BACK)") }
XButton2::  { show("XButton2 (thumb FWD)") }

; Some MX gesture-button mappings arrive as keystrokes — uncomment/adjust if needed:
; ^!#g::    show("Ctrl+Alt+Win+G (mapped gesture key)")

Esc::ExitApp
