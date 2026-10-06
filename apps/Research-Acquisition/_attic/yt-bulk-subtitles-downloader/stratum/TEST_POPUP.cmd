@echo off
rem One-click test for the Stratum popup (bypasses AutoHotkey entirely).
rem Uses the full-path Python312 because bare python/pythonw on PATH is the
rem hermes venv with no PySide6 (the original silent-failure bug).
echo Stratum test selection - if you can read this in the popup, it works. > "%TEMP%\stratum_selection.txt"
"C:\Users\David\AppData\Local\Programs\Python\Python312\python.exe" "%~dp003_ui_python\action_popup.py" --selection-file "%TEMP%\stratum_selection.txt"
pause
