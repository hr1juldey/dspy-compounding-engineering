"""Pytest configuration and shared fixtures."""

import json
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def reset_registry():
    """Reset the ServiceRegistry status before each test."""
    from config import registry

    # Clear status to ensure clean state
    registry.status.clear()
    registry.status.update(
        {
            "qdrant_available": None,
            "openai_key_available": None,
            "embeddings_ready": None,
            "learnings_ensured": False,
            "codebase_ensured": False,
        }
    )


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def mock_knowledge_base(temp_dir):
    """Create a mock knowledge base for testing."""
    kb_dir = temp_dir / ".knowledge"
    kb_dir.mkdir(exist_ok=True)
    return kb_dir


@pytest.fixture
def sample_learning():
    """Return a sample learning dictionary."""
    return {
        "category": "test",
        "summary": "Test learning summary",
        "content": "Detailed test learning content",
        "tags": ["test", "example"],
        "source": "test_source",
    }


class MCPClient:
    """Helper client for testing MCP server via stdio."""

    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.process = None
        self.next_id = 1

    def start_server(self):
        """Start MCP server subprocess."""
        self.process = subprocess.Popen(
            ["uv", "run", "python", "-m", "server.mcp.server"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        time.sleep(2)

    def stop_server(self):
        """Stop MCP server subprocess."""
        if self.process:
            self.process.terminate()
            self.process.wait(timeout=5)

    def send_request(self, method: str, params: dict | None = None) -> dict:
        """Send JSON-RPC request to MCP server."""
        request = {
            "jsonrpc": "2.0",
            "id": self.next_id,
            "method": method,
            "params": params or {},
        }
        self.next_id += 1

        self.process.stdin.write(json.dumps(request) + "\n")
        self.process.stdin.flush()

        response_line = self.process.stdout.readline()
        return json.loads(response_line)

    def call_tool(self, tool_name: str, arguments: dict) -> dict:
        """Call an MCP tool and return result."""
        return self.send_request("tools/call", {"name": tool_name, "arguments": arguments})


@pytest.fixture
def mcp_client():
    """Provide MCPClient for testing."""
    client = MCPClient()
    client.start_server()
    yield client
    client.stop_server()
