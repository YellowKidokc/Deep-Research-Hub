@echo off
:: Launch Clipboard panel in Edge app mode (requires sync_server.py running on :3456)
start "" msedge --app="http://127.0.0.1:3456/clipboard3" --window-size=390,720
