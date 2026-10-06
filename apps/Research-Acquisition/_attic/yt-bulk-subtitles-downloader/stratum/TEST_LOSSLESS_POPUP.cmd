@echo off
rem One-click test for the Stratum popup with the Lossless Compress action available.
echo We need a compact AI handoff packet that preserves the relationship dynamic, the live goal, the claims, the terms, and the next action. This is a test of the local lossless meaning compressor through Stratum. > "%TEMP%\stratum_selection.txt"
"C:\Users\David\AppData\Local\Programs\Python\Python312\python.exe" "%~dp003_ui_python\action_popup.py" --selection-file "%TEMP%\stratum_selection.txt"
pause
