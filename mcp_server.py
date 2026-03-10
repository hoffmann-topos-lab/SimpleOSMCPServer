import json
import subprocess
import time
import os
import sys
from datetime import datetime
from typing import Any, Dict
import asyncio
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions


CONFIG_PATH = "config.json"
with open(CONFIG_PATH, "r") as f:
    CONFIG = json.load(f)
SANDBOX_DIR = "/app/sandbox"
os.chdir(SANDBOX_DIR)
ACTIONS_LOG = CONFIG["logs"]["actions"]
ERRORS_LOG = CONFIG["logs"]["errors"]
COMMAND_TIMEOUT = CONFIG.get("command_timeout_seconds", 30)


os.makedirs(SANDBOX_DIR, exist_ok=True)
os.makedirs(os.path.dirname(ACTIONS_LOG), exist_ok=True)
os.makedirs(os.path.dirname(ERRORS_LOG), exist_ok=True)
os.chdir(SANDBOX_DIR)

def _ensure_log_file(path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if not os.path.exists(path):
        open(path, "a").close()

def log_action(entry: Dict[str, Any]):
    _ensure_log_file(ACTIONS_LOG)
    entry["timestamp"] = datetime.utcnow().isoformat()
    with open(ACTIONS_LOG, "a") as f:
        f.write(json.dumps(entry) + "\n")

def log_error(entry: Dict[str, Any]):
    _ensure_log_file(ERRORS_LOG)
    entry["timestamp"] = datetime.utcnow().isoformat()
    with open(ERRORS_LOG, "a") as f:
        f.write(json.dumps(entry) + "\n")

server = Server("generic-mcp-server")

@server.list_tools()
async def list_tools():
    return [
        Tool(
            name="user_command",
            description="Executa comandos arbitrários no terminal Linux",
            inputSchema={
                "type": "object",
                "properties": {
                    "command": {"type": "string"}
                },
                "required": ["command"]
            },
        ),
    ]

@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]):
    try:
        if name == "user_command":
            cmd = arguments["command"]

            log_action({
                "tool": "user_command",
                "command": cmd
            })
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=COMMAND_TIMEOUT,
            )
            return [
                TextContent(
                    type="text",
                    text=(
                        f"STDOUT:\n{result.stdout}\n\n"
                        f"STDERR:\n{result.stderr}\n\n"
                        f"EXIT CODE: {result.returncode}"
                    )
                )
            ]

        raise ValueError(f"Tool desconhecida: {name}")
    except Exception as e:
        log_error({
            "tool": name,
            "error": str(e)
        })
        return [
            TextContent(
                type="text",
                text=f"Erro: {str(e)}"
            )
        ]

async def main():
    async with stdio_server() as (read, write):
        await server.run(
            read,
            write,
            InitializationOptions(
                server_name="mcp-generic",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={}
                )
            )
        )
if __name__ == "__main__":
    asyncio.run(main())
