# ExtraClipboard (AutoHotkey v2)

ExtraClipboard provides a separate configurable clipboard slot with independent copy and paste shortcuts.

## Current Features

- Primary mode: configurable instant copy/paste hotkeys per slot (1-9)
- Legacy mode: optional active-slot copy/paste hotkeys
- Per-slot mode system (`Default`, `Incremental`, `Incremental Destination`)
- Configurable source copy combo (default `^c`) and target paste combo (default `^v`)
- Persistent settings in `ExtraClipboard.ini`
- Tray menu for quick actions
- Tray mode switching per slot (Slot Modes -> Slot N -> Default/Incremental)
- Tray mode switching per slot includes Incremental Destination
- Tray action to clear destination association for active slot/folder
- Settings GUI with live bind registration and clear buttons
- Settings GUI includes compact per-slot mode configuration panel (slot selector + mode fields)
- Destination mode panel shows active-folder family association preview and clear action
- Destination mode panel supports per-slot "Clear Association" hotkey binding
- Mode panel is placed on the right side to reduce vertical growth as slots/modes increase
- Source copy / target paste combos are live-bindable internal command keys (no clear)
- Structured log output in `logs/ExtraClipboard.log`
- Incremental mode supports decimal/hex/roman start/end tokens with auto-smart ambiguity detection
- Incremental mode can duplicate files/folders when slot text is a valid path and the file/folder name contains a supported number token
- Slot engine designed for future expansion to multiple slots and modes

## Run

1. Install AutoHotkey v2.
2. Run `ExtraClipboard.ahk`.

## Default Hotkeys

- Slot 1..9 copy/paste: no default (bind manually)
- Legacy active-slot copy/paste: no default (optional, bind manually)
- Selection copy combo / target paste combo: `Ctrl+C` / `Ctrl+V`

## Settings

Open from tray menu: **Settings**.

Fields:

- Slot 1..9 Copy/Paste hotkeys (primary mode)
- Active Slot Copy/Paste hotkeys (legacy optional mode)
- Selection Copy Combo
- Target Paste Combo
- Slot Count (1-9)
- Active Slot
- Enable debug logs
- Mode Configuration panel:
	- Config Slot (1-9)
	- Mode (`Default` / `Incremental` / `Incremental Destination`)
	- Operation (`Increase` / `Decrease`)
	- Step
	- Match Mode (`Auto-Smart` / `Start` / `End`)
	- Number System (`Decimal` / `Hexadecimal` / `Roman`)
	- Destination association status (for Incremental Destination)
	- Clear association for active folder (for Incremental Destination)
	- Clear association hotkey bind (for Incremental Destination)

Mode settings are currently persisted in `ExtraClipboard.ini` under `[SlotModes]` and can be switched quickly through the tray menu.

Notes:

- Per-slot hotkeys are only active up to current Slot Count.
- Slot hotkeys always work for slots 1-9; using a higher slot auto-expands Slot Count.
- Incremental mode `auto-smart` only increments when exactly one numeric token is found at start or end; if both are present it safely skips.
- If incremental mode cannot find a supported number, it pastes original content and shows a tooltip near the mouse.
- Incremental Destination mode copies the source file to the active destination folder using the next number in a detected/selected destination family.
- When multiple destination families exist, selection now opens as a clickable list (OK/double-click) instead of typed index.
- Destination folder resolution is focus-strict: it uses the currently focused file-manager window context and will not silently fallback to background/remembered folders.
- File Pilot destination folders are resolved from focused window title context (including relative paths like `Documents\\...`), then validated on disk.
- Per-slot destination-family association is remembered per folder and can be cleared by tray action or configured slot hotkey.
- When destination folder scan finds multiple families and no association exists, the clickable family picker is shown with a smart preselected row.
- When a valid association exists for the selected folder/slot segment, it is reused for continuous pasting.

Association behavior:

- First time in a folder with multiple families/segments: picker is shown to choose the target entry.
- After selecting one entry, that folder+slot association is reused for continuous pasting (no picker each time).
- Associations are validated against the currently selected family segment boundaries; stale out-of-range cursors are ignored.
- If the last-created destination file is deleted, cursor recovery can recreate that missing number on the next paste.
- Use clear-association action/hotkey to force re-selection.

Gapped numbering behavior:

- Destination families are segmented by real contiguous numeric runs (example: `1-16` and `19-20` become separate picker entries).
- If a selected segment has discontinuous numbering and no reusable cursor, destination mode prompts for start number.
- The selected start point is remembered via association (`lastNumber`) for continuous pasting in that folder/slot.
- Start options are segment boundaries (for decrease, starts from segment minimum; for increase, from segment maximum).

Destination direction:

- Incremental Destination mode now supports both directions via mode Operation:
	- `Increase`: next free value from current/selected upper progression.
	- `Decrease`: next free value from current/selected lower progression.
- Direction-aware association memory is isolated (`lastDirection`), so switching between Increase/Decrease does not reuse an incompatible start cursor.
- When decrease/increase walks into an occupied contiguous range, it jumps below the current minimum / above the current maximum to continue progression predictably.

Same-folder source fallback:

- If source path metadata is missing but slot text is a filename token, destination mode resolves source against the focused destination folder (enables same-folder file-manager workflows).
- To edit a slot mode from Settings: pick `Config Slot`, change values, then click `Save`.
- Hotkeys remain active while Settings is open; only active binding capture temporarily isolates hotkeys to prevent contamination.
- In settings, click `Bind` then press the combo directly in that row's live key field.
- Click `Clear` to remove a row's hotkey binding.
- On upgrade, old auto-generated slot bindings are automatically cleared.
- Hotkey validation blocks duplicates across active main + per-slot hotkeys.

## Debugging and Logs

- Log file: `logs/ExtraClipboard.log`
- Log levels: `INFO`, `WARN`, `ERROR`, `DEBUG`
- `DEBUG` entries are controlled by the settings checkbox
- Core operation logs include timing and payload size when available
- Hotkey registration/unregistration and slot routing are logged for diagnosis

## Future Expansion Direction

The slot engine already supports `SlotCount` and `ActiveSlot` internally. Adding dedicated hotkeys per slot or slot switching UI can be implemented without changing clipboard core behavior.
