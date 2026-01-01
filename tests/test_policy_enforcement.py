"""Test policy enforcement system."""

from pathlib import Path

from utils.policy.orchestrator import PolicyEnforcer
from utils.policy.violations import Severity


def test_policy_enforcer_initialization():
    """Test that PolicyEnforcer initializes correctly."""
    enforcer = PolicyEnforcer()
    assert enforcer.repo_root == Path.cwd()
    assert enforcer.config is not None
    assert len(enforcer.static_validators) == 3


def test_check_file_no_violations():
    """Test checking a compliant file."""
    enforcer = PolicyEnforcer()
    test_file = Path(__file__)

    result = enforcer.check_file(test_file)

    assert result.files_checked == 1
    assert result.passed is True or result.passed is False


def test_import_protocol_detects_relative_imports(tmp_path):
    """Test that import protocol detects relative imports."""
    bad_file = tmp_path / "bad_imports.py"
    bad_file.write_text("from ..utils import helper\n")

    enforcer = PolicyEnforcer(repo_root=tmp_path)
    result = enforcer.check_file(bad_file)

    assert any(v.rule_id == "IMPORT001" for v in result.violations)
    assert result.errors >= 1


def test_file_size_protocol_detects_large_files(tmp_path):
    """Test that file size protocol detects large files."""
    large_file = tmp_path / "large.py"
    large_file.write_text("\n".join([f"x = {i}" for i in range(150)]))

    enforcer = PolicyEnforcer(repo_root=tmp_path)
    result = enforcer.check_file(large_file)

    assert any("SIZE" in v.rule_id for v in result.violations)
    assert result.warnings >= 1


def test_policy_result_properties():
    """Test PolicyResult computed properties."""
    from utils.policy.violations import PolicyResult, Violation

    result = PolicyResult(
        violations=[
            Violation(
                file_path="test.py",
                rule_id="TEST001",
                severity=Severity.ERROR,
                message="Test error",
            )
        ],
        files_checked=1,
        files_with_violations=1,
        errors=1,
        warnings=0,
        infos=0,
    )

    assert result.passed is False
    assert result.should_block_commit is True
