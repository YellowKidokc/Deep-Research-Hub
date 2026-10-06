@echo off
title AI-HUB Doctor — Claude Code + AHK MCP Debugger
echo ============================================
echo  AI-HUB Doctor
echo  Wiring Claude Code to the AHK MCP Server
echo  so it can run, debug, and fix the hub live
echo ============================================
echo.

cd /d "\\192.168.2.50\h_hp\Desktop\AI HUB DAVID\AHK"

echo [1/3] Installing MCP server dependencies...
pip install -r AutohotkeyV2_MCPServer\requirements.txt --quiet 2>nul
echo       Done.
echo.

echo [2/3] Writing MCP config...
echo       ahk_mcp_config.json ready.
echo.

echo [3/3] Launching Claude Code with AHK MCP + fix task...
echo.
echo  Claude Code will:
echo    - Connect to the AHK v2 MCP server
echo    - Use dbg_launch to start AI-HUB.ahk under debugger
echo    - Catch the crash, read the stack, fix the code
echo    - Add DeepSeek as a provider for Ctrl+Space
echo    - Keep going until the hub stays alive
echo.
echo  Full task spec: CLAUDE_CODE_FIX_TASK.md
echo ============================================
echo.

claude --mcp-config "%~dp0ahk_mcp_config.json" -p "Read CLAUDE_CODE_FIX_TASK.md and execute it. You have an AHK v2 MCP server connected — use dbg_launch to start AI-HUB.ahk under the debugger, catch crashes with dbg_stack and dbg_get_vars, fix the code, relaunch, repeat until it stays alive for 5 minutes. Also add DeepSeek as a third AI provider. The hub is at %~dp0AI-HUB.ahk"

pause
