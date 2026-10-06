# Stratum

First local working slice for the Stratum Windows productivity app.

## Run the popup

```cmd
python 03_ui_python\action_popup.py
```

Install PySide6 first if needed:

```cmd
python -m pip install PySide6 pyperclip
```

## Run from AutoHotkey

Install AutoHotkey v2, then run:

```cmd
07_ahk\Stratum.ahk
```

Middle mouse or Ctrl+Alt+Space attempts to copy the current selection and opens the PySide action popup. If no selection is available, the popup falls back to the current clipboard text.

## Implemented slice

- `01_core/action_registry.py` loads `04_config/actions.json`, imports `08_actions/*.py`, runs `process(data)`, and logs to `05_logs/actions.log`.
- `01_core/clipboard_manager.py` reads/writes clipboard text and maintains 75 in-memory slots for future expansion.
- `03_ui_python/action_popup.py` displays selected/clipboard text, lists actions, runs actions, shows results, and copies results.
- `07_ahk/Stratum.ahk` keeps Windows-native hotkey/middle-click glue.

## Classification canon

Stratum now has a single classification home at:

- `06_engines/classification/`

Key files:

- `NABLA_CHI_UNIVERSAL_CLASSIFICATION_STANDARD_v1.0.md`
- `NABLA_CHI_CLASSIFICATION_QUICK_REFERENCE.md`

Popup actions:

- `classification_canon`
- `classification_quick_map`
