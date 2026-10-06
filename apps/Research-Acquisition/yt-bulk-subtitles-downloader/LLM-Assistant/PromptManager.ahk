; ============================================================
; Prompt Manager GUI for LLM AutoHotkey Assistant
; ------------------------------------------------------------
; Lets you enable/disable, reorder, and edit prompts without
; hand-editing Prompts.ahk. Prefs live in prompt_prefs.json.
; ============================================================

global gPMGui := ""
global gPMPrefsPath := A_ScriptDir "\prompt_prefs.json"
global gPMEditingIndex := 0

PromptManager_Boot() {
    PromptManager_ApplyPrefsToState()
    try A_TrayMenu.Add("Prompt Manager", (*) => PromptManager_Show())
    try A_TrayMenu.Add()
}

PromptManager_PollExternalOpenRequest(*) {
    flag := A_Temp "\llm_show_prompt_manager.flag"
    if !FileExist(flag)
        return
    try FileDelete(flag)
    PromptManager_Show()
}

PromptManager_Show(*) {
    global gPMGui, gPMEditingIndex
    if IsObject(gPMGui) {
        try {
            gPMGui.Show()
            WinActivate("ahk_id " gPMGui.Hwnd)
            PromptManager_RefreshList()
            return
        } catch {
            gPMGui := ""
        }
    }

    g := Gui("+AlwaysOnTop +Resize", "LLM Prompt Manager")
    g.BackColor := "101824"
    g.SetFont("s10 cE6EDF3", "Segoe UI")
    if (VerCompare(A_OSVersion, "10.0.17763") >= 0) {
        attr := (VerCompare(A_OSVersion, "10.0.18985") >= 0) ? 20 : 19
        try DllCall("dwmapi\DwmSetWindowAttribute", "Ptr", g.hWnd, "Int", attr, "Int*", true, "Int", 4)
    }

    g.Add("Text", "xm ym w640", "Switch prompts on/off, reorder them, and edit the system prompt used by ``.")
    g.SetFont("s9 c9FB0C3", "Segoe UI")
    g.Add("Text", "xm y+4 w640", "Disabled prompts stay in Prompts.ahk but are hidden from the menu.")

    g.SetFont("s10 cE6EDF3", "Segoe UI")
    lv := g.Add("ListView", "xm y+10 w640 h280 -Multi +Grid VScroll Checked", ["On", "Menu", "Name", "Models"])
    lv.OnEvent("ItemCheck", PromptManager_OnCheck)
    lv.OnEvent("ItemSelect", PromptManager_OnSelect)
    lv.OnEvent("DoubleClick", (*) => PromptManager_RunSelected())
    g.pmLV := lv

    g.Add("Text", "xm y+10", "Menu text")
    g.pmMenuEdit := g.Add("Edit", "xm y+4 w640", "")
    g.Add("Text", "xm y+8", "System prompt")
    g.pmSysEdit := g.Add("Edit", "xm y+4 w640 r8 VScroll", "")
    g.Add("Text", "xm y+8", "API models (comma-separated)")
    g.pmModelsEdit := g.Add("Edit", "xm y+4 w640", "")

    btnSave := g.Add("Button", "xm y+12 w110 h30", "Save Changes")
    btnSave.OnEvent("Click", (*) => PromptManager_SaveEdits())
    btnUp := g.Add("Button", "x+8 yp w90 h30", "Move Up")
    btnUp.OnEvent("Click", (*) => PromptManager_Move(-1))
    btnDown := g.Add("Button", "x+8 yp w90 h30", "Move Down")
    btnDown.OnEvent("Click", (*) => PromptManager_Move(1))
    btnRun := g.Add("Button", "x+8 yp w110 h30", "Run Prompt")
    btnRun.OnEvent("Click", (*) => PromptManager_RunSelected())
    btnReload := g.Add("Button", "x+8 yp w110 h30", "Reload File")
    btnReload.OnEvent("Click", (*) => PromptManager_ReloadFromFile())
    btnClose := g.Add("Button", "x+8 yp w90 h30", "Close")
    btnClose.OnEvent("Click", (*) => g.Hide())

    g.pmStatus := g.Add("Text", "xm y+10 w640 c9FB0C3", "")
    g.OnEvent("Close", (*) => g.Hide())
    g.OnEvent("Size", PromptManager_OnResize)

    gPMGui := g
    gPMEditingIndex := 0
    PromptManager_RefreshList()
    g.Show("w680 h620")
}

PromptManager_OnResize(guiObj, minMax, width, height) {
    if minMax = -1
        return
    try {
        guiObj.pmLV.Move(, , width - 40, height - 360)
        guiObj.pmMenuEdit.Move(, , width - 40)
        guiObj.pmSysEdit.Move(, , width - 40)
        guiObj.pmModelsEdit.Move(, , width - 40)
    }
}

PromptManager_RefreshList() {
    global gPMGui
    if !IsObject(gPMGui)
        return
    prefs := PromptManager_LoadPrefs()
    ; Show full catalog (including disabled) from original + order/overrides
    catalog := PromptManager_GetCatalog()
    lv := gPMGui.pmLV
    lv.Delete()
    for i, p in catalog {
        name := p.HasProp("promptName") ? p.promptName : ("Prompt " i)
        menuText := p.HasProp("menuText") ? p.menuText : name
        models := p.HasProp("APIModels") ? RegExReplace(p.APIModels, "\s+", " ") : ""
        if StrLen(models) > 60
            models := SubStr(models, 1, 60) "..."
        enabled := !PromptManager_IsDisabled(prefs, name)
        opts := enabled ? "Check" : ""
        lv.Add(opts, enabled ? "Yes" : "No", menuText, name, models)
    }
    lv.ModifyCol(1, 40)
    lv.ModifyCol(2, 220)
    lv.ModifyCol(3, 180)
    lv.ModifyCol(4, 180)
    liveCount := managePromptState("prompts", "get").Length
    try gPMGui.pmStatus.Text := catalog.Length " prompts · " liveCount " active in `` menu · prefs: prompt_prefs.json"
}

PromptManager_GetCatalog() {
    prefs := PromptManager_LoadPrefs()
    original := PromptManager_GetOriginal()
    byName := Map()
    for p in original
        byName[p.promptName] := p

    ordered := []
    if prefs.Has("order") {
        for name in prefs["order"] {
            if byName.Has(name) {
                ordered.Push(byName[name])
                byName.Delete(name)
            }
        }
    }
    for p in original {
        if byName.Has(p.promptName)
            ordered.Push(p)
    }

    catalog := []
    overrides := prefs.Has("overrides") ? prefs["overrides"] : Map()
    for p in ordered {
        q := PromptManager_ClonePrompt(p)
        name := q.promptName
        if (overrides is Map) && overrides.Has(name) {
            o := overrides[name]
            if o is Map {
                if o.Has("menuText")
                    q.menuText := o["menuText"]
                if o.Has("systemPrompt")
                    q.systemPrompt := o["systemPrompt"]
                if o.Has("APIModels")
                    q.APIModels := o["APIModels"]
            }
        }
        catalog.Push(q)
    }
    return catalog
}

PromptManager_GetOriginal() {
    static original := ""
    if original = "" {
        original := []
        ; First call: capture whatever Prompts.ahk loaded before prefs filter.
        ; If already filtered, still treat current as baseline once.
        for p in managePromptState("prompts", "get")
            original.Push(PromptManager_ClonePrompt(p))
        ; Prefer re-including from global prompts if available and larger
        try {
            if IsSet(prompts) && prompts.Length >= original.Length {
                original := []
                for p in prompts
                    original.Push(PromptManager_ClonePrompt(p))
            }
        }
    }
    return original
}

PromptManager_OnSelect(lv, row, selected := 0) {
    global gPMGui, gPMEditingIndex
    if row <= 0
        return
    catalog := PromptManager_GetCatalog()
    if row > catalog.Length
        return
    gPMEditingIndex := row
    p := catalog[row]
    gPMGui.pmMenuEdit.Value := p.HasProp("menuText") ? p.menuText : ""
    gPMGui.pmSysEdit.Value := p.HasProp("systemPrompt") ? p.systemPrompt : ""
    gPMGui.pmModelsEdit.Value := p.HasProp("APIModels") ? Trim(p.APIModels) : ""
}

PromptManager_OnCheck(lv, row, checked) {
    if row <= 0
        return
    catalog := PromptManager_GetCatalog()
    if row > catalog.Length
        return
    name := catalog[row].promptName
    prefs := PromptManager_LoadPrefs()
    disabled := prefs.Has("disabled") ? prefs["disabled"] : []
    newDisabled := []
    for d in disabled {
        if d != name
            newDisabled.Push(d)
    }
    if !checked
        newDisabled.Push(name)
    prefs["disabled"] := newDisabled
    PromptManager_SavePrefs(prefs)
    lv.Modify(row, , checked ? "Yes" : "No")
    PromptManager_ApplyPrefsToState()
    try gPMGui.pmStatus.Text := (checked ? "Enabled: " : "Disabled: ") name
}

PromptManager_SaveEdits(*) {
    global gPMGui, gPMEditingIndex
    if gPMEditingIndex <= 0 {
        try gPMGui.pmStatus.Text := "Select a prompt first"
        return
    }
    catalog := PromptManager_GetCatalog()
    if gPMEditingIndex > catalog.Length
        return
    name := catalog[gPMEditingIndex].promptName
    prefs := PromptManager_LoadPrefs()
    if !prefs.Has("overrides")
        prefs["overrides"] := Map()
    overrides := prefs["overrides"]
    if !(overrides is Map)
        overrides := Map()
    overrides[name] := Map(
        "menuText", gPMGui.pmMenuEdit.Value,
        "systemPrompt", gPMGui.pmSysEdit.Value,
        "APIModels", gPMGui.pmModelsEdit.Value
    )
    prefs["overrides"] := overrides
    PromptManager_SavePrefs(prefs)
    PromptManager_ApplyPrefsToState()
    PromptManager_RefreshList()
    try gPMGui.pmLV.Modify(gPMEditingIndex, "Select Focus Vis")
    try gPMGui.pmStatus.Text := "Saved override for: " name
}

PromptManager_Move(delta) {
    global gPMGui, gPMEditingIndex
    catalog := PromptManager_GetCatalog()
    row := gPMGui.pmLV.GetNext()
    if row <= 0
        row := gPMEditingIndex
    if row <= 0
        return
    newPos := row + delta
    if newPos < 1 || newPos > catalog.Length
        return
    names := []
    for p in catalog
        names.Push(p.promptName)
    tmp := names[row]
    names[row] := names[newPos]
    names[newPos] := tmp
    prefs := PromptManager_LoadPrefs()
    prefs["order"] := names
    PromptManager_SavePrefs(prefs)
    PromptManager_ApplyPrefsToState()
    gPMEditingIndex := newPos
    PromptManager_RefreshList()
    try gPMGui.pmLV.Modify(newPos, "Select Focus Vis")
    PromptManager_OnSelect(gPMGui.pmLV, newPos)
}

PromptManager_RunSelected(*) {
    global gPMGui
    row := gPMGui.pmLV.GetNext()
    if row <= 0 {
        try gPMGui.pmStatus.Text := "Select a prompt to run"
        return
    }
    name := gPMGui.pmLV.GetText(row, 3)
    live := managePromptState("prompts", "get")
    for i, p in live {
        if p.promptName = name {
            try gPMGui.Hide()
            promptMenuHandler(i)
            return
        }
    }
    try gPMGui.pmStatus.Text := "Prompt is disabled — enable it first"
}

PromptManager_ReloadFromFile(*) {
    ; Re-read Prompts.ahk by reloading the whole script (safest for AHK object literals).
    if MsgBox("Reload LLM Assistant from Prompts.ahk?`nUnsaved GUI edits should be Saved first.", "Reload", "YesNo Icon?") != "Yes"
        return
    Reload
}

PromptManager_IsDisabled(prefs, name) {
    if !prefs.Has("disabled")
        return false
    for d in prefs["disabled"] {
        if d = name
            return true
    }
    return false
}

PromptManager_ApplyPrefsToState() {
    prefs := PromptManager_LoadPrefs()
    original := PromptManager_GetOriginal()
    byName := Map()
    for p in original
        byName[p.promptName] := p

    ordered := []
    if prefs.Has("order") {
        for name in prefs["order"] {
            if byName.Has(name) {
                ordered.Push(byName[name])
                byName.Delete(name)
            }
        }
    }
    for p in original {
        if byName.Has(p.promptName)
            ordered.Push(p)
    }

    live := []
    overrides := prefs.Has("overrides") ? prefs["overrides"] : Map()
    for p in ordered {
        name := p.promptName
        if PromptManager_IsDisabled(prefs, name)
            continue
        q := PromptManager_ClonePrompt(p)
        if (overrides is Map) && overrides.Has(name) {
            o := overrides[name]
            if o is Map {
                if o.Has("menuText")
                    q.menuText := o["menuText"]
                if o.Has("systemPrompt")
                    q.systemPrompt := o["systemPrompt"]
                if o.Has("APIModels")
                    q.APIModels := o["APIModels"]
            }
        }
        live.Push(q)
    }
    managePromptState("prompts", "set", live)
}

PromptManager_ClonePrompt(p) {
    q := {
        promptName: p.promptName,
        menuText: p.HasProp("menuText") ? p.menuText : p.promptName,
        systemPrompt: p.HasProp("systemPrompt") ? p.systemPrompt : "",
        APIModels: p.HasProp("APIModels") ? p.APIModels : ""
    }
    if p.HasProp("tags")
        q.tags := p.tags
    if p.HasProp("isCustomPrompt")
        q.isCustomPrompt := p.isCustomPrompt
    if p.HasProp("isAutoPaste")
        q.isAutoPaste := p.isAutoPaste
    if p.HasProp("customPromptInitialMessage")
        q.customPromptInitialMessage := p.customPromptInitialMessage
    if p.HasProp("copyAsMarkdown")
        q.copyAsMarkdown := p.copyAsMarkdown
    if p.HasProp("skipConfirmation")
        q.skipConfirmation := p.skipConfirmation
    return q
}

PromptManager_LoadPrefs() {
    global gPMPrefsPath
    prefs := Map("order", [], "disabled", [], "overrides", Map())
    if !FileExist(gPMPrefsPath)
        return prefs
    try {
        raw := FileRead(gPMPrefsPath, "UTF-8")
        obj := jsongo.Parse(raw)
        if obj.Has("order") {
            prefs["order"] := []
            for v in obj["order"]
                prefs["order"].Push(v)
        }
        if obj.Has("disabled") {
            prefs["disabled"] := []
            for v in obj["disabled"]
                prefs["disabled"].Push(v)
        }
        if obj.Has("overrides") {
            overrides := Map()
            for name, o in obj["overrides"] {
                entry := Map()
                if o.Has("menuText")
                    entry["menuText"] := o["menuText"]
                if o.Has("systemPrompt")
                    entry["systemPrompt"] := o["systemPrompt"]
                if o.Has("APIModels")
                    entry["APIModels"] := o["APIModels"]
                overrides[name] := entry
            }
            prefs["overrides"] := overrides
        }
    } catch {
    }
    return prefs
}

PromptManager_SavePrefs(prefs) {
    global gPMPrefsPath
    obj := Map()
    obj["order"] := prefs.Has("order") ? prefs["order"] : []
    obj["disabled"] := prefs.Has("disabled") ? prefs["disabled"] : []
    overridesOut := Map()
    if prefs.Has("overrides") {
        for name, o in prefs["overrides"] {
            if o is Map
                overridesOut[name] := o
        }
    }
    obj["overrides"] := overridesOut
    FileOpen(gPMPrefsPath, "w", "UTF-8").Write(jsongo.Stringify(obj, , "  "))
}
