# ExtraClipboard Dark Theme Changelog

Updated: 2026-07-16

## Change

Applied a dark AI-hub style to the existing AutoHotkey v2 GUI without porting the app to the separate colorful GUI framework.

Updated:

- `ExtraClipboard.ahk`
- `ExtraClipboard.exe`

The Settings window and destination picker dialogs now use:

- dark window background
- light text
- cyan/accent section headers
- muted helper text
- dark edit/hotkey/list controls where AutoHotkey native controls allow it

Native Windows buttons may still render partly in the system style.

## Backup

Original files were backed up under:

```text
\\192.168.2.50\h_hp\Desktop\AI HUB DAVID\ExtraClipboard-main\backups
```

## Validation

Ran AutoHotkey v2 validation:

```text
C:\Program Files\AutoHotkey\v2\AutoHotkey64.exe /ErrorStdOut /Validate ExtraClipboard.ahk
```

Result: no parser errors.

Rebuilt executable with:

```text
C:\Program Files\AutoHotkey\Compiler\Ahk2Exe.exe
```

