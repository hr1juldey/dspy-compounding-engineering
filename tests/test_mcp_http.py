#!/usr/bin/env python3
"""
Test FastMCP HTTP transport - tools should be properly serialized.

Usage:
1. In one terminal: uv run python -m server.mcp.server http 12001
2. In another terminal: uv run python test_mcp_http.py
"""

import subprocess
import time

import requests


def test_http_transport():
    """Test MCP server with HTTP transport."""
    print("🚀 Starting MCP server with HTTP transport on port 12001...\n")

    server_process = subprocess.Popen(
        ["uv", "run", "python", "-m", "server.mcp.server", "http", "12001"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    # Wait for server to start
    time.sleep(3)

    try:
        # Test 1: Check if server is running
        print("📍 Test 1: Server health check...")
        try:
            response = requests.get("http://localhost:12001", timeout=5)
            print(f"✓ Server is responding (status: {response.status_code})\n")
        except requests.exceptions.ConnectionError:
            print("❌ Could not connect to server on localhost:12001")
            return

        # Test 2: List tools
        print("📋 Test 2: Listing tools via HTTP...")
        try:
            # Try common HTTP API paths for tool listing
            paths = [
                "/tools",
                "/mcp/tools",
                "/api/tools",
                "/__mcp__/tools",
            ]

            for path in paths:
                try:
                    response = requests.get(f"http://localhost:12001{path}", timeout=5)
                    if response.status_code == 200:
                        data = response.json()
                        tools = data.get("tools", [])
                        print(f"✓ Found tools at {path}: {len(tools)} tools")
                        if tools and len(tools) > 0:
                            print("\n✅ SUCCESS! Tools are being exposed via HTTP:\n")
                            for i, tool in enumerate(tools[:5], 1):
                                is_dict = isinstance(tool, dict)
                                name = tool.get("name", "unknown") if is_dict else str(tool)
                                print(f"  {i}. {name}")
                            if len(tools) > 5:
                                print(f"  ... and {len(tools) - 5} more")
                            return
                except Exception:
                    pass

            print("⚠️  Could not find tools endpoint. Trying POST to /mcp...")
            # Try POST with JSON-RPC
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/list",
                "params": {},
            }
            response = requests.post(
                "http://localhost:12001",
                json=payload,
                timeout=5,
                headers={"Content-Type": "application/json"},
            )
            if response.status_code == 200:
                data = response.json()
                if "result" in data:
                    tools = data["result"].get("tools", [])
                    print(f"✓ JSON-RPC tools/list returned: {len(tools)} tools")
                    if len(tools) > 0:
                        print("\n✅ SUCCESS! Tools are properly serialized via HTTP!\n")
                        for i, tool in enumerate(tools[:5], 1):
                            name = tool.get("name", "unknown")
                            print(f"  {i}. {name}")
                        if len(tools) > 5:
                            print(f"  ... and {len(tools) - 5} more")

        except Exception as e:
            print(f"❌ Error: {e}")

    finally:
        print("\n🛑 Stopping server...")
        server_process.terminate()
        try:
            server_process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            server_process.kill()


if __name__ == "__main__":
    test_http_transport()
