; ============================================================
; MODULE: Clipboard Tab
; ------------------------------------------------------------
; Native AI-HUB tab for hot slots + synced clipboard history.
; Talks to POF sync_server on http://127.0.0.1:3456
; ============================================================

global gClipBaseUrl := "http://127.0.0.1:3456"
global gClipSlotCacheDir := "D:\DONT TOUCH BOOT UP\AHK\slot_cache"
global gClipIndexFile := A_ScriptDir "\Data\clips_index.tsv"
global gClipRows := []          ; parallel to history LV: {id, title, slot, preview}
global gClipSelectedId := ""

if IsSet(HUB_CORE_LOADED) {
    RegisterTab("Clipboard", BuildClipboardTab, 25)
}

BuildClipboardTab() {
    global gShell, DARK_TEXT, gClipSlotCacheDir

    gShell.gui.SetFont("s10 Bold c" DARK_TEXT, "Segoe UI")
    gShell.gui.Add("Text", "xm+15 ym+45", "Clipboard Sync")
    gShell.gui.SetFont("s8 c888888", "Segoe UI")
    gShell.clipStatusTxt := gShell.gui.Add("Text", "xm+15 y+4 w900", "Slots + history from sync_server · double-click to copy")

    ; --- Actions row ---
    gShell.gui.SetFont("s9 Bold c" DARK_TEXT, "Segoe UI")
    gShell.btnClipRefresh := gShell.gui.Add("Button", "xm+15 y+10 w110 h28", "Sync Now")
    gShell.btnClipRefresh.OnEvent("Click", (*) => ClipTab_Refresh(true))
    ApplyDarkTheme(gShell.btnClipRefresh)

    gShell.btnClipSaveOs := gShell.gui.Add("Button", "x+8 yp w150 h28", "Save OS Clipboard")
    gShell.btnClipSaveOs.OnEvent("Click", (*) => ClipTab_SaveOsClipboard())
    ApplyDarkTheme(gShell.btnClipSaveOs)

    gShell.btnClipSavePrompt := gShell.gui.Add("Button", "x+8 yp w150 h28", "Save Selected Prompt")
    gShell.btnClipSavePrompt.OnEvent("Click", (*) => ClipTab_SaveSelectedPrompt())
    ApplyDarkTheme(gShell.btnClipSavePrompt)

    gShell.btnClipHtml := gShell.gui.Add("Button", "x+8 yp w130 h28", "Open HTML Panel")
    gShell.btnClipHtml.OnEvent("Click", (*) => LaunchHtmlPanel("http://127.0.0.1:3456/clipboard3", "POF-Clipboard"))
    ApplyDarkTheme(gShell.btnClipHtml)

    ; --- Hot slots (left) ---
    gShell.gui.SetFont("s9 Bold c" DARK_TEXT, "Segoe UI")
    gShell.gui.Add("Text", "xm+15 y+16", "Hot Slots")
    gShell.gui.SetFont("s8 c888888", "Segoe UI")
    gShell.gui.Add("Text", "xm+15 y+2", "Ctrl+Alt+1..0 pastes · click Copy / Assign")

    gShell.clipSlotsLV := gShell.gui.Add("ListView", "xm+15 y+8 w420 h280 -Multi +Grid VScroll",
        ["Slot", "Preview"])
    gShell.clipSlotsLV.OnEvent("DoubleClick", (*) => ClipTab_CopySelectedSlot())
    ApplyDarkListView(gShell.clipSlotsLV)

    gShell.btnClipCopySlot := gShell.gui.Add("Button", "xm+15 y+8 w90", "Copy Slot")
    gShell.btnClipCopySlot.OnEvent("Click", (*) => ClipTab_CopySelectedSlot())
    ApplyDarkTheme(gShell.btnClipCopySlot)

    gShell.btnClipAssignSlot := gShell.gui.Add("Button", "x+6 yp w140", "Assign OS Clip → Slot")
    gShell.btnClipAssignSlot.OnEvent("Click", (*) => ClipTab_AssignOsToSelectedSlot())
    ApplyDarkTheme(gShell.btnClipAssignSlot)

    gShell.btnClipClearSlot := gShell.gui.Add("Button", "x+6 yp w90", "Clear Slot")
    gShell.btnClipClearSlot.OnEvent("Click", (*) => ClipTab_ClearSelectedSlot())
    ApplyDarkTheme(gShell.btnClipClearSlot)

    ; --- History (right) ---
    gShell.gui.SetFont("s9 Bold c" DARK_TEXT, "Segoe UI")
    gShell.gui.Add("Text", "x460 ym+115", "Synced History")
    gShell.gui.SetFont("s8 c888888", "Segoe UI")
    gShell.gui.Add("Text", "x460 y+2", "From server DB · search filters the list")

    gShell.clipSearchEdit := gShell.gui.Add("Edit", "x460 y+8 w400", "")
    gShell.clipSearchEdit.OnEvent("Change", (*) => ClipTab_FilterHistory())
    ApplyDarkTheme(gShell.clipSearchEdit)
    ApplyInputTheme(gShell.clipSearchEdit)

    gShell.clipHistLV := gShell.gui.Add("ListView", "x460 y+8 w700 h280 -Multi +Grid VScroll",
        ["When", "Slot", "Title"])
    gShell.clipHistLV.OnEvent("DoubleClick", (*) => ClipTab_CopySelectedHistory())
    gShell.clipHistLV.OnEvent("ItemSelect", (*) => ClipTab_OnHistorySelect())
    ApplyDarkListView(gShell.clipHistLV)

    gShell.btnClipCopyHist := gShell.gui.Add("Button", "x460 y+8 w90", "Copy")
    gShell.btnClipCopyHist.OnEvent("Click", (*) => ClipTab_CopySelectedHistory())
    ApplyDarkTheme(gShell.btnClipCopyHist)

    gShell.btnClipToSlot := gShell.gui.Add("Button", "x+6 yp w130", "History → Slot…")
    gShell.btnClipToSlot.OnEvent("Click", (*) => ClipTab_HistoryToSlot())
    ApplyDarkTheme(gShell.btnClipToSlot)

    gShell.btnClipDelete := gShell.gui.Add("Button", "x+6 yp w90", "Delete")
    gShell.btnClipDelete.OnEvent("Click", (*) => ClipTab_DeleteSelectedHistory())
    ApplyDarkTheme(gShell.btnClipDelete)

    ; Preview pane
    gShell.gui.SetFont("s8 c888888", "Segoe UI")
    gShell.gui.Add("Text", "xm+15 y+14", "Preview")
    gShell.clipPreviewEdit := gShell.gui.Add("Edit", "xm+15 y+4 w1145 r5 ReadOnly", "")
    ApplyDarkTheme(gShell.clipPreviewEdit)
    ApplyInputTheme(gShell.clipPreviewEdit)

    ; Initial + periodic sync (gentle)
    SetTimer(() => ClipTab_Refresh(false), -800)
    SetTimer(() => ClipTab_Refresh(false), 20000)
}

ClipTab_SetStatus(msg) {
    global gShell
    try gShell.clipStatusTxt.Text := msg
}

ClipTab_Http(method, path, body := "") {
    global gClipBaseUrl
    req := ComObject("WinHttp.WinHttpRequest.5.1")
    req.Open(method, gClipBaseUrl path, false)
    req.SetTimeouts(2000, 2000, 4000, 4000)
    if body != "" {
        req.SetRequestHeader("Content-Type", "application/json")
        req.Send(body)
    } else {
        req.Send()
    }
    return {status: req.Status, text: req.ResponseText}
}

ClipTab_JsonEscape(str) {
    s := str ""
    s := StrReplace(s, "\", "\\")
    s := StrReplace(s, '"', '\"')
    s := StrReplace(s, "`r", "\r")
    s := StrReplace(s, "`n", "\n")
    s := StrReplace(s, "`t", "\t")
    return s
}

ClipTab_Refresh(showTip := false) {
    global gShell, gClipSlotCacheDir, gClipIndexFile, gClipRows

    ; 1) Ask server to rewrite slot_cache
    try ClipTab_Http("GET", "/api/slots/refresh")

    ; 2) Hot slots from plain text cache
    try {
        gShell.clipSlotsLV.Delete()
        loop 10 {
            n := A_Index
            f := gClipSlotCacheDir "\slot_" n ".txt"
            preview := ""
            if FileExist(f) {
                preview := Trim(FileRead(f, "UTF-8"))
                preview := StrReplace(StrReplace(preview, "`r", ""), "`n", " ")
                if StrLen(preview) > 70
                    preview := SubStr(preview, 1, 70) "..."
            }
            gShell.clipSlotsLV.Add("", n, preview = "" ? "(empty)" : preview)
        }
        gShell.clipSlotsLV.ModifyCol(1, 50)
        gShell.clipSlotsLV.ModifyCol(2, 350)
    } catch as e {
        ClipTab_SetStatus("Slot refresh failed: " e.Message)
    }

    ; 3) History index via Python helper → TSV for the ListView
    try {
        DirCreate(A_ScriptDir "\Data")
        exporter := A_ScriptDir "\tools\export_clips_index.py"
        if FileExist(exporter) {
            RunWait('py -3 "' exporter '" "' gClipIndexFile '"', A_ScriptDir, "Hide")
        }
    } catch as e {
        ClipTab_SetStatus("History sync failed: " e.Message)
        if showTip {
            ToolTip("Clipboard sync failed")
            SetTimer(() => ToolTip(), -1500)
        }
        return
    }

    gClipRows := []
    if FileExist(gClipIndexFile) {
        for line in StrSplit(FileRead(gClipIndexFile, "UTF-8"), "`n", "`r") {
            if Trim(line) = ""
                continue
            parts := StrSplit(line, "`t")
            if parts.Length < 4
                continue
            gClipRows.Push({
                id: parts[1],
                slot: parts.Length >= 2 ? parts[2] : "",
                when: parts.Length >= 3 ? parts[3] : "",
                title: parts.Length >= 4 ? parts[4] : "",
                preview: parts.Length >= 5 ? parts[5] : ""
            })
        }
    }
    ClipTab_FilterHistory()
    ClipTab_SetStatus("Synced · " gClipRows.Length " history items · slots from " gClipSlotCacheDir)
    if showTip {
        ToolTip("Clipboard synced")
        SetTimer(() => ToolTip(), -1200)
    }
}

ClipTab_FilterHistory() {
    global gShell, gClipRows
    q := ""
    try q := StrLower(Trim(gShell.clipSearchEdit.Value))
    gShell.clipHistLV.Delete()
    for row in gClipRows {
        hay := StrLower(row.title " " row.preview " " row.slot)
        if (q != "" && !InStr(hay, q))
            continue
        gShell.clipHistLV.Add("", row.when, row.slot = "" ? "-" : row.slot, row.title)
    }
    gShell.clipHistLV.ModifyCol(1, 140)
    gShell.clipHistLV.ModifyCol(2, 50)
    gShell.clipHistLV.ModifyCol(3, 480)
}

ClipTab_SelectedHistoryRow() {
    global gShell, gClipRows
    row := gShell.clipHistLV.GetNext()
    if row <= 0
        return 0
    ; Map visible LV row back to gClipRows via id+title matching filtered order
    q := ""
    try q := StrLower(Trim(gShell.clipSearchEdit.Value))
    visible := 0
    for i, item in gClipRows {
        hay := StrLower(item.title " " item.preview " " item.slot)
        if (q != "" && !InStr(hay, q))
            continue
        visible += 1
        if visible = row
            return i
    }
    return 0
}

ClipTab_OnHistorySelect(*) {
    global gShell, gClipRows, gClipSelectedId
    idx := ClipTab_SelectedHistoryRow()
    if idx <= 0
        return
    item := gClipRows[idx]
    gClipSelectedId := item.id
    try gShell.clipPreviewEdit.Value := item.preview
}

ClipTab_FetchContent(clipId) {
    if clipId = ""
        return ""
    try {
        res := ClipTab_Http("GET", "/api/clips/" clipId)
        if res.status != 200
            return ""
        ; Pull "content":"..." with basic unescape
        if RegExMatch(res.text, '"content"\s*:\s*"((?:[^"\\]|\\.)*)"', &m) {
            return ClipTab_JsonUnescape(m[1])
        }
    }
    return ""
}

ClipTab_JsonUnescape(str) {
    s := str ""
    s := StrReplace(s, "\n", "`n")
    s := StrReplace(s, "\r", "`r")
    s := StrReplace(s, "\t", "`t")
    s := StrReplace(s, '\"', '"')
    s := StrReplace(s, "\\", "\")
    return s
}

ClipTab_CopySelectedHistory(*) {
    global gClipRows, gShell
    idx := ClipTab_SelectedHistoryRow()
    if idx <= 0 {
        ToolTip("Select a history item")
        SetTimer(() => ToolTip(), -1000)
        return
    }
    item := gClipRows[idx]
    content := ClipTab_FetchContent(item.id)
    if content = ""
        content := item.preview
    A_Clipboard := content
    try gShell.clipPreviewEdit.Value := content
    ToolTip("Copied history item")
    SetTimer(() => ToolTip(), -1000)
}

ClipTab_CopySelectedSlot(*) {
    global gShell, gClipSlotCacheDir
    row := gShell.clipSlotsLV.GetNext()
    if row <= 0 {
        ToolTip("Select a slot")
        SetTimer(() => ToolTip(), -1000)
        return
    }
    n := Integer(gShell.clipSlotsLV.GetText(row, 1))
    f := gClipSlotCacheDir "\slot_" n ".txt"
    if !FileExist(f) {
        ToolTip("Slot " n " empty")
        SetTimer(() => ToolTip(), -1000)
        return
    }
    text := FileRead(f, "UTF-8")
    A_Clipboard := text
    try gShell.clipPreviewEdit.Value := text
    ToolTip("Copied slot " n)
    SetTimer(() => ToolTip(), -1000)
}

ClipTab_AssignOsToSelectedSlot(*) {
    global gShell
    row := gShell.clipSlotsLV.GetNext()
    if row <= 0 {
        ToolTip("Select a slot first")
        SetTimer(() => ToolTip(), -1000)
        return
    }
    n := Integer(gShell.clipSlotsLV.GetText(row, 1))
    content := A_Clipboard ""
    if Trim(content) = "" {
        ToolTip("OS clipboard is empty")
        SetTimer(() => ToolTip(), -1000)
        return
    }
    title := Trim(StrSplit(content, "`n", "`r")[1])
    if StrLen(title) > 80
        title := SubStr(title, 1, 80)
    body := '{"slot":' n ',"content":"' ClipTab_JsonEscape(content) '","title":"' ClipTab_JsonEscape(title) '"}'
    res := ClipTab_Http("POST", "/api/slots/assign", body)
    if res.status >= 200 && res.status < 300 {
        ToolTip("Assigned to slot " n)
        SetTimer(() => ToolTip(), -1200)
        ClipTab_Refresh(false)
    } else {
        ToolTip("Assign failed (" res.status ")")
        SetTimer(() => ToolTip(), -1500)
    }
}

ClipTab_ClearSelectedSlot(*) {
    global gShell
    row := gShell.clipSlotsLV.GetNext()
    if row <= 0
        return
    n := Integer(gShell.clipSlotsLV.GetText(row, 1))
    body := '{"slot":' n '}'
    res := ClipTab_Http("POST", "/api/slots/clear", body)
    if res.status >= 200 && res.status < 300 {
        ToolTip("Cleared slot " n)
        SetTimer(() => ToolTip(), -1000)
        ClipTab_Refresh(false)
    }
}

ClipTab_HistoryToSlot(*) {
    global gClipRows
    idx := ClipTab_SelectedHistoryRow()
    if idx <= 0 {
        ToolTip("Select a history item")
        SetTimer(() => ToolTip(), -1000)
        return
    }
    result := InputBox("Assign this history item to which slot? (1-10)", "History → Slot", "w320 h120", "1")
    if result.Result != "OK"
        return
    n := Integer(Trim(result.Value))
    if n < 1 || n > 10 {
        ToolTip("Slot must be 1-10")
        SetTimer(() => ToolTip(), -1000)
        return
    }
    item := gClipRows[idx]
    content := ClipTab_FetchContent(item.id)
    if content = ""
        content := item.preview
    body := '{"slot":' n ',"content":"' ClipTab_JsonEscape(content) '","title":"' ClipTab_JsonEscape(item.title) '"}'
    res := ClipTab_Http("POST", "/api/slots/assign", body)
    if res.status >= 200 && res.status < 300 {
        ToolTip("History → slot " n)
        SetTimer(() => ToolTip(), -1200)
        ClipTab_Refresh(false)
    } else {
        ToolTip("Failed (" res.status ")")
        SetTimer(() => ToolTip(), -1500)
    }
}

ClipTab_DeleteSelectedHistory(*) {
    global gClipRows
    idx := ClipTab_SelectedHistoryRow()
    if idx <= 0
        return
    item := gClipRows[idx]
    if MsgBox("Delete this history item from the server?`n`n" item.title, "Delete Clip", "YesNo Icon!") != "Yes"
        return
    res := ClipTab_Http("DELETE", "/api/clips/" item.id)
    if res.status = 204 || (res.status >= 200 && res.status < 300) {
        ToolTip("Deleted")
        SetTimer(() => ToolTip(), -1000)
        ClipTab_Refresh(false)
    } else {
        ToolTip("Delete failed (" res.status ")")
        SetTimer(() => ToolTip(), -1500)
    }
}

ClipTab_SaveOsClipboard(*) {
    content := A_Clipboard ""
    if Trim(content) = "" {
        ToolTip("OS clipboard empty")
        SetTimer(() => ToolTip(), -1000)
        return
    }
    title := Trim(StrSplit(content, "`n", "`r")[1])
    if StrLen(title) > 80
        title := SubStr(title, 1, 80)
    body := '{"content":"' ClipTab_JsonEscape(content) '","title":"' ClipTab_JsonEscape(title) '","category":"clipboard","tags":["manual","hub"]}'
    res := ClipTab_Http("POST", "/api/clips", body)
    if res.status = 201 || (res.status >= 200 && res.status < 300) {
        ToolTip("Saved OS clipboard to history")
        SetTimer(() => ToolTip(), -1200)
        ClipTab_Refresh(false)
    } else {
        ToolTip("Save failed (" res.status ")")
        SetTimer(() => ToolTip(), -1500)
    }
}

ClipTab_SaveSelectedPrompt(*) {
    global gShell, gPrompts
    row := 0
    try row := gShell.promptsLV.GetNext()
    if row <= 0 || row > gPrompts.Length {
        ToolTip("Select a prompt on the Prompts tab first")
        SetTimer(() => ToolTip(), -1800)
        return
    }
    p := gPrompts[row]
    content := p.template
    title := "Prompt: " p.name
    body := '{"content":"' ClipTab_JsonEscape(content) '","title":"' ClipTab_JsonEscape(title) '","category":"prompt","tags":["prompt","hub"]}'
    res := ClipTab_Http("POST", "/api/clips", body)
    if res.status = 201 || (res.status >= 200 && res.status < 300) {
        A_Clipboard := content
        ToolTip("Prompt saved to clipboard history + OS clipboard")
        SetTimer(() => ToolTip(), -1500)
        ClipTab_Refresh(false)
        try SetActiveTabByName("Clipboard")
    } else {
        ToolTip("Save prompt failed (" res.status ")")
        SetTimer(() => ToolTip(), -1500)
    }
}
