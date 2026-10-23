; YT-Transcript.ahk - AutoHotkey v1 watcher/GUI for YouTube capture
; Hotkeys:
;   Shift+F4 = detect current browser URL now
;   Shift+F5 = open control panel

#NoEnv
#SingleInstance Force
#Persistent
SetBatchLines, -1
SendMode, Input

ToolRoot := "D:\GitHub\yt-bulk-subtitles-downloader"
ToolMenu := ToolRoot . "\YTBSD_MENU.bat"
CaptureScript := A_ScriptDir . "\yt_capture_url.ps1"
EnvGet, UserProfileDir, USERPROFILE
if (UserProfileDir = "")
    UserProfileDir := A_Desktop
OutputDir := UserProfileDir . "\yt_captures"
LogDir := A_ScriptDir . "\logs"
SeenVideos := "|"
LastCheckedTitle := ""
CurrentUrl := ""

FileCreateDir, %LogDir%
Menu, Tray, NoStandard
Menu, Tray, Add, Detect YouTube now, ManualDetect
Menu, Tray, Add, Open control panel, ShowPanel
Menu, Tray, Add, Open transcript folder, OpenOutputFolder
Menu, Tray, Add
Menu, Tray, Add, Exit, ExitScript

SetTimer, WatchActiveYouTubeTab, 2500
Gosub, ShowPanel
return

+F4::
Gosub, ManualDetect
return

+F5::
Gosub, ShowPanel
return

WatchActiveYouTubeTab:
    if (!IsBrowserActive())
        return

    WinGetTitle, title, A
    if (!InStr(title, "YouTube"))
        return
    if (title = LastCheckedTitle)
        return
    LastCheckedTitle := title

    url := GetActiveBrowserUrl()
    if (!IsYouTubeVideoUrl(url))
        return

    video := ExtractVideoId(url)
    if (video = "")
        return

    if (InStr(SeenVideos, "|" . video . "|"))
        return

    SeenVideos := SeenVideos . video . "|"
    CurrentUrl := url
    Gosub, ShowVideoPrompt
return

ManualDetect:
    url := GetActiveBrowserUrl()
    if (!IsYouTubeVideoUrl(url)) {
        MsgBox, 48, YouTube Research Tool, I could not detect a YouTube video URL in the active browser tab.`n`nOpen a YouTube video page, then press Shift+F4 again.
        return
    }
    CurrentUrl := url
    Gosub, ShowVideoPrompt
return

ShowPanel:
    Gui, Panel:Destroy
    Gui, Panel:+AlwaysOnTop
    Gui, Panel:Font, s10, Segoe UI
    Gui, Panel:Add, Text, w520, Open a YouTube video in Chrome/Edge/Brave/Firefox. This watcher scans the active browser tab and asks what to do when it finds a video URL.
    Gui, Panel:Add, Text, w520 c555555, No typing needed. Shift+F4 scans the current tab now. Shift+F5 opens this panel.
    Gui, Panel:Add, Text, w520, Tool: %ToolRoot%
    Gui, Panel:Add, Text, w520, Output: %OutputDir%
    Gui, Panel:Add, Button, w160 gManualDetect, Detect Now
    Gui, Panel:Add, Button, x+8 w160 gOpenOutputFolder, Open Output
    Gui, Panel:Add, Button, x+8 w160 gOpenBulkMenu, Bulk Menu
    Gui, Panel:Add, Button, xm w160 gTroubleshootTool, Troubleshoot
    Gui, Panel:Add, Button, x+8 w160 gOpenToolFolder, Open Tool Folder
    Gui, Panel:Add, Button, x+8 w160 gHidePanel, Hide
    Gui, Panel:Show, AutoSize x40 y80, YouTube Research Tool
return

ShowVideoPrompt:
    video := ExtractVideoId(CurrentUrl)
    Gui, Prompt:Destroy
    Gui, Prompt:+AlwaysOnTop +ToolWindow
    Gui, Prompt:Font, s10, Segoe UI
    Gui, Prompt:Add, Text, w560, I scanned the active browser tab and found this YouTube video. If this is right, choose what to do.
    Gui, Prompt:Add, Edit, w560 r3 ReadOnly, %CurrentUrl%
    Gui, Prompt:Add, Text, w560 c555555, Video ID: %video%
    Gui, Prompt:Add, Button, w170 gRunSubtitles, Subtitles
    Gui, Prompt:Add, Button, x+8 w170 gRunAudio, Audio
    Gui, Prompt:Add, Button, x+8 w170 gRunVideo, Video
    Gui, Prompt:Add, Button, xm w170 gRunAll, All
    Gui, Prompt:Add, Button, x+8 w170 gOpenBulkMenu, Bulk Menu
    Gui, Prompt:Add, Button, xm w170 gOpenOutputFolder, Open Output
    Gui, Prompt:Add, Button, x+8 w170 gClosePrompt, Not This One
    Gui, Prompt:Add, Button, x+8 w170 gPauseWatcher, Stop Asking
    Gui, Prompt:Show, AutoSize x80 y120, YouTube Detected
return

RunSubtitles:
    url := CurrentUrl
    Gui, Prompt:Destroy
    RunForUrl("Subtitles", url)
return

RunAudio:
    url := CurrentUrl
    Gui, Prompt:Destroy
    RunForUrl("Audio", url)
return

RunVideo:
    url := CurrentUrl
    Gui, Prompt:Destroy
    RunForUrl("Video", url)
return

RunAll:
    url := CurrentUrl
    Gui, Prompt:Destroy
    RunForUrl("All", url)
return

ClosePrompt:
    Gui, Prompt:Destroy
return

PauseWatcher:
    SetTimer, WatchActiveYouTubeTab, Off
    Gui, Prompt:Destroy
    MsgBox, 64, YouTube Research Tool, Automatic YouTube prompts are paused for this AHK session.`n`nPress Shift+F4 to detect manually, or restart this script to turn auto-watch back on.
return

TroubleshootTool:
    RunCapture("Troubleshoot", "")
return

OpenBulkMenu:
    RunCapture("Menu", "")
return

OpenToolFolder:
    Run, explorer.exe "%ToolRoot%"
return

OpenOutputFolder:
    FileCreateDir, %OutputDir%
    Run, explorer.exe "%OutputDir%"
return

HidePanel:
    Gui, Panel:Hide
return

ExitScript:
    ExitApp
return

PanelGuiClose:
PanelGuiEscape:
    Gui, Panel:Hide
return

PromptGuiClose:
PromptGuiEscape:
    Gui, Prompt:Destroy
return

RunForUrl(mode, url) {
    MsgBox, 64, YouTube Capture, A command window will open now and run the capture.`n`nMode: %mode%`n`nLeave that window open until it finishes.
    RunCapture(mode, url)
}

RunCapture(mode, url) {
    global ToolRoot, CaptureScript
    if (!FileExist(CaptureScript)) {
        MsgBox, 16, YouTube Capture, Missing capture bridge:`n%CaptureScript%
        return
    }
    if (!FileExist(ToolRoot)) {
        MsgBox, 16, YouTube Capture, Missing downloader folder:`n%ToolRoot%
        return
    }
    if (url = "")
        cmd := ComSpec . " /k powershell.exe -NoProfile -ExecutionPolicy Bypass -File """ . CaptureScript . """ -Mode " . mode
    else
        cmd := ComSpec . " /k powershell.exe -NoProfile -ExecutionPolicy Bypass -File """ . CaptureScript . """ -Mode " . mode . " -Url """ . url . """"
    Run, %cmd%, %A_ScriptDir%
}

IsBrowserActive() {
    WinGet, exe, ProcessName, A
    StringLower, exe, exe
    return (exe = "chrome.exe"
        || exe = "msedge.exe"
        || exe = "brave.exe"
        || exe = "firefox.exe"
        || exe = "vivaldi.exe"
        || exe = "opera.exe")
}

GetActiveBrowserUrl() {
    saved := ClipboardAll
    Clipboard :=
    Send, ^l
    Sleep, 100
    Send, ^c
    ClipWait, 1
    if (ErrorLevel) {
        Clipboard := saved
        return ""
    }
    url := Trim(Clipboard)
    Send, {Esc}
    Sleep, 60
    Clipboard := saved
    return url
}

IsYouTubeVideoUrl(url) {
    return (InStr(url, "youtube.com/watch")
        || InStr(url, "youtu.be/")
        || InStr(url, "youtube.com/shorts/")
        || InStr(url, "youtube.com/live/"))
}

ExtractVideoId(url) {
    patterns := ["[?&]v=([A-Za-z0-9_-]{11})"
        , "youtu\.be/([A-Za-z0-9_-]{11})"
        , "/shorts/([A-Za-z0-9_-]{11})"
        , "/live/([A-Za-z0-9_-]{11})"
        , "/embed/([A-Za-z0-9_-]{11})"]
    for index, pattern in patterns {
        if (RegExMatch(url, pattern, m))
            return m1
    }
    return ""
}
