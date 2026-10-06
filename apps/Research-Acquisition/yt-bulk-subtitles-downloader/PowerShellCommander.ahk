#Requires AutoHotkey v2.0+
#SingleInstance Force

; Shift+Ctrl+Alt+P — Launch Startup Launcher popup
^+!p::
{
    batPath := "D:\DONT TOUCH BOOT UP\Codex-Powershell_GUI\START_STARTUP_LAUNCHER.bat"
    if FileExist(batPath)
        Run(batPath,, "Hide")
    else
        MsgBox("Startup Launcher not found at:`n" batPath, "Error", 16)
}
