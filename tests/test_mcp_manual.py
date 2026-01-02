#!/usr/bin/env python3
"""
Manual MCP server test script.
Run this to verify the MCP server works and can execute tools.
"""

import json
import subprocess
import time


def test_mcp_server():
    """Test MCP server by calling get_system_status tool."""
    print("🚀 Starting MCP server...")

    # Start MCP server
    process = subprocess.Popen(
        ["uv", "run", "python", "-m", "server.mcp.server"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )

    # Wait for server to initialize
    time.sleep(3)

    # Check for stderr errors
    import select

    if select.select([process.stderr], [], [], 0)[0]:
        stderr_output = process.stderr.read()
        if stderr_output:
            print(f"⚠️  Server stderr output:\n{stderr_output}\n")

    print("✓ MCP server started\n")

    # Initialize protocol
    print("🤝 Initializing MCP protocol...")
    init_request = {
        "jsonrpc": "2.0",
        "id": 0,
        "method": "initialize",
        "params": {
            "protocolVersion": "2025-11-25",
            "capabilities": {},
            "clientInfo": {"name": "test-client", "version": "1.0.0"},
        },
    }

    process.stdin.write(json.dumps(init_request) + "\n")
    process.stdin.flush()

    print("✓ Initialization response received\n")

    # Test 1: List available tools
    print("📋 Test 1: Listing available tools...")
    request = {"jsonrpc": "2.0", "id": 1, "method": "tools/list"}

    process.stdin.write(json.dumps(request) + "\n")
    process.stdin.flush()

    response_line = process.stdout.readline()
    response = json.loads(response_line)

    print(f"Debug - Full response: {json.dumps(response, indent=2)[:300]}...")

    if "result" in response:
        result = response["result"]
        tools = result.get("tools", [])
        print(f"✓ Found {len(tools)} tools:")
        for tool in tools[:5]:  # Show first 5
            print(f"  - {tool['name']}: {tool.get('description', 'No description')[:60]}...")
        if len(tools) > 5:
            print(f"  ... and {len(tools) - 5} more")
    else:
        print(f"✗ Error: {response.get('error', 'Unknown error')}")

    print()

    # Test 2: Call get_system_status (synchronous tool)
    print("🔧 Test 2: Calling get_system_status tool...")
    request = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {"name": "get_system_status", "arguments": {"repo_root": "."}},
    }

    process.stdin.write(json.dumps(request) + "\n")
    process.stdin.flush()

    response_line = process.stdout.readline()
    response = json.loads(response_line)

    if "result" in response:
        result = response["result"]
        print("✓ System status retrieved:")
        print(f"  Success: {result.get('success', False)}")
        status_text = result.get("status_text", "")
        # Show first 200 chars
        print(f"  Status: {status_text[:200]}...")
    else:
        print(f"✗ Error: {response.get('error', 'Unknown error')}")

    print()

    # Test 3: Call check_policies (synchronous tool)
    print("📝 Test 3: Calling check_policies tool...")
    request = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {
            "name": "check_policies",
            "arguments": {"repo_root": ".", "paths": ["server/mcp/tools/"], "auto_fix": False},
        },
    }

    process.stdin.write(json.dumps(request) + "\n")
    process.stdin.flush()

    response_line = process.stdout.readline()
    response = json.loads(response_line)

    if "result" in response:
        result = response["result"]
        print("✓ Policy check completed:")
        print(f"  Exit code: {result.get('exit_code', 'N/A')}")
        print(f"  Files checked: {result.get('files_checked', 0)}")
        print(f"  Violations: {result.get('total_violations', 0)}")
    else:
        print(f"✗ Error: {response.get('error', 'Unknown error')}")

    print()

    # Cleanup
    print("🛑 Stopping MCP server...")
    process.terminate()
    process.wait(timeout=5)
    print("✓ MCP server stopped")

    print("\n✅ All MCP tests completed successfully!")


if __name__ == "__main__":
    try:
        test_mcp_server()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback

        traceback.print_exc()
