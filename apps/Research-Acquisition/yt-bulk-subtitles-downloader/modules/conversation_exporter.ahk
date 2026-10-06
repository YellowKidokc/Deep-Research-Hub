; ============================================================
; Browser Conversation Exporter - AI Hub module
; Captures active browser page/conversation text and saves Markdown.
; First pass is universal copy-based; Chrome extension extraction can
; later replace CEV_CopyPageText for site-specific DOM capture.
; ============================================================

if IsSet(HUB_CORE_LOADED)
    RegisterTab("Export", Build_ConversationExportTab, 76)

global CEV_EXPORT_DIR := "E:\Exports\Conversations"
global CEV_Status := ""
global CEV_Preview := ""
global CEV_TitleEdit := ""
global CEV_UrlEdit := ""

^!+e::CEV_ExportOrTriggerClaude()

CEV_ExportOrTriggerClaude(*) {
    if CEV_TriggerClaudeTampermonkey()
        return
    CEV_ExportActiveBrowser()
}

CEV_TriggerClaudeTampermonkey() {
    hwnd := WinExist("A")
    if hwnd && CEV_IsClaudeWindow(hwnd) {
        CEV_SendTampermonkeyExport(hwnd)
        return true
    }

    hwnd := CEV_FindClaudeWindow()
    if !hwnd
        return false

    CEV_SendTampermonkeyExport(hwnd)
    return true
}

CEV_IsClaudeWindow(hwnd) {
    title := WinGetTitle("ahk_id " hwnd)
    proc := WinGetProcessName("ahk_id " hwnd)
    return proc = "Claude.exe"
        || InStr(title, "Claude")
        || InStr(title, "claude.ai")
}

CEV_FindClaudeWindow() {
    for spec in [
        "ahk_exe Claude.exe",
        "Claude ahk_exe chrome.exe",
        "Claude ahk_exe msedge.exe",
        "Claude ahk_exe brave.exe",
        "claude.ai ahk_exe chrome.exe",
        "claude.ai ahk_exe msedge.exe",
        "claude.ai ahk_exe brave.exe"
    ] {
        hwnd := WinExist(spec)
        if hwnd
            return hwnd
    }
    return 0
}

CEV_SendTampermonkeyExport(hwnd) {
    WinActivate("ahk_id " hwnd)
    if !WinWaitActive("ahk_id " hwnd, , 2) {
        CEV_SetStatus("Claude window found, but could not activate it.")
        return
    }
    Sleep(150)
    Send("^+e")
    CEV_SetStatus("Sent Claude Tampermonkey export trigger: Ctrl+Shift+E.")
}

Build_ConversationExportTab() {
    global gShell, CEV_Status, CEV_Preview, CEV_TitleEdit, CEV_UrlEdit, CEV_EXPORT_DIR
    g := gShell.gui

    g.SetFont("s10 cDDDDDD", "Segoe UI")
    g.AddText("xm+15 ym+52 w740", "Conversation Export")
    g.SetFont("s8 c888888", "Segoe UI")
    g.AddText("xm+15 y+8 w900", "Exports the active browser page or AI conversation to Markdown. Hotkey: Ctrl+Alt+Shift+E.")

    g.SetFont("s9 cDDDDDD", "Segoe UI")
    btnActive := g.AddButton("xm+15 y+18 w180 h32", "Export Active Browser")
    btnActive.OnEvent("Click", (*) => CEV_ExportActiveBrowser())
    btnClip := g.AddButton("x+8 yp w180 h32", "Save Clipboard")
    btnClip.OnEvent("Click", (*) => CEV_SaveClipboard())
    btnOpen := g.AddButton("x+8 yp w140 h32", "Open Export")
    btnOpen.OnEvent("Click", (*) => CEV_OpenExport())

    g.AddText("xm+15 y+18 w70", "Title")
    CEV_TitleEdit := g.AddEdit("x+8 yp-3 w760 Background111111 cE0E0E0")
    g.AddText("xm+15 y+12 w70", "URL")
    CEV_UrlEdit := g.AddEdit("x+8 yp-3 w760 Background111111 cE0E0E0")

    g.SetFont("s8 c888888", "Segoe UI")
    g.AddText("xm+15 y+14 w900", "Export folder: " CEV_EXPORT_DIR)
    g.AddText("xm+15 y+8 w900", "Best result: click inside the conversation first. For virtualized pages, scroll through the conversation once before exporting.")

    g.SetFont("s9 cE0E0E0", "Segoe UI")
    CEV_Preview := g.AddEdit("xm+15 y+14 w980 h390 Multi ReadOnly VScroll Background111111 cE0E0E0", "")
    CEV_Status := g.AddText("xm+15 y+10 w980 h36 c9FB0C3", "Ready.")
}

CEV_ExportActiveBrowser(*) {
    hwnd := WinExist("A")
    if !hwnd {
        CEV_SetStatus("No active window.")
        return
    }

    title := WinGetTitle("ahk_id " hwnd)
    url := CEV_GetActiveBrowserUrl()
    text := CEV_CopyPageText()
    if (Trim(text) = "") {
        CEV_SetStatus("Nothing copied. Click inside the conversation/page and try again.")
        return
    }

    path := CEV_WriteMarkdown(title, url, text)
    CEV_UpdateFields(title, url, text)
    CEV_SetStatus("Saved conversation export: " path)
}

CEV_SaveClipboard(*) {
    title := ""
    url := ""
    if IsObject(CEV_TitleEdit)
        title := Trim(CEV_TitleEdit.Value)
    if IsObject(CEV_UrlEdit)
        url := Trim(CEV_UrlEdit.Value)
    text := A_Clipboard
    if (Trim(text) = "") {
        CEV_SetStatus("Clipboard is empty.")
        return
    }
    if (title = "")
        title := "Clipboard Conversation Export"
    path := CEV_WriteMarkdown(title, url, text)
    CEV_UpdateFields(title, url, text)
    CEV_SetStatus("Saved clipboard export: " path)
}

CEV_GetActiveBrowserUrl() {
    saved := ClipboardAll()
    A_Clipboard := ""
    Send("^l")
    Sleep(100)
    Send("^c")
    if !ClipWait(1) {
        A_Clipboard := saved
        Send("{Escape}")
        return ""
    }
    url := Trim(A_Clipboard)
    Send("{Escape}")
    A_Clipboard := saved
    return url
}

CEV_CopyPageText() {
    saved := ClipboardAll()
    A_Clipboard := ""
    Send("{Escape}")
    Sleep(80)
    Send("^a")
    Sleep(120)
    Send("^c")
    if !ClipWait(2) {
        A_Clipboard := saved
        return ""
    }
    text := A_Clipboard
    A_Clipboard := saved
    return text
}

CEV_WriteMarkdown(title, url, text) {
    global CEV_EXPORT_DIR
    if !DirExist(CEV_EXPORT_DIR)
        DirCreate(CEV_EXPORT_DIR)

    cleanTitle := CEV_SafeName(title != "" ? title : "conversation")
    stamp := FormatTime(, "yyyy-MM-dd_HHmmss")
    path := CEV_EXPORT_DIR "\" stamp "_" cleanTitle ".md"

    md := "---`n"
    md .= "title: " CEV_YamlQuote(title) "`n"
    md .= "url: " CEV_YamlQuote(url) "`n"
    md .= "captured: " FormatTime(, "yyyy-MM-ddTHH:mm:ss") "`n"
    md .= "source_app: browser`n"
    md .= "type: conversation_export`n"
    md .= "---`n`n"
    md .= "# " (Trim(title) != "" ? Trim(title) : "Conversation Export") "`n`n"
    if (Trim(url) != "")
        md .= "Source: " url "`n`n"
    md .= text "`n"

    FileAppend(md, path, "UTF-8")
    return path
}

CEV_UpdateFields(title, url, text) {
    global CEV_TitleEdit, CEV_UrlEdit, CEV_Preview
    if IsObject(CEV_TitleEdit)
        CEV_TitleEdit.Value := title
    if IsObject(CEV_UrlEdit)
        CEV_UrlEdit.Value := url
    if IsObject(CEV_Preview)
        CEV_Preview.Value := SubStr(text, 1, 12000)
}

CEV_OpenExport(*) {
    global CEV_EXPORT_DIR
    if !DirExist(CEV_EXPORT_DIR)
        DirCreate(CEV_EXPORT_DIR)
    Run('explorer.exe "' CEV_EXPORT_DIR '"')
}

CEV_SafeName(value) {
    value := RegExReplace(value, '[<>:"/\\|?*]', "")
    value := RegExReplace(value, "\s+", " ")
    value := Trim(value)
    if (StrLen(value) > 90)
        value := SubStr(value, 1, 90)
    return value != "" ? value : "conversation"
}

CEV_YamlQuote(value) {
    return '"' StrReplace(value, '"', '\"') '"'
}

CEV_SetStatus(message) {
    global CEV_Status
    if IsObject(CEV_Status)
        CEV_Status.Text := message
}
