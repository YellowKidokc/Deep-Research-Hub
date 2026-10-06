# =========================================================================== #
# AutoHotkey v2 MCP Server                                                    #
# Want a clear path for learning AutoHotkey?                                  #
# Take a look at our AutoHotkey courses here: the-Automator.com/Discover      #
# They're structured in a way to make learning AHK EASY                       #
# And come with a 200% moneyback guarantee so you have NOTHING to risk!       #
# =========================================================================== #
# @author      Xeo786                                                         #
# @version     0.1.0                                                          #
# @copyright   Copyright (c) 2026 the-Automator                               #
# @link        https://the-Automator.com/AHKmcp                               #
# @created     2026-05-12                                                     #
# @modified    2026-05-12                                                     #
# @description MCP server exposing AutoHotkey v2 tooling (run, validate,      #
#              debug via DBGp, process control, library search) to LLM        #
#              clients over the Model Context Protocol.                       #
# =========================================================================== #
# @license     CC BY 4.0                                                      #
# =========================================================================== #
#   This work by the-Automator.com is licensed under CC BY 4.0
#
#   Attribution - You must give appropriate credit, provide a link to the license,
#   and indicate if changes were made.
#
#   You may do so in any reasonable manner, but not in any way that suggests the licensor
#   endorses you or your use.
#
#   No additional restrictions - You may not apply legal terms or technological measures that
#   legally restrict others from doing anything the license permits.

import os
import subprocess
import tempfile
import glob
import shutil
import uuid
import json
import time
import ctypes
import contextlib
import asyncio
from ctypes import wintypes
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Iterator
from mcp.server.fastmcp import FastMCP
from dbgp_client import (
    DbgpClient, DbgpError, DbgpConnectionError, get_registry,
)
from config import (
    resolve_ahk_path, resolve_lib_path, save_config, get_config, configure_paths,
    HISTORY_DIR, LIBRARY_INDEX_FILE,
)
import library_index

# Create the FastMCP server
mcp = FastMCP("AutoHotkey v2 MCP Server")

AHK_PATH = resolve_ahk_path()
GLOBAL_LIB_PATH = resolve_lib_path()

def _create_temp_ahk(script_content: str) -> str:
    """Helper to write content to a temp file and return its path."""
    fd, path = tempfile.mkstemp(suffix=".ahk", text=True)
    with os.fdopen(fd, 'w', encoding='utf-8') as f:
        f.write(script_content)
    return path

@contextlib.contextmanager
def _file_lock(lock_path: Path, timeout: float = 5.0) -> Iterator[None]:
    """Cross-process exclusive lock on a sidecar lock file.
    Windows: msvcrt.locking on byte 0; POSIX: fcntl.flock. The lock auto-releases
    if the holder process dies. Raises OSError on timeout.
    """
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    fp = open(lock_path, 'a+b')
    try:
        deadline = time.monotonic() + timeout
        if os.name == 'nt':
            import msvcrt
            while True:
                try:
                    msvcrt.locking(fp.fileno(), msvcrt.LK_NBLCK, 1)
                    break
                except OSError:
                    if time.monotonic() >= deadline:
                        raise OSError(f"Could not acquire {lock_path} within {timeout}s")
                    time.sleep(0.05)
        else:
            import fcntl
            fcntl.flock(fp.fileno(), fcntl.LOCK_EX)
        yield
    finally:
        try:
            if os.name == 'nt':
                import msvcrt
                fp.seek(0)
                msvcrt.locking(fp.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl
                fcntl.flock(fp.fileno(), fcntl.LOCK_UN)
        except Exception:
            pass
        fp.close()


def _read_history_safe(index_file: Path) -> List[Dict[str, Any]]:
    """Read history.json. On corruption, move it aside with an ISO timestamp
    so the next write doesn't overwrite a previous corruption event.
    """
    if not index_file.exists():
        return []
    try:
        with open(index_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except Exception as e:
        ts = datetime.now().strftime("%Y%m%dT%H%M%S")
        corrupt_path = index_file.with_name(f"history.corrupt-{ts}.json")
        try:
            shutil.move(str(index_file), str(corrupt_path))
            print(f"History index corrupted, moved to: {corrupt_path} ({e})")
        except Exception as move_err:
            print(f"History index corrupted but move failed: {move_err}")
        return []


def _atomic_write_json(target_path: Path, data: Any) -> None:
    """Write JSON atomically: tempfile in same dir + os.replace."""
    target_dir = str(target_path.parent)
    fd, tmp_path = tempfile.mkstemp(prefix=".history-", suffix=".tmp", dir=target_dir)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
        os.replace(tmp_path, target_path)
    except Exception:
        try:
            os.remove(tmp_path)
        except Exception:
            pass
        raise


def _log_action(script_content: str, tool_name: str, action_description: str, result: Optional[Dict[str, Any]] = None, workspace: Optional[str] = None):
    """Logs the script and metadata to the history directory.
    File-locked + atomic write so concurrent tool calls don't corrupt history.json.
    """
    try:
        now = datetime.now()
        date_folder = now.strftime("%Y-%m-%d")
        target_dir = HISTORY_DIR / date_folder
        target_dir.mkdir(parents=True, exist_ok=True)

        action_id = str(uuid.uuid4())
        filename = f"{now.strftime('%H-%M-%S')}_{action_id[:8]}.ahk"
        script_path = target_dir / filename
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(script_content)

        first_line = script_content.split('\n')[0].strip() if script_content else ""
        if len(first_line) > 100:
            first_line = first_line[:97] + "..."

        entry = {
            "id": action_id,
            "timestamp": now.isoformat(),
            "tool": tool_name,
            "description": action_description,
            "script_file": str(script_path),
            "workspace": workspace if workspace else os.getcwd(),
            "summary": first_line,
            "exit_code": result.get("exit_code") if result else None,
        }

        index_file = HISTORY_DIR / "history.json"
        lock_file = HISTORY_DIR / ".history.lock"
        with _file_lock(lock_file):
            history = _read_history_safe(index_file)
            history.insert(0, entry)
            if len(history) > 500:
                history = history[:500]
            _atomic_write_json(index_file, history)

    except Exception as e:
        # Non-critical: don't fail the tool call if logging fails
        print(f"Logging failed: {e}")

@mcp.tool()
def configure_paths(
    ahk_path: Optional[str] = None, 
    lib_path: Optional[str] = None, 
    use_dialog: bool = False
) -> Dict[str, str]:
    """
    Configure the paths for AutoHotkey and the Global Library.
    Settings are persisted to the user's AppData.
    If 'use_dialog' is True, native selection dialogs will be shown on the host.
    """
    from config import prompt_path
    
    config = get_config()
    
    if use_dialog:
        if not ahk_path:
            p = prompt_path("Select AutoHotkey64.exe", is_file=True)
            if p:
                ahk_path = p
        if not lib_path:
            p = prompt_path("Select Global Library Folder", is_file=False)
            if p:
                lib_path = p

    if ahk_path:
        config["ahk_path"] = ahk_path
    if lib_path:
        config["lib_path"] = lib_path
    
    if ahk_path or lib_path:
        save_config(config)
    
    # Update current session globals
    global AHK_PATH, GLOBAL_LIB_PATH
    if ahk_path:
        AHK_PATH = ahk_path
    if lib_path:
        GLOBAL_LIB_PATH = lib_path
        
    return {
        "status": "success",
        "ahk_path": AHK_PATH,
        "lib_path": GLOBAL_LIB_PATH
    }

_CREATE_NO_WINDOW = 0x08000000 if os.name == 'nt' else 0


async def _run_ahk_async(args: List[str], timeout: float) -> Dict[str, Any]:
    """Run an AHK process asynchronously, capturing stdout/stderr.
    Returns {stdout, stderr, exit_code} or {..., 'error': 'timeout'} on timeout.
    """
    proc = await asyncio.create_subprocess_exec(
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        creationflags=_CREATE_NO_WINDOW,
    )
    try:
        stdout_b, stderr_b = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        try:
            proc.kill()
            stdout_b, stderr_b = await proc.communicate()
        except Exception:
            stdout_b, stderr_b = b"", b""
        return {
            "stdout": (stdout_b or b"").decode("utf-8", errors="replace"),
            "stderr": (stderr_b or b"").decode("utf-8", errors="replace"),
            "exit_code": -1,
            "error": f"Script execution timed out after {timeout} seconds.",
        }
    return {
        "stdout": (stdout_b or b"").decode("utf-8", errors="replace"),
        "stderr": (stderr_b or b"").decode("utf-8", errors="replace"),
        "exit_code": proc.returncode if proc.returncode is not None else -2,
    }


@mcp.tool()
async def validate_ahk_syntax(script_content: str, action_description: str = "Syntax Validation", workspace: Optional[str] = None) -> str:
    """
    Validates AutoHotkey v2 syntax without executing the script.

    AGENT PROTOCOL: You MUST pass the absolute path of the current active project
    to the 'workspace' parameter. This ensures the action is logged to the correct
    project history for the user.
    """
    temp_path = _create_temp_ahk(script_content)
    try:
        result = await _run_ahk_async(
            [AHK_PATH, "/ErrorStdOut", "/Validate", temp_path],
            timeout=15.0,
        )
        if result["exit_code"] == 0:
            status_msg = "Syntax validation passed successfully. Exit code 0."
        else:
            status_msg = f"Syntax Error (Exit Code {result['exit_code']}):\n{result['stderr'].strip()}"

        _log_action(script_content, "validate_ahk_syntax", action_description,
                    {"exit_code": result["exit_code"]}, workspace)
        return status_msg
    except Exception as e:
        return f"Execution Error: {str(e)}"
    finally:
        try:
            os.remove(temp_path)
        except Exception:
            pass


@mcp.tool()
async def run_ahk_script(script_content: str, timeout_seconds: int = 3, action_description: str = "Manual Script Execution", workspace: Optional[str] = None) -> Dict[str, Any]:
    """
    Runs an AutoHotkey v2 script asynchronously with a strictly enforced timeout.
    Returns stdout, stderr, and exit_code. Other MCP tool calls are NOT blocked
    while this runs.

    AGENT PROTOCOL: You MUST pass the absolute path of the current active project
    to the 'workspace' parameter. This ensures the action is logged to the correct
    project history for the user.
    """
    temp_path = _create_temp_ahk(script_content)
    try:
        result = await _run_ahk_async(
            [AHK_PATH, "/ErrorStdOut", temp_path],
            timeout=float(timeout_seconds),
        )
        _log_action(script_content, "run_ahk_script", action_description, result, workspace)
        return result
    except Exception as e:
        return {
            "stdout": "",
            "stderr": str(e),
            "exit_code": -2,
            "error": "Failed to execute script.",
        }
    finally:
        try:
            os.remove(temp_path)
        except Exception:
            pass


@mcp.tool()
async def inspect_active_window(workspace: Optional[str] = None) -> Dict[str, str]:
    """
    Returns the Title, Class, and Process Name of the currently active window.

    AGENT PROTOCOL: You MUST pass the absolute path of the current active project
    to the 'workspace' parameter. This ensures the action is logged to the correct
    project history for the user.
    """
    script_content = '''#Requires AutoHotkey v2.0
#NoTrayIcon
try {
    title := WinGetTitle("A")
    cls := WinGetClass("A")
    exe := WinGetProcessName("A")
    FileAppend(title "`n" cls "`n" exe "`n", "*")
} catch as e {
    FileAppend("ERROR`n" e.Message "`n", "*")
}
'''
    result = await run_ahk_script(
        script_content, action_description="Inspect Active Window",
        timeout_seconds=2, workspace=workspace,
    )

    if result.get("exit_code") == 0 and result.get("stdout"):
        lines = result["stdout"].strip().split('\n')
        if len(lines) >= 3 and lines[0] != "ERROR":
            return {"title": lines[0], "class": lines[1], "exe": lines[2]}
        elif lines[0] == "ERROR":
            return {"error": "AHK Error", "details": "\n".join(lines[1:])}
        return {"error": "Unexpected output format", "raw_stdout": result["stdout"]}
    return {"error": "Failed to inspect active window.", "details": str(result)}

@mcp.tool()
def search_global_library(
    query: str,
    mode: str = "auto",
    limit: int = 20,
    offset: int = 0,
) -> Dict[str, Any]:
    """
    Search the global AutoHotkey library.

    mode='symbol' — match against indexed class/function/method names. Returns
        {name, kind, file, line, signature} for each hit.
    mode='text'   — substring grep over file contents. Returns
        {file, line, context} for each hit.
    mode='auto'   — try symbol first; fall back to text if no hits.

    limit: 1-200 results per call. offset: pagination start.
    """
    if not os.path.exists(GLOBAL_LIB_PATH):
        return {"error": f"Global library path not found: {GLOBAL_LIB_PATH}"}
    if not query:
        return {"error": "query is required"}
    if mode not in ("auto", "symbol", "text"):
        return {"error": f"invalid mode {mode!r}; must be 'auto', 'symbol', or 'text'"}

    limit = max(1, min(int(limit), 200))
    offset = max(0, int(offset))

    base = {
        "query": query,
        "requested_mode": mode,
        "limit": limit,
        "offset": offset,
        "lib_path": GLOBAL_LIB_PATH,
    }

    # Symbol mode (auto tries this first)
    if mode in ("auto", "symbol"):
        try:
            idx = library_index.get_index(Path(GLOBAL_LIB_PATH), LIBRARY_INDEX_FILE)
            sym_matches = idx.search(query, limit=limit, offset=offset)
            if sym_matches or mode == "symbol":
                return {
                    **base,
                    "actual_mode": "symbol",
                    "total_indexed": idx.total,
                    "count": len(sym_matches),
                    "matches": sym_matches,
                }
        except Exception as e:
            if mode == "symbol":
                return {**base, "error": f"symbol index failed: {e}"}
            # auto: fall through to text

    # Text mode (legacy substring grep)
    needle = query.lower()
    matches: List[Dict[str, Any]] = []
    skip = offset
    search_pattern = os.path.join(GLOBAL_LIB_PATH, "**", "*.ahk")
    for filepath in glob.glob(search_pattern, recursive=True):
        if len(matches) >= limit:
            break
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            for i, line in enumerate(lines):
                if needle in line.lower():
                    if skip > 0:
                        skip -= 1
                        continue
                    start = max(0, i - 1)
                    end = min(len(lines), i + 2)
                    context = "\n".join(l.rstrip() for l in lines[start:end])
                    rel = os.path.relpath(filepath, GLOBAL_LIB_PATH)
                    matches.append({"file": rel, "line": i + 1, "context": context})
                    if len(matches) >= limit:
                        break
        except Exception:
            continue

    return {
        **base,
        "actual_mode": "text",
        "count": len(matches),
        "matches": matches,
    }
    
@mcp.tool()
def update_server_config(ahk_path: str, lib_path: str) -> Dict[str, Any]:
    """
    Updates the server configuration with new AutoHotkey and Library paths.
    """
    return configure_paths(ahk_path, lib_path)

@mcp.tool()
def get_action_history(limit: int = 20) -> List[Dict[str, Any]]:
    """
    Returns the last N actions performed by the MCP server.
    """
    index_file = HISTORY_DIR / "history.json"
    if not index_file.exists():
        return []
    
    try:
        with open(index_file, "r", encoding="utf-8") as f:
            history = json.load(f)
            return history[:limit]
    except Exception as e:
        return [{"error": f"Failed to read history: {e}"}]

@mcp.tool()
def restore_action(action_id: str, target_path: str) -> Dict[str, str]:
    """
    Copies a previously performed action's script to a target file path.
    """
    index_file = HISTORY_DIR / "history.json"
    if not index_file.exists():
        return {"status": "error", "message": "No history found."}

    try:
        with open(index_file, "r", encoding="utf-8") as f:
            history = json.load(f)
        
        entry = next((e for e in history if e["id"] == action_id or e["id"].startswith(action_id)), None)
        if not entry:
            return {"status": "error", "message": f"Action ID {action_id} not found."}
        
        source_path = entry["script_file"]
        if not os.path.exists(source_path):
            return {"status": "error", "message": "Source script file no longer exists."}
        
        shutil.copy2(source_path, target_path)
        return {"status": "success", "message": f"Restored {action_id} to {target_path}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# ==========================================================================
# Process Management Tools
# ==========================================================================

def _process_exists(pid: int) -> bool:
    """Quick check whether a process with the given PID is alive (Windows)."""
    if pid <= 0:
        return False
    if os.name != 'nt':
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False
    try:
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = 0
        result = subprocess.run(
            ["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"],
            capture_output=True, text=True, timeout=3, encoding='utf-8', errors='replace',
            startupinfo=startupinfo,
        )
        return str(pid) in result.stdout and "No tasks" not in result.stdout
    except Exception:
        return False


def _parse_script_path_from_title(title: str) -> str:
    """AHK script main windows default to '<scriptpath> - AutoHotkey v<version>'."""
    if not title:
        return ""
    idx = title.rfind(" - AutoHotkey")
    if idx > 0:
        return title[:idx].strip()
    return ""


# --- Win32 enumeration ------------------------------------------------------
# Use ctypes directly. EnumWindows + InternalGetWindowText reads the title
# from the cached window text without sending WM_GETTEXT, so it never blocks
# on misbehaving target processes (an issue we hit when shelling to AHK).

if os.name == 'nt':
    _user32 = ctypes.WinDLL('user32', use_last_error=True)
    _kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)

    _WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    _user32.EnumWindows.argtypes = [_WNDENUMPROC, wintypes.LPARAM]
    _user32.EnumWindows.restype = wintypes.BOOL

    _user32.GetClassNameW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
    _user32.GetClassNameW.restype = ctypes.c_int

    _user32.InternalGetWindowText.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
    _user32.InternalGetWindowText.restype = ctypes.c_int

    _user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    _user32.GetWindowThreadProcessId.restype = wintypes.DWORD

    _kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    _kernel32.OpenProcess.restype = wintypes.HANDLE

    _kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    _kernel32.CloseHandle.restype = wintypes.BOOL

    _kernel32.QueryFullProcessImageNameW.argtypes = [
        wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD),
    ]
    _kernel32.QueryFullProcessImageNameW.restype = wintypes.BOOL

    _PROCESS_QUERY_LIMITED_INFORMATION = 0x1000


def _get_process_exe_path(pid: int) -> str:
    """Resolve a PID's full executable path via QueryFullProcessImageNameW."""
    if os.name != 'nt' or pid <= 0:
        return ""
    h = _kernel32.OpenProcess(_PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
    if not h:
        return ""
    try:
        buf = ctypes.create_unicode_buffer(1024)
        size = wintypes.DWORD(1024)
        if _kernel32.QueryFullProcessImageNameW(h, 0, buf, ctypes.byref(size)):
            return buf.value
        return ""
    finally:
        _kernel32.CloseHandle(h)


@mcp.tool()
def list_ahk_processes() -> List[Dict[str, Any]]:
    """
    Lists all running AutoHotkey scripts (uncompiled .ahk processes).

    Enumerates top-level windows of class 'AutoHotkey' (every AHK script has
    one, hidden or visible). Returns a list of {pid, exe, title, script_path,
    hwnd}. The script_path is parsed from the AHK main window title (default
    format '<scriptpath> - AutoHotkey v<version>'); scripts with custom titles
    yield an empty script_path.
    """
    if os.name != 'nt':
        return [{"error": "list_ahk_processes is Windows-only"}]

    seen_pids: set = set()
    found: List[Dict[str, Any]] = []
    self_pid = os.getpid()
    err_box: List[str] = []

    def callback(hwnd, _lparam):
        try:
            cls_buf = ctypes.create_unicode_buffer(64)
            if _user32.GetClassNameW(hwnd, cls_buf, 64) == 0:
                return True
            if cls_buf.value != "AutoHotkey":
                return True

            pid = wintypes.DWORD()
            _user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            pid_v = int(pid.value)
            if pid_v == 0 or pid_v == self_pid or pid_v in seen_pids:
                return True
            seen_pids.add(pid_v)

            title_buf = ctypes.create_unicode_buffer(512)
            _user32.InternalGetWindowText(hwnd, title_buf, 512)
            title = title_buf.value

            found.append({
                "pid": pid_v,
                "exe": _get_process_exe_path(pid_v),
                "title": title,
                "script_path": _parse_script_path_from_title(title),
                "hwnd": int(hwnd) if hwnd else 0,
            })
        except Exception as e:
            err_box.append(str(e))
        return True

    cb_ptr = _WNDENUMPROC(callback)
    if not _user32.EnumWindows(cb_ptr, 0):
        # EnumWindows returns FALSE on early exit OR error; check GetLastError
        last_err = ctypes.get_last_error()
        if last_err:
            return [{"error": f"EnumWindows failed: WinError {last_err}"}]
    if err_box:
        # Non-fatal — just annotate first error in the result
        return found + [{"warning": err_box[0]}]
    return found


@mcp.tool()
def find_ahk_script(name_or_substring: str) -> List[Dict[str, Any]]:
    """
    Find running AutoHotkey processes whose script_path or window title contains
    the given substring (case-insensitive). Convenience wrapper over
    list_ahk_processes for "find my script's PID before dbg_attach" workflows.
    """
    if not name_or_substring:
        return []
    needle = name_or_substring.lower()
    procs = list_ahk_processes()
    if procs and isinstance(procs[0], dict) and procs[0].get("error"):
        return procs
    return [
        p for p in procs
        if needle in (p.get("script_path") or "").lower()
        or needle in (p.get("title") or "").lower()
    ]


@mcp.tool()
def kill_ahk_script(pid: int, force: bool = False, timeout_seconds: float = 1.0) -> Dict[str, Any]:
    """
    Terminate an AutoHotkey process by PID.

    By default sends WM_CLOSE to the script's main window (graceful) and waits up
    to timeout_seconds; if it's still alive (or force=True), uses taskkill /F.

    Returns {ok, pid, was_running, method} or {ok: False, error}.
    """
    if pid <= 0:
        return {"ok": False, "error": "pid must be positive"}

    was_running = _process_exists(pid)
    if not was_running:
        return {"ok": True, "pid": pid, "was_running": False, "method": "noop"}

    method = "force" if force else "graceful"

    if not force:
        close_script = f'''#Requires AutoHotkey v2.0
#NoTrayIcon
DetectHiddenWindows(true)
try {{
    WinClose("ahk_pid {pid}")
    FileAppend("CLOSED`n", "*")
}} catch as e {{
    FileAppend("ERROR`t" e.Message "`n", "*")
}}
'''
        temp_path = _create_temp_ahk(close_script)
        try:
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = 0
            subprocess.run(
                [AHK_PATH, "/ErrorStdOut", temp_path],
                capture_output=True, text=True, timeout=3,
                encoding='utf-8', errors='replace',
                startupinfo=startupinfo,
            )
        except Exception:
            pass
        finally:
            try:
                os.remove(temp_path)
            except Exception:
                pass

        deadline = time.time() + timeout_seconds
        while time.time() < deadline:
            if not _process_exists(pid):
                return {"ok": True, "pid": pid, "was_running": True, "method": "graceful"}
            time.sleep(0.1)
        method = "force_after_graceful"

    try:
        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = 0
        result = subprocess.run(
            ["taskkill", "/F", "/PID", str(pid)],
            capture_output=True, text=True, timeout=5,
            encoding='utf-8', errors='replace',
            startupinfo=startupinfo,
        )
        if result.returncode == 0:
            return {"ok": True, "pid": pid, "was_running": True, "method": method}
        return {
            "ok": False, "pid": pid, "method": method,
            "error": (result.stderr.strip() or result.stdout.strip()
                      or f"taskkill exited {result.returncode}"),
        }
    except Exception as e:
        return {"ok": False, "pid": pid, "method": method, "error": str(e)}


_ahk_version_cache: Dict[str, str] = {}


@mcp.tool()
def get_ahk_version(path: Optional[str] = None) -> Dict[str, Any]:
    """
    Return the version string of an AutoHotkey executable.

    If path is None, uses the configured AHK_PATH. Result is cached per path
    for the lifetime of the server process.
    """
    target = path or AHK_PATH
    if not os.path.exists(target):
        return {"path": target, "error": "executable not found"}

    if target in _ahk_version_cache:
        return {"path": target, "version": _ahk_version_cache[target], "cached": True}

    version_script = '''#Requires AutoHotkey v2.0
#NoTrayIcon
FileAppend(A_AhkVersion, "*")
'''
    temp_path = _create_temp_ahk(version_script)
    try:
        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = 0
        result = subprocess.run(
            [target, "/ErrorStdOut", temp_path],
            capture_output=True, text=True, timeout=5,
            encoding='utf-8', errors='replace',
            startupinfo=startupinfo,
        )
        if result.returncode != 0:
            return {
                "path": target, "error": "AHK exited non-zero",
                "exit_code": result.returncode, "stderr": result.stderr.strip(),
            }
        version = (result.stdout or "").strip()
        if not version:
            return {"path": target, "error": "empty version output"}
        _ahk_version_cache[target] = version
        return {"path": target, "version": version, "cached": False}
    except subprocess.TimeoutExpired:
        return {"path": target, "error": "timed out"}
    except Exception as e:
        return {"path": target, "error": str(e)}
    finally:
        try:
            os.remove(temp_path)
        except Exception:
            pass


# ==========================================================================
# DBGp Debug Tools (async, multi-session)
# ==========================================================================

DBG_DEFAULT_PORT = 9005

# AHK built-in class names that pollute global variable listings
_AHK_BUILTINS = {
    "Any", "Array", "BoundFunc", "Buffer", "Class", "ClipboardAll",
    "Closure", "ComObjArray", "ComObject", "ComValue", "ComValueRef",
    "Enumerator", "Error", "File", "Float", "Func", "Gui", "IndexError",
    "InputHook", "Integer", "KeyError", "Map", "MemberError", "Menu",
    "MenuBar", "MethodError", "Number", "OSError", "Object",
    "PropertyError", "RegExMatchInfo", "String", "TargetError",
    "TimeoutError", "TypeError", "UnsetError", "UnsetItemError",
    "ValueError", "VarRef", "ZeroDivisionError",
}


async def _run_dbg(session_id: Optional[str], method: str, /, *args, **kwargs) -> Any:
    """Resolve a session, acquire its lock, run a sync DbgpClient method in a thread."""
    registry = get_registry()
    sid, client = registry.resolve(session_id)
    if not client.connected:
        raise RuntimeError(f"Session {sid} is not connected")
    fn = getattr(client, method)
    async with registry.lock(sid):
        return await asyncio.to_thread(fn, *args, **kwargs)


def _read_source_from_disk(session_id: Optional[str], file: str, begin_line: int, end_line: int) -> Dict[str, Any]:
    """Fallback for dbg_get_source: read the file directly when AHK's DBGp
    source command refuses. Uses the explicit `file` arg if given, otherwise
    the session's entry script.
    """
    try:
        registry = get_registry()
        _, client = registry.resolve(session_id)
        path = file or client.file
        if not path:
            return {"error": "No file path available for source fallback"}
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
        if begin_line > 0 or end_line > 0:
            start = max(begin_line - 1, 0) if begin_line > 0 else 0
            end = end_line if end_line > 0 else len(lines)
            lines = lines[start:end]
        return {"source": "".join(lines), "source_from": "disk", "path": path}
    except OSError as e:
        return {"error": f"Disk fallback failed: {e}"}
    except RuntimeError as e:
        return {"error": str(e)}


@mcp.tool()
async def dbg_attach(pid: int, port: int = DBG_DEFAULT_PORT, timeout: int = 5) -> Dict[str, Any]:
    """
    Attach the debugger to a running AutoHotkey script by PID.
    Starts a TCP listener, sends AHK_ATTACH_DEBUGGER to the target, and
    registers the session under id 'pid:{pid}@{port}'. Multiple concurrent
    sessions on different ports are supported.

    Returns {session_id, pid, port, status, file, ...}.
    """
    client = DbgpClient()
    try:
        client.start_listening(port=port)
    except Exception as e:
        return {"error": f"Failed to start listener on port {port}: {e}"}

    attach_script = f'''#Requires AutoHotkey v2.0
#NoTrayIcon
DetectHiddenWindows(true)
attach_msg := DllCall("RegisterWindowMessage", "Str", "AHK_ATTACH_DEBUGGER")
hwnds := WinGetList("ahk_class AutoHotkey ahk_pid {pid}")
if hwnds.Length = 0 {{
    FileAppend("ERROR: No AutoHotkey window found for PID {pid}`n", "*")
    ExitApp(1)
}}
sent := 0
for hwnd in hwnds {{
    try {{
        PostMessage(attach_msg, 0, {port},, hwnd)
        sent++
    }}
}}
FileAppend("SENT:" sent "`n", "*")
'''
    helper = await run_ahk_script(attach_script, timeout_seconds=3,
                                  action_description=f"dbg_attach helper (pid={pid})")
    if helper.get("exit_code") != 0 or "ERROR" in helper.get("stdout", ""):
        client.close()
        return {
            "error": "Failed to send AHK_ATTACH_DEBUGGER",
            "details": helper.get("stdout", "") + helper.get("stderr", ""),
        }

    try:
        info = await asyncio.to_thread(client.accept_connection, timeout)
    except DbgpConnectionError as e:
        client.close()
        return {"error": str(e)}

    sid = get_registry().register(client, pid=pid, port=port)

    # Configure session for AI-friendly usage; non-critical if it fails.
    try:
        async with get_registry().lock(sid):
            await asyncio.to_thread(client.feature_set, "max_depth", "2")
            await asyncio.to_thread(client.feature_set, "max_data", "1024")
            await asyncio.to_thread(client.feature_set, "max_children", "64")
    except Exception:
        pass

    info["session_id"] = sid
    info["pid"] = pid
    info["port"] = port
    return info


@mcp.tool()
async def dbg_launch(path: str, port: int = DBG_DEFAULT_PORT, timeout: int = 5) -> Dict[str, Any]:
    """
    Launch an AutoHotkey script with /Debug and connect the debugger immediately.
    Use this to catch load-time errors (e.g. syntax errors) that prevent attach.
    Returns {session_id, port, status, file, ...}.
    """
    client = DbgpClient()
    try:
        client.start_listening(port=port)
    except Exception as e:
        return {"error": f"Failed to start listener on port {port}: {e}"}

    try:
        # The = is mandatory; without it AHK treats /Debug as the script path.
        proc = await asyncio.create_subprocess_exec(
            AHK_PATH, "/ErrorStdOut", "/force", f"/Debug=127.0.0.1:{port}", path,
            creationflags=_CREATE_NO_WINDOW,
        )
    except Exception as e:
        client.close()
        return {"error": f"Failed to launch script: {e}"}

    try:
        info = await asyncio.to_thread(client.accept_connection, timeout)
    except DbgpConnectionError as e:
        client.close()
        return {"error": str(e)}

    sid = get_registry().register(client, pid=proc.pid, port=port)

    try:
        async with get_registry().lock(sid):
            await asyncio.to_thread(client.feature_set, "max_depth", "2")
            await asyncio.to_thread(client.feature_set, "max_data", "1024")
            await asyncio.to_thread(client.feature_set, "max_children", "64")
    except Exception:
        pass

    info["session_id"] = sid
    info["pid"] = proc.pid
    info["port"] = port
    return info


@mcp.tool()
async def dbg_list_sessions() -> Dict[str, Any]:
    """List all active DBGp debug sessions with their session_id, pid, port, and status."""
    sessions = get_registry().list()
    return {"count": len(sessions), "sessions": sessions}


@mcp.tool()
async def dbg_close_session(session_id: str) -> Dict[str, Any]:
    """Force-close a debug session and remove it from the registry without sending detach."""
    registry = get_registry()
    try:
        sid, client = registry.resolve(session_id)
    except RuntimeError as e:
        return {"status": "no_session", "error": str(e)}
    try:
        await asyncio.to_thread(client.close)
    except Exception:
        pass
    registry.remove(sid)
    return {"status": "closed", "session_id": sid}


@mcp.tool()
async def dbg_detach(session_id: Optional[str] = None) -> Dict[str, str]:
    """Detach a debug session, letting the script continue normally."""
    registry = get_registry()
    try:
        sid, client = registry.resolve(session_id)
    except RuntimeError as e:
        return {"status": "no_session", "message": str(e)}
    if client.connected:
        try:
            async with registry.lock(sid):
                await asyncio.to_thread(client.detach)
        except Exception:
            pass
    try:
        await asyncio.to_thread(client.close)
    except Exception:
        pass
    registry.remove(sid)
    return {"status": "detached", "session_id": sid}


@mcp.tool()
async def dbg_status(session_id: Optional[str] = None) -> Dict[str, Any]:
    """Get the current status of a debug session."""
    try:
        return await _run_dbg(session_id, "status")
    except DbgpError as e:
        return {"error": str(e)}
    except DbgpConnectionError as e:
        if session_id:
            get_registry().remove(session_id)
        return {"status": "disconnected", "error": str(e)}
    except RuntimeError as e:
        return {"status": "no_session", "message": str(e)}


@mcp.tool()
async def dbg_break(session_id: Optional[str] = None) -> Dict[str, Any]:
    """Pause execution of the running script (async break)."""
    try:
        return await _run_dbg(session_id, "send_break")
    except DbgpError as e:
        return {"error": str(e)}
    except RuntimeError as e:
        return {"error": str(e)}


@mcp.tool()
async def dbg_continue(mode: str = "run", session_id: Optional[str] = None) -> Dict[str, Any]:
    """Resume execution. mode: 'run', 'step_into', 'step_over', 'step_out'."""
    valid = {"run", "step_into", "step_over", "step_out"}
    if mode not in valid:
        return {"error": f"invalid mode {mode!r}; must be one of {sorted(valid)}"}
    try:
        return await _run_dbg(session_id, mode)
    except DbgpError as e:
        return {"error": str(e)}
    except RuntimeError as e:
        return {"error": str(e)}


@mcp.tool()
async def dbg_stack(session_id: Optional[str] = None) -> Dict[str, Any]:
    """Get the current call stack.

    AHK v2's DBGp engine often returns an empty stack when broken inside a
    SetTimer callback or other non-main thread. When that happens we return
    a single synthetic frame pointing at the session's entry script so the
    agent at least knows which file is paused.
    """
    def _synthetic():
        registry = get_registry()
        _, client = registry.resolve(session_id)
        if client.file:
            return {
                "frames": [{"level": 0, "type": "file", "filename": client.file, "lineno": 0}],
                "synthetic": True,
                "note": "AHK returned empty stack or rejected stack_get; fallback frame uses session entry file.",
            }
        return {"frames": []}
    try:
        frames = await _run_dbg(session_id, "stack_get")
        if frames:
            return {"frames": [f.to_dict() for f in frames]}
        return _synthetic()
    except DbgpError as e:
        if e.code == 3:
            return _synthetic()
        return {"error": str(e)}
    except RuntimeError as e:
        return {"error": str(e)}


@mcp.tool()
async def dbg_get_vars(context: int = 0, depth: int = 0, session_id: Optional[str] = None) -> Dict[str, Any]:
    """Get variables in a context (0=Local, 1=Global) at a given stack depth."""
    try:
        variables = await _run_dbg(session_id, "context_get", context_id=context, depth=depth)
        filtered = [
            v for v in variables
            if v.facet != "Builtin"
            and not (v.type == "object" and v.name in _AHK_BUILTINS)
            and not v.name.startswith("A_")
        ]
        return {"count": len(filtered), "variables": [v.to_dict() for v in filtered]}
    except DbgpError as e:
        return {"error": str(e)}
    except RuntimeError as e:
        return {"error": str(e)}


@mcp.tool()
async def dbg_get_var(name: str, context: int = 0, depth: int = 0, session_id: Optional[str] = None) -> Dict[str, Any]:
    """Get a single variable by name.

    AHK v2's DBGp engine rejects property_get's -n argument (DBGp error 3 /
    "invalid options") or ignores it and returns the first global. We fall
    back to eval(name) on those failures, which uses AHK's expression engine
    and reliably returns the requested variable.
    """
    async def _eval_fallback() -> Dict[str, Any]:
        try:
            ev = await _run_dbg(session_id, "eval", name)
            if ev is None:
                return {"error": f"Variable '{name}' not found"}
            return ev.to_dict()
        except DbgpError as ee:
            return {"error": str(ee)}
    try:
        var = await _run_dbg(session_id, "property_get", name, context_id=context, depth=depth)
        # AHK sometimes ignores -n and returns the FIRST property in the
        # context instead of the requested one. If the name doesn't match,
        # the response is not authoritative — fall back to eval.
        if var.name != name and var.fullname != name:
            return await _eval_fallback()
        return var.to_dict()
    except DbgpError as e:
        # 3 = invalid options, 4 = unimplemented, 300 = no <property> in response.
        if e.code in (3, 4, 300):
            return await _eval_fallback()
        return {"error": str(e)}
    except RuntimeError as e:
        return {"error": str(e)}


@mcp.tool()
async def dbg_set_var(name: str, value: str, session_id: Optional[str] = None) -> Dict[str, Any]:
    """Set a variable's value in the current context.

    NOTE: AHK v2's DBGp engine does not implement property_set and returns
    DBGp error 4. Use dbg_eval with an assignment expression instead, e.g.
    dbg_eval("counter := 999").
    """
    try:
        success = await _run_dbg(session_id, "property_set", name, value)
        return {"success": success}
    except DbgpError as e:
        return {"error": str(e)}
    except RuntimeError as e:
        return {"error": str(e)}


@mcp.tool()
async def dbg_eval(expression: str, session_id: Optional[str] = None) -> Dict[str, Any]:
    """Evaluate an AHK expression in the current execution context.
    The script must be in a 'break' state."""
    try:
        result = await _run_dbg(session_id, "eval", expression)
        if result:
            return result.to_dict()
        return {"result": None, "message": "Expression evaluated, no return value."}
    except DbgpError as e:
        return {"error": str(e)}
    except RuntimeError as e:
        return {"error": str(e)}


@mcp.tool()
async def dbg_set_breakpoint(file: str, line: int, session_id: Optional[str] = None) -> Dict[str, Any]:
    """Set a line breakpoint in a script file."""
    try:
        return await _run_dbg(session_id, "breakpoint_set", file=file, line=line)
    except DbgpError as e:
        return {"error": str(e)}
    except RuntimeError as e:
        return {"error": str(e)}


@mcp.tool()
async def dbg_list_breakpoints(session_id: Optional[str] = None) -> Dict[str, Any]:
    """List all active breakpoints."""
    try:
        bps = await _run_dbg(session_id, "breakpoint_list")
        return {"count": len(bps), "breakpoints": bps}
    except DbgpError as e:
        return {"error": str(e)}
    except RuntimeError as e:
        return {"error": str(e)}


@mcp.tool()
async def dbg_remove_breakpoint(breakpoint_id: str, session_id: Optional[str] = None) -> Dict[str, Any]:
    """Remove a breakpoint by its ID."""
    try:
        await _run_dbg(session_id, "breakpoint_remove", breakpoint_id)
        return {"success": True, "removed_id": breakpoint_id}
    except DbgpError as e:
        return {"error": str(e)}
    except RuntimeError as e:
        return {"error": str(e)}


@mcp.tool()
async def dbg_get_source(file: str = "", begin_line: int = 0, end_line: int = 0, session_id: Optional[str] = None) -> Dict[str, Any]:
    """Retrieve source code from the debugged script. If file is empty, gets the current file.

    AHK v2's DBGp engine rejects the source command with DBGp error 3 or
    returns empty content. We fall back to reading the file directly from
    disk, slicing to begin_line..end_line when requested.
    """
    try:
        src = await _run_dbg(
            session_id, "source",
            file=file if file else None,
            begin_line=begin_line, end_line=end_line,
        )
        if src:
            return {"source": src, "source_from": "dbgp"}
        return _read_source_from_disk(session_id, file, begin_line, end_line)
    except DbgpError as e:
        # AHK's source command may raise 3 (invalid options) or 4
        # (unimplemented). Both warrant the disk fallback.
        if e.code in (3, 4):
            return _read_source_from_disk(session_id, file, begin_line, end_line)
        return {"error": str(e)}
    except RuntimeError as e:
        return {"error": str(e)}


@mcp.tool()
async def dbg_stdout(mode: int = 1, session_id: Optional[str] = None) -> Dict[str, Any]:
    """Set stdout redirection for the debugged script.
    0=disable, 1=copy to debugger, 2=redirect to debugger only.

    WARNING: modes 1 and 2 cause AHK to mirror/redirect stdout to the DBGp
    socket. If the debugged script writes to stdout via FileAppend(..., "*"),
    the underlying handle can become invalid mid-run and the script will pop
    a "(6) The handle is invalid" error dialog. Use mode 0 (or don't call
    dbg_stdout at all) for scripts that write to stdout themselves.
    """
    try:
        success = await _run_dbg(session_id, "stdout", mode)
        return {"success": success, "mode": mode}
    except DbgpError as e:
        return {"error": str(e)}
    except RuntimeError as e:
        return {"error": str(e)}


if __name__ == "__main__":
    mcp.run()
