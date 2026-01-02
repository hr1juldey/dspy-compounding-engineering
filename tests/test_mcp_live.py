#!/usr/bin/env python3
"""
Live MCP server test - connects to a running server and queries tools.

Usage:
1. In one terminal: uv run python -m server.mcp.server
2. In another terminal: uv run python test_mcp_live.py
"""

import json
import subprocess
import time


def test_live_mcp_server():
    """Connect to running MCP server and test tool listing."""
    print("🔗 Connecting to running MCP server on stdin...\n")

    # Start the MCP server process
    print("Starting MCP server...")
    server_process = subprocess.Popen(
        ["uv", "run", "python", "-m", "server.mcp.server"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )

    # Wait for server to be ready
    time.sleep(3)

    try:
        # Step 1: Initialize protocol
        print("📮 Step 1: Sending initialize request...")
        init_msg = {
            "jsonrpc": "2.0",
            "id": 0,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-11-25",
                "capabilities": {},
                "clientInfo": {"name": "test-client", "version": "1.0.0"},
            },
        }

        server_process.stdin.write(json.dumps(init_msg) + "\n")
        server_process.stdin.flush()

        init_response = server_process.stdout.readline()
        if not init_response:
            print("❌ No response from server!")
            # Print stderr to see errors
            stderr_out = server_process.stderr.read()
            if stderr_out:
                print(f"Server stderr: {stderr_out}")
            return

        print("✓ Server initialized\n")

        # Step 2: List tools
        print("📋 Step 2: Requesting tool list...")
        tools_msg = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list",
            "params": {},
        }

        server_process.stdin.write(json.dumps(tools_msg) + "\n")
        server_process.stdin.flush()

        tools_response_line = server_process.stdout.readline()
        tools_response = json.loads(tools_response_line)

        if "result" in tools_response:
            tools = tools_response["result"].get("tools", [])
            print(f"✅ SUCCESS! Found {len(tools)} tools:\n")

            for i, tool in enumerate(tools, 1):
                name = tool.get("name", "unknown")
                desc = tool.get("description", "No description")[:70]
                print(f"  {i:2}. {name:30} - {desc}")

            if len(tools) == 0:
                print("⚠️  No tools registered - check imports in __main__.py")
            else:
                print(f"\n✓ MCP server is working with {len(tools)} tools!")
        else:
            print(f"❌ Error response: {tools_response.get('error', 'Unknown error')}")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()

    finally:
        # Cleanup
        print("\n🛑 Stopping server...")
        server_process.terminate()
        try:
            server_process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            server_process.kill()


if __name__ == "__main__":
    test_live_mcp_server()
