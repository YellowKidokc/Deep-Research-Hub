#Requires AutoHotkey v2.0+
#SingleInstance Force

CDriveAhkRoot := A_AppData "\Microsoft\Windows\Start Menu\Programs\Startup\AHK"
hubScript := CDriveAhkRoot "\AI-HUB.ahk"
commanderBat := "D:\DONT TOUCH BOOT UP\Codex-Powershell_GUI\start_commander.bat"

if FileExist(hubScript) {
    Run('"' A_AhkPath '" "' hubScript '"', CDriveAhkRoot)
} else if FileExist(commanderBat) {
    Run('"' commanderBat '"', "D:\DONT TOUCH BOOT UP\Codex-Powershell_GUI", "Hide")
} else {
    MsgBox("Could not find AI-HUB or Script Hub launcher.", "AI-HUB Startup", "Iconx")
}
