# AI-HUB Companion Integrations

Running `AI-HUB.ahk` starts these three source-preserved companion tools:

1. `AlwaysOnTop` — configurable global window pinning.
2. `ExtraClipboard` — independent clipboard slots and incremental file-copy modes.
3. `LLM-AutoHotkey-Assistant` — highlighted-text prompts through OpenRouter.

They intentionally run as separate AutoHotkey v2 processes. This gives David one launcher while preventing the projects' globals, GUI state, and hotkeys from colliding inside one interpreter.

Enable or disable each application in `..\config\integrations.ini`.

## First-run notes

- AlwaysOnTop opens its trigger configuration when no hotkey has been saved.
- ExtraClipboard ships with no copy/paste hotkeys assigned; configure them from its tray menu.
- The LLM assistant uses the backtick key for its prompt menu and needs an OpenRouter API key. Copy `LLM-AutoHotkey-Assistant\llm_api_key.example.txt` to `llm_api_key.local.txt` and replace its contents with the key. The local key file is ignored by Git. The `OPENROUTER_API_KEY` environment variable is also supported.

## Source and licensing

- AlwaysOnTop is by the-Automator and is preserved with its CC BY 4.0 attribution header.
- LLM AutoHotkey Assistant retains its `LICENSE` and `THIRD-PARTY-LICENSES.txt` files.
- ExtraClipboard is preserved as supplied, including its README and source dependencies; the compiled `ExtraClipboard.exe`, old logs, and machine-local `.claude` settings were intentionally not copied.
- WinMacros was not integrated because the supplied folder contains only a compiled executable and uninstaller, not reusable source code.
