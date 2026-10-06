"""Verify a local stdio MCP server initializes and exposes its tools."""
import asyncio
import sys
from fastmcp import Client


async def main():
    filesystem = "--filesystem" in sys.argv
    name = "master-eq-filesystem" if filesystem else "gpt-researcher-deepseek"
    command = "npx.cmd" if filesystem else "cmd.exe"
    args = (["-y", "@modelcontextprotocol/server-filesystem",
             r"D:\GitHub\Research-Acquisition",
             r"\\192.168.2.50\h_hp\Desktop\APIs\APIs\LEAN4\AXIOMS"]
            if filesystem else ["/c", r"D:\GitHub\Research-Acquisition\gptr-mcp\START_GPTR_MCP.bat"])
    config = {"mcpServers": {name: {"command": command, "args": args}}}
    async with Client(config, timeout=30) as client:
        tools = await client.list_tools()
        print("TOOLS=" + ",".join(tool.name for tool in tools))
        if filesystem:
            result = await client.call_tool("list_allowed_directories", {})
            print("ROOTS=" + ",".join(block.text for block in result.content if block.type == "text"))
            nas = await client.call_tool("list_directory", {"path": r"\\192.168.2.50\h_hp\Desktop\APIs\APIs\LEAN4\AXIOMS"})
            print("NAS_LIST_OK=" + str(not nas.is_error))


if __name__ == "__main__":
    asyncio.run(main())
