@echo off
:: Launch Task Calendar in Edge app mode (requires sync_server.py running on :3456)
start "" msedge --app="http://127.0.0.1:3456/calendar" --window-size=600,750
