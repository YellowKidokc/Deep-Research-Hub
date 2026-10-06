#Requires AutoHotkey v2.0
#SingleInstance Force
#Warn
SetWorkingDir A_ScriptDir
InstallKeybdHook()

class Logger {
    __New(logFilePath, debugEnabled := true) {
        this.logFilePath := logFilePath
        this.debugEnabled := debugEnabled
        SplitPath(logFilePath, , &logDir)
        if logDir != "" && !DirExist(logDir) {
            DirCreate(logDir)
        }
    }

    SetDebugEnabled(isEnabled) {
        this.debugEnabled := isEnabled ? true : false
        this.Info("Logger debug mode updated", Map("debugEnabled", this.debugEnabled))
    }

    Debug(message, data := "") {
        if !this.debugEnabled {
            return
        }
        this.Write("DEBUG", message, data)
    }

    Info(message, data := "") {
        this.Write("INFO", message, data)
    }

    Warn(message, data := "") {
        this.Write("WARN", message, data)
    }

    Error(message, data := "") {
        this.Write("ERROR", message, data)
    }

    Write(level, message, data := "") {
        ; --- Logging must never break app flow; treat log writes as best-effort only. ---
        timestamp := FormatTime(A_Now, "yyyy-MM-dd HH:mm:ss")
        payload := this.SerializeData(data)
        line := "[" timestamp "] [" level "] " message
        if payload != "" {
            line .= " | " payload
        }
        line .= "`n"

        ; Retry briefly in case another process holds a temporary lock on the file.
        maxAttempts := 4
        loop maxAttempts {
            try {
                FileAppend(line, this.logFilePath, "UTF-8")
                return
            } catch {
                if A_Index < maxAttempts {
                    Sleep(20)
                    continue
                }
            }
        }

        ; Final fallback: emit to debugger output without throwing.
        try {
            OutputDebug("ExtraClipboard logger fallback: " line)
        } catch {
        }
    }

    SerializeData(data) {
        if IsObject(data) {
            if data is Map {
                parts := []
                for key, value in data {
                    parts.Push(key ":" this.SerializeValue(value))
                }
                return "{" StrJoin(parts, ", ") "}"
            }
            return this.SerializeValue(data)
        }
        return this.SerializeValue(data)
    }

    SerializeValue(value) {
        if IsObject(value) {
            if value.HasProp("Size") {
                return "<binary size=" value.Size ">"
            }
            return "<object>"
        }
        val := value ""
        return StrReplace(val, "`n", "\n")
    }
}

class ConfigStore {
    __New(configPath, logger) {
        this.configPath := configPath
        this.logger := logger
        this.defaults := Map(
            "CopyHotkey", "",
            "PasteHotkey", "",
            "SourceCopyCombo", "^c",
            "TargetPasteCombo", "^v",
            "SlotCount", 1,
            "ActiveSlot", 1,
            "DebugEnabled", true,
            "ConfigVersion", 3
        )

        loop 9 {
            slotId := A_Index
            this.defaults["Slot" slotId "CopyHotkey"] := ""
            this.defaults["Slot" slotId "PasteHotkey"] := ""
            this.defaults["Slot" slotId "ClearDestinationAssociationHotkey"] := ""
            this.defaults["Slot" slotId "Mode"] := "default"
            this.defaults["Slot" slotId "IncrementOperation"] := "increase"
            this.defaults["Slot" slotId "IncrementStep"] := 1
            this.defaults["Slot" slotId "IncrementMatchMode"] := "auto-smart"
            this.defaults["Slot" slotId "IncrementNumberSystem"] := "decimal"
        }
    }

    Load() {
        cfg := Map()
        cfg["ConfigVersion"] := this.ClampInt(IniRead(this.configPath, "General", "ConfigVersion", this.defaults["ConfigVersion"]), 1, 999, 1)
        cfg["CopyHotkey"] := this.NormalizeHotkeyText(IniRead(this.configPath, "Hotkeys", "CopyHotkey", this.defaults["CopyHotkey"]))
        cfg["PasteHotkey"] := this.NormalizeHotkeyText(IniRead(this.configPath, "Hotkeys", "PasteHotkey", this.defaults["PasteHotkey"]))
        cfg["SourceCopyCombo"] := this.NormalizeHotkeyText(IniRead(this.configPath, "Hotkeys", "SourceCopyCombo", this.defaults["SourceCopyCombo"]))
        cfg["TargetPasteCombo"] := this.NormalizeHotkeyText(IniRead(this.configPath, "Hotkeys", "TargetPasteCombo", this.defaults["TargetPasteCombo"]))
        cfg["SlotCount"] := this.ClampInt(IniRead(this.configPath, "General", "SlotCount", this.defaults["SlotCount"]), 1, 9, 1)
        cfg["ActiveSlot"] := this.ClampInt(IniRead(this.configPath, "General", "ActiveSlot", this.defaults["ActiveSlot"]), 1, cfg["SlotCount"], 1)
        cfg["DebugEnabled"] := this.ToBool(IniRead(this.configPath, "General", "DebugEnabled", this.defaults["DebugEnabled"] ? "1" : "0"))
        loop 9 {
            slotId := A_Index
            copyKeyName := "Slot" slotId "CopyHotkey"
            pasteKeyName := "Slot" slotId "PasteHotkey"
            clearAssocHotkeyName := "Slot" slotId "ClearDestinationAssociationHotkey"
            cfg[copyKeyName] := this.NormalizeHotkeyText(IniRead(this.configPath, "Hotkeys", copyKeyName, this.defaults[copyKeyName]))
            cfg[pasteKeyName] := this.NormalizeHotkeyText(IniRead(this.configPath, "Hotkeys", pasteKeyName, this.defaults[pasteKeyName]))
            cfg[clearAssocHotkeyName] := this.NormalizeHotkeyText(IniRead(this.configPath, "Hotkeys", clearAssocHotkeyName, this.defaults[clearAssocHotkeyName]))

            modeKeyName := "Slot" slotId "Mode"
            operationKeyName := "Slot" slotId "IncrementOperation"
            stepKeyName := "Slot" slotId "IncrementStep"
            matchKeyName := "Slot" slotId "IncrementMatchMode"
            systemKeyName := "Slot" slotId "IncrementNumberSystem"

            cfg[modeKeyName] := this.NormalizeSlotMode(IniRead(this.configPath, "SlotModes", modeKeyName, this.defaults[modeKeyName]))
            cfg[operationKeyName] := this.NormalizeIncrementOperation(IniRead(this.configPath, "SlotModes", operationKeyName, this.defaults[operationKeyName]))
            cfg[stepKeyName] := this.ClampInt(IniRead(this.configPath, "SlotModes", stepKeyName, this.defaults[stepKeyName]), 1, 999999, 1)
            cfg[matchKeyName] := this.NormalizeIncrementMatchMode(IniRead(this.configPath, "SlotModes", matchKeyName, this.defaults[matchKeyName]))
            cfg[systemKeyName] := this.NormalizeIncrementNumberSystem(IniRead(this.configPath, "SlotModes", systemKeyName, this.defaults[systemKeyName]))
        }

        migrationChanged := false
        if cfg["ConfigVersion"] < 2 {
            migrationChanged := this.ApplyBindingMigration(&cfg)
            cfg["ConfigVersion"] := 2
        }

        if cfg["ConfigVersion"] < 3 {
            cfg["ConfigVersion"] := 3
            migrationChanged := true
        }

        if migrationChanged {
            this.logger.Info("Applied config migration for slot bindings", cfg)
            this.Save(cfg)
        }

        this.logger.Info("Configuration loaded", cfg)
        return cfg
    }

    Save(cfg) {
        IniWrite(cfg["CopyHotkey"], this.configPath, "Hotkeys", "CopyHotkey")
        IniWrite(cfg["PasteHotkey"], this.configPath, "Hotkeys", "PasteHotkey")
        IniWrite(cfg["SourceCopyCombo"], this.configPath, "Hotkeys", "SourceCopyCombo")
        IniWrite(cfg["TargetPasteCombo"], this.configPath, "Hotkeys", "TargetPasteCombo")
        loop 9 {
            slotId := A_Index
            copyKeyName := "Slot" slotId "CopyHotkey"
            pasteKeyName := "Slot" slotId "PasteHotkey"
            clearAssocHotkeyName := "Slot" slotId "ClearDestinationAssociationHotkey"
            IniWrite(cfg[copyKeyName], this.configPath, "Hotkeys", copyKeyName)
            IniWrite(cfg[pasteKeyName], this.configPath, "Hotkeys", pasteKeyName)
            IniWrite(cfg[clearAssocHotkeyName], this.configPath, "Hotkeys", clearAssocHotkeyName)

            modeKeyName := "Slot" slotId "Mode"
            operationKeyName := "Slot" slotId "IncrementOperation"
            stepKeyName := "Slot" slotId "IncrementStep"
            matchKeyName := "Slot" slotId "IncrementMatchMode"
            systemKeyName := "Slot" slotId "IncrementNumberSystem"

            modeValue := cfg.Has(modeKeyName) ? cfg[modeKeyName] : this.defaults[modeKeyName]
            operationValue := cfg.Has(operationKeyName) ? cfg[operationKeyName] : this.defaults[operationKeyName]
            stepValue := cfg.Has(stepKeyName) ? cfg[stepKeyName] : this.defaults[stepKeyName]
            matchValue := cfg.Has(matchKeyName) ? cfg[matchKeyName] : this.defaults[matchKeyName]
            systemValue := cfg.Has(systemKeyName) ? cfg[systemKeyName] : this.defaults[systemKeyName]

            IniWrite(this.NormalizeSlotMode(modeValue), this.configPath, "SlotModes", modeKeyName)
            IniWrite(this.NormalizeIncrementOperation(operationValue), this.configPath, "SlotModes", operationKeyName)
            IniWrite(this.ClampInt(stepValue, 1, 999999, 1), this.configPath, "SlotModes", stepKeyName)
            IniWrite(this.NormalizeIncrementMatchMode(matchValue), this.configPath, "SlotModes", matchKeyName)
            IniWrite(this.NormalizeIncrementNumberSystem(systemValue), this.configPath, "SlotModes", systemKeyName)
        }
        IniWrite(cfg["SlotCount"], this.configPath, "General", "SlotCount")
        IniWrite(cfg["ActiveSlot"], this.configPath, "General", "ActiveSlot")
        IniWrite(cfg["DebugEnabled"] ? "1" : "0", this.configPath, "General", "DebugEnabled")
        IniWrite(this.ClampInt(cfg["ConfigVersion"], 1, 999, 2), this.configPath, "General", "ConfigVersion")
        this.logger.Info("Configuration saved", cfg)
    }

    ApplyBindingMigration(&cfg) {
        changed := false
        loop 9 {
            slotId := A_Index
            copyKeyName := "Slot" slotId "CopyHotkey"
            pasteKeyName := "Slot" slotId "PasteHotkey"

            copyValue := Trim(cfg[copyKeyName])
            pasteValue := Trim(cfg[pasteKeyName])

            if this.IsLegacyAutoSlotCopy(slotId, copyValue) {
                cfg[copyKeyName] := ""
                changed := true
            }
            if this.IsLegacyAutoSlotPaste(slotId, pasteValue) {
                cfg[pasteKeyName] := ""
                changed := true
            }
        }
        return changed
    }

    IsLegacyAutoSlotCopy(slotId, hotkeyText) {
        normalized := StrLower(Trim(hotkeyText))
        return normalized = StrLower("!" slotId) || normalized = StrLower("^" slotId)
    }

    IsLegacyAutoSlotPaste(slotId, hotkeyText) {
        normalized := StrLower(Trim(hotkeyText))
        return normalized = StrLower("!+" slotId) || normalized = StrLower("!" slotId) || normalized = StrLower("^+" slotId)
    }

    ClampInt(raw, minVal, maxVal, fallback) {
        try {
            numeric := Integer(raw)
        } catch {
            return fallback
        }
        if numeric < minVal {
            return minVal
        }
        if numeric > maxVal {
            return maxVal
        }
        return numeric
    }

    ToBool(raw) {
        value := Trim(StrLower(raw ""))
        return value = "1" || value = "true" || value = "yes" || value = "on"
    }

    NormalizeHotkeyText(raw) {
        ; "None" from GUI Hotkey controls should persist as an empty/unbound hotkey.
        value := Trim(raw "")
        return StrLower(value) = "none" ? "" : value
    }

    NormalizeSlotMode(raw) {
        value := StrLower(Trim(raw ""))
        if value = "incremental" || value = "incremental-destination" {
            return value
        }
        return "default"
    }

    NormalizeIncrementOperation(raw) {
        value := StrLower(Trim(raw ""))
        return value = "decrease" ? "decrease" : "increase"
    }

    NormalizeIncrementMatchMode(raw) {
        value := StrLower(Trim(raw ""))
        if value = "start" || value = "end" || value = "auto-smart" {
            return value
        }
        return "auto-smart"
    }

    NormalizeIncrementNumberSystem(raw) {
        value := StrLower(Trim(raw ""))
        if value = "decimal" || value = "hexadecimal" || value = "roman" {
            return value
        }
        return "decimal"
    }
}

class SlotModeRegistry {
    __New(logger) {
        this.logger := logger
        this.modes := Map()
        this.Register("default", DefaultSlotMode(logger))
        this.Register("incremental", IncrementalSlotMode(logger))
        this.Register("incremental-destination", IncrementalDestinationSlotMode(logger))
    }

    Register(modeKey, modeHandler) {
        this.modes[modeKey] := modeHandler
        this.logger.Debug("Slot mode registered", Map("modeKey", modeKey))
    }

    Resolve(modeKey) {
        normalized := StrLower(Trim(modeKey ""))
        if this.modes.Has(normalized) {
            return this.modes[normalized]
        }
        this.logger.Warn("Unknown slot mode, using default", Map("modeKey", modeKey))
        return this.modes["default"]
    }
}

class DefaultSlotMode {
    __New(logger) {
        this.logger := logger
    }

    PreparePaste(slotId, slotState, modeConfig, appContext := "") {
        this.logger.Debug("Default slot mode selected", Map("slotId", slotId))
        pasteOptions := this.BuildDefaultPasteOptions(slotId, slotState, appContext)

        ; --- Root-cause fix for folder pastes: when slot points to a real filesystem item
        ; and destination folder is known, perform direct copy instead of relying on clipboard
        ; format fidelity from third-party file managers.
        if this.TryPrepareDirectFileSystemPaste(slotId, slotState, appContext, &directResult) {
            return directResult
        }

        return Map(
            "success", true,
            "payloadData", slotState["data"],
            "pasteOptions", pasteOptions,
            "persistText", "",
            "statusMessage", ""
        )
    }

    BuildDefaultPasteOptions(slotId, slotState, appContext) {
        options := Map("profile", "default", "restoreDelayMs", 70)
        if !IsObject(slotState) || !slotState.Has("metadata") || !IsObject(slotState["metadata"]) {
            return options
        }

        metadata := slotState["metadata"]
        sourceIsPhotoshop := metadata.Has("isPhotoshopSource") && metadata["isPhotoshopSource"]
        hasPhotoshopFormats := metadata.Has("hasPhotoshopFormats") && metadata["hasPhotoshopFormats"]
        if !sourceIsPhotoshop && !hasPhotoshopFormats {
            return options
        }

        targetProcess := ""
        if IsObject(appContext) {
            diagnostics := appContext.GetActiveWindowDiagnostics()
            targetProcess := diagnostics.Has("process") ? diagnostics["process"] : ""
        }

        ; Photoshop/private formats often need a longer clipboard hand-off before restore.
        options["profile"] := "photoshop-private"
        options["restoreDelayMs"] := 350

        this.logger.Info("Default mode selected Photoshop paste profile", Map(
            "slotId", slotId,
            "sourceProcess", metadata.Has("captureProcess") ? metadata["captureProcess"] : "",
            "targetProcess", targetProcess,
            "hasPhotoshopFormats", hasPhotoshopFormats
        ))
        return options
    }

    TryPrepareDirectFileSystemPaste(slotId, slotState, appContext, &resultOut) {
        resultOut := ""
        if !IsObject(appContext) {
            return false
        }

        sourcePath := appContext.ResolveSlotSourcePath(slotState)
        if sourcePath = "" || !FileExist(sourcePath) {
            return false
        }

        destinationFolder := appContext.ResolveActiveDestinationFolder(slotId)
        if destinationFolder = "" || !InStr(FileExist(destinationFolder), "D") {
            this.logger.Debug("Default mode direct copy skipped: destination folder unavailable", Map("slotId", slotId, "source", sourcePath))
            return false
        }

        SplitPath(sourcePath, &sourceName)
        if sourceName = "" {
            this.logger.Warn("Default mode direct copy skipped: source name unavailable", Map("slotId", slotId, "source", sourcePath))
            return false
        }

        targetPath := destinationFolder "\\" sourceName
        if StrLower(targetPath) = StrLower(sourcePath) {
            this.logger.Debug("Default mode direct copy skipped: source and target are identical", Map("slotId", slotId, "path", sourcePath))
            return false
        }

        sourceKind := FileExist(sourcePath)
        if sourceKind = "" {
            return false
        }

        if InStr(FileExist(targetPath), "D") || (!InStr(sourceKind, "D") && FileExist(targetPath)) {
            resultOut := Map(
                "success", true,
                "handledWithoutPaste", true,
                "payloadData", slotState["data"],
                "persistText", "",
                "statusMessage", "Target already exists: " targetPath
            )
            this.logger.Warn("Default mode direct copy skipped: target already exists", Map("slotId", slotId, "source", sourcePath, "target", targetPath))
            return true
        }

        try {
            if InStr(sourceKind, "D") {
                ; Directory copy preserves full tree content.
                DirCopy(sourcePath, targetPath, false)
            } else {
                FileCopy(sourcePath, targetPath, false)
            }
        } catch error {
            this.logger.Warn("Default mode direct copy failed; falling back to clipboard paste", Map("slotId", slotId, "source", sourcePath, "target", targetPath, "error", error.HasProp("Message") ? error.Message : "unknown"))
            return false
        }

        this.logger.Info("Default mode copied filesystem item directly", Map("slotId", slotId, "source", sourcePath, "target", targetPath, "isDirectory", InStr(sourceKind, "D") ? 1 : 0))
        resultOut := Map(
            "success", true,
            "handledWithoutPaste", true,
            "payloadData", slotState["data"],
            "persistText", "",
            "statusMessage", "Copied: " targetPath
        )
        return true
    }
}

class IncrementalSlotMode {
    __New(logger) {
        this.logger := logger
    }

    PreparePaste(slotId, slotState, modeConfig, appContext := "") {
        ; --- Source selection policy: prefer resolvable file-path text for file actions. ---
        sourceText := this.GetBestSourceText(slotState)

        operation := modeConfig["operation"]
        step := modeConfig["step"]
        matchMode := modeConfig["matchMode"]
        numberSystem := modeConfig["numberSystem"]
        delta := operation = "decrease" ? -step : step

        this.logger.Info("Incremental mode paste requested", Map("slotId", slotId, "operation", operation, "step", step, "matchMode", matchMode, "numberSystem", numberSystem))

        resolvedSourcePath := ""
        if this.TryBuildIncrementedFilePath(sourceText, delta, matchMode, numberSystem, &incrementedPath, &fileReason, &resolvedSourcePath) {
            if this.TryCreateFileOrDirCopy(resolvedSourcePath, incrementedPath, &copyError) {
                return Map(
                    "success", true,
                    "handledWithoutPaste", true,
                    "payloadData", slotState["data"],
                    "persistText", incrementedPath,
                    "statusMessage", "Incremented file: " incrementedPath
                )
            }

            this.logger.Warn("Incremental file copy failed", Map("slotId", slotId, "error", copyError, "source", resolvedSourcePath, "target", incrementedPath))
            return Map(
                "success", false,
                "payloadData", slotState["data"],
                "persistText", "",
                "statusMessage", copyError
            )
        }

        if FileExist(Trim(sourceText)) {
            this.logger.Warn("Incremental file parse skipped", Map("slotId", slotId, "reason", fileReason, "source", sourceText))
            return Map(
                "success", true,
                "payloadData", slotState["data"],
                "persistText", "",
                "statusMessage", "Could not find numbers to increment"
            )
        }

        if sourceText = "" {
            return Map(
                "success", true,
                "payloadData", slotState["data"],
                "persistText", "",
                "statusMessage", "Could not find numbers to increment"
            )
        }

        parseResult := this.IncrementText(sourceText, delta, matchMode, numberSystem)
        if !parseResult["success"] {
            this.logger.Warn("Incremental text parse skipped", Map("slotId", slotId, "reason", parseResult["reason"], "sourceText", sourceText))
            return Map(
                "success", true,
                "payloadData", slotState["data"],
                "persistText", "",
                "statusMessage", "Could not find numbers to increment"
            )
        }

        newText := parseResult["text"]
        this.logger.Info("Incremental text generated", Map("slotId", slotId, "before", sourceText, "after", newText, "token", parseResult["token"] ""))

        return Map(
            "success", true,
            "payloadData", newText,
            "persistText", newText,
            "statusMessage", ""
        )
    }

    GetBestSourceText(slotState) {
        ; --- Highest-priority source: explicit per-slot sourcePath captured at copy-time from Explorer selection. ---
        if slotState.Has("sourcePath") {
            storedPath := this.NormalizeCandidateClipboardText(slotState["sourcePath"])
            if storedPath != "" && FileExist(storedPath) {
                this.logger.Debug("Mode source selected from slot sourcePath", Map("candidate", storedPath))
                return storedPath
            }
        }

        slotText := slotState.Has("text") ? (slotState["text"] "") : ""
        slotText := this.NormalizeCandidateClipboardText(slotText)

        rawData := slotState["data"]
        if !IsObject(rawData) {
            if Trim(slotText) != "" {
                return slotText
            }
            return this.NormalizeCandidateClipboardText(rawData "")
        }

        ; --- Preferred path for file payloads: resolve actual source path from CF_HDROP data. ---
        if this.TryExtractFirstClipboardFilePath(rawData, &resolvedFilePath) {
            normalizedPath := this.NormalizeCandidateClipboardText(resolvedFilePath)
            if normalizedPath != "" {
                this.logger.Debug("Mode source selected from CF_HDROP", Map("candidate", normalizedPath))
                return normalizedPath
            }
        }

        originalClipboard := ClipboardAll()
        extractedText := ""
        try {
            A_Clipboard := rawData
            ClipWait(0.2)
            extractedText := A_Clipboard ""
        } catch {
        }
        A_Clipboard := originalClipboard
        extractedText := this.NormalizeCandidateClipboardText(extractedText)

        ; --- Choose the best available text for file resolution first, then text increment fallback. ---
        if extractedText != "" && FileExist(extractedText) {
            this.logger.Debug("Mode source selected from raw clipboard path", Map("candidate", extractedText))
            return extractedText
        }
        if slotText != "" && FileExist(slotText) {
            this.logger.Debug("Mode source selected from slot text path", Map("candidate", slotText))
            return slotText
        }
        if extractedText != "" {
            this.logger.Debug("Mode source selected from raw clipboard text", Map("candidate", extractedText))
            return extractedText
        }
        if slotText != "" {
            this.logger.Debug("Mode source selected from slot text", Map("candidate", slotText))
            return slotText
        }
        return ""
    }

    TryExtractFirstClipboardFilePath(rawData, &filePathOut) {
        filePathOut := ""
        originalClipboard := ClipboardAll()
        clipboardOpened := false

        try {
            A_Clipboard := rawData
            ClipWait(0.2)

            clipboardOpened := DllCall("OpenClipboard", "ptr", 0, "int")
            if !clipboardOpened {
                this.logger.Debug("CF_HDROP extraction skipped: OpenClipboard failed")
                return false
            }

            ; CF_HDROP = 15, contains file-drop list with full source paths.
            hDrop := DllCall("GetClipboardData", "uint", 15, "ptr")
            if !hDrop {
                this.logger.Debug("CF_HDROP extraction skipped: CF_HDROP not present")
                return false
            }

            fileCount := DllCall("shell32\\DragQueryFileW", "ptr", hDrop, "uint", 0xFFFFFFFF, "ptr", 0, "uint", 0, "uint")
            if fileCount < 1 {
                this.logger.Debug("CF_HDROP extraction skipped: no files in drop handle")
                return false
            }

            fileLen := DllCall("shell32\\DragQueryFileW", "ptr", hDrop, "uint", 0, "ptr", 0, "uint", 0, "uint")
            if fileLen < 1 {
                this.logger.Debug("CF_HDROP extraction skipped: first path length invalid")
                return false
            }

            pathBuffer := Buffer((fileLen + 1) * 2, 0)
            DllCall("shell32\\DragQueryFileW", "ptr", hDrop, "uint", 0, "ptr", pathBuffer, "uint", fileLen + 1, "uint")
            filePathOut := StrGet(pathBuffer, "UTF-16")
            return filePathOut != ""
        } catch error {
            this.logger.Debug("CF_HDROP extraction failed", Map(
                "error", error.HasProp("Message") ? error.Message : "unknown"
            ))
            return false
        } finally {
            if clipboardOpened {
                try {
                    DllCall("CloseClipboard")
                } catch {
                }
            }
            A_Clipboard := originalClipboard
        }
    }

    NormalizeCandidateClipboardText(rawText) {
        text := Trim(rawText "")
        if text = "" {
            return ""
        }

        ; File clipboard text can include CRLF lists; use first non-empty entry for single-file mode.
        for line in StrSplit(text, "`n") {
            cleanedLine := Trim(StrReplace(line, "`r", ""))
            if cleanedLine = "" {
                continue
            }
            ; Remove wrapping quotes if present.
            if SubStr(cleanedLine, 1, 1) = '"' && SubStr(cleanedLine, -1) = '"' && StrLen(cleanedLine) >= 2 {
                cleanedLine := SubStr(cleanedLine, 2, StrLen(cleanedLine) - 2)
            }
            return cleanedLine
        }
        return ""
    }

    TryBuildIncrementedFilePath(sourceText, delta, matchMode, numberSystem, &targetPath, &reason, &resolvedSourcePath) {
        targetPath := ""
        reason := ""
        resolvedSourcePath := ""

        cleaned := this.NormalizeCandidateClipboardText(sourceText)
        if InStr(cleaned, "`n") || InStr(cleaned, "`r") {
            reason := "Multiple file paths are not supported in incremental mode"
            return false
        }

        ; --- Resolve file source robustly: absolute path first, then Explorer-folder fallback for filename-only clipboard text. ---
        resolvedSourcePath := this.ResolveExistingSourcePath(cleaned)
        sourceKind := FileExist(resolvedSourcePath)
        if !sourceKind {
            this.logger.Debug("Incremental file path not found", Map("candidate", cleaned, "resolvedCandidate", resolvedSourcePath))
            reason := "Source is not an existing file path"
            return false
        }

        if InStr(sourceKind, "D") {
            SplitPath(resolvedSourcePath, &dirName, &parentDir)
            textResult := this.IncrementText(dirName, delta, matchMode, numberSystem)
            if !textResult["success"] {
                this.logger.Debug("Directory name increment parse failed", Map("source", resolvedSourcePath, "reason", textResult["reason"]))
                reason := textResult["reason"]
                return false
            }
            targetPath := parentDir "\\" textResult["text"]
        } else {
            SplitPath(resolvedSourcePath, &fileName, &fileDir, &fileExt, &fileNameNoExt)
            textResult := this.IncrementText(fileNameNoExt, delta, matchMode, numberSystem)
            if !textResult["success"] {
                this.logger.Debug("File name increment parse failed", Map("source", resolvedSourcePath, "fileNameNoExt", fileNameNoExt, "reason", textResult["reason"]))
                reason := textResult["reason"]
                return false
            }

            suffix := fileExt != "" ? "." fileExt : ""
            targetPath := fileDir "\\" textResult["text"] suffix
        }

        this.logger.Debug("Incremental file target candidate", Map("source", resolvedSourcePath, "target", targetPath))

        if FileExist(targetPath) {
            reason := "Target already exists: " targetPath
            return false
        }

        return true
    }

    ResolveExistingSourcePath(candidatePath) {
        cleaned := this.NormalizeCandidateClipboardText(candidatePath)
        if cleaned = "" {
            return ""
        }

        if FileExist(cleaned) {
            return cleaned
        }

        ; --- If clipboard only contains a file name, resolve it against active Explorer folder. ---
        SplitPath(cleaned, , &candidateDir)
        if candidateDir = "" {
            explorerDir := this.GetActiveExplorerDirectory()
            if explorerDir != "" {
                resolved := explorerDir "\\" cleaned
                if FileExist(resolved) {
                    this.logger.Debug("Resolved filename using active Explorer folder", Map("fileName", cleaned, "directory", explorerDir, "resolved", resolved))
                    return resolved
                }
                this.logger.Debug("Explorer folder resolution candidate not found", Map("fileName", cleaned, "directory", explorerDir, "resolved", resolved))
            }
        }

        return cleaned
    }

    GetActiveExplorerDirectory() {
        ; --- Resolve currently focused Explorer folder to support filename-only clipboard entries. ---
        try {
            activeWindowHwnd := WinExist("A")
            if !activeWindowHwnd {
                return ""
            }

            shellApp := ComObject("Shell.Application")
            for explorerWindow in shellApp.Windows {
                try {
                    if explorerWindow.HWND != activeWindowHwnd {
                        continue
                    }
                    if !IsObject(explorerWindow.Document) || !IsObject(explorerWindow.Document.Folder) {
                        continue
                    }
                    folderPath := explorerWindow.Document.Folder.Self.Path
                    return folderPath ""
                } catch {
                    continue
                }
            }
        } catch {
        }
        return ""
    }

    TryCreateFileOrDirCopy(sourcePath, targetPath, &errorText) {
        errorText := ""
        try {
            sourceKind := FileExist(sourcePath)
            if sourceKind = "" {
                errorText := "Source file no longer exists"
                return false
            }

            if InStr(sourceKind, "D") {
                DirCopy(sourcePath, targetPath, false)
            } else {
                FileCopy(sourcePath, targetPath, false)
            }
            return true
        } catch error {
            errorText := error.HasProp("Message") ? error.Message : "Failed to copy source"
            return false
        }
    }

    IncrementText(sourceText, delta, matchMode, numberSystem) {
        candidateStart := this.FindTokenAtStart(sourceText, numberSystem)
        candidateEnd := this.FindTokenAtEnd(sourceText, numberSystem)

        selected := ""
        normalizedMatchMode := matchMode

        if normalizedMatchMode = "start" {
            selected := candidateStart
        } else if normalizedMatchMode = "end" {
            selected := candidateEnd
        } else {
            if IsObject(candidateStart) && !IsObject(candidateEnd) {
                selected := candidateStart
            } else if !IsObject(candidateStart) && IsObject(candidateEnd) {
                selected := candidateEnd
            } else if IsObject(candidateStart) && IsObject(candidateEnd) {
                if candidateStart["start"] = candidateEnd["start"] && candidateStart["end"] = candidateEnd["end"] {
                    selected := candidateStart
                } else {
                    return Map("success", false, "reason", "Ambiguous numeric token: start and end numbers both present")
                }
            }
        }

        if !IsObject(selected) {
            return Map("success", false, "reason", "No supported number token found")
        }

        valueInfo := this.ParseTokenValue(selected["token"], numberSystem)
        if !valueInfo["success"] {
            return Map("success", false, "reason", valueInfo["reason"])
        }

        newValue := valueInfo["value"] + delta
        formatted := this.FormatTokenValue(newValue, numberSystem, valueInfo)
        if formatted = "" {
            return Map("success", false, "reason", "Number cannot be represented for selected system")
        }

        beforeText := SubStr(sourceText, 1, selected["start"] - 1)
        afterText := SubStr(sourceText, selected["end"] + 1)
        outputText := beforeText formatted afterText

        return Map(
            "success", true,
            "text", outputText,
            "token", selected["token"],
            "newToken", formatted,
            "start", selected["start"],
            "end", selected["end"]
        )
    }

    FindTokenAtStart(text, numberSystem) {
        return this.FindTokenByPattern(text, numberSystem, true)
    }

    FindTokenAtEnd(text, numberSystem) {
        return this.FindTokenByPattern(text, numberSystem, false)
    }

    FindTokenByPattern(text, numberSystem, atStart) {
        pattern := this.GetSystemPattern(numberSystem, atStart)
        if pattern = "" {
            return ""
        }

        if !RegExMatch(text, pattern, &match) {
            return ""
        }

        return Map(
            "token", match[1],
            "start", match.Pos(1),
            "end", match.Pos(1) + match.Len(1) - 1
        )
    }

    GetSystemPattern(numberSystem, atStart) {
        if numberSystem = "decimal" {
            return atStart ? "^([+-]?\d+)" : "([+-]?\d+)$"
        }
        if numberSystem = "hexadecimal" {
            return atStart ? "i)^(0x[0-9a-f]+|[0-9a-f]+)" : "i)(0x[0-9a-f]+|[0-9a-f]+)$"
        }
        if numberSystem = "roman" {
            return atStart ? "i)^([ivxlcdm]+)" : "i)([ivxlcdm]+)$"
        }
        return ""
    }

    ParseTokenValue(token, numberSystem) {
        if numberSystem = "decimal" {
            try {
                numeric := Integer(token)
                digitsOnly := RegExReplace(token, "^[+-]")
                hasLeadingZeros := StrLen(digitsOnly) > 1 && SubStr(digitsOnly, 1, 1) = "0"
                return Map(
                    "success", true,
                    "value", numeric,
                    "padWidth", StrLen(digitsOnly),
                    "hasLeadingZeros", hasLeadingZeros,
                    "signPrefix", numeric < 0 ? "-" : ""
                )
            } catch {
                return Map("success", false, "reason", "Invalid decimal number")
            }
        }

        if numberSystem = "hexadecimal" {
            if !RegExMatch(token, "i)^(0x)?([0-9a-f]+)$", &hexMatch) {
                return Map("success", false, "reason", "Invalid hexadecimal number")
            }

            prefix := hexMatch[1]
            digits := hexMatch[2]
            numeric := 0
            loop Parse, StrUpper(digits) {
                ch := A_LoopField
                code := Ord(ch)
                numeric := numeric * 16
                if code >= Ord("0") && code <= Ord("9") {
                    numeric += code - Ord("0")
                } else {
                    numeric += code - Ord("A") + 10
                }
            }

            return Map(
                "success", true,
                "value", numeric,
                "prefix", prefix,
                "padWidth", StrLen(digits),
                "isUpper", digits = StrUpper(digits)
            )
        }

        if numberSystem = "roman" {
            numeric := this.RomanToInt(token)
            if numeric <= 0 {
                return Map("success", false, "reason", "Invalid roman numeral")
            }
            return Map(
                "success", true,
                "value", numeric,
                "isUpper", token = StrUpper(token)
            )
        }

        return Map("success", false, "reason", "Unsupported number system")
    }

    FormatTokenValue(newValue, numberSystem, valueInfo) {
        if numberSystem = "decimal" {
            if valueInfo["hasLeadingZeros"] {
                absValue := Abs(newValue)
                body := Format("{:0" valueInfo["padWidth"] "}", absValue)
                return newValue < 0 ? "-" body : body
            }
            return newValue ""
        }

        if numberSystem = "hexadecimal" {
            if newValue < 0 {
                return ""
            }
            converted := this.IntToBase(newValue, 16)
            if valueInfo.Has("padWidth") && valueInfo["padWidth"] > StrLen(converted) {
                while StrLen(converted) < valueInfo["padWidth"] {
                    converted := "0" converted
                }
            }
            if !valueInfo["isUpper"] {
                converted := StrLower(converted)
            }
            return valueInfo["prefix"] converted
        }

        if numberSystem = "roman" {
            if newValue <= 0 || newValue > 3999 {
                return ""
            }
            roman := this.IntToRoman(newValue)
            return valueInfo["isUpper"] ? roman : StrLower(roman)
        }

        return ""
    }

    IntToBase(numberValue, baseValue) {
        if numberValue = 0 {
            return "0"
        }
        digits := "0123456789ABCDEF"
        output := ""
        current := numberValue
        while current > 0 {
            remainder := Mod(current, baseValue)
            output := SubStr(digits, remainder + 1, 1) output
            current := Floor(current / baseValue)
        }
        return output
    }

    RomanToInt(romanText) {
        values := Map("I", 1, "V", 5, "X", 10, "L", 50, "C", 100, "D", 500, "M", 1000)
        text := StrUpper(Trim(romanText))
        if text = "" {
            return 0
        }

        total := 0
        previous := 0
        loop Parse, text {
            ch := A_LoopField
            if !values.Has(ch) {
                return 0
            }
            current := values[ch]
            if current > previous {
                total += current - (2 * previous)
            } else {
                total += current
            }
            previous := current
        }

        canonical := this.IntToRoman(total)
        return canonical = text ? total : 0
    }

    IntToRoman(numberValue) {
        if numberValue <= 0 || numberValue > 3999 {
            return ""
        }

        mapping := [
            Map("value", 1000, "token", "M"),
            Map("value", 900, "token", "CM"),
            Map("value", 500, "token", "D"),
            Map("value", 400, "token", "CD"),
            Map("value", 100, "token", "C"),
            Map("value", 90, "token", "XC"),
            Map("value", 50, "token", "L"),
            Map("value", 40, "token", "XL"),
            Map("value", 10, "token", "X"),
            Map("value", 9, "token", "IX"),
            Map("value", 5, "token", "V"),
            Map("value", 4, "token", "IV"),
            Map("value", 1, "token", "I")
        ]

        output := ""
        remaining := numberValue
        for entry in mapping {
            while remaining >= entry["value"] {
                output .= entry["token"]
                remaining -= entry["value"]
            }
        }
        return output
    }
}

class IncrementalDestinationSlotMode {
    __New(logger) {
        this.logger := logger
    }

    PreparePaste(slotId, slotState, modeConfig, appContext := "") {
        if !IsObject(appContext) {
            return Map("success", false, "statusMessage", "Incremental Destination requires app context")
        }

        direction := modeConfig.Has("operation") ? modeConfig["operation"] : "increase"
        direction := direction = "decrease" ? "decrease" : "increase"
        stepValue := modeConfig.Has("step") ? modeConfig["step"] : 1
        stepValue := stepValue < 1 ? 1 : stepValue

        destinationFolder := appContext.ResolveActiveDestinationFolder(slotId)
        if destinationFolder = "" || !InStr(FileExist(destinationFolder), "D") {
            this.logger.Warn("Incremental destination failed: destination folder unavailable", Map("slotId", slotId, "destinationFolder", destinationFolder))
            return Map("success", true, "handledWithoutPaste", true, "statusMessage", "Could not resolve destination folder")
        }

        sourcePath := appContext.ResolveSlotSourcePath(slotState)
        if (sourcePath = "" || !FileExist(sourcePath)) && slotState.Has("text") {
            ; Same-folder resilience: if copy captured only a file name token, resolve against focused destination folder.
            fallbackName := appContext.slotEngine.NormalizeClipboardPathCandidate(slotState["text"])
            SplitPath(fallbackName, &nameOnly, &nameDir)
            if nameOnly != "" && nameDir = "" {
                sameFolderCandidate := destinationFolder "\\" nameOnly
                if FileExist(sameFolderCandidate) {
                    sourcePath := sameFolderCandidate
                    this.logger.Debug("Recovered source path using destination folder fallback", Map("slotId", slotId, "sourcePath", sourcePath, "folder", destinationFolder))
                }
            }
        }

        if sourcePath = "" || !FileExist(sourcePath) {
            this.logger.Warn("Incremental destination failed: source path unavailable", Map("slotId", slotId, "sourcePath", sourcePath))
            return Map("success", true, "handledWithoutPaste", true, "statusMessage", "Could not resolve source file path")
        }

        sourceKind := FileExist(sourcePath)
        if InStr(sourceKind, "D") {
            return Map("success", true, "handledWithoutPaste", true, "statusMessage", "Incremental destination currently supports files only")
        }

        SplitPath(sourcePath, &sourceFileName, &sourceDir, &sourceExtension, &sourceNameNoExt)
        sourceFamily := this.ParseFileFamily(sourceNameNoExt, sourceExtension)

        try {
            fileFamilies := this.ScanDestinationFamilies(destinationFolder, sourceExtension)
        } catch error {
            errorText := "<scan error>"
            try {
                errorText := appContext.FormatError(error)
            } catch {
                try {
                    errorText := this.DescribeErrorObject(error)
                } catch {
                }
            }
            this.logger.Error("Incremental destination family scan failed", Map(
                "slotId", slotId,
                "folder", destinationFolder,
                "sourceExtension", sourceExtension,
                "error", errorText
            ))
            return Map("success", true, "handledWithoutPaste", true, "statusMessage", "Could not scan destination families")
        }
        association := appContext.GetDestinationFamilyAssociation(slotId, destinationFolder)
        selectedFamily := ""
        preselectedFamilyIndex := 0
        preselectedFromAssociation := false
        sourceFamilyIndex := IsObject(sourceFamily) ? this.FindMatchingFamilyIndex(fileFamilies, sourceFamily) : 0

        this.logger.Debug("Incremental destination families scanned", Map(
            "slotId", slotId,
            "folder", destinationFolder,
            "extension", sourceExtension,
            "familyCount", fileFamilies.Length,
            "hasAssociation", IsObject(association) ? 1 : 0,
            "familiesPreview", this.BuildFamilyBoundaryPreview(fileFamilies)
        ))

        if IsObject(association) {
            preselectedFamilyIndex := this.FindMatchingFamilyIndex(fileFamilies, association)
            if preselectedFamilyIndex > 0 {
                preselectedFromAssociation := true
                this.logger.Debug("Stored destination association available as picker preselection", Map("slotId", slotId, "folder", destinationFolder, "index", preselectedFamilyIndex))
            } else {
                this.logger.Debug("Stored destination association not found in scanned families", Map("slotId", slotId, "folder", destinationFolder))
            }
        }

        if preselectedFamilyIndex = 0 && sourceFamilyIndex > 0 {
            ; Prefer source-derived family when no remembered association exists.
            ; This keeps destination mode deterministic in multi-family folders.
            preselectedFamilyIndex := sourceFamilyIndex
            preselectedFromAssociation := false
            this.logger.Debug("Using source-derived family as default target", Map("slotId", slotId, "folder", destinationFolder, "index", sourceFamilyIndex, "sourceFile", sourceFileName))
        }

        if !IsObject(selectedFamily) {
            if fileFamilies.Length = 1 {
                selectedFamily := fileFamilies[1]
                this.logger.Debug("Incremental destination selected only available family", Map("slotId", slotId, "folder", destinationFolder, "prefix", selectedFamily["prefix"], "suffix", selectedFamily["suffix"]))
            } else if fileFamilies.Length > 1 {
                ; Remembered association is authoritative for continuous pasting in the same folder.
                ; Without a remembered association, always prompt to keep alternate families discoverable.
                if preselectedFromAssociation && preselectedFamilyIndex > 0 {
                    selectedFamily := fileFamilies[preselectedFamilyIndex]
                    this.logger.Debug("Reusing stored destination family association", Map("slotId", slotId, "folder", destinationFolder, "index", preselectedFamilyIndex, "prefix", selectedFamily["prefix"], "suffix", selectedFamily["suffix"]))
                } else {
                    promptDefaultIndex := preselectedFamilyIndex > 0 ? preselectedFamilyIndex : 1
                    this.logger.Debug("Prompting destination family selection (no stored association)", Map("slotId", slotId, "folder", destinationFolder, "defaultIndex", promptDefaultIndex, "sourceFamilyIndex", sourceFamilyIndex))
                    selectedFamily := appContext.PromptDestinationFamilySelection(slotId, destinationFolder, fileFamilies, preselectedFamilyIndex > 0 ? preselectedFamilyIndex : 1)
                    if !IsObject(selectedFamily) {
                        return Map("success", true, "handledWithoutPaste", true, "statusMessage", "Incremental destination cancelled")
                    }
                }
            }
        }

        if !IsObject(selectedFamily) {
            if IsObject(sourceFamily) {
                selectedFamily := sourceFamily
                this.logger.Debug("Using source-derived family for destination mode", Map("slotId", slotId, "sourceFile", sourceFileName))
            }
        }

        if !IsObject(selectedFamily) {
            return Map("success", true, "handledWithoutPaste", true, "statusMessage", "No file family found for destination")
        }

        familyNumbers := this.GetFamilyNumbers(destinationFolder, selectedFamily)
        hasGaps := this.HasNumberGaps(familyNumbers)

        associationLastNumber := 0
        associationLastDirection := ""
        associationHasLastNumber := false
        if IsObject(association) && association.Has("lastNumber") {
            try {
                associationLastNumber := Integer(association["lastNumber"])
                associationHasLastNumber := true
            } catch {
                associationLastNumber := 0
                associationHasLastNumber := false
            }
        }
        if IsObject(association) && association.Has("lastDirection") {
            associationLastDirection := StrLower(Trim(association["lastDirection"] ""))
        }

        if associationLastDirection != direction {
            this.logger.Debug("Ignoring stored lastNumber due to direction change", Map("slotId", slotId, "folder", destinationFolder, "storedDirection", associationLastDirection, "requestedDirection", direction, "storedLastNumber", associationLastNumber))
            associationLastNumber := 0
            associationHasLastNumber := false
        }

        if familyNumbers.Length > 0 {
            defaultStartNumber := direction = "decrease" ? familyNumbers[1] : familyNumbers[familyNumbers.Length]
        } else {
            defaultStartNumber := 0
        }

        minFamilyNumber := familyNumbers.Length > 0 ? familyNumbers[1] : 0
        maxFamilyNumber := familyNumbers.Length > 0 ? familyNumbers[familyNumbers.Length] : 0

        if associationHasLastNumber && familyNumbers.Length > 0 {
            associationInRange := associationLastNumber >= minFamilyNumber && associationLastNumber <= maxFamilyNumber
            associationEdgeRecoverable := direction = "decrease"
                ? (associationLastNumber = (minFamilyNumber - stepValue))
                : (associationLastNumber = (maxFamilyNumber + stepValue))
            if !associationInRange && !associationEdgeRecoverable {
                ; Ignore stale cursor values from a different segment/family run.
                ; Example: stored -1 should never drive a selected 19..20 segment.
                this.logger.Debug("Ignoring stored lastNumber outside selected family segment", Map(
                    "slotId", slotId,
                    "folder", destinationFolder,
                    "direction", direction,
                    "storedLastNumber", associationLastNumber,
                    "segmentMin", minFamilyNumber,
                    "segmentMax", maxFamilyNumber,
                    "step", stepValue
                ))
                associationLastNumber := 0
                associationHasLastNumber := false
            }
        }

        this.logger.Debug("Incremental destination family boundaries", Map(
            "slotId", slotId,
            "folder", destinationFolder,
            "direction", direction,
            "numbersFound", familyNumbers.Length,
            "minNumber", familyNumbers.Length > 0 ? familyNumbers[1] : 0,
            "maxNumber", familyNumbers.Length > 0 ? familyNumbers[familyNumbers.Length] : 0,
            "numbersPreview", this.BuildNumberListPreview(familyNumbers),
            "defaultStart", defaultStartNumber
        ))

        startNumber := associationHasLastNumber ? associationLastNumber : defaultStartNumber
        if associationHasLastNumber {
            associationLastExists := this.NumberListContains(familyNumbers, associationLastNumber)
            if !associationLastExists {
                ; Association recovery: if the previously created destination file was deleted,
                ; rewind the cursor so the next paste recreates that missing number instead of skipping it.
                startNumber := direction = "decrease" ? (associationLastNumber + stepValue) : (associationLastNumber - stepValue)
                this.logger.Debug("Stored destination cursor missing in folder, rewinding to recreate missing number", Map(
                    "slotId", slotId,
                    "folder", destinationFolder,
                    "direction", direction,
                    "storedLastNumber", associationLastNumber,
                    "rewoundStart", startNumber,
                    "step", stepValue
                ))
            }
        }

        if hasGaps && !associationHasLastNumber {
            ; Gap-aware edge case: force explicit start point when discontinuous numbering is detected.
            ; Applies to both single-family and multi-family folders after a concrete family is selected.
            startCandidates := this.BuildGapStartCandidates(familyNumbers, direction)
            chosenStartNumber := appContext.PromptDestinationStartNumberSelection(slotId, destinationFolder, selectedFamily, startCandidates, defaultStartNumber, direction)
            if chosenStartNumber = "" {
                return Map("success", true, "handledWithoutPaste", true, "statusMessage", "Incremental destination cancelled")
            }
            startNumber := chosenStartNumber
            this.logger.Debug("Destination start point selected for gapped family", Map("slotId", slotId, "folder", destinationFolder, "startNumber", startNumber, "direction", direction))
        }

        if !associationHasLastNumber && startNumber = 0 && direction = "increase" {
            return Map("success", true, "handledWithoutPaste", true, "statusMessage", "Could not determine destination start point")
        }

        nextNumber := direction = "decrease" ? (startNumber - stepValue) : (startNumber + stepValue)
        attempt := 0
        maxAttempts := 5000
        targetPath := ""
        hasExistingNumbers := familyNumbers.Length > 0
        minExistingNumber := minFamilyNumber
        maxExistingNumber := maxFamilyNumber

        this.logger.Debug("Incremental destination numbering initialized", Map("slotId", slotId, "direction", direction, "step", stepValue, "startNumber", startNumber, "nextNumber", nextNumber, "numbersFound", familyNumbers.Length, "hasGaps", hasGaps ? 1 : 0, "associationLastNumber", associationLastNumber))

        loop maxAttempts {
            candidateName := selectedFamily["prefix"] this.FormatNumberWithPadding(nextNumber, selectedFamily["padWidth"]) selectedFamily["suffix"]
            targetPath := destinationFolder "\\" candidateName (sourceExtension != "" ? "." sourceExtension : "")
            if !FileExist(targetPath) {
                break
            }

            if direction = "decrease" && hasExistingNumbers && nextNumber > minExistingNumber {
                ; When descending through an occupied lower range, jump below the current minimum.
                nextNumber := minExistingNumber - stepValue
                this.logger.Debug("Decrease collision hit existing range, jumping below minimum", Map("slotId", slotId, "minExisting", minExistingNumber, "nextNumber", nextNumber))
            } else if direction = "increase" && hasExistingNumbers && nextNumber < maxExistingNumber {
                ; Symmetric behavior for increasing from lower starts across occupied upper ranges.
                nextNumber := maxExistingNumber + stepValue
                this.logger.Debug("Increase collision hit existing range, jumping above maximum", Map("slotId", slotId, "maxExisting", maxExistingNumber, "nextNumber", nextNumber))
            } else {
                nextNumber := direction = "decrease" ? (nextNumber - stepValue) : (nextNumber + stepValue)
            }
            attempt += 1
        }

        if targetPath = "" || FileExist(targetPath) {
            return Map("success", true, "handledWithoutPaste", true, "statusMessage", "Could not find available destination name")
        }

        try {
            FileCopy(sourcePath, targetPath, false)
        } catch error {
            this.logger.Warn("Incremental destination copy failed", Map("slotId", slotId, "source", sourcePath, "target", targetPath, "error", error.HasProp("Message") ? error.Message : "unknown"))
            return Map("success", true, "handledWithoutPaste", true, "statusMessage", "Failed to copy destination file")
        }

        selectedFamily["maxNumber"] := nextNumber
        selectedFamily["lastDirection"] := direction
        appContext.SetDestinationFamilyAssociation(slotId, destinationFolder, selectedFamily)
        this.logger.Info("Incremental destination file created", Map("slotId", slotId, "source", sourcePath, "target", targetPath, "familyPrefix", selectedFamily["prefix"], "familySuffix", selectedFamily["suffix"]))

        return Map("success", true, "handledWithoutPaste", true, "statusMessage", "Created: " targetPath)
    }

    ScanDestinationFamilies(destinationFolder, extensionFilter) {
        ; Build base families, then split by true contiguous numeric runs.
        ; This avoids fake splits caused by digit growth (9 -> 10) while preserving real gaps.
        familiesByKey := Map()
        filesConsidered := 0
        familiesDetected := 0
        scanStage := "init"
        activeFamilyKey := ""

        try {
            scanStage := "collect-files"
            loop Files, destinationFolder "\\*", "F" {
                filesConsidered += 1
                SplitPath(A_LoopFileName, , , &fileExt, &fileNameNoExt)
                if StrLower(fileExt) != StrLower(extensionFilter) {
                    continue
                }

                family := this.ParseFileFamily(fileNameNoExt, fileExt)
                if !IsObject(family) {
                    continue
                }

                familyKey := StrLower(family["prefix"] "|" family["suffix"] "|" family["extension"] "|" family["padWidth"])
                if !familiesByKey.Has(familyKey) {
                    entry := Map(
                        "familyKey", familyKey,
                        "prefix", family["prefix"],
                        "suffix", family["suffix"],
                        "extension", family["extension"],
                        "padWidth", family["padWidth"],
                        "number", family["number"],
                        "numbers", [],
                        "numberSet", Map()
                    )
                    familiesByKey[familyKey] := entry
                    familiesDetected += 1
                }

                entry := familiesByKey[familyKey]
                numberKey := family["number"] ""
                if !entry["numberSet"].Has(numberKey) {
                    entry["numberSet"][numberKey] := true
                    entry["numbers"].Push(family["number"])
                }
            }

            scanStage := "segment-families"
            results := []
            for _, entry in familiesByKey {
                activeFamilyKey := entry.Has("familyKey") ? entry["familyKey"] : ""
                numbers := entry["numbers"]
                if numbers.Length < 1 {
                    continue
                }
                if numbers.Length > 1 {
                    this.SortNumberArrayAscending(numbers)
                }

                segmentStart := numbers[1]
                segmentEnd := numbers[1]
                loop numbers.Length - 1 {
                    currentValue := numbers[A_Index]
                    nextValue := numbers[A_Index + 1]
                    if nextValue = currentValue + 1 {
                        segmentEnd := nextValue
                        continue
                    }

                    results.Push(this.CloneFamilyWithSegment(entry, segmentStart, segmentEnd))
                    segmentStart := nextValue
                    segmentEnd := nextValue
                }

                results.Push(this.CloneFamilyWithSegment(entry, segmentStart, segmentEnd))
            }

            ; Keep discovery order for stability; deterministic sorting is optional and can be restored later.
            scanStage := "completed"

            this.logger.Debug("Destination family scan completed", Map(
                "folder", destinationFolder,
                "extension", extensionFilter,
                "filesConsidered", filesConsidered,
                "baseFamilies", familiesDetected,
                "segmentedFamilies", results.Length
            ))
            return results
        } catch error {
            this.logger.Error("Destination family scan internal failure", Map(
                "folder", destinationFolder,
                "extension", extensionFilter,
                "stage", scanStage,
                "activeFamilyKey", activeFamilyKey,
                "filesConsidered", filesConsidered,
                "baseFamilies", familiesDetected,
                "error", this.DescribeErrorObject(error)
            ))
            throw error
        }
    }

    DescribeErrorObject(errorObj) {
        ; Local defensive serializer for scan-time failures (independent from appContext methods).
        details := []
        try {
            if IsObject(errorObj) {
                try {
                    message := errorObj.Message
                    if message != "" {
                        details.Push("Message=" message)
                    }
                } catch {
                }
                try {
                    line := errorObj.Line
                    if line != "" {
                        details.Push("Line=" line)
                    }
                } catch {
                }
                try {
                    errorFilePath := errorObj.File
                    if errorFilePath != "" {
                        details.Push("File=" errorFilePath)
                    }
                } catch {
                }
                try {
                    what := errorObj.What
                    if what != "" {
                        details.Push("What=" what)
                    }
                } catch {
                }
                try {
                    extra := errorObj.Extra
                    if extra != "" {
                        details.Push("Extra=" extra)
                    }
                } catch {
                }
                try {
                    details.Push("Type=" Type(errorObj))
                } catch {
                }
                try {
                    details.Push("String=" String(errorObj))
                } catch {
                }
            }
        } catch {
        }

        if details.Length > 0 {
            summary := ""
            loop details.Length {
                if A_Index > 1 {
                    summary .= " | "
                }
                summary .= details[A_Index]
            }
            return summary
        }
        return "<unknown error object>"
    }

    CloneFamilyWithSegment(baseFamily, segmentStart, segmentEnd) {
        familyClone := Map(
            "prefix", baseFamily["prefix"],
            "suffix", baseFamily["suffix"],
            "extension", baseFamily["extension"],
            "padWidth", baseFamily["padWidth"],
            "number", baseFamily["number"],
            "minNumber", segmentStart,
            "maxNumber", segmentEnd,
            "segmentMin", segmentStart,
            "segmentMax", segmentEnd
        )
        return familyClone
    }

    ParseFileFamily(fileNameNoExt, fileExt) {
        ; Signed-number aware parsing keeps decrease mode consistent once numbering crosses below zero.
        if !RegExMatch(fileNameNoExt, "^(.*?)(-?\d+)([^\d]*)$", &match) {
            return ""
        }

        numberToken := match[2]
        numberValue := Integer(numberToken)
        numberDigits := numberToken
        if SubStr(numberDigits, 1, 1) = "-" {
            numberDigits := SubStr(numberDigits, 2)
        }
        ; Treat pad width as a naming-template signal only when leading zeros are explicit.
        ; Example: 001 => padWidth 3, but 1/10/100 => padWidth 0 (variable natural width).
        padWidth := (StrLen(numberDigits) > 1 && SubStr(numberDigits, 1, 1) = "0") ? StrLen(numberDigits) : 0
        return Map(
            "prefix", match[1],
            "suffix", match[3],
            "number", numberValue,
            "padWidth", padWidth,
            "extension", StrLower(fileExt)
        )
    }

    FindMatchingFamily(familyList, expectedFamily) {
        for family in familyList {
            if StrLower(family["prefix"]) = StrLower(expectedFamily["prefix"])
                && StrLower(family["suffix"]) = StrLower(expectedFamily["suffix"])
                && StrLower(family["extension"]) = StrLower(expectedFamily["extension"])
                && family["padWidth"] = expectedFamily["padWidth"] {
                if expectedFamily.Has("lastNumber") {
                    try {
                        expectedNumber := Integer(expectedFamily["lastNumber"])
                        if family.Has("segmentMin") && family.Has("segmentMax") {
                            if expectedNumber < family["segmentMin"] || expectedNumber > family["segmentMax"] {
                                continue
                            }
                        }
                    } catch {
                    }
                }
                return family
            }
        }
        return ""
    }

    FindMatchingFamilyIndex(familyList, expectedFamily) {
        loop familyList.Length {
            family := familyList[A_Index]
            if StrLower(family["prefix"]) = StrLower(expectedFamily["prefix"])
                && StrLower(family["suffix"]) = StrLower(expectedFamily["suffix"])
                && StrLower(family["extension"]) = StrLower(expectedFamily["extension"])
                && family["padWidth"] = expectedFamily["padWidth"] {
                if expectedFamily.Has("lastNumber") {
                    try {
                        expectedNumber := Integer(expectedFamily["lastNumber"])
                        if family.Has("segmentMin") && family.Has("segmentMax") {
                            if expectedNumber < family["segmentMin"] || expectedNumber > family["segmentMax"] {
                                continue
                            }
                        }
                    } catch {
                    }
                }
                return A_Index
            }
        }
        return 0
    }

    GetFamilyMaxNumber(destinationFolder, family) {
        maxValue := -1
        loop Files, destinationFolder "\\*", "F" {
            SplitPath(A_LoopFileName, , , &fileExt, &fileNameNoExt)
            if StrLower(fileExt) != StrLower(family["extension"]) {
                continue
            }
            candidate := this.ParseFileFamily(fileNameNoExt, fileExt)
            if !IsObject(candidate) {
                continue
            }
            if StrLower(candidate["prefix"]) != StrLower(family["prefix"]) || StrLower(candidate["suffix"]) != StrLower(family["suffix"]) {
                continue
            }
            if candidate["number"] > maxValue {
                maxValue := candidate["number"]
            }
        }
        return maxValue < 0 ? 0 : maxValue
    }

    GetFamilyNumbers(destinationFolder, family) {
        numbersByValue := Map()
        loop Files, destinationFolder "\\*", "F" {
            SplitPath(A_LoopFileName, , , &fileExt, &fileNameNoExt)
            if StrLower(fileExt) != StrLower(family["extension"]) {
                continue
            }
            candidate := this.ParseFileFamily(fileNameNoExt, fileExt)
            if !IsObject(candidate) {
                continue
            }
            if StrLower(candidate["prefix"]) != StrLower(family["prefix"]) || StrLower(candidate["suffix"]) != StrLower(family["suffix"]) {
                continue
            }
            if family.Has("padWidth") && candidate["padWidth"] != family["padWidth"] {
                continue
            }
            if family.Has("segmentMin") && candidate["number"] < family["segmentMin"] {
                continue
            }
            if family.Has("segmentMax") && candidate["number"] > family["segmentMax"] {
                continue
            }
            numberKey := candidate["number"] ""
            if !numbersByValue.Has(numberKey) {
                numbersByValue[numberKey] := candidate["number"]
            }
        }

        numbers := []
        for _, value in numbersByValue {
            numbers.Push(value)
        }
        if numbers.Length > 1 {
            ; Numeric sort is mandatory: text sort can place 20 before 3 and break decrease-mode minimum detection.
            this.SortNumberArrayAscending(numbers)
        }
        return numbers
    }

    SortNumberArrayAscending(numberList) {
        ; Stable insertion sort keeps behavior deterministic across AHK versions without relying on sort comparator support.
        if numberList.Length < 2 {
            return
        }

        loop numberList.Length - 1 {
            index := A_Index + 1
            value := numberList[index]
            cursor := index - 1
            while cursor >= 1 && numberList[cursor] > value {
                numberList[cursor + 1] := numberList[cursor]
                cursor -= 1
            }
            numberList[cursor + 1] := value
        }
    }

    HasNumberGaps(numberList) {
        if numberList.Length < 2 {
            return false
        }
        loop numberList.Length - 1 {
            currentValue := numberList[A_Index]
            nextValue := numberList[A_Index + 1]
            if (nextValue - currentValue) > 1 {
                return true
            }
        }
        return false
    }

    NumberListContains(numberList, targetNumber) {
        loop numberList.Length {
            if numberList[A_Index] = targetNumber {
                return true
            }
        }
        return false
    }

    BuildGapStartCandidates(numberList, direction) {
        ; Build contiguous segments and expose segment boundaries as user-selectable start points.
        if numberList.Length < 1 {
            return []
        }

        candidates := []
        segmentStart := numberList[1]
        segmentEnd := numberList[1]

        loop numberList.Length - 1 {
            currentValue := numberList[A_Index]
            nextValue := numberList[A_Index + 1]
            if nextValue = currentValue + 1 {
                segmentEnd := nextValue
                continue
            }

            candidate := direction = "decrease" ? segmentStart : segmentEnd
            candidates.Push(candidate)

            segmentStart := nextValue
            segmentEnd := nextValue
        }

        candidates.Push(direction = "decrease" ? segmentStart : segmentEnd)
        return candidates
    }

    BuildNumberListPreview(numberList) {
        ; Compact list preview for debugging real folder state without flooding logs.
        if numberList.Length < 1 {
            return "[]"
        }

        maxShown := 20
        preview := "["
        loop numberList.Length {
            if A_Index > maxShown {
                preview .= " ..."
                break
            }
            if A_Index > 1 {
                preview .= ","
            }
            preview .= numberList[A_Index]
        }
        preview .= "]"
        return preview
    }

    BuildFamilyBoundaryPreview(familyList) {
        ; Summarize family detection with min/max boundaries for fast troubleshooting.
        if familyList.Length < 1 {
            return "[]"
        }

        maxShown := 12
        preview := "["
        loop familyList.Length {
            if A_Index > maxShown {
                preview .= " ..."
                break
            }
            if A_Index > 1 {
                preview .= "; "
            }
            family := familyList[A_Index]
            minValue := family.Has("minNumber") ? family["minNumber"] : family["maxNumber"]
            preview .= family["prefix"] "*" family["suffix"] "{w=" family["padWidth"] "," minValue "->" family["maxNumber"] "}"
        }
        preview .= "]"
        return preview
    }

    FormatNumberWithPadding(numberValue, padWidth) {
        ; Preserve sign while padding absolute digits (e.g., -3 with width 2 => -03).
        if padWidth < 1 {
            return numberValue ""
        }

        if numberValue < 0 {
            return "-" Format("{:0" padWidth "}", Abs(numberValue))
        }
        return Format("{:0" padWidth "}", numberValue)
    }
}

class ClipboardSlots {
    __New(slotCount, logger) {
        this.logger := logger
        this.slots := Map()
        this.lastResolvedSourceDir := ""
        this.SetSlotCount(slotCount)
    }

    SetSlotCount(slotCount) {
        normalized := slotCount < 1 ? 1 : (slotCount > 9 ? 9 : slotCount)
        existing := this.slots
        this.slots := Map()
        loop normalized {
            slotId := A_Index
            if existing.Has(slotId) {
                this.slots[slotId] := existing[slotId]
                if !this.slots[slotId].Has("text") {
                    this.slots[slotId]["text"] := ""
                }
                if !this.slots[slotId].Has("sourcePath") {
                    this.slots[slotId]["sourcePath"] := ""
                }
                if !this.slots[slotId].Has("metadata") {
                    this.slots[slotId]["metadata"] := Map()
                }
            } else {
                this.slots[slotId] := Map("hasData", false, "data", "", "text", "", "sourcePath", "", "metadata", Map())
            }
        }
        this.logger.Info("Slot count updated", Map("slotCount", normalized))
    }

    CaptureFromSelection(slotId, sourceCopyCombo) {
        if !this.slots.Has(slotId) {
            this.logger.Warn("Capture attempted on invalid slot", Map("slotId", slotId))
            return false
        }

        captureWindow := this.GetActiveWindowSnapshot()
        sourceProcess := captureWindow["process"]
        isPhotoshopSource := this.IsPhotoshopProcess(sourceProcess)

        originalClipboard := ClipboardAll()
        A_Clipboard := ""

        startTick := A_TickCount
        preCopySequence := this.GetClipboardSequenceNumber()
        Send(sourceCopyCombo)
        clipWaitSeconds := isPhotoshopSource ? 2.5 : 0.8
        copied := ClipWait(clipWaitSeconds)

        sequenceAdvanced := false
        anyClipboardContent := false
        if !copied {
            ; Some apps (notably Photoshop/private clipboard producers) may publish delayed
            ; or non-text formats that ClipWait can miss; sequence/content fallback catches that.
            sequenceAdvanced := this.WaitForClipboardSequenceAdvance(preCopySequence, isPhotoshopSource ? 2200 : 600)
            if sequenceAdvanced {
                copied := true
            } else {
                anyClipboardContent := this.HasClipboardAnyContent()
                copied := anyClipboardContent
            }
        }

        if !copied {
            A_Clipboard := originalClipboard
            this.logger.Warn("Capture failed: clipboard update timeout", Map(
                "slotId", slotId,
                "sourceCopyCombo", sourceCopyCombo,
                "sourceProcess", sourceProcess,
                "clipWaitSeconds", clipWaitSeconds,
                "sequenceAdvanced", sequenceAdvanced,
                "anyClipboardContent", anyClipboardContent
            ))
            return false
        }

        previousSourcePath := this.slots[slotId]["sourcePath"]
        previousTextValue := this.slots[slotId]["text"]
        capturedText := A_Clipboard ""
        capturedData := ClipboardAll()
        formatSnapshot := this.GetClipboardFormatSnapshot()

        if isPhotoshopSource && !this.HasStableReplayFormats(formatSnapshot["names"]) {
            this.logger.Warn("Photoshop capture looks app-private; attempting materialization via Copy Merged", Map(
                "slotId", slotId,
                "initialFormatCount", formatSnapshot["count"],
                "initialFormats", formatSnapshot["preview"]
            ))

            if this.TryMaterializePhotoshopClipboardWithCopyMerged(sourceCopyCombo, &materializedText, &materializedData, &materializedFormats) {
                capturedText := materializedText
                capturedData := materializedData
                formatSnapshot := materializedFormats
                this.logger.Info("Photoshop capture materialized via Copy Merged", Map(
                    "slotId", slotId,
                    "formatCount", formatSnapshot["count"],
                    "formats", formatSnapshot["preview"]
                ))
            } else {
                ; Do not store non-isolatable private payloads; they can alias to "latest"
                ; Photoshop state and make different slots paste the same content.
                A_Clipboard := originalClipboard
                this.logger.Warn("Photoshop capture materialization failed; capture rejected to avoid cross-slot aliasing", Map("slotId", slotId))
                return false
            }
        }

        capturedSourcePath := this.ResolveCopiedSourcePath(slotId, capturedText, previousSourcePath, previousTextValue)
        captureMetadata := this.BuildCaptureMetadata(captureWindow, formatSnapshot, capturedSourcePath)
        this.slots[slotId]["data"] := capturedData
        this.slots[slotId]["text"] := capturedText
        this.slots[slotId]["sourcePath"] := capturedSourcePath
        this.slots[slotId]["metadata"] := captureMetadata
        this.slots[slotId]["hasData"] := true
        A_Clipboard := originalClipboard

        elapsed := A_TickCount - startTick
        size := capturedData.HasProp("Size") ? capturedData.Size : 0
        this.logger.Info("Captured data into slot", Map("slotId", slotId, "elapsedMs", elapsed, "bytes", size, "sourcePath", capturedSourcePath))
        this.logger.Debug("Slot capture metadata", Map("slotId", slotId, "captureProcess", captureMetadata["captureProcess"], "hasPhotoshopFormats", captureMetadata["hasPhotoshopFormats"], "formatCount", captureMetadata["formatCount"]))
        return true
    }

    HasStableReplayFormats(formatNames) {
        if !IsObject(formatNames) {
            return false
        }

        for formatName in formatNames {
            normalized := StrLower(formatName)
            if normalized = "cf_unicodetext" || normalized = "cf_text" || normalized = "cf_hdrop"
                || normalized = "cf_dib" || normalized = "cf_dibv5" || normalized = "cf_bitmap"
                || InStr(normalized, "html format") || InStr(normalized, "rich text") {
                return true
            }
        }
        return false
    }

    TryMaterializePhotoshopClipboardWithCopyMerged(sourceCopyCombo, &capturedTextOut, &capturedDataOut, &formatSnapshotOut) {
        capturedTextOut := ""
        capturedDataOut := ""
        formatSnapshotOut := Map("names", [], "preview", "", "count", 0)

        ; Try a sequence of materialization commands. Some Photoshop contexts ignore
        ; Copy Merged depending on active tool/state; we probe multiple commands.
        attempts := [
            Map("label", "copy-merged", "command", "^+c"),
            Map("label", "standard-copy", "command", "^c")
        ]

        for attempt in attempts {
            if this.TryMaterializePhotoshopClipboardAttempt(attempt["label"], attempt["command"], &attemptText, &attemptData, &attemptFormats) {
                capturedTextOut := attemptText
                capturedDataOut := attemptData
                formatSnapshotOut := attemptFormats
                return true
            }
        }

        ; Final fallback: round-trip through a temporary Photoshop document.
        ; This can force materialization of private layer payloads into stable formats.
        if this.TryMaterializePhotoshopViaNewDocumentRoundtrip(&roundtripText, &roundtripData, &roundtripFormats) {
            capturedTextOut := roundtripText
            capturedDataOut := roundtripData
            formatSnapshotOut := roundtripFormats
            return true
        }

        return false
    }

    TryMaterializePhotoshopClipboardAttempt(attemptLabel, commandText, &capturedTextOut, &capturedDataOut, &formatSnapshotOut) {
        capturedTextOut := ""
        capturedDataOut := ""
        formatSnapshotOut := Map("names", [], "preview", "", "count", 0)

        preSequence := this.GetClipboardSequenceNumber()
        A_Clipboard := ""

        ; Release synthetic key state from slot hotkey chords before issuing
        ; Photoshop clipboard commands, improving command reliability.
        Sleep(40)
        Send(commandText)

        copied := ClipWait(1.8)
        if !copied {
            copied := this.WaitForClipboardSequenceAdvance(preSequence, 1800)
            if !copied && !this.HasClipboardAnyContent() {
                this.logger.Debug("Photoshop materialization attempt produced no clipboard update", Map("attempt", attemptLabel, "command", commandText))
                return false
            }
        }

        attemptText := A_Clipboard ""
        attemptData := ClipboardAll()
        attemptFormats := this.GetClipboardFormatSnapshot()

        stable := this.HasStableReplayFormats(attemptFormats["names"])
        this.logger.Debug("Photoshop materialization attempt result", Map(
            "attempt", attemptLabel,
            "command", commandText,
            "formatCount", attemptFormats["count"],
            "formats", attemptFormats["preview"],
            "stable", stable ? 1 : 0,
            "bytes", attemptData.HasProp("Size") ? attemptData.Size : 0
        ))

        if !stable {
            return false
        }

        capturedTextOut := attemptText
        capturedDataOut := attemptData
        formatSnapshotOut := attemptFormats
        return true
    }

    TryMaterializePhotoshopViaNewDocumentRoundtrip(&capturedTextOut, &capturedDataOut, &formatSnapshotOut) {
        capturedTextOut := ""
        capturedDataOut := ""
        formatSnapshotOut := Map("names", [], "preview", "", "count", 0)

        this.logger.Debug("Photoshop materialization roundtrip started", Map())

        ; Create a new document from current clipboard, then recopy from that document.
        ; In many Photoshop states, this converts private DataObject payloads into
        ; stable image formats (CF_DIB/CF_DIBV5/etc.) that can be isolated per slot.
        Send("^n")
        Sleep(220)
        Send("{Enter}")
        Sleep(420)

        preSequence := this.GetClipboardSequenceNumber()
        A_Clipboard := ""
        Send("^a")
        Sleep(80)
        Send("^c")

        copied := ClipWait(1.8)
        if !copied {
            copied := this.WaitForClipboardSequenceAdvance(preSequence, 1800)
        }

        ; Try to close temporary document without saving.
        Send("^w")
        Sleep(120)
        Send("!n")
        Sleep(70)
        Send("{Esc}")

        if !copied && !this.HasClipboardAnyContent() {
            this.logger.Debug("Photoshop materialization roundtrip produced no clipboard update", Map())
            return false
        }

        attemptText := A_Clipboard ""
        attemptData := ClipboardAll()
        attemptFormats := this.GetClipboardFormatSnapshot()
        stable := this.HasStableReplayFormats(attemptFormats["names"])

        this.logger.Debug("Photoshop materialization roundtrip result", Map(
            "formatCount", attemptFormats["count"],
            "formats", attemptFormats["preview"],
            "stable", stable ? 1 : 0,
            "bytes", attemptData.HasProp("Size") ? attemptData.Size : 0
        ))

        if !stable {
            return false
        }

        capturedTextOut := attemptText
        capturedDataOut := attemptData
        formatSnapshotOut := attemptFormats
        return true
    }

    GetClipboardSequenceNumber() {
        try {
            return DllCall("user32\\GetClipboardSequenceNumber", "uint")
        } catch {
            return 0
        }
    }

    WaitForClipboardSequenceAdvance(previousSequence, timeoutMs) {
        if previousSequence < 1 {
            return false
        }

        startTick := A_TickCount
        while (A_TickCount - startTick) < timeoutMs {
            currentSequence := this.GetClipboardSequenceNumber()
            if currentSequence > previousSequence {
                return true
            }
            Sleep(40)
        }
        return false
    }

    HasClipboardAnyContent() {
        clipboardOpened := false
        try {
            clipboardOpened := DllCall("OpenClipboard", "ptr", 0, "int")
            if !clipboardOpened {
                return false
            }

            firstFormat := DllCall("EnumClipboardFormats", "uint", 0, "uint")
            return firstFormat != 0
        } catch {
            return false
        } finally {
            if clipboardOpened {
                try {
                    DllCall("CloseClipboard")
                } catch {
                }
            }
        }
    }

    BuildCaptureMetadata(windowSnapshot, formatSnapshot, capturedSourcePath) {
        metadata := Map(
            "captureProcess", windowSnapshot["process"],
            "captureClass", windowSnapshot["class"],
            "captureTitle", windowSnapshot["title"],
            "capturedAtTick", A_TickCount,
            "sourcePath", capturedSourcePath,
            "formatPreview", formatSnapshot["preview"],
            "formatCount", formatSnapshot["count"],
            "hasPhotoshopFormats", this.HasPhotoshopClipboardFormats(formatSnapshot["names"]) ? 1 : 0,
            "isPhotoshopSource", this.IsPhotoshopProcess(windowSnapshot["process"]) ? 1 : 0
        )
        return metadata
    }

    IsPhotoshopProcess(processName) {
        return InStr(StrLower(Trim(processName "")), "photoshop") ? true : false
    }

    HasPhotoshopClipboardFormats(formatNames) {
        if !IsObject(formatNames) {
            return false
        }
        for formatName in formatNames {
            normalized := StrLower(formatName)
            if InStr(normalized, "photoshop") || InStr(normalized, "adobe") {
                return true
            }
        }
        return false
    }

    GetActiveWindowSnapshot() {
        snapshot := Map("title", "", "class", "", "process", "")
        try {
            snapshot["title"] := WinGetTitle("A")
        } catch {
        }
        try {
            snapshot["class"] := WinGetClass("A")
        } catch {
        }
        try {
            snapshot["process"] := WinGetProcessName("A")
        } catch {
        }
        return snapshot
    }

    GetClipboardFormatSnapshot() {
        names := []
        preview := ""
        count := 0
        clipboardOpened := false

        try {
            clipboardOpened := DllCall("OpenClipboard", "ptr", 0, "int")
            if !clipboardOpened {
                return Map("names", names, "preview", preview, "count", count)
            }

            formatId := 0
            maxFormats := 64
            loop {
                formatId := DllCall("EnumClipboardFormats", "uint", formatId, "uint")
                if !formatId {
                    break
                }

                count += 1
                if names.Length < maxFormats {
                    names.Push(this.GetClipboardFormatDisplayName(formatId))
                }
            }
        } catch {
        } finally {
            if clipboardOpened {
                try {
                    DllCall("CloseClipboard")
                } catch {
                }
            }
        }

        if names.Length > 0 {
            preview := "["
            loop names.Length {
                if A_Index > 1 {
                    preview .= ", "
                }
                preview .= names[A_Index]
                if A_Index >= 12 {
                    if count > A_Index {
                        preview .= ", ..."
                    }
                    break
                }
            }
            preview .= "]"
        }

        return Map("names", names, "preview", preview, "count", count)
    }

    GetClipboardFormatDisplayName(formatId) {
        static standardNames := Map(
            1, "CF_TEXT",
            2, "CF_BITMAP",
            3, "CF_METAFILEPICT",
            4, "CF_SYLK",
            5, "CF_DIF",
            6, "CF_TIFF",
            7, "CF_OEMTEXT",
            8, "CF_DIB",
            9, "CF_PALETTE",
            10, "CF_PENDATA",
            11, "CF_RIFF",
            12, "CF_WAVE",
            13, "CF_UNICODETEXT",
            14, "CF_ENHMETAFILE",
            15, "CF_HDROP",
            16, "CF_LOCALE",
            17, "CF_DIBV5"
        )

        if standardNames.Has(formatId) {
            return standardNames[formatId]
        }

        formatNameBuffer := Buffer(512, 0)
        try {
            length := DllCall("GetClipboardFormatNameW", "uint", formatId, "ptr", formatNameBuffer, "int", 255, "int")
            if length > 0 {
                return StrGet(formatNameBuffer, length, "UTF-16")
            }
        } catch {
        }

        return "Format#" formatId
    }

    ResolveCopiedSourcePath(slotId, capturedText, previousSourcePath := "", previousTextValue := "") {
        ; --- Core file-source resolution at copy-time (works with custom file managers that provide CF_HDROP). ---
        if this.TryGetFirstClipboardFilePath(&clipboardFilePath) {
            this.RememberResolvedSourceDir(clipboardFilePath)
            this.logger.Debug("Resolved source path from CF_HDROP at copy-time", Map("path", clipboardFilePath))
            return clipboardFilePath
        }

        textCandidate := this.NormalizeClipboardPathCandidate(capturedText)
        if textCandidate != "" && FileExist(textCandidate) {
            this.RememberResolvedSourceDir(textCandidate)
            this.logger.Debug("Resolved source path from clipboard text at copy-time", Map("path", textCandidate))
            return textCandidate
        }

        ; --- Smart fallback for custom file managers that copy only file names (no path metadata). ---
        if this.TryResolveFilenameWithHints(textCandidate, previousSourcePath, previousTextValue, &hintResolvedPath) {
            this.RememberResolvedSourceDir(hintResolvedPath)
            this.logger.Debug("Resolved source path using directory hints", Map("slotId", slotId, "fileName", textCandidate, "path", hintResolvedPath))
            return hintResolvedPath
        }

        ; --- Last-resort failsafe for custom file managers: bounded filename search across smart roots. ---
        if this.TryResolveFilenameBySearch(textCandidate, previousSourcePath, previousTextValue, &searchedResolvedPath) {
            this.RememberResolvedSourceDir(searchedResolvedPath)
            this.logger.Debug("Resolved source path using bounded filename search", Map("slotId", slotId, "fileName", textCandidate, "path", searchedResolvedPath))
            return searchedResolvedPath
        }

        ; --- Custom file manager fallback: inspect active window title/text for directory paths. ---
        if this.TryResolveFilenameFromActiveWindowContext(textCandidate, &windowResolvedPath) {
            this.RememberResolvedSourceDir(windowResolvedPath)
            this.logger.Debug("Resolved source path using active-window context", Map("slotId", slotId, "fileName", textCandidate, "path", windowResolvedPath))
            return windowResolvedPath
        }

        this.logger.Debug("No source path resolved at copy-time", Map("slotId", slotId, "capturedText", textCandidate))
        return ""
    }

    TryResolveFilenameBySearch(fileNameCandidate, previousSourcePath, previousTextValue, &resolvedPathOut) {
        resolvedPathOut := ""
        candidate := this.NormalizeClipboardPathCandidate(fileNameCandidate)
        if candidate = "" {
            return false
        }

        SplitPath(candidate, &candidateName, &candidateDir)
        if candidateDir != "" {
            return false
        }

        roots := this.BuildFilenameSearchRoots(previousSourcePath, previousTextValue)
        if roots.Length = 0 {
            return false
        }

        ; Keep search bounded to avoid UI stalls on large file trees.
        maxScannedFiles := 25000
        scannedFiles := 0
        matchCount := 0
        firstMatchPath := ""
        seenMatchPaths := Map()
        targetLower := StrLower(candidateName)
        stopSearch := false

        for rootPath in roots {
            if stopSearch {
                break
            }

            try {
                loop Files, rootPath "\\*", "RF" {
                    scannedFiles += 1

                    if StrLower(A_LoopFileName) = targetLower {
                        normalizedFullPath := StrLower(A_LoopFileFullPath)
                        if seenMatchPaths.Has(normalizedFullPath) {
                            ; Same file may be encountered via overlapping roots; ignore duplicate hit.
                            continue
                        }
                        seenMatchPaths[normalizedFullPath] := true

                        matchCount += 1
                        if matchCount = 1 {
                            firstMatchPath := A_LoopFileFullPath
                        } else {
                            this.logger.Debug("Filename search ambiguous", Map("fileName", candidateName, "firstMatch", firstMatchPath, "secondMatch", A_LoopFileFullPath, "scanned", scannedFiles))
                            return false
                        }
                    }

                    if scannedFiles >= maxScannedFiles {
                        stopSearch := true
                        break
                    }
                }
            } catch {
                continue
            }
        }

        if matchCount = 1 {
            resolvedPathOut := firstMatchPath
            return true
        }

        this.logger.Debug("Filename search did not resolve path", Map("fileName", candidateName, "scanned", scannedFiles, "roots", roots.Length, "stoppedEarly", stopSearch, "uniqueMatches", matchCount))
        return false
    }

    BuildFilenameSearchRoots(previousSourcePath, previousTextValue) {
        roots := []
        this.PushHintDirectory(roots, this.ExtractDirectoryIfExists(previousSourcePath))
        this.PushHintDirectory(roots, this.ExtractDirectoryIfExists(previousTextValue))
        this.PushHintDirectory(roots, this.lastResolvedSourceDir)

        ; Workspace-friendly roots as practical defaults for script-driven clipboard workflows.
        this.PushHintDirectory(roots, A_ScriptDir)
        try {
            this.PushHintDirectory(roots, A_MyDocuments)
        } catch {
        }
        try {
            this.PushHintDirectory(roots, A_Desktop)
        } catch {
        }

        ; Parent folder of script directory catches adjacent project folders.
        SplitPath(A_ScriptDir, , &scriptParentDir)
        this.PushHintDirectory(roots, scriptParentDir)

        return roots
    }

    TryResolveFilenameWithHints(fileNameCandidate, previousSourcePath, previousTextValue, &resolvedPathOut) {
        resolvedPathOut := ""
        candidate := this.NormalizeClipboardPathCandidate(fileNameCandidate)
        if candidate = "" {
            return false
        }

        ; If candidate already includes a directory and still does not exist, hints will not help.
        SplitPath(candidate, &candidateName, &candidateDir)
        if candidateDir != "" {
            return false
        }

        hintDirectories := []
        this.PushHintDirectory(hintDirectories, this.ExtractDirectoryIfExists(previousSourcePath))
        this.PushHintDirectory(hintDirectories, this.ExtractDirectoryIfExists(previousTextValue))
        this.PushHintDirectory(hintDirectories, this.lastResolvedSourceDir)

        for hintDir in hintDirectories {
            potentialPath := hintDir "\\" candidate
            if FileExist(potentialPath) {
                resolvedPathOut := potentialPath
                return true
            }
        }

        return false
    }

    PushHintDirectory(hintDirectories, hintDir) {
        normalized := Trim(hintDir "")
        if normalized = "" {
            return
        }
        for existing in hintDirectories {
            if StrLower(existing) = StrLower(normalized) {
                return
            }
        }
        hintDirectories.Push(normalized)
    }

    ExtractDirectoryIfExists(pathCandidate) {
        normalized := this.NormalizeClipboardPathCandidate(pathCandidate)
        if normalized = "" {
            return ""
        }

        ; If this is already a directory path, keep it when it exists.
        pathKind := FileExist(normalized)
        if pathKind != "" && InStr(pathKind, "D") {
            return normalized
        }

        if pathKind != "" {
            SplitPath(normalized, , &dirPath)
            return dirPath
        }

        return ""
    }

    RememberResolvedSourceDir(resolvedPath) {
        normalized := this.NormalizeClipboardPathCandidate(resolvedPath)
        if normalized = "" || !FileExist(normalized) {
            return
        }

        SplitPath(normalized, , &resolvedDir)
        if resolvedDir != "" {
            this.lastResolvedSourceDir := resolvedDir
        }
    }

    TryResolveFilenameFromActiveWindowContext(fileNameCandidate, &resolvedPathOut) {
        resolvedPathOut := ""
        normalizedName := this.NormalizeClipboardPathCandidate(fileNameCandidate)
        if normalizedName = "" {
            return false
        }

        ; Only run this fallback for filename-only values.
        SplitPath(normalizedName, , &nameDir)
        if nameDir != "" {
            return false
        }

        activeTitle := ""
        activeText := ""
        try {
            activeTitle := WinGetTitle("A")
        } catch {
        }
        try {
            activeText := WinGetText("A")
        } catch {
        }

        directoryHints := this.ExtractExistingDirectoriesFromWindowText(activeTitle "`n" activeText)
        for hintDir in directoryHints {
            candidatePath := hintDir "\\" normalizedName
            if FileExist(candidatePath) {
                resolvedPathOut := candidatePath
                return true
            }
        }

        return false
    }

    ExtractExistingDirectoriesFromWindowText(rawText) {
        results := []
        source := rawText ""
        if source = "" {
            return results
        }

        ; Match Windows absolute paths in title/control text.
        pathPattern := 'i)([a-z]:\\[^<>:"/\|\?\*`r`n]+(?:\\[^<>:"/\|\?\*`r`n]+)*)'
        searchPos := 1
        while RegExMatch(source, pathPattern, &match, searchPos) {
            pathValue := Trim(match[1])
            if pathValue != "" {
                pathKind := FileExist(pathValue)
                if pathKind != "" {
                    if InStr(pathKind, "D") {
                        this.PushHintDirectory(results, pathValue)
                    } else {
                        SplitPath(pathValue, , &parentDir)
                        this.PushHintDirectory(results, parentDir)
                    }
                }
            }
            searchPos := match.Pos(1) + match.Len(1)
        }

        return results
    }

    TryGetFirstClipboardFilePath(&filePathOut) {
        filePathOut := ""
        clipboardOpened := false
        try {
            clipboardOpened := DllCall("OpenClipboard", "ptr", 0, "int")
            if !clipboardOpened {
                return false
            }

            ; CF_HDROP = 15: standard file-drop clipboard format.
            hDrop := DllCall("GetClipboardData", "uint", 15, "ptr")
            if !hDrop {
                return false
            }

            fileCount := DllCall("shell32\\DragQueryFileW", "ptr", hDrop, "uint", 0xFFFFFFFF, "ptr", 0, "uint", 0, "uint")
            if fileCount < 1 {
                return false
            }

            fileLen := DllCall("shell32\\DragQueryFileW", "ptr", hDrop, "uint", 0, "ptr", 0, "uint", 0, "uint")
            if fileLen < 1 {
                return false
            }

            pathBuffer := Buffer((fileLen + 1) * 2, 0)
            DllCall("shell32\\DragQueryFileW", "ptr", hDrop, "uint", 0, "ptr", pathBuffer, "uint", fileLen + 1, "uint")
            filePathOut := StrGet(pathBuffer, "UTF-16")
            return filePathOut != ""
        } catch {
            return false
        } finally {
            if clipboardOpened {
                try {
                    DllCall("CloseClipboard")
                } catch {
                }
            }
        }
    }

    NormalizeClipboardPathCandidate(rawText) {
        text := Trim(rawText "")
        if text = "" {
            return ""
        }

        for line in StrSplit(text, "`n") {
            cleaned := Trim(StrReplace(line, "`r", ""))
            if cleaned = "" {
                continue
            }
            if SubStr(cleaned, 1, 1) = '"' && SubStr(cleaned, -1) = '"' && StrLen(cleaned) >= 2 {
                cleaned := SubStr(cleaned, 2, StrLen(cleaned) - 2)
            }
            return cleaned
        }
        return ""
    }

    PasteToTarget(slotId, targetPasteCombo) {
        if !this.slots.Has(slotId) {
            this.logger.Warn("Paste attempted on invalid slot", Map("slotId", slotId))
            return false
        }
        if !this.slots[slotId]["hasData"] {
            this.logger.Warn("Paste attempted with empty slot", Map("slotId", slotId))
            return false
        }

        return this.PastePayloadToTarget(slotId, this.slots[slotId]["data"], targetPasteCombo)
    }

    PastePayloadToTarget(slotId, payloadData, targetPasteCombo, pasteOptions := "") {
        originalClipboard := ClipboardAll()
        restoreDelayMs := 70
        profile := "default"
        if IsObject(pasteOptions) {
            if pasteOptions.Has("restoreDelayMs") {
                restoreDelayMs := Max(50, pasteOptions["restoreDelayMs"])
            }
            if pasteOptions.Has("profile") && pasteOptions["profile"] != "" {
                profile := pasteOptions["profile"]
            }
        }

        startTick := A_TickCount
        A_Clipboard := payloadData
        ClipWait(0.2)
        Send(targetPasteCombo)
        ; Some app-private clipboard payloads (e.g., Photoshop) need a longer hand-off
        ; window before clipboard restoration to avoid partial/incorrect paste replay.
        Sleep(restoreDelayMs)
        A_Clipboard := originalClipboard

        elapsed := A_TickCount - startTick
        dataSize := IsObject(payloadData) && payloadData.HasProp("Size") ? payloadData.Size : StrLen(payloadData "")
        this.logger.Info("Pasted payload from slot", Map("slotId", slotId, "elapsedMs", elapsed, "size", dataSize, "profile", profile, "restoreDelayMs", restoreDelayMs))
        return true
    }

    ClearSlot(slotId) {
        if !this.slots.Has(slotId) {
            return
        }
        this.slots[slotId]["hasData"] := false
        this.slots[slotId]["data"] := ""
        this.slots[slotId]["text"] := ""
        this.slots[slotId]["sourcePath"] := ""
        this.logger.Info("Slot cleared", Map("slotId", slotId))
    }

    HasData(slotId) {
        return this.slots.Has(slotId) && this.slots[slotId]["hasData"]
    }

    GetSlotState(slotId) {
        if !this.slots.Has(slotId) {
            return ""
        }
        return this.slots[slotId]
    }

    GetSlotMetadata(slotId) {
        if !this.slots.Has(slotId) {
            return Map()
        }
        if !this.slots[slotId].Has("metadata") || !IsObject(this.slots[slotId]["metadata"]) {
            return Map()
        }
        return this.slots[slotId]["metadata"]
    }

    UpdateSlotTextValue(slotId, textValue) {
        if !this.slots.Has(slotId) {
            return
        }
        this.slots[slotId]["hasData"] := true
        this.slots[slotId]["text"] := textValue ""
        this.slots[slotId]["data"] := textValue ""
        this.slots[slotId]["sourcePath"] := FileExist(textValue "") ? (textValue "") : ""
        this.slots[slotId]["metadata"] := Map()
        this.logger.Debug("Slot text value updated", Map("slotId", slotId, "text", this.slots[slotId]["text"]))
    }

    UpdateSlotSourcePath(slotId, sourcePath) {
        if !this.slots.Has(slotId) {
            return
        }
        normalized := Trim(sourcePath "")
        if normalized = "" {
            return
        }
        this.slots[slotId]["sourcePath"] := normalized
        this.logger.Debug("Slot source path updated", Map("slotId", slotId, "sourcePath", normalized))
    }

    GetSlotSourcePath(slotId) {
        if !this.slots.Has(slotId) {
            return ""
        }
        return this.slots[slotId].Has("sourcePath") ? this.slots[slotId]["sourcePath"] : ""
    }
}

class ExtraClipboardApp {
    __New() {
        ; --- App paths and core services ---
        this.appDir := A_ScriptDir
        this.configPath := this.appDir "\\ExtraClipboard.ini"
        this.logPath := this.appDir "\\logs\\ExtraClipboard.log"
        this.destinationAssociationsPath := this.appDir "\\data\\DestinationAssociations.ini"

        this.logger := Logger(this.logPath, true)
        this.configStore := ConfigStore(this.configPath, this.logger)
        this.config := this.configStore.Load()
        this.logger.SetDebugEnabled(this.config["DebugEnabled"])
        this.modeRegistry := SlotModeRegistry(this.logger)

        this.slotEngine := ClipboardSlots(this.config["SlotCount"], this.logger)
        this.destinationFamilyAssociations := this.LoadDestinationFamilyAssociations()
        this.lastResolvedDestinationFolder := ""

        this.destinationFamilyPickerGui := ""
        this.destinationFamilyPickerListView := ""
        this.destinationFamilyPickerList := ""
        this.destinationFamilyPickerResultIndex := 0

        this.destinationStartPickerGui := ""
        this.destinationStartPickerListView := ""
        this.destinationStartPickerResultNumber := 0

        this.copyHotkeyCallback := ObjBindMethod(this, "HandleCopyHotkey")
        this.pasteHotkeyCallback := ObjBindMethod(this, "HandlePasteHotkey")
        this.slotCopyHotkeyCallbacks := Map()
        this.slotPasteHotkeyCallbacks := Map()
        this.slotClearDestinationAssociationHotkeyCallbacks := Map()
        this.registeredHotkeys := []

        ; --- Binding capture state (prevents runtime hotkey interference while binding) ---
        this.isBindingCaptureActive := false
        this.bindingTargetKey := ""
        this.bindingPreviousValue := ""
        this.bindingSuppressChange := false
        this.bindingPreviousSuspendState := false
        this.bindingInputHook := ""
        this.bindingCapturedValue := ""
        this.bindingGuardUntilTick := 0

        ; --- Settings mode state (runtime hotkeys use focus-aware suppression while settings is open). ---
        this.isSettingsModeActive := false

        loop 9 {
            slotId := A_Index
            this.slotCopyHotkeyCallbacks[slotId] := ObjBindMethod(this, "HandleSlotCopyHotkey", slotId)
            this.slotPasteHotkeyCallbacks[slotId] := ObjBindMethod(this, "HandleSlotPasteHotkey", slotId)
            this.slotClearDestinationAssociationHotkeyCallbacks[slotId] := ObjBindMethod(this, "HandleSlotClearDestinationAssociationHotkey", slotId)
        }

        this.RegisterHotkeys()
        this.BuildTrayMenu()
        this.logger.Info("ExtraClipboard app initialized")
    }

    RegisterHotkeys() {
        ; --- Runtime hotkey registry ---
        this.UnregisterHotkeys()

        this.TryRegisterHotkey(this.config["CopyHotkey"], this.copyHotkeyCallback, "main copy")
        this.TryRegisterHotkey(this.config["PasteHotkey"], this.pasteHotkeyCallback, "main paste")

        loop 9 {
            slotId := A_Index
            slotCopyHotkey := this.config[this.GetSlotCopyHotkeyKey(slotId)]
            slotPasteHotkey := this.config[this.GetSlotPasteHotkeyKey(slotId)]
            clearAssociationHotkey := this.config[this.GetSlotClearDestinationAssociationHotkeyKey(slotId)]
            this.TryRegisterHotkey(slotCopyHotkey, this.slotCopyHotkeyCallbacks[slotId], "slot " slotId " copy")
            this.TryRegisterHotkey(slotPasteHotkey, this.slotPasteHotkeyCallbacks[slotId], "slot " slotId " paste")
            this.TryRegisterHotkey(clearAssociationHotkey, this.slotClearDestinationAssociationHotkeyCallbacks[slotId], "slot " slotId " clear destination association")
        }
    }

    UnregisterHotkeys() {
        if !this.registeredHotkeys.Length {
            return
        }

        for entry in this.registeredHotkeys {
            try {
                Hotkey(entry["hotkey"], entry["callback"], "Off")
            } catch {
            }
        }
        this.registeredHotkeys := []
    }

    TryRegisterHotkey(hotkeyText, callback, hotkeyLabel) {
        hotkeyNormalized := Trim(hotkeyText)
        if hotkeyNormalized = "" {
            this.logger.Debug("Skipped empty hotkey registration", Map("label", hotkeyLabel))
            return
        }

        try {
            Hotkey(hotkeyNormalized, callback, "On")
            this.registeredHotkeys.Push(Map("hotkey", hotkeyNormalized, "callback", callback, "label", hotkeyLabel))
            this.logger.Info("Registered hotkey", Map("label", hotkeyLabel, "hotkey", hotkeyNormalized))
        } catch error {
            this.logger.Error("Failed to register hotkey", Map("label", hotkeyLabel, "hotkey", hotkeyNormalized, "error", this.FormatError(error)))
            MsgBox("Failed to register hotkey for " hotkeyLabel ": " hotkeyNormalized)
        }
    }

    GetSlotCopyHotkeyKey(slotId) {
        return "Slot" slotId "CopyHotkey"
    }

    GetSlotPasteHotkeyKey(slotId) {
        return "Slot" slotId "PasteHotkey"
    }

    GetSlotClearDestinationAssociationHotkeyKey(slotId) {
        return "Slot" slotId "ClearDestinationAssociationHotkey"
    }

    GetSlotModeKey(slotId) {
        return "Slot" slotId "Mode"
    }

    GetSlotIncrementOperationKey(slotId) {
        return "Slot" slotId "IncrementOperation"
    }

    GetSlotIncrementStepKey(slotId) {
        return "Slot" slotId "IncrementStep"
    }

    GetSlotIncrementMatchModeKey(slotId) {
        return "Slot" slotId "IncrementMatchMode"
    }

    GetSlotIncrementNumberSystemKey(slotId) {
        return "Slot" slotId "IncrementNumberSystem"
    }

    LoadDestinationFamilyAssociations() {
        associations := Map()
        try {
            count := Integer(IniRead(this.destinationAssociationsPath, "Associations", "Count", 0))
        } catch {
            count := 0
        }

        loop count {
            rowKey := "Row" A_Index
            rawRow := IniRead(this.destinationAssociationsPath, "Associations", rowKey, "")
            if rawRow = "" {
                continue
            }
            parts := StrSplit(rawRow, "|")
            if parts.Length < 7 {
                continue
            }

            slotId := Integer(parts[1])
            folderPath := parts[2]
            assocKey := this.BuildDestinationAssociationKey(slotId, folderPath)
            associations[assocKey] := Map(
                "slotId", slotId,
                "folderPath", folderPath,
                "prefix", parts[3],
                "suffix", parts[4],
                "extension", parts[5],
                "padWidth", Integer(parts[6]),
                "lastNumber", Integer(parts[7]),
                "lastDirection", parts.Length >= 8 ? StrLower(Trim(parts[8])) : "increase"
            )
        }

        this.logger.Debug("Loaded destination family associations", Map("count", associations.Count))
        return associations
    }

    SaveDestinationFamilyAssociations() {
        if !DirExist(this.appDir "\\data") {
            DirCreate(this.appDir "\\data")
        }

        index := 0
        for _, association in this.destinationFamilyAssociations {
            index += 1
            rowValue := association["slotId"] "|" association["folderPath"] "|" association["prefix"] "|" association["suffix"] "|" association["extension"] "|" association["padWidth"] "|" association["lastNumber"] "|" (association.Has("lastDirection") ? association["lastDirection"] : "increase")
            IniWrite(rowValue, this.destinationAssociationsPath, "Associations", "Row" index)
        }
        IniWrite(index, this.destinationAssociationsPath, "Associations", "Count")

        clearIndex := index + 1
        loop 200 {
            try {
                IniDelete(this.destinationAssociationsPath, "Associations", "Row" clearIndex)
            } catch {
            }
            clearIndex += 1
        }
    }

    BuildDestinationAssociationKey(slotId, folderPath) {
        return slotId "|" StrLower(this.NormalizeFolderPath(folderPath))
    }

    NormalizeFolderPath(folderPath) {
        normalized := Trim(folderPath "")
        while SubStr(normalized, 0) = "\\" || SubStr(normalized, 0) = "/" {
            normalized := SubStr(normalized, 1, StrLen(normalized) - 1)
        }
        return normalized
    }

    ResolveSlotSourcePath(slotState) {
        if slotState.Has("sourcePath") {
            candidate := Trim(slotState["sourcePath"] "")
            if candidate != "" && FileExist(candidate) {
                return candidate
            }
        }

        textCandidate := slotState.Has("text") ? Trim(slotState["text"] "") : ""
        if textCandidate != "" && FileExist(textCandidate) {
            return textCandidate
        }

        return ""
    }

    ResolveActiveDestinationFolder(slotId := 0) {
        ; Resolve destination folder in priority order: Explorer selection, Explorer directory,
        ; active window text/title path hints. Keep this focus-strict to avoid background-window misrouting.
        selectedPath := this.GetActiveExplorerSelectedPath()
        if selectedPath != "" {
            selectedKind := FileExist(selectedPath)
            if selectedKind != "" {
                if InStr(selectedKind, "D") {
                    resolved := this.NormalizeFolderPath(selectedPath)
                    this.lastResolvedDestinationFolder := resolved
                    this.logger.Debug("Resolved destination folder from Explorer selection", Map("folder", resolved, "slotId", slotId))
                    return resolved
                }
                SplitPath(selectedPath, , &selectedDir)
                if selectedDir != "" {
                    resolved := this.NormalizeFolderPath(selectedDir)
                    this.lastResolvedDestinationFolder := resolved
                    this.logger.Debug("Resolved destination folder from Explorer selected file", Map("folder", resolved, "slotId", slotId))
                    return resolved
                }
            }
        }

        activeDir := this.GetActiveExplorerDirectory()
        if activeDir != "" {
            resolved := this.NormalizeFolderPath(activeDir)
            this.lastResolvedDestinationFolder := resolved
            this.logger.Debug("Resolved destination folder from active Explorer directory", Map("folder", resolved, "slotId", slotId))
            return resolved
        }

        if this.TryResolveDestinationFolderFromActiveWindowContext(&windowFolderPath) {
            resolved := this.NormalizeFolderPath(windowFolderPath)
            this.lastResolvedDestinationFolder := resolved
            this.logger.Debug("Resolved destination folder from active window context", Map("folder", resolved, "slotId", slotId))
            return resolved
        }

        ; Do not fallback to remembered/associated folders for paste resolution.
        ; This guarantees destination always follows the currently focused window context.
        diagnostics := this.GetActiveWindowDiagnostics()
        this.logger.Debug("Destination folder resolution failed (focused window only)", Map(
            "slotId", slotId,
            "activeTitle", diagnostics["title"],
            "activeClass", diagnostics["class"],
            "activeProcess", diagnostics["process"]
        ))
        return ""
    }

    GetActiveWindowDiagnostics() {
        info := Map("title", "", "class", "", "process", "")
        try {
            info["title"] := WinGetTitle("A")
        } catch {
        }
        try {
            info["class"] := WinGetClass("A")
        } catch {
        }
        try {
            info["process"] := WinGetProcessName("A")
        } catch {
        }
        return info
    }

    TryResolveDestinationFolderFromActiveWindowContext(&resolvedFolderOut) {
        resolvedFolderOut := ""
        activeTitle := ""
        activeText := ""

        try {
            activeTitle := WinGetTitle("A")
        } catch {
        }
        try {
            activeText := WinGetText("A")
        } catch {
        }

        ; File Pilot exposes folder in title like: "TEST-2 (Documents\AutoHotkey\TEST-2) - File Pilot ..."
        if this.TryExtractFilePilotFolderFromTitle(activeTitle, &filePilotFolder) {
            resolvedFolderOut := filePilotFolder
            return true
        }

        folderCandidates := this.ExtractExistingDirectoriesFromWindowText(activeTitle "`n" activeText)
        if folderCandidates.Length < 1 {
            return false
        }

        resolvedFolderOut := folderCandidates[1]
        return true
    }

    TryExtractFilePilotFolderFromTitle(windowTitle, &folderOut) {
        folderOut := ""
        title := Trim(windowTitle "")
        if title = "" {
            return false
        }

        if !InStr(StrLower(title), "file pilot") {
            return false
        }

        ; Extract text inside the first (...) token in title.
        if !RegExMatch(title, "\(([^\)]+)\)", &match) {
            this.logger.Debug("File Pilot title parse failed: missing parenthesized folder token", Map("title", title))
            return false
        }

        candidate := Trim(match[1])
        if candidate = "" {
            return false
        }

        if InStr(FileExist(candidate), "D") {
            folderOut := this.NormalizeFolderPath(candidate)
            this.logger.Debug("Resolved File Pilot folder from absolute title token", Map("folder", folderOut, "title", title))
            return true
        }

        if this.TryResolveRelativeFolderFromKnownRoots(candidate, &resolvedFromRelative) {
            folderOut := this.NormalizeFolderPath(resolvedFromRelative)
            this.logger.Debug("Resolved File Pilot folder from relative title token", Map("folder", folderOut, "relative", candidate, "title", title))
            return true
        }

        this.logger.Debug("File Pilot title token did not resolve to folder", Map("token", candidate, "title", title))
        return false
    }

    TryResolveRelativeFolderFromKnownRoots(relativeToken, &resolvedFolderOut) {
        resolvedFolderOut := ""
        relativePath := Trim(StrReplace(relativeToken "", "/", "\\"), "\\")
        if relativePath = "" {
            return false
        }

        candidateRoots := []
        try {
            this.PushUniqueFolder(candidateRoots, EnvGet("USERPROFILE"))
        } catch {
        }
        try {
            this.PushUniqueFolder(candidateRoots, A_MyDocuments)
            SplitPath(A_MyDocuments, , &myDocsParent)
            this.PushUniqueFolder(candidateRoots, myDocsParent)
        } catch {
        }
        try {
            this.PushUniqueFolder(candidateRoots, A_Desktop)
            SplitPath(A_Desktop, , &desktopParent)
            this.PushUniqueFolder(candidateRoots, desktopParent)
        } catch {
        }
        this.PushUniqueFolder(candidateRoots, A_ScriptDir)

        for root in candidateRoots {
            fullCandidate := this.NormalizeFolderPath(root "\\" relativePath)
            if InStr(FileExist(fullCandidate), "D") {
                resolvedFolderOut := fullCandidate
                return true
            }
        }

        return false
    }

    ExtractExistingDirectoriesFromWindowText(rawText) {
        results := []
        source := rawText ""
        if source = "" {
            return results
        }

        pathPattern := 'i)([a-z]:\\[^<>:"/\|\?\*`r`n]+(?:\\[^<>:"/\|\?\*`r`n]+)*)'
        searchPos := 1
        while RegExMatch(source, pathPattern, &match, searchPos) {
            pathValue := Trim(match[1])
            if pathValue != "" {
                pathKind := FileExist(pathValue)
                if pathKind != "" {
                    if InStr(pathKind, "D") {
                        this.PushUniqueFolder(results, pathValue)
                    } else {
                        SplitPath(pathValue, , &parentDir)
                        if parentDir != "" {
                            this.PushUniqueFolder(results, parentDir)
                        }
                    }
                }
            }
            searchPos := match.Pos(1) + match.Len(1)
        }

        return results
    }

    PushUniqueFolder(folderList, folderPath) {
        normalized := this.NormalizeFolderPath(folderPath)
        if normalized = "" {
            return
        }
        for existing in folderList {
            if StrLower(existing) = StrLower(normalized) {
                return
            }
        }
        folderList.Push(normalized)
    }

    GetActiveExplorerDirectory() {
        try {
            activeWindowHwnd := WinExist("A")
            if !activeWindowHwnd {
                return ""
            }

            shellApp := ComObject("Shell.Application")
            for explorerWindow in shellApp.Windows {
                try {
                    if explorerWindow.HWND != activeWindowHwnd {
                        continue
                    }
                    if !IsObject(explorerWindow.Document) || !IsObject(explorerWindow.Document.Folder) {
                        continue
                    }
                    folderPath := explorerWindow.Document.Folder.Self.Path
                    if folderPath != "" {
                        return folderPath ""
                    }
                } catch {
                    continue
                }
            }
        } catch {
        }
        return ""
    }

    GetDestinationFamilyAssociation(slotId, folderPath) {
        assocKey := this.BuildDestinationAssociationKey(slotId, folderPath)
        if this.destinationFamilyAssociations.Has(assocKey) {
            return this.destinationFamilyAssociations[assocKey]
        }
        return ""
    }

    SetDestinationFamilyAssociation(slotId, folderPath, familyInfo) {
        assocKey := this.BuildDestinationAssociationKey(slotId, folderPath)
        lastDirection := familyInfo.Has("lastDirection") ? StrLower(Trim(familyInfo["lastDirection"] "")) : "increase"
        if lastDirection != "decrease" {
            lastDirection := "increase"
        }
        this.destinationFamilyAssociations[assocKey] := Map(
            "slotId", slotId,
            "folderPath", this.NormalizeFolderPath(folderPath),
            "prefix", familyInfo["prefix"],
            "suffix", familyInfo["suffix"],
            "extension", familyInfo["extension"],
            "padWidth", familyInfo["padWidth"],
            "lastNumber", familyInfo.Has("maxNumber") ? familyInfo["maxNumber"] : 0,
            "lastDirection", lastDirection
        )
        this.SaveDestinationFamilyAssociations()
        this.logger.Debug("Destination family association saved", Map("slotId", slotId, "folder", folderPath, "prefix", familyInfo["prefix"], "suffix", familyInfo["suffix"], "lastNumber", this.destinationFamilyAssociations[assocKey]["lastNumber"], "lastDirection", lastDirection))
    }

    ClearDestinationFamilyAssociation(slotId, folderPath) {
        assocKey := this.BuildDestinationAssociationKey(slotId, folderPath)
        if !this.destinationFamilyAssociations.Has(assocKey) {
            return false
        }
        this.destinationFamilyAssociations.Delete(assocKey)
        this.SaveDestinationFamilyAssociations()
        this.logger.Info("Destination family association cleared", Map("slotId", slotId, "folder", folderPath))
        return true
    }

    PromptDestinationFamilySelection(slotId, folderPath, familyList, preselectedIndex := 0) {
        ; Click-based picker avoids index typing mistakes and works better with many families.
        ; Keep Family column wide so long naming templates remain visible.
        ; Show both min and max boundaries to make decrease/increase intent explicit per family.
        this.destinationFamilyPickerResultIndex := 0
        this.destinationFamilyPickerList := familyList

        pickerGui := Gui("+Owner +AlwaysOnTop", "Choose Destination Family")
        pickerGui.SetFont("s10", "Segoe UI")
        pickerGui.AddText("xm w860", "Slot " slotId " destination families in:")
        pickerGui.AddText("xm y+2 w860", folderPath)
        pickerGui.AddText("xm y+10 w860", "Select a family and click OK (double-click also selects).")

        pickerList := pickerGui.AddListView("xm y+8 w980 r12 Grid", ["#", "Family", "Extension", "Current Min", "Current Max"])
        loop familyList.Length {
            family := familyList[A_Index]
            sampleName := family["prefix"] this.FormatDestinationNumber(family["maxNumber"], family["padWidth"]) family["suffix"]
            minNumber := family.Has("minNumber") ? family["minNumber"] : family["maxNumber"]
            pickerList.Add("", A_Index, sampleName, family["extension"], minNumber, family["maxNumber"])
        }
        pickerList.ModifyCol(1, 45)
        pickerList.ModifyCol(2, 560)
        pickerList.ModifyCol(3, 120)
        pickerList.ModifyCol(4, 120)
        pickerList.ModifyCol(5, 120)

        initialRow := preselectedIndex >= 1 && preselectedIndex <= familyList.Length ? preselectedIndex : 1
        pickerList.Modify(initialRow, "Select Focus")

        okButton := pickerGui.AddButton("xm y+12 w90", "OK")
        cancelButton := pickerGui.AddButton("x+10 yp w90", "Cancel")

        this.destinationFamilyPickerGui := pickerGui
        this.destinationFamilyPickerListView := pickerList

        this.logger.Debug("Destination family picker opened", Map("slotId", slotId, "folder", folderPath, "familyCount", familyList.Length, "preselectedIndex", initialRow))

        okButton.OnEvent("Click", ObjBindMethod(this, "OnDestinationFamilyPickerAccept"))
        cancelButton.OnEvent("Click", ObjBindMethod(this, "OnDestinationFamilyPickerCancel"))
        pickerList.OnEvent("DoubleClick", ObjBindMethod(this, "OnDestinationFamilyPickerAccept"))
        pickerGui.OnEvent("Close", ObjBindMethod(this, "OnDestinationFamilyPickerCancel"))
        pickerGui.OnEvent("Escape", ObjBindMethod(this, "OnDestinationFamilyPickerCancel"))

        pickerGui.Show("AutoSize Center")
        WinWaitClose("ahk_id " pickerGui.Hwnd)

        selectedIndex := this.destinationFamilyPickerResultIndex
        this.destinationFamilyPickerResultIndex := 0
        this.destinationFamilyPickerGui := ""
        this.destinationFamilyPickerListView := ""
        this.destinationFamilyPickerList := ""

        if selectedIndex < 1 || selectedIndex > familyList.Length {
            this.logger.Info("Destination family selection cancelled", Map("slotId", slotId, "folder", folderPath))
            return ""
        }

        selectedFamily := familyList[selectedIndex]
        this.logger.Info("Destination family selected", Map("slotId", slotId, "folder", folderPath, "index", selectedIndex, "prefix", selectedFamily["prefix"], "suffix", selectedFamily["suffix"]))
        return selectedFamily
    }

    PromptDestinationStartNumberSelection(slotId, folderPath, familyInfo, numberList, defaultStartNumber, direction) {
        ; Gap-aware start picker: explicit choice prevents accidental numbering jumps.
        if numberList.Length < 1 {
            return defaultStartNumber
        }

        this.destinationStartPickerHasSelection := false
        this.destinationStartPickerResultNumber := 0

        pickerGui := Gui("+Owner +AlwaysOnTop", "Choose Destination Start Point")
        pickerGui.SetFont("s10", "Segoe UI")
        pickerGui.AddText("xm w860", "Slot " slotId " has discontinuous numbering in:")
        pickerGui.AddText("xm y+2 w860", folderPath)
        pickerGui.AddText("xm y+8 w860", "Direction: " (direction = "decrease" ? "Decrease from minimum" : "Increase from maximum") " | Select start number.")

        pickerList := pickerGui.AddListView("xm y+8 w860 r12 Grid", ["Number", "Family Sample"])
        loop numberList.Length {
            numberValue := numberList[A_Index]
            sampleName := familyInfo["prefix"] this.FormatDestinationNumber(numberValue, familyInfo["padWidth"]) familyInfo["suffix"]
            pickerList.Add("", numberValue, sampleName)
        }
        pickerList.ModifyCol(1, 120)
        pickerList.ModifyCol(2, 690)

        initialRow := this.FindNumberRowIndex(numberList, defaultStartNumber)
        if initialRow < 1 {
            initialRow := direction = "decrease" ? 1 : numberList.Length
        }
        pickerList.Modify(initialRow, "Select Focus")

        okButton := pickerGui.AddButton("xm y+12 w90", "OK")
        cancelButton := pickerGui.AddButton("x+10 yp w90", "Cancel")

        this.destinationStartPickerGui := pickerGui
        this.destinationStartPickerListView := pickerList

        this.logger.Debug("Destination start picker opened", Map("slotId", slotId, "folder", folderPath, "direction", direction, "numberCount", numberList.Length, "defaultStart", defaultStartNumber))

        okButton.OnEvent("Click", ObjBindMethod(this, "OnDestinationStartPickerAccept"))
        cancelButton.OnEvent("Click", ObjBindMethod(this, "OnDestinationStartPickerCancel"))
        pickerList.OnEvent("DoubleClick", ObjBindMethod(this, "OnDestinationStartPickerAccept"))
        pickerGui.OnEvent("Close", ObjBindMethod(this, "OnDestinationStartPickerCancel"))
        pickerGui.OnEvent("Escape", ObjBindMethod(this, "OnDestinationStartPickerCancel"))

        pickerGui.Show("AutoSize Center")
        WinWaitClose("ahk_id " pickerGui.Hwnd)

        selectedNumber := this.destinationStartPickerResultNumber
        selected := this.destinationStartPickerHasSelection
        this.destinationStartPickerHasSelection := false
        this.destinationStartPickerResultNumber := 0
        this.destinationStartPickerGui := ""
        this.destinationStartPickerListView := ""

        if !selected {
            this.logger.Info("Destination start picker cancelled", Map("slotId", slotId, "folder", folderPath))
            return ""
        }

        this.logger.Info("Destination start number selected", Map("slotId", slotId, "folder", folderPath, "selectedNumber", selectedNumber, "direction", direction))
        return selectedNumber
    }

    OnDestinationStartPickerAccept(*) {
        if !this.HasProp("destinationStartPickerGui") || !IsObject(this.destinationStartPickerGui) {
            return
        }
        selectedNumber := this.GetDestinationStartPickerSelectedNumber()
        if selectedNumber = "" {
            this.ShowActionToolTip("Select a start number first")
            return
        }

        this.destinationStartPickerHasSelection := true
        this.destinationStartPickerResultNumber := selectedNumber
        try {
            this.destinationStartPickerGui.Destroy()
        } catch {
        }
    }

    OnDestinationStartPickerCancel(*) {
        this.destinationStartPickerHasSelection := false
        this.destinationStartPickerResultNumber := 0
        if this.HasProp("destinationStartPickerGui") && IsObject(this.destinationStartPickerGui) {
            try {
                this.destinationStartPickerGui.Destroy()
            } catch {
            }
        }
    }

    GetDestinationStartPickerSelectedNumber() {
        if !this.HasProp("destinationStartPickerListView") || !IsObject(this.destinationStartPickerListView) {
            return ""
        }
        selectedRow := this.destinationStartPickerListView.GetNext(0, "F")
        if selectedRow < 1 {
            selectedRow := this.destinationStartPickerListView.GetNext(0)
        }
        if selectedRow < 1 {
            return ""
        }
        valueText := this.destinationStartPickerListView.GetText(selectedRow, 1)
        try {
            return Integer(valueText)
        } catch {
            return ""
        }
    }

    FindNumberRowIndex(numberList, targetNumber) {
        loop numberList.Length {
            if numberList[A_Index] = targetNumber {
                return A_Index
            }
        }
        return 0
    }

    FormatDestinationNumber(numberValue, padWidth) {
        ; Keep display consistent with actual destination naming for signed numbers.
        if padWidth < 1 {
            return numberValue ""
        }
        if numberValue < 0 {
            return "-" Format("{:0" padWidth "}", Abs(numberValue))
        }
        return Format("{:0" padWidth "}", numberValue)
    }

    OnDestinationFamilyPickerAccept(*) {
        if !this.HasProp("destinationFamilyPickerGui") || !IsObject(this.destinationFamilyPickerGui) {
            return
        }
        selectedIndex := this.GetDestinationFamilyPickerSelectedIndex()
        if selectedIndex < 1 {
            this.ShowActionToolTip("Select a family first")
            return
        }

        this.destinationFamilyPickerResultIndex := selectedIndex
        try {
            this.destinationFamilyPickerGui.Destroy()
        } catch {
        }
    }

    OnDestinationFamilyPickerCancel(*) {
        this.destinationFamilyPickerResultIndex := 0
        if this.HasProp("destinationFamilyPickerGui") && IsObject(this.destinationFamilyPickerGui) {
            try {
                this.destinationFamilyPickerGui.Destroy()
            } catch {
            }
        }
    }

    GetDestinationFamilyPickerSelectedIndex() {
        if !this.HasProp("destinationFamilyPickerListView") || !IsObject(this.destinationFamilyPickerListView) {
            return 0
        }
        selected := this.destinationFamilyPickerListView.GetNext(0, "F")
        if selected < 1 {
            selected := this.destinationFamilyPickerListView.GetNext(0)
        }
        return selected
    }

    ClearDestinationAssociationForSlot(slotId, showNotification := true) {
        folderPath := this.ResolveActiveDestinationFolder(slotId)
        if folderPath = "" {
            if showNotification {
                this.ShowActionToolTip("No active destination folder to clear")
            }
            return false
        }

        cleared := this.ClearDestinationFamilyAssociation(slotId, folderPath)
        if showNotification {
            this.ShowActionToolTip(cleared ? "Cleared destination association for slot " slotId : "No saved association for this folder")
        }
        return cleared
    }

    ClearActiveSlotDestinationAssociation(*) {
        slotId := this.config["ActiveSlot"]
        this.ClearDestinationAssociationForSlot(slotId, true)
    }

    BuildTrayMenu() {
        ; --- Tray menu reflects all supported slots (1-9) for direct operations and legacy active-slot selection. ---
        A_TrayMenu.Delete()
        A_TrayMenu.Add("Copy to ExtraClipboard", ObjBindMethod(this, "HandleCopyHotkey"))
        A_TrayMenu.Add("Paste from ExtraClipboard", ObjBindMethod(this, "HandlePasteHotkey"))
        A_TrayMenu.Add("Clear Active Slot", ObjBindMethod(this, "ClearActiveSlot"))
        A_TrayMenu.Add()
        loop 9 {
            slotId := A_Index
            A_TrayMenu.Add("Copy to Slot " slotId, ObjBindMethod(this, "HandleSlotCopyHotkey", slotId))
        }
        A_TrayMenu.Add()
        loop 9 {
            slotId := A_Index
            A_TrayMenu.Add("Paste from Slot " slotId, ObjBindMethod(this, "HandleSlotPasteHotkey", slotId))
        }
        A_TrayMenu.Add()
        loop 9 {
            slotId := A_Index
            A_TrayMenu.Add("Set Active Slot: " slotId, ObjBindMethod(this, "SetActiveSlot", slotId))
        }
        A_TrayMenu.Add()
        slotModesMenu := Menu()
        loop 9 {
            slotId := A_Index
            slotModeSubMenu := Menu()
            currentMode := this.GetSlotMode(slotId)
            slotModeSubMenu.Add("Default", ObjBindMethod(this, "SetSlotModeFromTray", slotId, "default"))
            slotModeSubMenu.Add("Incremental", ObjBindMethod(this, "SetSlotModeFromTray", slotId, "incremental"))
            slotModeSubMenu.Add("Incremental Destination", ObjBindMethod(this, "SetSlotModeFromTray", slotId, "incremental-destination"))
            if currentMode = "incremental" {
                slotModeSubMenu.Check("Incremental")
            } else if currentMode = "incremental-destination" {
                slotModeSubMenu.Check("Incremental Destination")
            } else {
                slotModeSubMenu.Check("Default")
            }
            slotModesMenu.Add("Slot " slotId, slotModeSubMenu)
        }
        A_TrayMenu.Add("Slot Modes", slotModesMenu)
        A_TrayMenu.Add("Clear Destination Association (Active Slot)", ObjBindMethod(this, "ClearActiveSlotDestinationAssociation"))
        A_TrayMenu.Add()
        A_TrayMenu.Add("Settings", ObjBindMethod(this, "ShowSettingsGui"))
        A_TrayMenu.Add("Open Log File", ObjBindMethod(this, "OpenLogFile"))
        A_TrayMenu.Add("Exit", ObjBindMethod(this, "ExitAppNow"))
        A_IconTip := "ExtraClipboard"
    }

    SetSlotModeFromTray(slotId, modeKey, *) {
        this.EnsureSlotAvailable(slotId)
        modeConfigKey := this.GetSlotModeKey(slotId)
        normalizedMode := this.configStore.NormalizeSlotMode(modeKey)
        this.config[modeConfigKey] := normalizedMode
        this.configStore.Save(this.config)
        this.BuildTrayMenu()
        this.logger.Info("Slot mode changed from tray", Map("slotId", slotId, "mode", normalizedMode))
        modeLabel := normalizedMode = "incremental" ? "Incremental" : (normalizedMode = "incremental-destination" ? "Incremental Destination" : "Default")
        this.ShowActionToolTip("Slot " slotId " mode: " modeLabel)
    }

    HandleCopyHotkey(*) {
        if !this.ShouldRunRuntimeHotkey("active copy") {
            return
        }
        try {
            activeSlot := this.config["ActiveSlot"]
            success := this.slotEngine.CaptureFromSelection(activeSlot, this.config["SourceCopyCombo"])
            if success {
                this.UpdateSlotSourcePathFromActiveExplorer(activeSlot)
            }
            this.ShowActionToolTip(success ? "Copied to ExtraClipboard slot " activeSlot : "Copy failed")
        } catch error {
            this.logger.Error("Unhandled error in copy hotkey handler", Map("error", this.FormatError(error)))
            this.ShowActionToolTip("Copy error")
        }
    }

    HandlePasteHotkey(*) {
        if !this.ShouldRunRuntimeHotkey("active paste") {
            return
        }
        try {
            activeSlot := this.config["ActiveSlot"]
            pasteResult := this.PasteSlotWithMode(activeSlot)
            this.ShowActionToolTip(pasteResult["message"])
        } catch error {
            this.logger.Error("Unhandled error in paste hotkey handler", Map("error", this.FormatError(error)))
            this.ShowActionToolTip("Paste error")
        }
    }

    HandleSlotCopyHotkey(slotId, *) {
        if !this.ShouldRunRuntimeHotkey("slot " slotId " copy") {
            return
        }
        try {
            this.EnsureSlotAvailable(slotId)

            this.config["ActiveSlot"] := slotId
            success := this.slotEngine.CaptureFromSelection(slotId, this.config["SourceCopyCombo"])
            if success {
                this.UpdateSlotSourcePathFromActiveExplorer(slotId)
            }
            this.ShowActionToolTip(success ? "Copied to slot " slotId : "Copy failed for slot " slotId)
        } catch error {
            this.logger.Error("Unhandled error in slot copy handler", Map("slotId", slotId, "error", this.FormatError(error)))
            this.ShowActionToolTip("Slot copy error")
        }
    }

    UpdateSlotSourcePathFromActiveExplorer(slotId) {
        ; --- Reliable file-source metadata capture: grab first selected item path from active Explorer window. ---
        existingSourcePath := this.slotEngine.GetSlotSourcePath(slotId)
        if existingSourcePath != "" {
            this.logger.Debug("Skipped Explorer source capture because slot already has sourcePath", Map("slotId", slotId, "sourcePath", existingSourcePath))
            return
        }

        selectedPath := this.GetActiveExplorerSelectedPath()
        this.slotEngine.UpdateSlotSourcePath(slotId, selectedPath)
        if selectedPath != "" {
            this.logger.Debug("Captured Explorer source path for slot", Map("slotId", slotId, "path", selectedPath))
            return
        }
        this.logger.Debug("Explorer source path unavailable for slot copy", Map("slotId", slotId))
    }

    GetActiveExplorerSelectedPath() {
        try {
            activeWindowHwnd := WinExist("A")
            if !activeWindowHwnd {
                return ""
            }

            shellApp := ComObject("Shell.Application")
            for explorerWindow in shellApp.Windows {
                try {
                    if explorerWindow.HWND != activeWindowHwnd {
                        continue
                    }
                    selectedItems := explorerWindow.Document.SelectedItems()
                    if !IsObject(selectedItems) || selectedItems.Count < 1 {
                        return ""
                    }
                    firstItem := selectedItems.Item(0)
                    return firstItem.Path ""
                } catch {
                    continue
                }
            }
        } catch {
        }
        return ""
    }

    HandleSlotPasteHotkey(slotId, *) {
        if !this.ShouldRunRuntimeHotkey("slot " slotId " paste") {
            return
        }
        try {
            this.EnsureSlotAvailable(slotId)

            this.config["ActiveSlot"] := slotId
            pasteResult := this.PasteSlotWithMode(slotId)
            this.ShowActionToolTip(pasteResult["message"])
        } catch error {
            errorText := "<slot paste error>"
            try {
                errorText := this.FormatError(error)
            } catch {
            }
            try {
                this.logger.Error("Unhandled error in slot paste handler", Map("slotId", slotId, "error", errorText))
            } catch {
            }
            this.ShowActionToolTip("Slot paste error")
        }
    }

    HandleSlotClearDestinationAssociationHotkey(slotId, *) {
        if !this.ShouldRunRuntimeHotkey("slot " slotId " clear association") {
            return
        }
        try {
            this.EnsureSlotAvailable(slotId)
            this.config["ActiveSlot"] := slotId
            this.ClearDestinationAssociationForSlot(slotId, true)
            if this.HasProp("settingsGui") && IsObject(this.settingsGui) {
                try {
                    selectedModeSlot := this.GetSelectedModePanelSlot()
                    if selectedModeSlot = slotId {
                        this.RefreshModePanelDestinationAssociationState(slotId)
                    }
                } catch {
                }
            }
        } catch error {
            this.logger.Error("Unhandled error in clear association hotkey handler", Map("slotId", slotId, "error", this.FormatError(error)))
            this.ShowActionToolTip("Clear association error")
        }
    }

    PasteSlotWithMode(slotId) {
        if !this.slotEngine.HasData(slotId) {
            this.logger.Warn("Paste skipped: slot has no data", Map("slotId", slotId))
            return Map("success", false, "message", "Slot " slotId " empty or paste failed")
        }

        slotState := this.slotEngine.GetSlotState(slotId)
        modeKey := this.GetSlotMode(slotId)
        modeConfig := this.BuildSlotModeConfig(slotId)
        modeHandler := this.modeRegistry.Resolve(modeKey)
        prepared := modeHandler.PreparePaste(slotId, slotState, modeConfig, this)

        if !prepared["success"] {
            statusText := prepared.Has("statusMessage") && prepared["statusMessage"] != "" ? prepared["statusMessage"] : "Incremental paste failed"
            return Map("success", false, "message", statusText)
        }

        if prepared.Has("handledWithoutPaste") && prepared["handledWithoutPaste"] {
            if prepared.Has("persistText") && prepared["persistText"] != "" {
                this.slotEngine.UpdateSlotTextValue(slotId, prepared["persistText"])
            }
            directMessage := prepared.Has("statusMessage") && prepared["statusMessage"] != "" ? prepared["statusMessage"] : "Mode action completed"
            return Map("success", true, "message", directMessage)
        }

        payload := prepared["payloadData"]
        pasteOptions := prepared.Has("pasteOptions") ? prepared["pasteOptions"] : ""
        success := this.slotEngine.PastePayloadToTarget(slotId, payload, this.config["TargetPasteCombo"], pasteOptions)
        if !success {
            return Map("success", false, "message", "Slot " slotId " empty or paste failed")
        }

        if prepared.Has("persistText") && prepared["persistText"] != "" {
            this.slotEngine.UpdateSlotTextValue(slotId, prepared["persistText"])
        }

        status := prepared.Has("statusMessage") ? prepared["statusMessage"] : ""
        if status != "" {
            return Map("success", true, "message", status)
        }
        return Map("success", true, "message", "Pasted from slot " slotId)
    }

    GetSlotMode(slotId) {
        key := this.GetSlotModeKey(slotId)
        value := this.config.Has(key) ? this.config[key] : "default"
        return this.configStore.NormalizeSlotMode(value)
    }

    BuildSlotModeConfig(slotId) {
        modeConfig := Map(
            "mode", this.GetSlotMode(slotId),
            "operation", this.GetConfigValueOrDefault(this.GetSlotIncrementOperationKey(slotId), "increase"),
            "step", this.configStore.ClampInt(this.GetConfigValueOrDefault(this.GetSlotIncrementStepKey(slotId), 1), 1, 999999, 1),
            "matchMode", this.GetConfigValueOrDefault(this.GetSlotIncrementMatchModeKey(slotId), "auto-smart"),
            "numberSystem", this.GetConfigValueOrDefault(this.GetSlotIncrementNumberSystemKey(slotId), "decimal")
        )
        modeConfig["operation"] := this.configStore.NormalizeIncrementOperation(modeConfig["operation"])
        modeConfig["matchMode"] := this.configStore.NormalizeIncrementMatchMode(modeConfig["matchMode"])
        modeConfig["numberSystem"] := this.configStore.NormalizeIncrementNumberSystem(modeConfig["numberSystem"])
        return modeConfig
    }

    GetConfigValueOrDefault(configKey, fallbackValue) {
        return this.config.Has(configKey) ? this.config[configKey] : fallbackValue
    }

    ClearActiveSlot(*) {
        activeSlot := this.config["ActiveSlot"]
        this.slotEngine.ClearSlot(activeSlot)
        this.ShowActionToolTip("Cleared slot " activeSlot)
    }

    SetActiveSlot(slotId, *) {
        if slotId < 1 || slotId > 9 {
            this.logger.Warn("Attempted to set invalid active slot", Map("slotId", slotId))
            this.ShowActionToolTip("Slot " slotId " is invalid")
            return
        }

        this.EnsureSlotAvailable(slotId)

        this.config["ActiveSlot"] := slotId
        this.configStore.Save(this.config)
        this.logger.Info("Active slot changed", Map("slotId", slotId))
        this.ShowActionToolTip("Active slot set to " slotId)
    }

    EnsureSlotAvailable(slotId) {
        if slotId < 1 || slotId > 9 {
            return
        }

        if slotId > this.config["SlotCount"] {
            this.config["SlotCount"] := slotId
            this.slotEngine.SetSlotCount(this.config["SlotCount"])
            this.configStore.Save(this.config)
            this.logger.Info("Slot count auto-expanded from slot hotkey", Map("slotId", slotId, "slotCount", this.config["SlotCount"]))
            if this.HasProp("guiSlotCount") && IsObject(this.guiSlotCount) {
                this.guiSlotCount.Text := this.config["SlotCount"]
            }
            return
        }

        this.slotEngine.SetSlotCount(this.config["SlotCount"])
    }

    ShowSettingsGui(*) {
        ; --- Enter settings isolation before any UI interaction to avoid hotkey contamination. ---
        this.EnterSettingsMode()

        if this.HasProp("settingsGui") && IsObject(this.settingsGui) {
            try {
                this.settingsGui.Show()
                return
            } catch {
            }
        }

        settingsWindow := Gui("", "ExtraClipboard Settings")
        settingsWindow.SetFont("s10", "Segoe UI")

        this.guiBindingControls := Map()
        this.guiBindingLabels := Map()

        ; --- Layout constants: left column uses relative flow; right panel uses absolute positions. ---
        ; Keep absolute controls added AFTER left-flow controls to avoid y-anchor contamination.
        rightPanelX := 590
        rightPanelY := 34
        rightPanelW := 340
        rowLabelW := 120
        rowFieldW := 180

        settingsWindow.AddText("xm w560", "Primary Mode: instant per-slot hotkeys (Bind and press key combo, Clear to remove)")
        loop 9 {
            slotId := A_Index
            this.AddBindingRow(settingsWindow, "Slot " slotId " Copy", this.GetSlotCopyHotkeyKey(slotId), slotId = 1 ? "xm y+10" : "xm y+8")
            this.AddBindingRow(settingsWindow, "Slot " slotId " Paste", this.GetSlotPasteHotkeyKey(slotId), "xm y+6")
        }

        settingsWindow.AddText("xm y+14 w560", "Legacy Mode (optional): active-slot copy/paste")
        this.AddBindingRow(settingsWindow, "Active Slot Copy", "CopyHotkey", "xm y+8")
        this.AddBindingRow(settingsWindow, "Active Slot Paste", "PasteHotkey", "xm y+6")

        settingsWindow.AddText("xm y+14 w560", "Internal copy/paste command keys (not legacy binds)")
        settingsWindow.AddText("xm y+2 w560", "These are the keys ExtraClipboard sends to apps for copy/paste. Keep defaults unless needed.")
        this.AddBindingRow(settingsWindow, "Selection Copy Combo", "SourceCopyCombo", "xm y+8", false)
        this.AddBindingRow(settingsWindow, "Target Paste Combo", "TargetPasteCombo", "xm y+6", false)

        settingsWindow.AddText("xm y+10 w170", "Slot Count (1-9)")
        this.guiSlotCount := settingsWindow.AddEdit("x+10 yp-2 w170 Number", this.config["SlotCount"])

        settingsWindow.AddText("xm y+10 w170", "Active Slot")
        this.guiActiveSlot := settingsWindow.AddEdit("x+10 yp-2 w170 Number", this.config["ActiveSlot"])

        this.guiDebugEnabled := settingsWindow.AddCheckBox("xm y+16", "Enable debug logs")
        this.guiDebugEnabled.Value := this.config["DebugEnabled"] ? 1 : 0

        this.guiStatus := settingsWindow.AddText("xm y+14 w560", "")

        saveButton := settingsWindow.AddButton("xm y+16 w105", "Save")
        saveButton.OnEvent("Click", ObjBindMethod(this, "SaveSettingsFromGui"))

        cancelButton := settingsWindow.AddButton("x+10 yp w105", "Close")
        cancelButton.OnEvent("Click", ObjBindMethod(this, "CloseSettingsGui"))

        logButton := settingsWindow.AddButton("x+10 yp w115", "Open Log")
        logButton.OnEvent("Click", ObjBindMethod(this, "OpenLogFile"))

        ; --- Right panel is absolute-positioned and independent from left flow. ---
        settingsWindow.AddGroupBox("x" rightPanelX " y" rightPanelY " w" rightPanelW " h470", "Slot Mode Configuration")
        settingsWindow.AddText("x" (rightPanelX + 12) " y" (rightPanelY + 26) " w" (rightPanelW - 24), "Scalable mode editor for selected slot.")

        settingsWindow.AddText("x" (rightPanelX + 12) " y" (rightPanelY + 54) " w" rowLabelW, "Config Slot")
        this.guiModeSlotSelect := settingsWindow.AddDropDownList("x" (rightPanelX + 12 + rowLabelW + 8) " y" (rightPanelY + 51) " w" rowFieldW " Choose" this.config["ActiveSlot"], ["1", "2", "3", "4", "5", "6", "7", "8", "9"])
        this.guiModeSlotSelect.OnEvent("Change", ObjBindMethod(this, "OnModeSlotSelectionChanged"))

        settingsWindow.AddText("x" (rightPanelX + 12) " y" (rightPanelY + 84) " w" rowLabelW, "Mode")
        this.guiModeType := settingsWindow.AddDropDownList("x" (rightPanelX + 12 + rowLabelW + 8) " y" (rightPanelY + 81) " w" rowFieldW, ["Default", "Incremental", "Incremental Destination"])
        this.guiModeType.OnEvent("Change", ObjBindMethod(this, "OnModeTypeChanged"))

        this.guiModeField1Label := settingsWindow.AddText("x" (rightPanelX + 12) " y" (rightPanelY + 114) " w" rowLabelW, "")
        this.guiModeField1Control := settingsWindow.AddDropDownList("x" (rightPanelX + 12 + rowLabelW + 8) " y" (rightPanelY + 111) " w" rowFieldW, ["Increase", "Decrease"])

        this.guiModeField2Label := settingsWindow.AddText("x" (rightPanelX + 12) " y" (rightPanelY + 144) " w" rowLabelW, "")
        this.guiModeField2Control := settingsWindow.AddEdit("x" (rightPanelX + 12 + rowLabelW + 8) " y" (rightPanelY + 142) " w" rowFieldW " Number", "1")

        this.guiModeField3Label := settingsWindow.AddText("x" (rightPanelX + 12) " y" (rightPanelY + 174) " w" rowLabelW, "")
        this.guiModeField3Control := settingsWindow.AddDropDownList("x" (rightPanelX + 12 + rowLabelW + 8) " y" (rightPanelY + 171) " w" rowFieldW, ["Auto-Smart", "Start", "End"])

        this.guiModeField4Label := settingsWindow.AddText("x" (rightPanelX + 12) " y" (rightPanelY + 204) " w" rowLabelW, "")
        this.guiModeField4Control := settingsWindow.AddDropDownList("x" (rightPanelX + 12 + rowLabelW + 8) " y" (rightPanelY + 201) " w" rowFieldW, ["Decimal", "Hexadecimal", "Roman"])

        this.guiModeHint := settingsWindow.AddText("x" (rightPanelX + 12) " y" (rightPanelY + 234) " w" (rightPanelW - 24), "")

        this.guiModeDestinationAssociationLabel := settingsWindow.AddText("x" (rightPanelX + 12) " y" (rightPanelY + 262) " w" rowLabelW, "Destination Family")
        this.guiModeDestinationAssociationValue := settingsWindow.AddText("x" (rightPanelX + 12 + rowLabelW + 8) " y" (rightPanelY + 262) " w" rowFieldW " h54", "")
        this.guiModeDestinationClearAssociationButton := settingsWindow.AddButton("x" (rightPanelX + 12) " y" (rightPanelY + 322) " w" (rightPanelW - 24), "Clear Association for Active Folder")
        this.guiModeDestinationClearAssociationButton.OnEvent("Click", ObjBindMethod(this, "ClearModePanelDestinationAssociation"))

        settingsWindow.AddText("x" (rightPanelX + 12) " y" (rightPanelY + 356) " w" rowLabelW, "Clear Assoc HK")
        this.guiModeDestinationClearHotkey := settingsWindow.AddHotkey("x" (rightPanelX + 12 + rowLabelW + 8) " y" (rightPanelY + 353) " w120", "")
        this.guiModeDestinationClearBindButton := settingsWindow.AddButton("x+6 yp-1 w52", "Bind")
        this.guiModeDestinationClearBindButton.OnEvent("Click", ObjBindMethod(this, "StartBindingForModeDestinationClearHotkey"))
        this.guiModeDestinationClearClearButton := settingsWindow.AddButton("x+6 yp w52", "Clear")
        this.guiModeDestinationClearClearButton.OnEvent("Click", ObjBindMethod(this, "ClearModeDestinationClearHotkey"))

        this.LoadModePanelForSlot(this.config["ActiveSlot"])
        this.ApplyModeEditorLayoutForSelectedMode()

        settingsWindow.OnEvent("Close", ObjBindMethod(this, "CloseSettingsGui"))
        settingsWindow.OnEvent("Escape", ObjBindMethod(this, "OnSettingsEscape"))
        this.settingsGui := settingsWindow

        settingsWindow.Show("w950 AutoSize")
        this.logger.Info("Settings GUI opened")
    }

    OnModeSlotSelectionChanged(*) {
        selectedSlot := this.GetSelectedModePanelSlot()
        this.LoadModePanelForSlot(selectedSlot)
        this.ApplyModeEditorLayoutForSelectedMode()
        this.logger.Debug("Mode panel slot changed", Map("slotId", selectedSlot))
    }

    OnModeTypeChanged(*) {
        this.RefreshModePanelDestinationAssociationState(this.GetSelectedModePanelSlot())
        this.ApplyModeEditorLayoutForSelectedMode()
    }

    GetSelectedModePanelSlot() {
        if !this.HasProp("guiModeSlotSelect") || !IsObject(this.guiModeSlotSelect) {
            return this.config["ActiveSlot"]
        }

        selectedText := Trim(this.guiModeSlotSelect.Text)
        return this.configStore.ClampInt(selectedText, 1, 9, this.config["ActiveSlot"])
    }

    LoadModePanelForSlot(slotId) {
        modeKey := this.GetSlotMode(slotId)
        clearAssocHotkeyKey := this.GetSlotClearDestinationAssociationHotkeyKey(slotId)
        operationKey := this.configStore.NormalizeIncrementOperation(this.GetConfigValueOrDefault(this.GetSlotIncrementOperationKey(slotId), "increase"))
        stepValue := this.configStore.ClampInt(this.GetConfigValueOrDefault(this.GetSlotIncrementStepKey(slotId), 1), 1, 999999, 1)
        matchModeKey := this.configStore.NormalizeIncrementMatchMode(this.GetConfigValueOrDefault(this.GetSlotIncrementMatchModeKey(slotId), "auto-smart"))
        numberSystemKey := this.configStore.NormalizeIncrementNumberSystem(this.GetConfigValueOrDefault(this.GetSlotIncrementNumberSystemKey(slotId), "decimal"))

        if modeKey = "incremental" {
            this.guiModeType.Choose(2)
        } else if modeKey = "incremental-destination" {
            this.guiModeType.Choose(3)
        } else {
            this.guiModeType.Choose(1)
        }
        this.guiModeField1Control.Choose(operationKey = "decrease" ? 2 : 1)
        this.guiModeField2Control.Text := stepValue

        if matchModeKey = "start" {
            this.guiModeField3Control.Choose(2)
        } else if matchModeKey = "end" {
            this.guiModeField3Control.Choose(3)
        } else {
            this.guiModeField3Control.Choose(1)
        }

        if numberSystemKey = "hexadecimal" {
            this.guiModeField4Control.Choose(2)
        } else if numberSystemKey = "roman" {
            this.guiModeField4Control.Choose(3)
        } else {
            this.guiModeField4Control.Choose(1)
        }

        this.guiBindingControls[clearAssocHotkeyKey] := this.guiModeDestinationClearHotkey
        this.guiBindingLabels[clearAssocHotkeyKey] := "Slot " slotId " clear destination association"
        this.guiModeDestinationClearHotkey.Value := this.GetConfigValueOrDefault(clearAssocHotkeyKey, "")

        this.RefreshModePanelDestinationAssociationState(slotId)
        this.ApplyModeEditorLayoutForSelectedMode()
    }

    ApplyModeEditorLayoutForSelectedMode() {
        modeText := StrLower(Trim(this.guiModeType.Text))
        isIncremental := modeText = "incremental"
        isDestinationIncremental := modeText = "incremental destination"

        if isIncremental {
            this.guiModeField1Label.Text := "Operation"
            this.guiModeField2Label.Text := "Step"
            this.guiModeField3Label.Text := "Match Mode"
            this.guiModeField4Label.Text := "Number System"
            this.SetModeDetailFieldVisible(this.guiModeField1Label, this.guiModeField1Control, true)
            this.SetModeDetailFieldVisible(this.guiModeField2Label, this.guiModeField2Control, true)
            this.SetModeDetailFieldVisible(this.guiModeField3Label, this.guiModeField3Control, true)
            this.SetModeDetailFieldVisible(this.guiModeField4Label, this.guiModeField4Control, true)
            this.SetDestinationModeControlsVisible(false)
            this.guiModeHint.Text := "Auto-Smart increments only when one unambiguous start/end token exists."
            return
        }

        if isDestinationIncremental {
            this.guiModeField1Label.Text := "Direction"
            this.SetModeDetailFieldVisible(this.guiModeField1Label, this.guiModeField1Control, true)

            this.guiModeField2Label.Text := "Step"
            this.SetModeDetailFieldVisible(this.guiModeField2Label, this.guiModeField2Control, true)

            this.SetModeDetailFieldVisible(this.guiModeField3Label, this.guiModeField3Control, false)
            this.SetModeDetailFieldVisible(this.guiModeField4Label, this.guiModeField4Control, false)
            this.SetDestinationModeControlsVisible(true)
            this.guiModeHint.Text := "Direction controls numbering: Increase from current max/start or Decrease from current min/start."
            return
        }

        this.SetModeDetailFieldVisible(this.guiModeField1Label, this.guiModeField1Control, false)
        this.SetModeDetailFieldVisible(this.guiModeField2Label, this.guiModeField2Control, false)
        this.SetModeDetailFieldVisible(this.guiModeField3Label, this.guiModeField3Control, false)
        this.SetModeDetailFieldVisible(this.guiModeField4Label, this.guiModeField4Control, false)
        this.SetDestinationModeControlsVisible(false)
        this.guiModeHint.Text := "Default mode uses exact paste behavior (no extra mode parameters)."
    }

    SetDestinationModeControlsVisible(isVisible) {
        this.guiModeDestinationAssociationLabel.Opt(isVisible ? "-Hidden" : "+Hidden")
        this.guiModeDestinationAssociationValue.Opt(isVisible ? "-Hidden" : "+Hidden")
        this.guiModeDestinationClearAssociationButton.Opt(isVisible ? "-Hidden" : "+Hidden")
        this.guiModeDestinationClearAssociationButton.Opt(isVisible ? "-Disabled" : "+Disabled")
        this.guiModeDestinationClearHotkey.Opt(isVisible ? "-Hidden" : "+Hidden")
        this.guiModeDestinationClearHotkey.Opt(isVisible ? "-Disabled" : "+Disabled")
        this.guiModeDestinationClearBindButton.Opt(isVisible ? "-Hidden" : "+Hidden")
        this.guiModeDestinationClearBindButton.Opt(isVisible ? "-Disabled" : "+Disabled")
        this.guiModeDestinationClearClearButton.Opt(isVisible ? "-Hidden" : "+Hidden")
        this.guiModeDestinationClearClearButton.Opt(isVisible ? "-Disabled" : "+Disabled")
    }

    RefreshModePanelDestinationAssociationState(slotId := 0) {
        if slotId < 1 {
            slotId := this.GetSelectedModePanelSlot()
        }

        folderPath := this.ResolveActiveDestinationFolder(slotId)
        if folderPath = "" {
            this.guiModeDestinationAssociationValue.Text := "No active destination folder detected"
            return
        }

        association := this.GetDestinationFamilyAssociation(slotId, folderPath)
        if IsObject(association) {
            previewName := association["prefix"] "#" association["suffix"]
            if association["extension"] != "" {
                previewName .= "." association["extension"]
            }
            this.guiModeDestinationAssociationValue.Text := "Folder: " folderPath "`nFamily: " previewName
            return
        }

        this.guiModeDestinationAssociationValue.Text := "Folder: " folderPath "`nFamily: none"
    }

    StartBindingForModeDestinationClearHotkey(*) {
        this.StartBindingForKey(this.GetSlotClearDestinationAssociationHotkeyKey(this.GetSelectedModePanelSlot()))
    }

    ClearModeDestinationClearHotkey(*) {
        this.ClearBindingForKey(this.GetSlotClearDestinationAssociationHotkeyKey(this.GetSelectedModePanelSlot()))
    }

    ClearModePanelDestinationAssociation(*) {
        slotId := this.GetSelectedModePanelSlot()
        this.ClearDestinationAssociationForSlot(slotId, true)
        this.RefreshModePanelDestinationAssociationState(slotId)
    }

    SetModeDetailFieldVisible(labelControl, valueControl, isVisible) {
        labelControl.Opt(isVisible ? "-Hidden" : "+Hidden")
        valueControl.Opt(isVisible ? "-Hidden" : "+Hidden")
        valueControl.Opt(isVisible ? "-Disabled" : "+Disabled")
    }

    EnterSettingsMode() {
        if this.isSettingsModeActive {
            return
        }
        ; Settings mode remains active for focus-aware hotkey suppression and diagnostics.
        ; Runtime hotkeys stay registered so background operation continues.
        this.isSettingsModeActive := true
        this.logger.Info("Entered settings mode")
    }

    ExitSettingsMode() {
        if !this.isSettingsModeActive {
            return
        }
        this.isSettingsModeActive := false
        this.bindingGuardUntilTick := A_TickCount + 250
        this.RegisterHotkeys()
        this.logger.Info("Exited settings mode")
    }

    IsRuntimeHotkeySuppressed() {
        ; Runtime hotkeys are suppressed only when settings is currently focused,
        ; during explicit bind capture, or during short post-capture guard windows.
        return this.IsSettingsWindowFocused() || this.isBindingCaptureActive || this.IsInBindingGuardWindow()
    }

    GetRuntimeHotkeySuppressionReason() {
        if this.IsSettingsWindowFocused() {
            return "settings-focused"
        }
        if this.isBindingCaptureActive {
            return "binding-capture-active"
        }
        if this.IsInBindingGuardWindow() {
            return "binding-guard-window"
        }
        return ""
    }

    ShouldRunRuntimeHotkey(actionLabel) {
        reason := this.GetRuntimeHotkeySuppressionReason()
        if reason = "" {
            return true
        }

        this.logger.Debug("Runtime hotkey suppressed", Map("action", actionLabel, "reason", reason))
        return false
    }

    IsSettingsWindowFocused() {
        if !this.isSettingsModeActive {
            return false
        }
        if !this.HasProp("settingsGui") || !IsObject(this.settingsGui) {
            return false
        }
        try {
            return WinActive("ahk_id " this.settingsGui.Hwnd) ? true : false
        } catch {
            return false
        }
    }

    AddBindingRow(settingsWindow, label, configKey, rowOptions := "xm y+8", allowClear := true) {
        settingsWindow.AddText(rowOptions " w140", label)
        bindingControl := settingsWindow.AddHotkey("x+8 yp-3 w180", this.config[configKey])
        bindButton := settingsWindow.AddButton("x+8 yp-1 w70", "Bind")

        bindButton.OnEvent("Click", ObjBindMethod(this, "StartBindingForKey", configKey))
        if allowClear {
            clearButton := settingsWindow.AddButton("x+6 yp w70", "Clear")
            clearButton.OnEvent("Click", ObjBindMethod(this, "ClearBindingForKey", configKey))
        }

        this.guiBindingControls[configKey] := bindingControl
        this.guiBindingLabels[configKey] := label
    }

    StartBindingForKey(configKey, *) {
        ; --- Bind entrypoint is fully guarded so GUI clicks never throw runtime popups. ---
        try {
            if !this.guiBindingControls.Has(configKey) {
                return
            }

            ; --- Binding capture is exclusive: stop all runtime hotkeys first. ---
            if this.isBindingCaptureActive {
                this.EndBindingCapture("Previous binding capture cancelled", true)
            }

            label := this.guiBindingLabels.Has(configKey) ? this.guiBindingLabels[configKey] : configKey
            targetControl := this.guiBindingControls[configKey]
            this.isBindingCaptureActive := true
            this.bindingTargetKey := configKey
            this.bindingPreviousValue := targetControl.Value
            this.bindingCapturedValue := ""

            this.EnterBindingIsolationMode()
            this.ActivateSettingsWindowForBinding()

            this.guiStatus.Text := "Binding mode active for " label ". Press combo now (Esc to cancel)."
            this.logger.Info("Binding capture started", Map("configKey", configKey, "label", label, "previousValue", this.bindingPreviousValue))

            if !this.BeginRawBindingCapture() {
                this.EndBindingCapture("Binding capture unavailable", true)
                this.guiStatus.Text := "Could not start binding capture (see log)."
                return
            }
        } catch error {
            this.logger.Error("Binding capture failed to start", Map("configKey", configKey, "error", this.FormatError(error)))
            if this.isBindingCaptureActive {
                this.EndBindingCapture("Binding capture error", true)
            }
            this.guiStatus.Text := "Binding capture error (see log)."
        }
    }

    ActivateSettingsWindowForBinding() {
        ; Keep focus on the settings window (not the Hotkey input control) so native
        ; Hotkey-control parsing cannot mutate the value while raw capture is active.
        if !this.HasProp("settingsGui") || !IsObject(this.settingsGui) {
            return
        }
        try {
            WinActivate("ahk_id " this.settingsGui.Hwnd)
        } catch {
        }
    }

    BeginRawBindingCapture() {
        ; --- Raw key capture path: independent from Hotkey control change quirks. ---
        try {
            this.bindingInputHook := InputHook("L0")
            this.bindingInputHook.KeyOpt("{All}", "N")
            this.bindingInputHook.OnKeyDown := ObjBindMethod(this, "OnBindingKeyDown")
            this.bindingInputHook.Start()
            this.logger.Debug("Raw binding capture started")
            return true
        } catch error {
            this.bindingInputHook := ""
            this.logger.Error("Failed to start raw binding capture", Map("error", this.FormatError(error)))
            return false
        }
    }

    OnBindingKeyDown(inputHookObj, vkCode, scanCode) {
        try {
            if !this.isBindingCaptureActive {
                return
            }

            keyName := this.ResolveBindingKeyName(vkCode, scanCode)
            normalizedName := StrLower(Trim(keyName))

            this.logger.Debug("Raw binding key down", Map("keyName", keyName, "vk", vkCode, "sc", scanCode))

            if this.IsModifierKeyName(normalizedName) {
                this.logger.Debug("Ignored modifier key during binding capture", Map("keyName", keyName, "normalized", normalizedName, "vk", vkCode, "sc", scanCode))
                return
            }

            if normalizedName = "escape" {
                this.EndBindingCapture("Binding capture cancelled", true)
                return
            }

            capturedHotkey := this.BuildCapturedHotkeyFromCurrentState(keyName)
            if capturedHotkey = "" {
                this.logger.Debug("Ignoring key in binding capture because no valid hotkey could be built", Map("keyName", keyName, "vk", vkCode, "sc", scanCode))
                return
            }
            if this.IsModifierOnlyHotkey(capturedHotkey) {
                this.logger.Warn("Rejected modifier-only binding capture", Map("hotkey", capturedHotkey, "keyName", keyName, "vk", vkCode, "sc", scanCode))
                this.guiStatus.Text := "Binding requires a non-modifier key (example: Ctrl+1)."
                return
            }

            this.bindingCapturedValue := capturedHotkey
            if this.guiBindingControls.Has(this.bindingTargetKey) {
                this.bindingSuppressChange := true
                this.guiBindingControls[this.bindingTargetKey].Value := capturedHotkey
                this.bindingSuppressChange := false
            }

            label := this.guiBindingLabels.Has(this.bindingTargetKey) ? this.guiBindingLabels[this.bindingTargetKey] : this.bindingTargetKey
            this.logger.Info("Binding captured", Map("configKey", this.bindingTargetKey, "label", label, "hotkey", capturedHotkey))
            this.EndBindingCapture("Bound " label " -> " capturedHotkey)
        } catch error {
            this.logger.Error("Unhandled error during binding key capture", Map("error", this.FormatError(error), "vk", vkCode, "sc", scanCode))
            this.EndBindingCapture("Binding capture error", true)
            this.guiStatus.Text := "Binding capture error (see log)."
        }
    }

    ResolveBindingKeyName(vkCode, scanCode) {
        ; Resolve by multiple token formats because some keyboards/drivers report
        ; vk/sc combinations that only decode correctly with one of these forms.
        candidates := [
            Format("vk{:02X}sc{:03X}", vkCode, scanCode),
            Format("vk{:02X}", vkCode),
            Format("sc{:03X}", scanCode)
        ]

        for token in candidates {
            try {
                resolved := Trim(GetKeyName(token))
                if resolved != "" {
                    return resolved
                }
            } catch {
            }
        }
        return ""
    }

    IsModifierKeyName(normalizedKeyName) {
        ; InputHook/GetKeyName can report modifiers with multiple aliases
        ; (e.g. LControl, LCtrl, LMenu, etc.). Keep one canonical filter so
        ; modifier presses are never treated as bind base keys.
        modifiers := Map(
            "ctrl", 1,
            "control", 1,
            "lctrl", 1,
            "rctrl", 1,
            "lcontrol", 1,
            "rcontrol", 1,
            "shift", 1,
            "lshift", 1,
            "rshift", 1,
            "alt", 1,
            "menu", 1,
            "lalt", 1,
            "ralt", 1,
            "lmenu", 1,
            "rmenu", 1,
            "win", 1,
            "lwin", 1,
            "rwin", 1,
            "lwindows", 1,
            "rwindows", 1
        )
        return modifiers.Has(normalizedKeyName)
    }

    BuildCapturedHotkeyFromCurrentState(baseKeyName) {
        normalizedBase := this.NormalizeBindingBaseKeyName(baseKeyName)
        if normalizedBase = "" {
            return ""
        }

        modPrefix := ""
        if GetKeyState("Ctrl", "P") {
            modPrefix .= "^"
        }
        if GetKeyState("Alt", "P") {
            modPrefix .= "!"
        }
        if GetKeyState("Shift", "P") {
            modPrefix .= "+"
        }
        if GetKeyState("LWin", "P") || GetKeyState("RWin", "P") {
            modPrefix .= "#"
        }
        return modPrefix normalizedBase
    }

    NormalizeBindingBaseKeyName(baseKeyName) {
        normalized := Trim(baseKeyName)
        if normalized = "" {
            return ""
        }

        if this.IsModifierKeyName(StrLower(normalized)) {
            return ""
        }

        return normalized
    }

    IsModifierOnlyHotkey(hotkeyText) {
        normalized := Trim(hotkeyText)
        if normalized = "" {
            return true
        }
        return RegExMatch(normalized, "^[\^\!\+\#<>]+$") ? true : false
    }

    EnterBindingIsolationMode() {
        ; --- Hard isolation against accidental runtime actions while binding. ---
        this.bindingPreviousSuspendState := A_IsSuspended
        ; AHK v2 function-style Suspend() expects a numeric state, not "On"/"Off" strings.
        Suspend(1)
        this.UnregisterHotkeys()
        this.logger.Debug("Entered binding isolation mode", Map("previousSuspendState", this.bindingPreviousSuspendState))
    }

    ClearBindingForKey(configKey, *) {
        if !this.guiBindingControls.Has(configKey) {
            return
        }

        if this.isBindingCaptureActive && this.bindingTargetKey = configKey {
            this.EndBindingCapture("Binding capture cancelled", true)
        }

        this.guiBindingControls[configKey].Value := ""
        label := this.guiBindingLabels.Has(configKey) ? this.guiBindingLabels[configKey] : configKey
        this.guiStatus.Text := "Cleared binding: " label
        this.logger.Info("Binding cleared from settings UI", Map("configKey", configKey, "label", label))
    }

    EndBindingCapture(statusText := "", restorePrevious := false) {
        ; --- End bind mode safely: restore UI value, wait key release, then re-enable runtime hotkeys. ---
        if !this.isBindingCaptureActive {
            return
        }

        if IsObject(this.bindingInputHook) {
            try {
                this.bindingInputHook.Stop()
            } catch {
            }
        }
        this.bindingInputHook := ""

        targetKey := this.bindingTargetKey
        if restorePrevious && targetKey != "" && this.guiBindingControls.Has(targetKey) {
            this.bindingSuppressChange := true
            this.guiBindingControls[targetKey].Value := this.bindingPreviousValue
            this.bindingSuppressChange := false
        }

        finalHotkey := ""
        if targetKey != "" && this.guiBindingControls.Has(targetKey) {
            finalHotkey := this.NormalizeGuiHotkeyValue(this.guiBindingControls[targetKey].Value)
        }

        this.WaitForBindReleaseBarrier(finalHotkey)
        this.bindingGuardUntilTick := A_TickCount + 250

        this.isBindingCaptureActive := false
        this.bindingTargetKey := ""
        this.bindingPreviousValue := ""
        this.bindingCapturedValue := ""

        this.RegisterHotkeys()
        this.ExitBindingIsolationMode()
        if statusText != "" {
            this.guiStatus.Text := statusText
        }
        this.logger.Debug("Binding capture ended", Map("status", statusText, "restored", restorePrevious))
    }

    WaitForBindReleaseBarrier(hotkeyText) {
        ; --- Prevent immediate retrigger by waiting for pressed keys/modifiers to be released. ---
        baseKey := this.ExtractBaseKeyFromHotkey(hotkeyText)
        if baseKey != "" && GetKeyState(baseKey, "P") {
            KeyWait(baseKey, "T0.7")
            this.logger.Debug("Release barrier waited for base key", Map("baseKey", baseKey))
        }

        for modKey in ["Ctrl", "Alt", "Shift", "LWin", "RWin"] {
            if GetKeyState(modKey, "P") {
                KeyWait(modKey, "T0.7")
                this.logger.Debug("Release barrier waited for modifier", Map("modifier", modKey))
            }
        }

        Sleep(50)
    }

    ExtractBaseKeyFromHotkey(hotkeyText) {
        normalized := Trim(hotkeyText)
        if normalized = "" {
            return ""
        }
        return RegExReplace(normalized, "[\^\!\+\#<>]", "")
    }

    IsInBindingGuardWindow() {
        return A_TickCount < this.bindingGuardUntilTick
    }

    ExitBindingIsolationMode() {
        ; --- Restore global suspend state exactly as it was before bind mode. ---
        if !this.bindingPreviousSuspendState {
            Suspend(0)
        } else {
            Suspend(1)
        }
        this.logger.Debug("Exited binding isolation mode", Map("restoredSuspendState", this.bindingPreviousSuspendState))
    }

    CloseSettingsGui(*) {
        if this.isBindingCaptureActive {
            this.EndBindingCapture("Binding capture cancelled (window closed)", true)
        }
        if this.HasProp("settingsGui") && IsObject(this.settingsGui) {
            this.settingsGui.Hide()
        }
        this.ExitSettingsMode()
    }

    OnSettingsEscape(*) {
        if this.isBindingCaptureActive {
            this.EndBindingCapture("Binding capture cancelled", true)
            return
        }
        this.CloseSettingsGui()
    }

    SaveSettingsFromGui(*) {
        ; --- Settings save pipeline: collect -> validate -> persist -> apply runtime state. ---
        try {
            newConfig := Map()
            newConfig["CopyHotkey"] := this.GetGuiHotkeyValue("CopyHotkey")
            newConfig["PasteHotkey"] := this.GetGuiHotkeyValue("PasteHotkey")
            newConfig["SourceCopyCombo"] := this.GetGuiHotkeyValue("SourceCopyCombo")
            newConfig["TargetPasteCombo"] := this.GetGuiHotkeyValue("TargetPasteCombo")
            newConfig["SlotCount"] := this.configStore.ClampInt(this.guiSlotCount.Text, 1, 9, 1)
            newConfig["ActiveSlot"] := this.configStore.ClampInt(this.guiActiveSlot.Text, 1, newConfig["SlotCount"], 1)
            newConfig["DebugEnabled"] := this.guiDebugEnabled.Value = 1
            newConfig["ConfigVersion"] := this.config.Has("ConfigVersion") ? this.configStore.ClampInt(this.config["ConfigVersion"], 1, 999, 3) : 3
            loop 9 {
                slotId := A_Index
                copyKeyName := this.GetSlotCopyHotkeyKey(slotId)
                pasteKeyName := this.GetSlotPasteHotkeyKey(slotId)
                clearAssocKeyName := this.GetSlotClearDestinationAssociationHotkeyKey(slotId)
                newConfig[copyKeyName] := this.GetGuiHotkeyValue(copyKeyName)
                newConfig[pasteKeyName] := this.GetGuiHotkeyValue(pasteKeyName)
                newConfig[clearAssocKeyName] := this.GetConfigValueOrDefault(clearAssocKeyName, "")

                modeKey := this.GetSlotModeKey(slotId)
                operationKey := this.GetSlotIncrementOperationKey(slotId)
                stepKey := this.GetSlotIncrementStepKey(slotId)
                matchModeKey := this.GetSlotIncrementMatchModeKey(slotId)
                numberSystemKey := this.GetSlotIncrementNumberSystemKey(slotId)

                newConfig[modeKey] := this.configStore.NormalizeSlotMode(this.GetConfigValueOrDefault(modeKey, "default"))
                newConfig[operationKey] := this.configStore.NormalizeIncrementOperation(this.GetConfigValueOrDefault(operationKey, "increase"))
                newConfig[stepKey] := this.configStore.ClampInt(this.GetConfigValueOrDefault(stepKey, 1), 1, 999999, 1)
                newConfig[matchModeKey] := this.configStore.NormalizeIncrementMatchMode(this.GetConfigValueOrDefault(matchModeKey, "auto-smart"))
                newConfig[numberSystemKey] := this.configStore.NormalizeIncrementNumberSystem(this.GetConfigValueOrDefault(numberSystemKey, "decimal"))
            }

            this.CollectModePanelIntoConfig(&newConfig)

            ; --- Operation combo failsafe: preserve existing/internal defaults if UI value is empty. ---
            fallbackApplied := false
            if newConfig["SourceCopyCombo"] = "" {
                newConfig["SourceCopyCombo"] := this.config.Has("SourceCopyCombo") && this.config["SourceCopyCombo"] != "" ? this.config["SourceCopyCombo"] : "^c"
                fallbackApplied := true
            }
            if newConfig["TargetPasteCombo"] = "" {
                newConfig["TargetPasteCombo"] := this.config.Has("TargetPasteCombo") && this.config["TargetPasteCombo"] != "" ? this.config["TargetPasteCombo"] : "^v"
                fallbackApplied := true
            }

            if fallbackApplied {
                this.logger.Warn("Empty operation combos replaced with defaults", Map("SourceCopyCombo", newConfig["SourceCopyCombo"], "TargetPasteCombo", newConfig["TargetPasteCombo"]))
                if this.guiBindingControls.Has("SourceCopyCombo") {
                    this.guiBindingControls["SourceCopyCombo"].Value := newConfig["SourceCopyCombo"]
                }
                if this.guiBindingControls.Has("TargetPasteCombo") {
                    this.guiBindingControls["TargetPasteCombo"].Value := newConfig["TargetPasteCombo"]
                }
            }

            validationError := this.ValidateConfig(newConfig)
            if validationError != "" {
                this.guiStatus.Text := validationError
                this.logger.Warn("Settings save validation failed", Map("error", validationError))
                return
            }

            this.config := newConfig
            this.slotEngine.SetSlotCount(this.config["SlotCount"])
            this.configStore.Save(this.config)
            this.logger.SetDebugEnabled(this.config["DebugEnabled"])
            this.RegisterHotkeys()

            this.guiStatus.Text := "Settings saved successfully"
            this.logger.Info("Settings applied successfully", this.BuildHotkeySnapshot(this.config))
        } catch error {
            this.guiStatus.Text := "Failed to save settings"
            this.logger.Error("Failed while saving settings", Map("error", this.FormatError(error), "snapshot", this.BuildSafeUiSnapshot()))
        }
    }

    CollectModePanelIntoConfig(&cfg) {
        selectedSlot := this.GetSelectedModePanelSlot()
        modeKey := this.GetSlotModeKey(selectedSlot)
        operationKey := this.GetSlotIncrementOperationKey(selectedSlot)
        stepKey := this.GetSlotIncrementStepKey(selectedSlot)
        matchModeKey := this.GetSlotIncrementMatchModeKey(selectedSlot)
        numberSystemKey := this.GetSlotIncrementNumberSystemKey(selectedSlot)
        clearAssocHotkeyKey := this.GetSlotClearDestinationAssociationHotkeyKey(selectedSlot)

        modeText := StrLower(Trim(this.guiModeType.Text))
        chosenMode := modeText = "incremental" ? "incremental" : (modeText = "incremental destination" ? "incremental-destination" : "default")

        chosenOperation := StrLower(Trim(this.guiModeField1Control.Text)) = "decrease" ? "decrease" : "increase"
        chosenStep := this.configStore.ClampInt(this.guiModeField2Control.Text, 1, 999999, 1)

        matchModeText := StrLower(Trim(this.guiModeField3Control.Text))
        chosenMatchMode := matchModeText = "start" ? "start" : (matchModeText = "end" ? "end" : "auto-smart")

        numberSystemText := StrLower(Trim(this.guiModeField4Control.Text))
        if numberSystemText = "hexadecimal" {
            chosenSystem := "hexadecimal"
        } else if numberSystemText = "roman" {
            chosenSystem := "roman"
        } else {
            chosenSystem := "decimal"
        }

        cfg[modeKey] := this.configStore.NormalizeSlotMode(chosenMode)
        cfg[operationKey] := this.configStore.NormalizeIncrementOperation(chosenOperation)
        cfg[stepKey] := chosenStep
        cfg[matchModeKey] := this.configStore.NormalizeIncrementMatchMode(chosenMatchMode)
        cfg[numberSystemKey] := this.configStore.NormalizeIncrementNumberSystem(chosenSystem)
        cfg[clearAssocHotkeyKey] := this.GetGuiHotkeyValue(clearAssocHotkeyKey)

        this.logger.Debug("Collected mode panel into config", Map(
            "slotId", selectedSlot,
            "mode", cfg[modeKey],
            "operation", cfg[operationKey],
            "step", cfg[stepKey],
            "matchMode", cfg[matchModeKey],
            "numberSystem", cfg[numberSystemKey],
            "clearAssocHotkey", cfg[clearAssocHotkeyKey]
        ))
    }

    BuildSafeUiSnapshot() {
        snapshot := Map()
        try {
            snapshot["slotCountText"] := this.HasProp("guiSlotCount") ? this.guiSlotCount.Text : ""
            snapshot["activeSlotText"] := this.HasProp("guiActiveSlot") ? this.guiActiveSlot.Text : ""
            snapshot["modePanelSlot"] := this.HasProp("guiModeSlotSelect") ? this.guiModeSlotSelect.Text : ""
            snapshot["modePanelType"] := this.HasProp("guiModeType") ? this.guiModeType.Text : ""
            snapshot["modePanelOperation"] := this.HasProp("guiModeField1Control") ? this.guiModeField1Control.Text : ""
            snapshot["modePanelStep"] := this.HasProp("guiModeField2Control") ? this.guiModeField2Control.Text : ""
            snapshot["modePanelMatchMode"] := this.HasProp("guiModeField3Control") ? this.guiModeField3Control.Text : ""
            snapshot["modePanelNumberSystem"] := this.HasProp("guiModeField4Control") ? this.guiModeField4Control.Text : ""
            snapshot["modePanelClearAssocHotkey"] := this.HasProp("guiModeDestinationClearHotkey") ? this.guiModeDestinationClearHotkey.Value : ""
            snapshot["isSettingsModeActive"] := this.isSettingsModeActive
            snapshot["isBindingCaptureActive"] := this.isBindingCaptureActive
        } catch {
        }
        return snapshot
    }

    GetGuiHotkeyValue(configKey) {
        if !this.guiBindingControls.Has(configKey) {
            return ""
        }

        ; Hotkey controls display "None" for empty binds; convert it to true empty.
        return this.NormalizeGuiHotkeyValue(this.guiBindingControls[configKey].Value)
    }

    NormalizeGuiHotkeyValue(rawValue) {
        normalized := Trim(rawValue)
        return StrLower(normalized) = "none" ? "" : normalized
    }

    BuildHotkeySnapshot(cfg) {
        snapshot := Map(
            "CopyHotkey", cfg["CopyHotkey"],
            "PasteHotkey", cfg["PasteHotkey"],
            "SourceCopyCombo", cfg["SourceCopyCombo"],
            "TargetPasteCombo", cfg["TargetPasteCombo"],
            "SlotCount", cfg["SlotCount"],
            "ActiveSlot", cfg["ActiveSlot"]
        )
        loop 9 {
            slotId := A_Index
            snapshot[this.GetSlotCopyHotkeyKey(slotId)] := cfg[this.GetSlotCopyHotkeyKey(slotId)]
            snapshot[this.GetSlotPasteHotkeyKey(slotId)] := cfg[this.GetSlotPasteHotkeyKey(slotId)]
            snapshot[this.GetSlotClearDestinationAssociationHotkeyKey(slotId)] := cfg[this.GetSlotClearDestinationAssociationHotkeyKey(slotId)]
            snapshot[this.GetSlotModeKey(slotId)] := cfg.Has(this.GetSlotModeKey(slotId)) ? cfg[this.GetSlotModeKey(slotId)] : "default"
        }
        return snapshot
    }

    FormatError(errorObj) {
        try {
            if IsObject(errorObj) {
                detail := ""

                try {
                    if errorObj.Message != "" {
                        detail := errorObj.Message
                    }
                } catch {
                }
                try {
                    if errorObj.Extra != "" {
                        detail .= (detail != "" ? " | " : "") "Extra=" errorObj.Extra
                    }
                } catch {
                }
                try {
                    if errorObj.What != "" {
                        detail .= (detail != "" ? " | " : "") "What=" errorObj.What
                    }
                } catch {
                }
                try {
                    if errorObj.File != "" {
                        detail .= (detail != "" ? " | " : "") "File=" errorObj.File
                    }
                } catch {
                }
                try {
                    if errorObj.Line != "" {
                        detail .= (detail != "" ? " | " : "") "Line=" errorObj.Line
                    }
                } catch {
                }
                try {
                    if errorObj.Stack != "" {
                        detail .= (detail != "" ? " | " : "") "Stack=" errorObj.Stack
                    }
                } catch {
                }

                if detail != "" {
                    return detail
                }
                return "<error object type=" Type(errorObj) ">"
            }
        } catch {
        }
        try {
            return String(errorObj)
        } catch {
            return "<unknown error>"
        }
    }

    ValidateConfig(cfg) {
        if cfg["SourceCopyCombo"] = "" {
            return "Selection copy combo cannot be empty"
        }
        if cfg["TargetPasteCombo"] = "" {
            return "Target paste combo cannot be empty"
        }

        seenHotkeys := Map()
        duplicateError := ""

        this.CheckAndTrackHotkey(cfg["CopyHotkey"], "Active slot copy hotkey", seenHotkeys, &duplicateError)
        if duplicateError != "" {
            return duplicateError
        }

        this.CheckAndTrackHotkey(cfg["PasteHotkey"], "Active slot paste hotkey", seenHotkeys, &duplicateError)
        if duplicateError != "" {
            return duplicateError
        }

        loop cfg["SlotCount"] {
            slotId := A_Index
            this.CheckAndTrackHotkey(cfg[this.GetSlotCopyHotkeyKey(slotId)], "Slot " slotId " copy hotkey", seenHotkeys, &duplicateError)
            if duplicateError != "" {
                return duplicateError
            }

            this.CheckAndTrackHotkey(cfg[this.GetSlotPasteHotkeyKey(slotId)], "Slot " slotId " paste hotkey", seenHotkeys, &duplicateError)
            if duplicateError != "" {
                return duplicateError
            }

            this.CheckAndTrackHotkey(cfg[this.GetSlotClearDestinationAssociationHotkeyKey(slotId)], "Slot " slotId " clear association hotkey", seenHotkeys, &duplicateError)
            if duplicateError != "" {
                return duplicateError
            }
        }

        return ""
    }

    CheckAndTrackHotkey(hotkeyText, label, seenHotkeys, &errorText) {
        normalized := StrLower(Trim(hotkeyText))
        if normalized = "" {
            return
        }

        if seenHotkeys.Has(normalized) {
            errorText := label " duplicates " seenHotkeys[normalized]
            return
        }

        seenHotkeys[normalized] := label
    }

    OpenLogFile(*) {
        if !FileExist(this.logPath) {
            FileAppend("", this.logPath, "UTF-8")
        }
        Run(this.logPath)
    }

    ShowActionToolTip(text) {
        MouseGetPos(&mouseX, &mouseY)
        ToolTip(text, mouseX + 16, mouseY + 16)
        SetTimer(() => ToolTip(), -1000)
        this.logger.Debug("User notification", Map("message", text))
    }

    ExitAppNow(*) {
        this.logger.Info("ExtraClipboard app exiting")
        ExitApp()
    }
}

StrJoin(items, separator := "") {
    result := ""
    for index, item in items {
        if index > 1 {
            result .= separator
        }
        result .= item
    }
    return result
}

app := ExtraClipboardApp()