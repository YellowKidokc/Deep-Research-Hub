# AutoHotkey v2 MCP Server

**Created by [Xeo786](https://github.com/Xeo786)**

## What is it?
This is a custom **Model Context Protocol (MCP)** server built in Python, designed specifically to bridge the gap between AI coding assistants and the AutoHotkey v2 ecosystem on Windows. 

MCP is an open standard that enables AI models to connect securely to local data sources and tools. This server exposes powerful, specialized tools to the AI, granting it the context, execution, and **live debugging** capabilities needed to write perfect AHK scripts.

## Why was it created?
AutoHotkey v2 introduced strict object-oriented syntax, removing graceful failures and silent errors that existed in v1. When an AI tries to write AHK code blindly, it often:
1. Mixes up v1 and v2 syntax.
2. Cannot tell if the target window title or class is correct.
3. Cannot verify if the script even launches without crashing.
4. Doesn't know what custom libraries the user already has installed.
5. **Cannot debug running scripts** to diagnose issues.
6. **No record of past work**: Without history, it's hard to "bring back" or review a script the AI ran 5 minutes ago.

This server solves **all** of these problems by giving the AI eyes (inspect active window), knowledge (search library), hands (validate and run), a **full debugger** (DBGp protocol integration), and now a **complete action history** with a dedicated GUI.

---

## How does it help the AI? (Features)

The server exposes tools in two categories:

### Core Tools

#### 1. `validate_ahk_syntax`
- **What it does:** Runs external AHK code through AutoHotkey's `/Validate` switch, sending syntax errors to `/ErrorStdOut`.
- **How it helps:** The AI can verify that the code it just wrote is syntactically sound, catching missing braces, undefined variables, or v1 legacy commands *before* handing the script to the user.

#### 2. `run_ahk_script`
- **What it does:** Executes a temporary script and forcefully captures standard output (`FileAppend(text, "*")`) and runtime errors, strictly enforcing a timeout (e.g., 3 seconds) to prevent infinite loops.
- **How it helps:** The AI can test logical behavior (e.g., "Does this Regex expression actually match correctly in AHK?"). Fast feedback loops mean fewer broken scripts.

#### 3. `inspect_active_window`
- **What it does:** Runs a tiny script returning the Title, Class (`ahk_class`), and Executable (`ahk_exe`) of whatever window the user currently has focused.
- **How it helps:** Finding correct window hooks is tedious. The user can just focus an app, ask the AI to "write a script for my active window," and the AI can pull the exact selectors needed for `WinActivate` or `ControlSend`.

#### 4. `search_global_library`
- **What it does:** Searches the user's master AHK library. Two modes:
    - **`mode="symbol"`** — looks up class / function / method *names* in a prebuilt index, returning `{name, kind, file, line, signature}`. Fast, structured, and the right choice when you know what you're looking for by name (e.g., `cJSON`, `Logger.Info`, `WinClip`).
    - **`mode="text"`** — substring grep over file contents (legacy behavior), returning `{file, line, context}`. Right for searching for code fragments or strings that aren't symbol names.
    - **`mode="auto"`** (default) — try symbol first, fall back to text. Supports `limit` (1-200) and `offset` for pagination.
- **How it helps:** Instead of reinventing the wheel (like creating a new WebSocket class), the AI can find the user's existing custom wrappers in milliseconds and reuse them — by symbol name, with file:line precision.

#### 5. `configure_paths`
- **What it does:** Sets and persists the `AHK_PATH` and `GLOBAL_LIB_PATH` to the user's `AppData`.
- **New Feature:** Supports `use_dialog=True` to pop up native Windows file/directory selection dialogs on the host machine for easy setup.
- **How it helps:** Allows the server to remain portable and tool-neutral, letting the user (or AI) configure the exact binaries and libraries to use without editing the source code.

#### 6. `get_action_history` & `restore_action`
- **What it does:** Allows the AI to retrieve metadata about past scripts it has run and "restore" them (copy from history) back to its current workspace.
- **How it helps:** Enables the AI to recall previous successful logic or bring back a script the user previously saw but didn't save.

#### 7. Process Management
- **What it does:** Discover, identify, and terminate AutoHotkey processes without leaving the chat.
- **How it helps:** Removes the friction of asking the user to find a PID before `dbg_attach`; lets the AI clean up runaway scripts itself.

| Tool | Description |
|---|---|
| `list_ahk_processes()` | Enumerate every running AHK script via top-level `ahk_class AutoHotkey` windows. Returns `{pid, exe, title, script_path, hwnd}` for each. The AHK main-window title's default format `'<scriptpath> - AutoHotkey v<ver>'` is parsed into `script_path`. |
| `find_ahk_script(name_or_substring)` | Convenience wrapper over `list_ahk_processes()` that filters by case-insensitive substring match against `script_path` and `title`. Use this before `dbg_attach` when the user mentions "my script" without a PID. |
| `kill_ahk_script(pid, force?, timeout_seconds?)` | Terminate a script by PID. Default sends `WM_CLOSE` (graceful) and waits up to `timeout_seconds`; falls back to `taskkill /F` if it doesn't exit. Pass `force=True` to skip straight to force-kill. |
| `get_ahk_version(path?)` | Return the version of an AHK exe (defaults to the configured `AHK_PATH`). Cached per path for the server's lifetime. |

---

## Action History & GUI

The server now automatically logs every script execution to `%AppData%\AutoHotkey_MCP_Server\history\`.

### MCP Action History GUI
A standalone AHK v2 GUI is included (`MCP Action History.ahk`) within the server directory.
- **Features:**
    - **Live View:* Browse all past actions in a sortable ListView.
    - **Preview:** Inspect the source code of any historical action.
    - **Workspace Affinity:** Each action logs the workspace (CWD) where it was run.
    - **One-Click Restore:** Quickly restore any script back to its original workspace with a timestamped filename.
    - **History Management:** Delete selected entries or wipe the entire history to keep your workspace clean.

---

### DBGp Live Debugger Tools

These tools allow the AI to **attach to and debug running AutoHotkey scripts** in real-time using the [DBGp protocol](https://xdebug.org/docs/dbgp). This is the same protocol used by SciTE4AutoHotkey and VS Code debug adapters.

**Concurrent sessions:** Every `dbg_*` tool accepts an optional `session_id` parameter. `dbg_attach` and `dbg_launch` register their connection in a session registry (id form: `'pid:{pid}@{port}'`) and return that id. With one session active, `session_id` may be omitted (singleton fallback). With multiple sessions, every call must pass `session_id` to disambiguate. Different sessions run truly in parallel — breaking one does not affect another. Subprocess execution (`run_ahk_script`, `validate_ahk_syntax`) is also async, so a long-running script no longer blocks the MCP server.

#### Connection Management
| Tool | Description |
|---|---|
| `dbg_attach(pid, port?, timeout?)` | Attach to a running AHK script by PID. Starts a TCP listener, sends `AHK_ATTACH_DEBUGGER`, registers the session, and returns `{session_id, pid, port, status, file, ...}`. Run multiple times on different ports for concurrent debug sessions. |
| `dbg_launch(path, port?, timeout?)` | Launch an AHK script under `/Debug` and connect immediately. Useful for catching load-time errors (e.g. syntax errors) that prevent normal startup. Returns the same shape as `dbg_attach`. |
| `dbg_detach(session_id?)` | Detach a session, letting the script continue normally. Removes it from the registry. |
| `dbg_close_session(session_id)` | Force-close without sending detach (use when the script is already gone). |
| `dbg_list_sessions()` | List every active session with id, pid, port, connected status, and current file. |
| `dbg_status(session_id?)` | Get the current debugger state (`break`, `running`, `stopped`, etc.) for a session. |

All execution / inspection / breakpoint / I/O tools take the same optional `session_id` parameter as the connection-management tools above.

#### Execution Control
| Tool | Description |
|---|---|
| `dbg_break(session_id?)` | Pause execution of a running script. |
| `dbg_continue(mode, session_id?)` | Resume execution: `run`, `step_into`, `step_over`, or `step_out`. |

#### Inspection & Evaluation
| Tool | Description |
|---|---|
| `dbg_stack(session_id?)` | Get the current call stack (file, line, function). |
| `dbg_get_vars(context, depth, session_id?)` | Get all variables in a context (`0`=Local, `1`=Global) at a stack depth. Filters AHK built-in classes automatically. |
| `dbg_get_var(name, context, depth, session_id?)` | Get a single variable by name. |
| `dbg_set_var(name, value, session_id?)` | Set a variable's value at runtime. |
| `dbg_eval(expression, session_id?)` | Evaluate any AHK expression in the current context (must be paused inside a function). |
| `dbg_get_source(file, begin_line, end_line, session_id?)` | Retrieve source code from the debugged script. |

#### Breakpoints
| Tool | Description |
|---|---|
| `dbg_set_breakpoint(file, line, session_id?)` | Set a line breakpoint. |
| `dbg_list_breakpoints(session_id?)` | List all active breakpoints. |
| `dbg_remove_breakpoint(breakpoint_id, session_id?)` | Remove a breakpoint by ID. |

#### I/O
| Tool | Description |
|---|---|
| `dbg_stdout(mode, session_id?)` | Redirect script stdout to the debugger: `0`=disable, `1`=copy, `2`=redirect. |

---

## Example Workflows

### Basic: Write and Validate a Script

**User:** "Write a script that closes my active window and logs it using my `MyLogger.ahk` library."

**AI Process (Under the hood):**
1. **AI calls `inspect_active_window`** -> Finds out the user is in "Notepad" (`ahk_class Notepad`).
2. **AI calls `search_global_library("MyLogger")`** -> Discovers it needs to use `Logger.Info("Closed")`.
3. **AI writes the draft script.**
4. **AI calls `validate_ahk_syntax`** -> Realizes it forgot a closing brace.
5. **AI fixes the code and gives the user a guaranteed-to-work script.**

### Advanced: Debug a Stuck Script

**User:** "My UIA-tester script seems stuck. Can you figure out why?"

**AI Process:**
1. **AI calls `find_ahk_script("UIA-tester")`** -> Returns `[{pid: 12345, script_path: "...UIA-tester.ahk", ...}]`.
2. **AI calls `dbg_attach(pid=12345)`** -> Connects to the running script.
3. **AI calls `dbg_break()`** -> Pauses execution.
4. **AI calls `dbg_stack()`** -> Sees script is stuck in `MyFunction()` at line 42.
5. **AI calls `dbg_get_vars(context=0)`** -> Inspects local variables, finds `retryCount = 999`.
6. **AI calls `dbg_eval("retryCount := 0")`** -> Resets the counter.
7. **AI calls `dbg_continue(mode="run")`** -> Resumes the script.
8. **AI calls `dbg_detach()`** -> Disconnects cleanly.
9. **AI explains:** "Your script was stuck in an infinite retry loop. I reset `retryCount` to 0."

### Restoration: "Bring back the script you ran earlier"

**User:** "Can you bring back that window inspection script you ran a few minutes ago? I want to keep it in my project."

**AI Process:**
1. **AI calls `get_action_history`** -> Finds the ID of the recent `inspect_active_window` tool call.
2. **AI calls `restore_action(id, "s:/path/to/project/InspectHelper.ahk")`** -> Copies the script from history back to the user's project folder.
3. **AI explains:** "I've restored that script to your project as `InspectHelper.ahk`."

---

## Installation

1. Install Python 3.10+.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Configure your AutoHotkey and Library paths using the `configure_paths` tool.

---

## Connecting to Antigravity

Antigravity can leverage this server to provide expert AutoHotkey assistance. To connect this server to your Antigravity instance, add it to your `antigravity.json` or your global MCP configuration:

```json
{
  "mcpServers": {
    "ahk-v2-server": {
      "command": "python",
      "args": ["path/to/server.py"],
      "env": {
        "AHK_PATH": "C:\\Program Files\\AutoHotkey\\v2\\AutoHotkey64.exe",
        "GLOBAL_LIB_PATH": "C:\\Users\\YourUser\\Documents\\AutoHotkey\\Lib"
      }
    }
  }
}
```
### Zero Configuration (Antigravity Only)
If you are an **Antigravity** user, you can skip manual JSON editing:
1. **Clone** this repository locally.
2. Open an Antigravity chat and tell it the **absolute path** to the repo.
3. Ask it to: *"Connect to the MCP server in this directory."*

**The Experience:**
Once connected, try asking:
> *"Can you use the AutoHotkey v2 MCP? How does it feel to have these tools at your disposal?"*

You will see that with these "eyes and hands," Antigravity's ability to automate your Windows environment becomes exponentially more effective—transforming from a guessing assistant into a precise systems architect.

### What can you ask Antigravity?
Once connected, you can leverage the full power of AutoHotkey through simple prompts:
- **System Awareness**: *"Inspect my active window and tell me its class."*
- **Live Debugging**: *"Attach to my script (PID 1234) and find out why it's stuck."*
- **Library Integration**: *"Write a new automation script using my existing local libraries."*
- **Office Automation**: *"Highlight row X on my active Excel workbook using ComObject."*
- **Web Automation**: *"Use Rufaydium to create a Chrome session and inspect the target webpage."*
- **Error Resolution**: *"I have an AutoHotkey error popup; please diagnose and fix it."*
- **Complex Workflows**: *"Scan my document, extract all keywords, and create a summary table in a new Excel workbook."*
- **History Management**: *"Show me the last 5 things you did,"* or *"Restore the script from my last execution to this folder."*

---

## License
This project is licensed under the **Creative Commons Attribution 4.0 International (CC BY 4.0)** license. You are free to share and adapt the work for any purpose, including commercially, as long as you give appropriate credit. See the [LICENSE](LICENSE) file for details.
