; ============================================================
; YouTube Transcript Watcher - AI Hub module
; Watches active browser YouTube videos and can fetch pasted URLs
; from the AI Hub YT tab. Runs inside AI-HUB, not as its own AHK app.
; ============================================================

if IsSet(HUB_CORE_LOADED)
    RegisterTab("YT", Build_YTWTab, 75)

global YTW_FETCHER := "D:\DONT TOUCH BAT SCRIPT\yt_transcript_fetch.py"
global YTW_PYTHON := "C:\Users\David\AppData\Local\Programs\Python\Python312\python.exe"
global YTW_EXPORT_DIR := "E:\Exports\YouTube Transcripts"
global YTW_LOG := A_ScriptDir "\logs\yt_transcript_watcher.log"
global YTW_SEEN := Map()
global YTW_PENDING := ""
global YTW_ENABLED := true
global YTW_BROWSERS := "chrome.exe,msedge.exe,firefox.exe,brave.exe"
global YTW_Status := ""
global YTW_UrlEdit := ""
global YTW_TitleText := ""
global YTW_EnableChk := ""

YTW_Init()

^!+y::YTW_AskNow()

YTW_Init() {
    global YTW_LOG
    try {
        logDir := RegExReplace(YTW_LOG, "\\[^\\]+$")
        if !DirExist(logDir)
            DirCreate(logDir)
    }
    SetTimer(YTW_Tick, 2000)
}

Build_YTWTab() {
    global gShell, YTW_Status, YTW_UrlEdit, YTW_TitleText, YTW_EnableChk
    global YTW_FETCHER, YTW_EXPORT_DIR
    g := gShell.gui

    g.SetFont("s10 cDDDDDD", "Segoe UI")
    g.AddText("xm+15 ym+52 w660", "YouTube Transcript Watcher")
    g.SetFont("s8 c888888", "Segoe UI")
    g.AddText("xm+15 y+8 w880", "Watches the active browser for YouTube videos. Ctrl+Alt+Shift+Y asks now. Paste a YouTube URL below to fetch from the hub.")

    g.SetFont("s9 cDDDDDD", "Segoe UI")
    YTW_EnableChk := g.AddCheckbox("xm+15 y+18 w260 cDDDDDD", "Watcher enabled")
    YTW_EnableChk.Value := YTW_ENABLED ? 1 : 0
    YTW_EnableChk.OnEvent("Click", (*) => YTW_SetEnabledFromGui())

    btnAsk := g.AddButton("x+10 yp-3 w130 h28", "Ask Now")
    btnAsk.OnEvent("Click", (*) => YTW_AskNow())
    btnOpen := g.AddButton("x+8 yp w140 h28", "Open Export")
    btnOpen.OnEvent("Click", (*) => YTW_OpenExport())
    btnLog := g.AddButton("x+8 yp w120 h28", "Open Log")
    btnLog.OnEvent("Click", (*) => YTW_OpenLog())

    g.AddText("xm+15 y+20 w80", "URL")
    YTW_UrlEdit := g.AddEdit("x+8 yp-3 w690 Background111111 cE0E0E0")
    btnClip := g.AddButton("x+8 yp-1 w120 h26", "Use Clipboard")
    btnClip.OnEvent("Click", (*) => YTW_UseClipboardUrl())

    btnFetch := g.AddButton("xm+103 y+8 w140 h30", "Fetch URL")
    btnFetch.OnEvent("Click", (*) => YTW_FetchFromGui())
    btnClear := g.AddButton("x+8 yp w90 h30", "Clear Seen")
    btnClear.OnEvent("Click", (*) => YTW_ClearSeen())

    g.SetFont("s8 c888888", "Segoe UI")
    g.AddText("xm+15 y+22 w130", "Fetcher:")
    g.AddText("x+8 yp w760 cAAAAAA", YTW_FETCHER)
    g.AddText("xm+15 y+6 w130", "Export:")
    g.AddText("x+8 yp w760 cAAAAAA", YTW_EXPORT_DIR)

    g.SetFont("s9 c9FB0C3", "Segoe UI")
    YTW_TitleText := g.AddText("xm+15 y+24 w920 h28", "Current video: none")
    YTW_Status := g.AddText("xm+15 y+8 w920 h44", "Ready.")
}

YTW_SetEnabledFromGui(*) {
    global YTW_ENABLED, YTW_EnableChk
    YTW_ENABLED := IsObject(YTW_EnableChk) && YTW_EnableChk.Value = 1
    YTW_SetStatus(YTW_ENABLED ? "Watcher enabled." : "Watcher paused.")
}

YTW_Tick() {
    global YTW_PENDING, YTW_SEEN, YTW_ENABLED
    if !YTW_ENABLED
        return
    title := YTW_ActiveYouTubeTitle()
    YTW_UpdateCurrentTitle(title)
    if (title = "") {
        YTW_PENDING := ""
        return
    }
    if YTW_SEEN.Has(title)
        return
    if (YTW_PENDING = title) {
        YTW_SEEN[title] := 1
        YTW_Prompt(title)
        YTW_PENDING := ""
    } else {
        YTW_PENDING := title
    }
}

YTW_ActiveYouTubeTitle() {
    global YTW_BROWSERS
    try {
        exe := WinGetProcessName("A")
        if !InStr(YTW_BROWSERS, exe)
            return ""
        title := WinGetTitle("A")
        if !InStr(title, " - YouTube")
            return ""
        title := RegExReplace(title, "i)\s-\sYouTube.*$", "")
        title := RegExReplace(title, "^\(\d+\)\s*", "")
        return Trim(title)
    }
    return ""
}

YTW_Prompt(title) {
    prompt := Gui("+AlwaysOnTop -MinimizeBox +ToolWindow", "Transcript?")
    prompt.BackColor := "101824"
    prompt.SetFont("s10 cE6EDF3", "Segoe UI")
    short := (StrLen(title) > 66) ? SubStr(title, 1, 63) "..." : title
    prompt.AddText("w360 c62D6FF", "Download transcript?")
    prompt.AddText("w360 c9FB0C3", short)
    yes := prompt.AddButton("w120 Default", "Yes - grab it")
    no := prompt.AddButton("x+12 w90", "No")
    yes.OnEvent("Click", (*) => (prompt.Destroy(), YTW_GrabActive(title)))
    no.OnEvent("Click", (*) => prompt.Destroy())
    SetTimer((*) => (WinExist("ahk_id " prompt.Hwnd) ? prompt.Destroy() : 0), -15000)
    prompt.Show("NoActivate x" (A_ScreenWidth - 430) " y" (A_ScreenHeight - 230))
}

YTW_AskNow(*) {
    global YTW_SEEN
    title := YTW_ActiveYouTubeTitle()
    if (title = "") {
        YTW_SetStatus("No YouTube video in the active browser window.")
        ToolTip("No YouTube video in the active window")
        SetTimer(() => ToolTip(), -1500)
        return
    }
    YTW_SEEN[title] := 1
    YTW_Prompt(title)
}

YTW_GrabActive(title) {
    url := YTW_GetBrowserUrl()
    if !YTW_IsYouTubeUrl(url) {
        YTW_SetStatus("Could not read a YouTube URL from the address bar.")
        ToolTip("Could not read a YouTube URL")
        SetTimer(() => ToolTip(), -2500)
        return
    }
    YTW_RunFetcher(url, title)
}

YTW_FetchFromGui(*) {
    global YTW_UrlEdit
    if !IsObject(YTW_UrlEdit) {
        YTW_SetStatus("YT tab is not ready yet.")
        return
    }
    url := Trim(YTW_UrlEdit.Value)
    if !YTW_IsYouTubeUrl(url) {
        YTW_SetStatus("Paste a valid youtube.com/watch, youtube.com/shorts, or youtu.be URL first.")
        return
    }
    YTW_RunFetcher(url, "manual URL")
}

YTW_UseClipboardUrl(*) {
    global YTW_UrlEdit
    if IsObject(YTW_UrlEdit)
        YTW_UrlEdit.Value := Trim(A_Clipboard)
}

YTW_RunFetcher(url, title := "") {
    global YTW_FETCHER, YTW_PYTHON, YTW_LOG
    if !FileExist(YTW_FETCHER) {
        YTW_SetStatus("Fetcher not found: " YTW_FETCHER)
        return
    }
    py := FileExist(YTW_PYTHON) ? YTW_PYTHON : "python"
    YTW_SetStatus("Fetching transcript for " (title != "" ? title : url) "...")
    YTW_AppendLog("START " url)
    cmd := 'cmd.exe /c ""' py '" "' YTW_FETCHER '" "' url '" >> "' YTW_LOG '" 2>&1"'
    try {
        Run(cmd, "D:\DONT TOUCH BAT SCRIPT", "Hide")
        YTW_SetStatus("Transcript fetch started. Output will land in E: > Exports > YouTube Transcripts.")
    } catch as err {
        YTW_SetStatus("Could not start fetcher: " err.Message)
        YTW_AppendLog("ERROR " err.Message)
    }
}

YTW_GetBrowserUrl() {
    saved := ClipboardAll()
    A_Clipboard := ""
    Send("^l")
    Sleep(120)
    Send("^c")
    if !ClipWait(1) {
        A_Clipboard := saved
        return ""
    }
    url := A_Clipboard
    Send("{Escape}")
    A_Clipboard := saved
    return Trim(url)
}

YTW_IsYouTubeUrl(url) {
    return InStr(url, "youtube.com/watch") || InStr(url, "youtube.com/shorts/") || InStr(url, "youtu.be/")
}

YTW_OpenExport(*) {
    global YTW_EXPORT_DIR
    if !DirExist(YTW_EXPORT_DIR)
        DirCreate(YTW_EXPORT_DIR)
    Run('explorer.exe "' YTW_EXPORT_DIR '"')
}

YTW_OpenLog(*) {
    global YTW_LOG
    if !FileExist(YTW_LOG)
        FileAppend("", YTW_LOG, "UTF-8")
    Run('notepad.exe "' YTW_LOG '"')
}

YTW_ClearSeen(*) {
    global YTW_SEEN, YTW_PENDING
    YTW_SEEN := Map()
    YTW_PENDING := ""
    YTW_SetStatus("Cleared this-session YouTube skip list.")
}

YTW_UpdateCurrentTitle(title) {
    global YTW_TitleText
    if IsObject(YTW_TitleText)
        YTW_TitleText.Text := title = "" ? "Current video: none" : "Current video: " title
}

YTW_SetStatus(message) {
    global YTW_Status
    if IsObject(YTW_Status)
        YTW_Status.Text := message
}

YTW_AppendLog(message) {
    global YTW_LOG
    try FileAppend(FormatTime(, "yyyy-MM-dd HH:mm:ss") " | " message "`n", YTW_LOG, "UTF-8")
}
