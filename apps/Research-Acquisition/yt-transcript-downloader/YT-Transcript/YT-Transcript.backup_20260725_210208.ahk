; YT-Transcript.ahk - AHK v2 - POF 2828 AI HUB
; Shift+F4 on any YouTube tab: confirm -> save transcript and copy markdown.
; Requires: Python 3.12 or python on PATH + youtube-transcript-api.
#Requires AutoHotkey v2.0
#SingleInstance Force

ScriptPy := A_ScriptDir . "\get_transcript.py"
LogFile  := A_ScriptDir . "\yt_transcript.log"
PythonExe := "C:\Users\David\AppData\Local\Programs\Python\Python312\python.exe"

+F4:: {
    global ScriptPy, LogFile, PythonExe
    ; Grab URL from the browser address bar (works in Chrome/Edge/Brave/Firefox)
    saved := ClipboardAll()
    A_Clipboard := ""
    Send "^l"
    Sleep 120
    Send "^c"
    if !ClipWait(1) {
        A_Clipboard := saved
        TrayTip "YT Transcript", "Couldn't read the address bar.", 3
        return
    }
    url := Trim(A_Clipboard)
    Send "{Escape}"          ; drop focus back to the page
    A_Clipboard := saved     ; restore whatever was on the clipboard

    if !(InStr(url, "youtube.com/watch") || InStr(url, "youtu.be/")
      || InStr(url, "youtube.com/shorts") || InStr(url, "youtube.com/live")) {
        TrayTip "YT Transcript", "Not a YouTube video URL:`n" . url, 3
        return
    }

    if MsgBox("Download transcript for:`n`n" . url, "YT Transcript", "YesNo Icon?") != "Yes"
        return

    ; Run python, capture output to log, read result back.
    py := FileExist(PythonExe) ? PythonExe : "python"
    cmd := 'cmd /c ""' . py . '" "' . ScriptPy . '" "' . url . '" > "' . LogFile . '" 2>&1"'
    exitCode := RunWait(cmd, , "Hide")
    result := ""
    try result := Trim(FileRead(LogFile))

    if (exitCode = 0)
        TrayTip "YT Transcript - Saved + Copied", result, 5
    else
        MsgBox "Transcript failed (exit " . exitCode . "):`n`n" . result, "YT Transcript", "Icon!"
}
