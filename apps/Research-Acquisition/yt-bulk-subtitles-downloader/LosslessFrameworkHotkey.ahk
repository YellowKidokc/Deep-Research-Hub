#Requires AutoHotkey v2.0+
#SingleInstance Force
Persistent

; Ctrl+Shift+L - create/use a lossless vial framework for the selected file or active folder.
^+l::
{
    selected := GetSelectedExplorerItems()
    source := selected.Length >= 1 ? selected[1] : ""
    target := ""
    if (source = "")
        target := GetActiveExplorerFolder()
    if (source = "" && target = "") {
        source := FileSelect(, , "Pick source file for lossless vial (Cancel to pick a folder)", "Documents (*.md; *.txt; *.html; *.htm)")
        if (source = "") {
            target := DirSelect(, 3, "Pick the folder for _LOSSLESS_VIALS")
            if (target = "")
                return
        }
    }

    ps1 := A_AppData "\Microsoft\Windows\Start Menu\Programs\Startup\_LOSSLESS_SUMMARY\Invoke-LosslessFramework.ps1"
    if !FileExist(ps1) {
        MsgBox("Lossless commander not found:`n" ps1, "Lossless Framework", 16)
        return
    }

    if (selected.Length > 1) {
        plan := AskBatchPlan(selected.Length)
        if (plan = "")
            return
        listFile := A_Temp "\lossless_sources_" A_TickCount ".txt"
        text := ""
        for path in selected
            text .= path "`n"
        FileAppend(text, listFile, "UTF-8")
        cmd := 'powershell.exe -NoProfile -ExecutionPolicy Bypass -File "' ps1 '" -SourceListFile "' listFile '" -BatchPlan "' plan '" -OpenAfter'
    } else if (source != "") {
        cmd := 'powershell.exe -NoProfile -ExecutionPolicy Bypass -File "' ps1 '" -SourcePath "' source '" -OpenAfter'
    } else {
        cmd := 'powershell.exe -NoProfile -ExecutionPolicy Bypass -File "' ps1 '" -TargetFolder "' target '" -OpenAfter'
    }
    exitCode := RunWait(cmd, , "Hide")
    if (exitCode = 0) {
        where := source != "" ? source : target
        TrayTip("Lossless Framework", "Created/refreshed vial for:`n" where, 5)
    } else {
        where := source != "" ? source : target
        MsgBox("PowerShell commander failed with exit code " exitCode ".`nInput:`n" where, "Lossless Framework", 16)
    }
}

AskBatchPlan(count) {
    msg := "You selected " count " items.`n`nYes = one super document`nNo = independent vials`nCancel = both"
    result := MsgBox(msg, "Lossless Framework", "YesNoCancel Icon?")
    if (result = "Yes")
        return "super"
    if (result = "No")
        return "independent"
    if (result = "Cancel")
        return "both"
    return ""
}

GetSelectedExplorerItems() {
    items := []
    hwnd := WinGetID("A")
    className := WinGetClass("ahk_id " hwnd)
    if !(className = "CabinetWClass" || className = "ExploreWClass")
        return items

    shell := ComObject("Shell.Application")
    for window in shell.Windows {
        try {
            if (window.HWND = hwnd) {
                selected := window.Document.SelectedItems
                if (selected.Count >= 1) {
                    Loop selected.Count {
                        path := selected.Item(A_Index - 1).Path
                        if FileExist(path)
                            items.Push(path)
                    }
                }
            }
        }
    }
    return items
}

GetActiveExplorerFolder() {
    hwnd := WinGetID("A")
    className := WinGetClass("ahk_id " hwnd)
    if !(className = "CabinetWClass" || className = "ExploreWClass")
        return ""

    shell := ComObject("Shell.Application")
    for window in shell.Windows {
        try {
            if (window.HWND = hwnd) {
                path := window.Document.Folder.Self.Path
                if DirExist(path)
                    return path
            }
        }
    }
    return ""
}
