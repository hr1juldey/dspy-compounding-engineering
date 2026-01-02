"""
Basic MCP tools validation tests.

These tests validate that MCP tools can be imported and have correct structure.
"""

from pathlib import Path


def test_all_tool_modules_import():
    """Test that all tool modules can be imported."""
    import server.mcp.tools.analysis
    import server.mcp.tools.execution
    import server.mcp.tools.knowledge
    import server.mcp.tools.repository
    import server.mcp.tools.system

    assert server.mcp.tools.analysis is not None
    assert server.mcp.tools.execution is not None
    assert server.mcp.tools.knowledge is not None
    assert server.mcp.tools.repository is not None
    assert server.mcp.tools.system is not None


def test_mcp_server_can_be_imported():
    """Test that MCP server module can be imported."""
    from server.mcp import server

    assert server.mcp is not None


def test_all_services_exist():
    """Test that all required service classes exist."""
    from server.application.services.analyze_service import AnalyzeService
    from server.application.services.check_service import CheckService
    from server.application.services.codify_service import CodifyService
    from server.application.services.compress_kb_service import CompressKBService
    from server.application.services.garden_service import GardenService
    from server.application.services.generate_command_service import GenerateCommandService
    from server.application.services.index_codebase_service import IndexCodebaseService
    from server.application.services.plan_service import PlanService
    from server.application.services.repo_service import RepoService
    from server.application.services.review_service import ReviewService
    from server.application.services.triage_service import TriageService
    from server.application.services.work_service import WorkService

    services = [
        AnalyzeService,
        CheckService,
        CodifyService,
        CompressKBService,
        GardenService,
        GenerateCommandService,
        IndexCodebaseService,
        PlanService,
        RepoService,
        ReviewService,
        TriageService,
        WorkService,
    ]

    for service in services:
        assert service is not None


def test_all_celery_tasks_exist():
    """Test that all required Celery tasks exist."""
    from server.infrastructure.celery.tasks.analyze import analyze_code_task
    from server.infrastructure.celery.tasks.check import check_policies_task
    from server.infrastructure.celery.tasks.codify import codify_task
    from server.infrastructure.celery.tasks.compress_kb import compress_kb_task
    from server.infrastructure.celery.tasks.garden import garden_task
    from server.infrastructure.celery.tasks.generate_command import generate_command_task
    from server.infrastructure.celery.tasks.index_codebase import index_codebase_task
    from server.infrastructure.celery.tasks.plan import generate_plan_task
    from server.infrastructure.celery.tasks.review import review_code_task
    from server.infrastructure.celery.tasks.triage import triage_task
    from server.infrastructure.celery.tasks.work import execute_work_task

    tasks = [
        analyze_code_task,
        check_policies_task,
        codify_task,
        compress_kb_task,
        garden_task,
        generate_command_task,
        index_codebase_task,
        generate_plan_task,
        review_code_task,
        triage_task,
        execute_work_task,
    ]

    for task in tasks:
        assert task is not None


def test_tool_modules_pass_policy():
    """Test that all tool modules pass policy checks."""
    from utils.policy.orchestrator import PolicyEnforcer

    enforcer = PolicyEnforcer()

    tool_files = [
        Path("server/mcp/tools/analysis.py"),
        Path("server/mcp/tools/execution.py"),
        Path("server/mcp/tools/knowledge.py"),
        Path("server/mcp/tools/repository.py"),
        Path("server/mcp/tools/system.py"),
        Path("server/mcp/tools/__init__.py"),
    ]

    for file_path in tool_files:
        result = enforcer.check_file(file_path)
        error_violations = [v for v in result.violations if v.severity == "ERROR"]
        assert len(error_violations) == 0, f"{file_path} has ERROR violations: {error_violations}"
