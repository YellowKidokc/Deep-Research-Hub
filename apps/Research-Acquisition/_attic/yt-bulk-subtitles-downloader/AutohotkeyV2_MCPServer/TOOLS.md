# AutoHotkey v2 MCP Server — Tool Reference

All tools are exposed under the MCP namespace `mcp__autohotkey-v2__*`. Tools marked **async** don't block other MCP work.

---

## Script Execution & Validation

### `validate_ahk_syntax(script_content, action_description?, workspace?)` — async
Runs `AutoHotkey64.exe /Validate /ErrorStdOut` against the script content. Returns `"Syntax validation passed..."` or the error text.
- **Catches:** tokenizer errors, missing `#Include` paths, missing `<Lib>` includes, undefined identifiers in some cases.
- **Blind spots:** does NOT enforce `#Requires`, does NOT detect top-level `throw`, does NOT detect runtime errors. *Pass `/Validate` ≠ "will run."*
- Always pair with `run_ahk_script` for true confidence.

### `run_ahk_script(script_content, timeout_seconds=3, action_description?, workspace?)` — async
Writes content to a temp `.ahk`, executes it with `/ErrorStdOut`, returns `{stdout, stderr, exit_code}`. Other MCP calls are NOT blocked while this runs.
- `exit_code = -1` means the timeout fired (script may have popped a blocking MsgBox).
- `exit_code = 2` is AHK's load-time-error code; `stderr` will have the line number.

### `inspect_active_window(workspace?)` — async
Returns `{title, class, exe}` of the currently active window. Useful for orienting before automation.

---

## Library / Codebase Navigation

### `search_global_library(query, mode="auto", limit=20, offset=0)`
Searches the user's `mylib` (default `C:\Users\AA\Documents\AHK\mylib`).
- **`mode="symbol"`** — structured `{name, kind, file, line, signature}` from a prebuilt index of classes, functions, and methods. Use first when looking up a class or function name.
- **`mode="text"`** — substring grep over file contents.
- **`mode="auto"`** — symbol first, falls back to text on no hits.
- Pagination via `limit` (1–200) + `offset`. Index is mtime-invalidated.

---

## Configuration & History

| Tool | Purpose |
|---|---|
| `configure_paths(ahk_path?, lib_path?, ...)` | Update server config (AHK exe, library, history dir) at runtime; persists to config.json. |
| `update_server_config(ahk_path, lib_path)` | Convenience wrapper for the two most-used paths. |
| `get_action_history(limit=20)` | Read recent tool actions. Workspace-scoped if logged with a workspace. |
| `restore_action(action_id, target_path)` | Recover a past script payload to disk. |

History writes are **file-locked + atomic** (msvcrt + tempfile + os.replace). On corruption, the bad file is moved aside as `history.corrupt-<ISO>.json`.

---

## Process Management

### `list_ahk_processes()`
Enumerates every running AutoHotkey*.exe via ctypes `EnumWindows` + `InternalGetWindowText` (cached window text — won't hang on misbehaving windows). Returns `[{pid, exe, script_path, title, hwnd, started_at}]`.

### `find_ahk_script(name_or_substring)`
Case-insensitive substring filter over `list_ahk_processes()`. Resolves "my snipping script" → PID without asking the user.

### `kill_ahk_script(pid, force=False, timeout_seconds=1.0)`
Graceful TerminateProcess; escalates to `taskkill /F /PID` if still alive after `timeout_seconds` or `force=True`. Logged to action history.

### `get_ahk_version(path?)`
Reads `FileVersion` from the AHK exe (no subprocess spawned). Cached per-path.

---

## DBGp Live Debugging (Multi-Session)

The MCP supports **multiple concurrent debug sessions**. Every `dbg_*` tool accepts an optional `session_id`. With one session, omit it (singleton fallback). With several, pass `session_id` explicitly. Use different `port` values (9005, 9006, 9007, ...) when attaching in parallel.

### Connection management

| Tool | Purpose |
|---|---|
| `dbg_attach(pid, port=9005, timeout=5)` | Send `AHK_ATTACH_DEBUGGER` to a running script and connect. Returns `{session_id, pid, port, status}`. Target must NOT already have a debugger. Cannot cross UAC. |
| `dbg_launch(path, port=9005, timeout=5)` | Spawn a script under `/Debug=...` and connect immediately. Catches load-time errors that prevent attach. |
| `dbg_detach(session_id?)` | Stop debugging; script resumes normally. |
| `dbg_close_session(session_id)` | Force-close + remove from registry without sending detach. |
| `dbg_list_sessions()` | List all `{session_id, pid, port, status}`. |
| `dbg_status(session_id?)` | Current status (`break`, `running`, `stopped`, ...) of a session. |

### Execution control

| Tool | Purpose |
|---|---|
| `dbg_break(session_id?)` | Pause execution. |
| `dbg_continue(mode, session_id?)` | `mode` ∈ `run`, `step_over`, `step_into`, `step_out`. |
| `dbg_stack(session_id?)` | Current call stack (frames with file/line/function). |

### State inspection

| Tool | Purpose |
|---|---|
| `dbg_get_vars(context=0, depth=0, session_id?)` | All variables. `context=0` locals, `context=1` globals. |
| `dbg_get_var(name, context=0, depth=0, session_id?)` | One variable by name. |
| `dbg_set_var(name, value, session_id?)` | Write a variable live. |
| `dbg_eval(expression, session_id?)` | Evaluate any AHK expression. **Only works when paused inside a function** — set a breakpoint first if paused at top level. |

### Breakpoints

| Tool | Purpose |
|---|---|
| `dbg_set_breakpoint(file, line, session_id?)` | Add a line breakpoint. |
| `dbg_list_breakpoints(session_id?)` | List active breakpoints. |
| `dbg_remove_breakpoint(breakpoint_id, session_id?)` | Remove one. |

### Source & I/O

| Tool | Purpose |
|---|---|
| `dbg_get_source(file?, begin_line?, end_line?, session_id?)` | Retrieve script source from the target. |
| `dbg_stdout(mode=1, session_id?)` | Forward script stdout to the debug session. `mode` 0/1/2 = none/copy/redirect. |

---

## Workflow Recipes

**"My script is broken"**
1. `validate_ahk_syntax(content)` — quick parser pass.
2. `run_ahk_script(content)` — actual load + run; only this catches `#Requires` mismatches and top-level `throw`.

**"Debug a running script"**
1. `find_ahk_script("name")` → PID.
2. `dbg_attach(pid)` → capture `session_id`.
3. `dbg_break()`, `dbg_stack()`, `dbg_get_vars(context=1)` to inspect.
4. `dbg_set_breakpoint(file, line)` + `dbg_continue("run")` to land in a function for `dbg_eval`.
5. `dbg_detach()` when done.

**"Catch a load-time error"**
- `dbg_launch(path)` instead of `dbg_attach` — connects under `/Debug` so even a script that dies on `#Include` can be inspected. *(Known caveat: if the process exits before the DBGp handshake, `dbg_launch` currently times out instead of surfacing stderr — pair with `run_ahk_script` for now.)*

**"Two scripts at once"**
- `dbg_attach(pid_a, port=9005)` → `sid_a`
- `dbg_attach(pid_b, port=9006)` → `sid_b`
- Pass `session_id=sid_a` / `sid_b` on every subsequent call.

---

## Known Limitations

- `validate_ahk_syntax` is a parser, not a loader — passes scripts that AHK refuses to run (top-level `throw`, `#Requires` mismatches). Always run for true validation.
- `dbg_launch` doesn't surface subprocess stderr if the script dies before the DBGp handshake — it times out instead.
- `run_ahk_script` returns `exit_code=-1` when a script pops a blocking MsgBox (including AHK's default error dialog) — looks like a timeout, not a runtime error.
- DBGp cannot cross UAC boundaries (non-admin → admin process).
- DBGp requires the target to NOT already have a debugger (VS Code, SciTE, etc. block attach).
