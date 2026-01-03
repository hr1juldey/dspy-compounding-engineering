"""Entry point for running MCP server as module: python -m server.mcp"""

import sys

from server.mcp.server import mcp

if __name__ == "__main__":
    # DEBUG: Check tools before running
    print(f"DEBUG: Tools registered = {list(mcp._tool_manager._tools.keys())}", file=sys.stderr)

    transport = sys.argv[1] if len(sys.argv) > 1 else "stdio"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 12001

    if transport in ("http", "streamable-http"):
        print(f"Starting MCP server on HTTP :{port} (transport={transport})", file=sys.stderr)
        mcp.run(transport=transport, host="0.0.0.0", port=port)
    else:
        print("Starting MCP server on stdio (primary transport)", file=sys.stderr)
        mcp.run()
