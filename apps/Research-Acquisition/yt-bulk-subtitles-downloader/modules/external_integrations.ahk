; ============================================================
; EXTERNAL INTEGRATIONS
; Starts the source-preserved companion tools in separate AHK
; processes. Separate processes prevent globals and hotkeys from
; colliding with AI-HUB while preserving one-script startup.
; ============================================================

global AIH_INTEGRATIONS_ROOT := AIH_GetIntegrationsRoot()
global AIH_INTEGRATIONS_CONFIG := AIH_INTEGRATIONS_ROOT "\config\integrations.ini"
global AIH_INTEGRATION_SCRIPTS := Map(
    "AlwaysOnTop", "integrations\AlwaysOnTop\AlwaysOnTop.ahk",
    "ExtraClipboard", "ExtraClipboard\ExtraClipboard.ahk",
    "LLMAssistant", "LLM-Assistant\LLM AutoHotkey Assistant.ahk",
    "Stratum", "integrations\stratum pop up\07_ahk\Stratum.ahk",
    "WindowCaptureRouter", "integrations\WindowCaptureRouter\WindowRouterHotkeys.ahk",
    "CommandCenter", "command_center\command_center.ahk"
)

AIH_IntegrationsBoot() {
    global AIH_INTEGRATIONS_CONFIG

    enabled := IniRead(AIH_INTEGRATIONS_CONFIG, "Integrations", "Enabled", "1")
    if enabled != "1"
        return

    delayMs := 2500
    try delayMs := Max(0, Integer(IniRead(AIH_INTEGRATIONS_CONFIG, "Integrations", "StartupDelayMs", "2500")))
    SetTimer(AIH_LaunchEnabledIntegrations, -delayMs)
}

AIH_LaunchEnabledIntegrations() {
    global AIH_INTEGRATIONS_ROOT, AIH_INTEGRATIONS_CONFIG, AIH_INTEGRATION_SCRIPTS

    for name, relativePath in AIH_INTEGRATION_SCRIPTS {
        if IniRead(AIH_INTEGRATIONS_CONFIG, "Integrations", name, "1") != "1"
            continue
        AIH_LaunchIntegration(name, AIH_INTEGRATIONS_ROOT "\" relativePath)
    }
}

AIH_GetIntegrationsRoot() {
    SplitPath(A_LineFile, , &moduleDirectory)
    SplitPath(moduleDirectory, , &hubRoot)
    return hubRoot
}

AIH_LaunchIntegration(name, scriptPath) {
    if !FileExist(scriptPath) {
        OutputDebug("AI-HUB integration missing: " name " at " scriptPath)
        return false
    }

    if AIH_IsIntegrationRunning(scriptPath)
        return true

    SplitPath(scriptPath, , &workingDir)
    try {
        Run('"' A_AhkPath '" "' scriptPath '"', workingDir, , &pid)
        return true
    } catch Error as err {
        OutputDebug("AI-HUB could not launch " name ": " err.Message)
        return false
    }
}

AIH_IsIntegrationRunning(scriptPath) {
    previousSetting := A_DetectHiddenWindows
    DetectHiddenWindows(true)
    try {
        normalizedPath := StrLower(scriptPath)
        for hwnd in WinGetList("ahk_class AutoHotkey") {
            try {
                if InStr(StrLower(WinGetTitle("ahk_id " hwnd)), normalizedPath)
                    return true
            }
        }
    } finally {
        DetectHiddenWindows(previousSetting)
    }
    return false
}
