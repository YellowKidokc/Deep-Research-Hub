/**
 * =========================================================================== *
 * Want a clear path for learning AutoHotkey?                                  *
 * Take a look at our AutoHotkey courses here: the-Automator.com/Discover      *
 * They're structured in a way to make learning AHK EASY                       *
 * And come with a 200% moneyback guarantee so you have NOTHING to risk!       *
 * =========================================================================== *
 * @author      the-Automator                                                  *
 * @version     0.0.2                                                          *
 * @copyright   Copyright (c) 2024 the-Automator                               *
 * @link        https://the-Automator.com/AlwaysonTop?src=app                  *
 * @created     2024-09-19                                                     *
 * @modified    2026-06-19                                                     *
 * @description Always on Top, the ultimate tool to keep your essential        *
 *              windows visible at all times.                                  *
 * =========================================================================== *
 * @license     CC BY 4.0                                                      *
 * =========================================================================== *
   This work by the-Automator.com is licensed under CC BY 4.0

   Attribution - You must give appropriate credit , provide a link to the license,
   and indicate if changes were made.

   You may do so in any reasonable manner, but not in any way that suggests the licensor
   endorses you or your use.

   No additional restrictions - You may not apply legal terms or technological measures that
   legally restrict others from doing anything the license permits.
 */

#SingleInstance
#Requires AutoHotkey v2.0+
#include <Triggers>
;--
;@Ahk2Exe-SetVersion     0.0.2
;@Ahk2Exe-SetMainIcon    res\main.ico
;@Ahk2Exe-SetProductName AlwaysonTop
;@Ahk2Exe-SetDescription Always on Top, the ultimate tool to keep your essential windows visible at all times.


#include <ScriptObject>
script := {
	        base : ScriptObj(),
	     version : "0.0.2",
	      author : "the-Automator",
	       email : "joe@the-automator.com",
	     crtdate : "Sep 19 2024",
	     moddate : "Jun 19 2026",
	   resfolder : A_ScriptDir "\res",
	    iconfile : A_ScriptDir "\res\main.ico" ,
	      config : "",
	homepagetext : "the-automator.com/AlwaysonTop",
	homepagelink : "the-Automator.com/AlwaysonTop?src=app",
	   VideoLink : "",
	  	 DevPath : "S:\AlwaysOnTop\AlwaysOnTop.ahk",
	  donateLink : "",
	        hwnd : 0,
}


ini := A_ScriptDir "\settings.ini"
prefixText := IniRead(ini, "Settings", "PrefixText", "AlwaysOnTop ")
TraySetIcon(A_ScriptDir "\res\Pin3.ico")
triggers.AddHotkey(toggleSetTop,'AlwaysonTop')
chb := triggers.addCheckbox(updateTitle,'xm+150 y+m+10 -checked','Update Title')
ui := triggers.ui
prefixEdit := ui.AddEdit('x+10 yp-2 w300', prefixText)


triggers.FinishMenu('Settings')
triggers.save.onEvent('Click', savePrefix)
if !FileExist(Triggers.ini) ; if user running program first time which mean there is no ini file created yet so user will be asked to change the default hotkeys
	triggers.Show()
triggers.tray.AddStandard() ; to add standard menu
PreviousRemember

PreviousRemember(*)
{
    LastActiveWindow := IniRead(ini,"Title","Window","AlwaysOnTop")
    if WinExist(LastActiveWindow)
    {
        WinActivate LastActiveWindow
        ; Toggle AlwaysOnTop
        WinSetAlwaysOnTop(-1, LastActiveWindow)
    }
}



updateTitle(ctrl,*)
{
	; do nothing just for reference
	; WinSetTitle "A",, "AlwaysOnTop"
	; if ctrl.value
	; 	tooltip 'click checkbox' 
	; else
	; 	tooltip
}

toggleSetTop(*)
{
    ; Store the active window's title and handle
    activeWin := WinGetTitle("A")
    winHandle := WinExist("A")
    
    ; Toggle AlwaysOnTop
    WinSetAlwaysOnTop(-1, "A")
    
    ; Check if window is now AlwaysOnTop
    isOnTop := WinGetExStyle("A") & 0x8 ; 0x8 is WS_EX_TOPMOST
    prefixText := IniRead(Triggers.ini, "Settings", "PrefixText", "AlwaysOnTop ")
    ; Update the title if the checkbox is checked
    TitleName := " - " prefixText
    if chb.value {
        ; Add or remove prefix based on AlwaysOnTop state
        if isOnTop {
            if !InStr(activeWin, prefixText) {
                WinSetTitle(activeWin TitleName , winHandle)
                IniWrite(activeWin TitleName,ini,"Title","Window")
            }
        } else {
            if InStr(activeWin, prefixText)
            {
                newTitle := StrReplace(activeWin,TitleName)
                WinSetTitle(newTitle , winHandle)
                IniWrite(newTitle,ini,"Title","Window")
            }
        }
    }

    
}

savePrefix(*)
{
    IniWrite(prefixEdit.value,ini,"Settings","PrefixText")
    ;msgbox prefixEdit.value
}