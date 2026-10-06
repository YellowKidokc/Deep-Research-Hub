"""
Stratum Local Bridge
Tiny WebSocket server (port 9877) that connects the Stratum PWA to AutoHotkey.
The PWA auto-detects this bridge. When connected, shortcuts execute locally.
When not connected, the PWA falls back to clipboard-only mode.

Install: pip install websockets pyperclip
Run:     pythonw bridge.py  (or add to startup)
"""

import asyncio
import json
import subprocess
import sys
from pathlib import Path

try:
    import websockets
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "websockets", "pyperclip"])
    import websockets

import pyperclip

# ── Config ──
PORT = 9877
AHK_PATH = r"C:\Program Files\AutoHotkey\v2\AutoHotkey64.exe"
STRATUM_DIR = Path(r"D:\DONT TOUCH BOOT UP\stratum")

# ── Action Handlers ──
async def handle_action(data):
    action = data.get("action", "")

    if action == "clipboard_set":
        text = data.get("text", "")
        pyperclip.copy(text)
        return {"status": "ok", "action": "clipboard_set"}

    elif action == "clipboard_get":
        text = pyperclip.paste()
        return {"status": "ok", "content": text}

    elif action == "run_prompt":
        # Get selected text from clipboard, run through prompt
        selected = pyperclip.paste()
        prompt_content = data.get("content", "")
        return {
            "status": "ok",
            "action": "run_prompt",
            "selected_text": selected,
            "prompt": prompt_content,
        }

    elif action == "ahk_execute":
        # Run an AHK script by name
        script_name = data.get("script", "")
        script_path = STRATUM_DIR / "07_ahk" / script_name
        if script_path.exists() and script_path.suffix == ".ahk":
            subprocess.Popen([AHK_PATH, str(script_path)])
            return {"status": "ok", "action": "ahk_execute", "script": script_name}
        return {"status": "error", "message": f"Script not found: {script_name}"}

    elif action == "hotkey_send":
        # Simulate a keystroke via AHK
        keys = data.get("keys", "")
        ahk_cmd = f'#Requires AutoHotkey v2.0+\nSend "{keys}"'
        proc = subprocess.Popen(
            [AHK_PATH, "/script", "*"],
            stdin=subprocess.PIPE,
        )
        proc.communicate(ahk_cmd.encode())
        return {"status": "ok", "action": "hotkey_send"}

    elif action == "ping":
        return {"status": "ok", "action": "pong", "bridge_version": "1.0"}

    return {"status": "error", "message": f"Unknown action: {action}"}


# ── WebSocket Server ──
async def handler(websocket):
    print(f"[bridge] Client connected from {websocket.remote_address}")
    try:
        async for message in websocket:
            try:
                data = json.loads(message)
                result = await handle_action(data)
                await websocket.send(json.dumps(result))
            except json.JSONDecodeError:
                await websocket.send(json.dumps({"status": "error", "message": "Invalid JSON"}))
            except Exception as e:
                await websocket.send(json.dumps({"status": "error", "message": str(e)}))
    except websockets.exceptions.ConnectionClosed:
        print("[bridge] Client disconnected")


async def main():
    print(f"[bridge] Stratum Bridge starting on ws://localhost:{PORT}")
    print(f"[bridge] AHK path: {AHK_PATH}")
    print(f"[bridge] Stratum dir: {STRATUM_DIR}")

    async with websockets.serve(handler, "localhost", PORT):
        print(f"[bridge] Ready — PWA will auto-detect")
        await asyncio.Future()  # run forever


if __name__ == "__main__":
    asyncio.run(main())
