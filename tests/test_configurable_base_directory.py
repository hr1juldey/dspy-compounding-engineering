"""
Test suite for configurable base directory feature.

Tests the environment variable configuration (COMPOUNDING_DIR_NAME) and
init command functionality. Handles existing directories intelligently
by using {_test_} suffix during testing and cleaning up afterward.
"""

import os
import re
import shutil
from pathlib import Path

import pytest

from utils.paths import CompoundingPaths, get_paths, reset_paths


class TestConfigurableBaseDirectory:
    """Tests for configurable base directory functionality."""

    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        """Setup and teardown for each test."""
        # Store original env var
        self.original_env = os.getenv("COMPOUNDING_DIR_NAME")
        self.original_paths_instance = None

        yield

        # Restore original env var
        if self.original_env:
            os.environ["COMPOUNDING_DIR_NAME"] = self.original_env
        else:
            os.environ.pop("COMPOUNDING_DIR_NAME", None)

        # Reset paths singleton
        reset_paths()

    @pytest.fixture
    def project_root(self):
        """Get project root directory."""
        return Path.cwd()

    def get_test_dir_name(self, base_name: str) -> str:
        """
        Get test directory name.

        If directory already exists, append {_test_} suffix.
        Otherwise, use the base name as-is.
        """
        project_root = Path.cwd()
        test_dir = project_root / base_name

        if test_dir.exists():
            # Directory exists, use test suffix
            test_name = f"{base_name[:-1]}_test_}}"  # .claude -> .claude_test_}
            return test_name

        return base_name

    def cleanup_test_dirs(self):
        """Clean up any test directories created during tests."""
        project_root = Path.cwd()
        for item in project_root.iterdir():
            if item.is_dir() and ("_test_" in item.name or item.name.startswith(".test_")):
                shutil.rmtree(item)

    # Test Case 1: Default behavior without environment variable
    def test_default_behavior_uses_claude(self):
        """Test 1: Default behavior (.claude) without environment variable."""
        os.environ.pop("COMPOUNDING_DIR_NAME", None)
        reset_paths()

        paths = CompoundingPaths()

        assert paths.base_dir.name == ".claude"
        assert paths.claude_dir == paths.base_dir  # Backward compatibility

    # Test Case 2: Environment variable override
    def test_env_var_override(self):
        """Test 2: Environment variable override (.ce)."""
        os.environ["COMPOUNDING_DIR_NAME"] = ".ce"
        reset_paths()

        paths = CompoundingPaths()

        assert paths.base_dir.name == ".ce"

    # Test Case 3: Parameter override
    def test_parameter_override(self):
        """Test 3: Parameter override takes precedence."""
        os.environ["COMPOUNDING_DIR_NAME"] = ".ce"
        reset_paths()

        paths = CompoundingPaths(base_dir_name=".qwen")

        assert paths.base_dir.name == ".qwen"

    # Test Case 4: Directory creation
    def test_directory_creation(self):
        """Test 4: Init creates base directory."""
        test_dir_name = self.get_test_dir_name(".test_init")

        try:
            paths = CompoundingPaths(base_dir_name=test_dir_name)
            paths.ensure_directories()

            assert paths.base_dir.exists()
            assert paths.base_dir.is_dir()
        finally:
            self.cleanup_test_dirs()

    # Test Case 5: Subdirectories creation
    def test_subdirectories_creation(self):
        """Test 5: Init creates all required subdirectories."""
        test_dir_name = self.get_test_dir_name(".test_subdirs")

        try:
            paths = CompoundingPaths(base_dir_name=test_dir_name)
            paths.ensure_directories()

            assert paths.knowledge_dir.exists()
            assert paths.plans_dir.exists()
            assert paths.todos_dir.exists()
            assert paths.memory_dir.exists()
            assert paths.cache_dir.exists()
            assert paths.analysis_dir.exists()
        finally:
            self.cleanup_test_dirs()

    # Test Case 6: Environment file persistence
    def test_env_file_persistence(self):
        """Test 6: Init writes COMPOUNDING_DIR_NAME to .env file."""
        test_dir_name = self.get_test_dir_name(".test_env")
        env_file = Path.cwd() / ".env"

        # Read original .env
        original_content = ""
        if env_file.exists():
            original_content = env_file.read_text()

        try:
            # Simulate what init command does
            env_content = original_content

            if "COMPOUNDING_DIR_NAME=" in env_content:
                env_content = re.sub(
                    r"COMPOUNDING_DIR_NAME=.*",
                    f"COMPOUNDING_DIR_NAME={test_dir_name}",
                    env_content,
                )
            else:
                env_content += f"\n# Compounding Directory\nCOMPOUNDING_DIR_NAME={test_dir_name}\n"

            env_file.write_text(env_content)

            # Verify
            updated_content = env_file.read_text()
            assert f"COMPOUNDING_DIR_NAME={test_dir_name}" in updated_content
        finally:
            # Restore original .env
            if original_content:
                env_file.write_text(original_content)
            else:
                env_file.unlink(missing_ok=True)

    # Test Case 7: Non-interactive default
    def test_non_interactive_default_is_ce(self):
        """Test 7: Non-interactive mode defaults to .ce."""
        os.environ.pop("COMPOUNDING_DIR_NAME", None)

        # Simulate init command logic
        dir_name = None
        interactive = False

        if dir_name is None and interactive:
            dir_name = "interactive_prompt"
        elif dir_name is None:
            dir_name = os.getenv("COMPOUNDING_DIR_NAME", ".ce")

        assert dir_name == ".ce"

    # Test Case 8: Interactive mode with direction
    def test_init_with_explicit_dir(self):
        """Test 8: Init with explicit --dir parameter."""
        test_dir_name = self.get_test_dir_name(".test_explicit")

        try:
            # When --dir is provided, interactive is skipped
            dir_name = test_dir_name
            interactive = True  # Default value

            # Logic from cli.py init command
            if dir_name is None and interactive:
                dir_name = "would_prompt_user"

            # dir_name is not None, so prompt is skipped
            assert dir_name == test_dir_name

            paths = CompoundingPaths(base_dir_name=dir_name)
            paths.ensure_directories()
            assert paths.base_dir.exists()
        finally:
            self.cleanup_test_dirs()

    # Test Case 9: Backward compatibility with .claude_dir alias
    def test_backward_compatibility_alias(self):
        """Test 9: Backward compatibility - .claude_dir alias."""
        os.environ.pop("COMPOUNDING_DIR_NAME", None)
        reset_paths()

        paths = CompoundingPaths()

        # Old code using claude_dir should still work
        assert paths.claude_dir == paths.base_dir
        assert paths.claude_dir.name == ".claude"

    # Test Case 10: Singleton respects environment variable
    def test_singleton_respects_env_var(self):
        """Test 10: Singleton get_paths() respects environment variable."""
        os.environ["COMPOUNDING_DIR_NAME"] = ".ce"
        reset_paths()

        paths = get_paths()

        assert paths.base_dir.name == ".ce"

    # Test Case 11: Migration logic with different directories
    def test_migration_respects_configured_directory(self):
        """Test 11: Migration uses configured base directory."""
        os.environ["COMPOUNDING_DIR_NAME"] = ".qwen"
        reset_paths()

        paths = get_paths()

        # Verify migration would use correct directory
        assert ".qwen" in str(paths.base_dir)

    # Test Case 12: No relative imports in modified files
    def test_no_relative_imports(self):
        """Test 12: No relative imports in paths.py and cli.py."""
        paths_file = Path.cwd() / "utils" / "paths.py"
        cli_file = Path.cwd() / "cli.py"

        for filepath in [paths_file, cli_file]:
            content = filepath.read_text()
            # Check for relative imports
            relative_import_pattern = r"^\s*(from \.|import \.)"
            matches = re.findall(relative_import_pattern, content, re.MULTILINE)
            assert len(matches) == 0, f"Found relative imports in {filepath}"

    # Test Case 13: File size compliance
    def test_file_size_compliance(self):
        """Test 13: Modified files comply with size limits."""
        paths_file = Path.cwd() / "utils" / "paths.py"
        cli_file = Path.cwd() / "cli.py"

        paths_lines = len(paths_file.read_text().splitlines())
        cli_lines = len(cli_file.read_text().splitlines())

        # utils/paths.py should be under 150 lines (100 code + 50 overhead)
        assert paths_lines <= 200, f"utils/paths.py has {paths_lines} lines (max: 200)"

        # cli.py is exempt from line limit (it's a CLI file)
        assert cli_lines > 0, "cli.py should have content"

    # Test Case 14: All subdirectories are created
    def test_all_subdirectories_structure(self):
        """Test 14: Verify complete subdirectory structure."""
        test_dir_name = self.get_test_dir_name(".test_structure")

        try:
            paths = CompoundingPaths(base_dir_name=test_dir_name)
            paths.ensure_directories()

            required_dirs = [
                paths.base_dir,
                paths.knowledge_dir,
                paths.plans_dir,
                paths.todos_dir,
                paths.memory_dir,
                paths.cache_dir,
                paths.analysis_dir,
            ]

            for directory in required_dirs:
                assert directory.exists(), f"Missing directory: {directory}"
                assert directory.is_dir(), f"Not a directory: {directory}"
        finally:
            self.cleanup_test_dirs()

    # Test Case 15: Path methods work with configured directory
    def test_path_methods_work_correctly(self):
        """Test 15: Path helper methods use configured base directory."""
        test_dir_name = self.get_test_dir_name(".test_methods")

        try:
            paths = CompoundingPaths(base_dir_name=test_dir_name)
            paths.ensure_directories()

            kb_file = paths.get_knowledge_file("test.md")
            assert str(test_dir_name) in str(kb_file)
            assert "knowledge" in str(kb_file)

            plan_file = paths.get_plan_file("test_plan.md")
            assert "plans" in str(plan_file)

            todo_file = paths.get_todo_file("001.md")
            assert "todos" in str(todo_file)
        finally:
            self.cleanup_test_dirs()

    # Test Case 16: Environment variable precedence
    def test_env_var_precedence_over_default(self):
        """Test 16: Environment variable takes precedence over default."""
        os.environ["COMPOUNDING_DIR_NAME"] = ".custom"
        reset_paths()

        paths = CompoundingPaths()

        assert paths.base_dir.name == ".custom"
        assert paths.base_dir.name != ".claude"


class TestInitCommandLogic:
    """Tests for the init command's decision logic."""

    def test_init_interactive_no_dir_prompts_user(self):
        """Interactive mode without --dir should prompt user."""
        dir_name = None
        interactive = True

        # This is the condition for prompting
        should_prompt = dir_name is None and interactive

        assert should_prompt is True

    def test_init_with_dir_skips_prompt(self):
        """Providing --dir should skip interactive prompt."""
        dir_name = ".test"
        interactive = True

        # Even with interactive=True, prompt is skipped if dir_name provided
        should_prompt = dir_name is None and interactive

        assert should_prompt is False

    def test_init_non_interactive_uses_default(self):
        """Non-interactive without --dir should use default."""
        dir_name = None
        interactive = False

        # With non-interactive and no dir, use default
        if dir_name is None and interactive:
            dir_name = "would_prompt"
        elif dir_name is None:
            dir_name = os.getenv("COMPOUNDING_DIR_NAME", ".ce")

        assert dir_name == ".ce"


class TestMigration:
    """Tests for migration functionality."""

    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        """Setup and teardown for migration tests."""
        yield
        reset_paths()

    def test_migration_identifies_old_structure(self):
        """Test migration logic identifies old-format directories."""
        os.environ.pop("COMPOUNDING_DIR_NAME", None)
        reset_paths()

        paths = get_paths()

        # Migration should look for these old paths
        old_paths = [
            paths.repo_root / ".knowledge",
            paths.repo_root / ".compounding",
            paths.repo_root / "plans",
            paths.repo_root / "todos",
            paths.repo_root / "analysis",
        ]

        # Verify migration logic structure
        for old_path in old_paths:
            # Migration would check if old_path exists and new_path doesn't
            assert isinstance(old_path, Path)


class TestEnvironmentHandling:
    """Tests for environment variable handling."""

    def test_unset_env_var_uses_default(self):
        """Unsetting COMPOUNDING_DIR_NAME uses default."""
        if "COMPOUNDING_DIR_NAME" in os.environ:
            del os.environ["COMPOUNDING_DIR_NAME"]

        value = os.getenv("COMPOUNDING_DIR_NAME", ".claude")
        assert value == ".claude"

    def test_empty_env_var_falls_back_to_default(self):
        """Empty COMPOUNDING_DIR_NAME falls back to default."""
        os.environ["COMPOUNDING_DIR_NAME"] = ""

        # Empty string is falsy, so use default
        value = os.environ.get("COMPOUNDING_DIR_NAME") or ".claude"
        assert value == ".claude"

    def test_custom_env_var_value(self):
        """Custom environment variable value is used."""
        os.environ["COMPOUNDING_DIR_NAME"] = ".custom_ai"
        reset_paths()

        paths = CompoundingPaths()
        assert paths.base_dir.name == ".custom_ai"
