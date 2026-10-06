#Requires AutoHotkey v2.0
#SingleInstance Force

; Stratum Windows-native glue. Middle mouse captures selected text if possible,
; then launches the PySide action popup with selection fallback to clipboard.
;
; NOTE: PythonExe must be the FULL PATH to a Python that has PySide6 installed.
; A bare "pythonw.exe" resolves through PATH and on this machine lands in the
; hermes-agent venv (no PySide6) -> popup dies silently. Do not shorten it.

RootDir := RegExReplace(A_ScriptDir, "\\07_ahk$")
PopupScript := RootDir "\03_ui_python\action_popup.py"
PythonExe := "C:\Users\David\AppData\Local\Programs\Python\Python312\pythonw.exe"

MButton::LaunchStratumPopup()
^!Space::LaunchStratumPopup()

LaunchStratumPopup() {
    global PopupScript, PythonExe
    selection := CaptureSelection()
    ; Selection goes through a temp file: command-line args mangle newlines,
    ; quotes, and long text. The popup deletes the file after reading it.
    selFile := A_Temp "\stratum_selection.txt"
    try FileDelete(selFile)
    if (selection != "")
        FileAppend(selection, selFile, "UTF-8")
    Run('"' PythonExe '" "' PopupScript '" --selection-file "' selFile '"', , "Hide")
}

CaptureSelection() {
    oldClip := ClipboardAll()
    A_Clipboard := ""
    Send "^c"
    if ClipWait(0.4) {
        text := A_Clipboard
        A_Clipboard := oldClip
        return text
    }
    A_Clipboard := oldClip
    return ""
}
