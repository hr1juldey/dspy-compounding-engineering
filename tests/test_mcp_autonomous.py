"""
Autonomous MCP agent integration tests.

These tests validate the MCP server's ability to autonomously build
projects using only Ollama and local resources.
"""

import subprocess
import time
from pathlib import Path

import pytest
import requests


def wait_for_task(mcp_client, task_id: str, timeout: int = 600) -> dict:
    """Wait for async task to complete and return result."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        response = mcp_client.call_tool("get_task_status", {"task_id": task_id})

        if "result" in response and response["result"].get("ready"):
            return response["result"].get("result", {})

        time.sleep(2)

    raise TimeoutError(f"Task {task_id} did not complete within {timeout}s")


def test_mcp_server_lists_all_tools(mcp_client):
    """Test that MCP server exposes all 17 tools."""
    response = mcp_client.send_request("tools/list")

    assert "result" in response
    tools = response["result"]["tools"]
    tool_names = [t["name"] for t in tools]

    expected_tools = [
        "analyze_code",
        "check_policies",
        "codify_feedback",
        "compress_knowledge_base",
        "configure_llm",
        "execute_work",
        "garden_knowledge",
        "generate_command",
        "generate_plan",
        "get_repo_status",
        "get_system_status",
        "get_task_status",
        "index_codebase",
        "initialize_repo",
        "review_code",
        "triage_issues",
    ]

    for tool in expected_tools:
        assert tool in tool_names, f"Tool '{tool}' not found in MCP server"

    assert len(tool_names) >= 17, f"Expected >= 17 tools, got {len(tool_names)}"


def test_configure_llm_tool(mcp_client):
    """Test LLM configuration tool."""
    response = mcp_client.call_tool("configure_llm", {"provider": "ollama", "model": "qwen2.5:7b"})

    assert "result" in response
    result = response["result"]
    assert result["success"] is True
    assert result["provider"] == "ollama"
    assert result["model"] == "qwen2.5:7b"


def test_get_system_status_tool(mcp_client):
    """Test system status diagnostic tool."""
    response = mcp_client.call_tool("get_system_status", {"repo_root": "."})

    assert "result" in response
    result = response["result"]
    assert result["success"] is True
    assert "status_text" in result


def test_initialize_repo_tool(mcp_client, temp_dir):
    """Test repository initialization tool."""
    test_repo = temp_dir / "test_repo"
    test_repo.mkdir()

    response = mcp_client.call_tool("initialize_repo", {"repo_root": str(test_repo)})

    assert "result" in response
    compounding_dir = test_repo / ".compounding"
    assert compounding_dir.exists()


@pytest.mark.autonomous
@pytest.mark.timeout(3600)
def test_build_mimicus_from_plan_to_mvp(mcp_client):
    """
    Ultimate integration test: Build mimicus autonomously.

    Given:
    - Mimicus repo with HLD/LLD/VARIABLE_NAMES.md
    - No code (empty repo)
    - MCP configured with Ollama

    When:
    - MCP autonomously executes: plan → work → review → fix loop

    Then:
    - Mimicus MVP runs successfully
    - FastAPI server starts
    - Basic mock endpoints work
    - All tests pass
    """
    mimicus_root = Path("/home/riju279/Documents/Tools/mimicus/mimicus")

    if not mimicus_root.exists():
        pytest.skip("Mimicus repo not found at expected location")

    # 1. Configure LLM to use Ollama
    llm_response = mcp_client.call_tool(
        "configure_llm", {"provider": "ollama", "model": "qwen2.5:7b"}
    )
    assert llm_response["result"]["success"]

    # 2. Initialize repo
    init_response = mcp_client.call_tool("initialize_repo", {"repo_root": str(mimicus_root)})
    assert "result" in init_response

    # 3. Index codebase (will index docs)
    index_response = mcp_client.call_tool(
        "index_codebase", {"repo_root": str(mimicus_root), "recreate": True}
    )
    task_id = index_response["result"]["task_id"]
    wait_for_task(mcp_client, task_id, timeout=300)

    # 4. Generate implementation plan from HLD/LLD
    plan_response = mcp_client.call_tool(
        "generate_plan",
        {
            "repo_root": str(mimicus_root),
            "feature_description": "Read HLD.md and LLD.md. Build complete FastAPI mock.",
        },
    )
    task_id = plan_response["result"]["task_id"]
    plan_result = wait_for_task(mcp_client, task_id, timeout=600)
    assert plan_result.get("success")

    # 5. Autonomous execution loop
    max_iterations = 10
    mvp_ready = False

    for _ in range(max_iterations):
        # Execute work
        work_response = mcp_client.call_tool(
            "execute_work", {"repo_root": str(mimicus_root), "pattern": None, "dry_run": False}
        )
        task_id = work_response["result"]["task_id"]
        work_result = wait_for_task(mcp_client, task_id, timeout=600)

        if not work_result.get("success"):
            break

        # Review code
        review_response = mcp_client.call_tool(
            "review_code", {"repo_root": str(mimicus_root), "pr_url_or_id": "latest"}
        )
        task_id = review_response["result"]["task_id"]
        wait_for_task(mcp_client, task_id, timeout=300)

        # Check policies
        check_response = mcp_client.call_tool(
            "check_policies", {"repo_root": str(mimicus_root), "auto_fix": True}
        )
        check_result = check_response["result"]

        if check_result.get("exit_code") != 0:
            # Create todos for violations
            triage_response = mcp_client.call_tool(
                "triage_issues", {"repo_root": str(mimicus_root), "pattern": "policy"}
            )
            task_id = triage_response["result"]["task_id"]
            wait_for_task(mcp_client, task_id, timeout=300)
            continue

        # Try to run mimicus
        try:
            proc = subprocess.Popen(
                ["uvicorn", "main:app", "--port", "8888"],
                cwd=mimicus_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            time.sleep(5)

            # Test basic endpoint
            response = requests.get("http://localhost:8888/", timeout=5)
            if response.status_code == 200:
                mvp_ready = True
                proc.terminate()
                proc.wait(timeout=5)
                break

            proc.terminate()
            proc.wait(timeout=5)

        except Exception as e:
            # Failed to run - create todo
            mcp_client.call_tool(
                "codify_feedback",
                {
                    "repo_root": str(mimicus_root),
                    "feedback": f"Runtime error: {e}. Fix and retry.",
                    "source": "autonomous_test",
                },
            )
            continue

    assert mvp_ready, f"Failed to build mimicus MVP in {max_iterations} iterations"
