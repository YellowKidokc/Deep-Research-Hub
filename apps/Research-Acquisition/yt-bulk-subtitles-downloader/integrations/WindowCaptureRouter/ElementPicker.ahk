#Requires AutoHotkey v2.0

; AHK stays thin: Python owns UIA inspection, overlay drawing, OCR, clipboard,
; and the routing GUI handoff.

LaunchElementPicker(RouterCommand) {
    Run RouterCommand " pick-element"
}

LaunchRegionPicker(RouterCommand) {
    Run RouterCommand " pick-region"
}
