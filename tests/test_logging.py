"""Tests for logging and debugging functionality."""

import os
import sys
import pytest
import logging
import tempfile
from pathlib import Path
from io import StringIO

from src.cli import configure_logging, parse_args, run_search, ToolConfig, main


class TestConfigureLogging:
    """Tests for logging configuration."""

    def test_default_mode_minimal_output(self, capsys, caplog):
        """Test default mode shows only warnings and errors."""
        configure_logging(verbose=False, quiet=False)

        logger = logging.getLogger("test_logger")
        logger.debug("This is a debug message")
        logger.info("This is an info message")
        logger.warning("This is a warning message")
        logger.error("This is an error message")

        captured = capsys.readouterr()

        # Only WARNING and ERROR should appear in stderr
        assert "debug message" not in captured.err.lower()
        assert "info message" not in captured.err.lower()
        assert "warning message" in captured.err.lower()
        assert "error message" in captured.err.lower()

    def test_verbose_mode_shows_debug(self, capsys):
        """Test verbose mode shows debug messages."""
        configure_logging(verbose=True, quiet=False)

        logger = logging.getLogger("test_logger")
        logger.debug("Debug message in verbose")
        logger.info("Info message in verbose")

        captured = capsys.readouterr()

        # All levels should appear
        assert "debug message" in captured.err.lower()
        assert "info message" in captured.err.lower()

    def test_quiet_mode_only_errors(self, capsys):
        """Test quiet mode shows only errors."""
        configure_logging(verbose=False, quiet=True)

        logger = logging.getLogger("test_logger")
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")

        captured = capsys.readouterr()

        # Only ERROR should appear
        assert "debug message" not in captured.err.lower()
        assert "info message" not in captured.err.lower()
        assert "warning message" not in captured.err.lower()
        assert "error message" in captured.err.lower()

    def test_log_file_creation(self):
        """Test that log file is created with debug content."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
            log_file = f.name

        try:
            # Remove the file so we can test creation
            Path(log_file).unlink(missing_ok=True)

            configure_logging(verbose=False, quiet=False, log_file=log_file)

            logger = logging.getLogger("test_logger")
            logger.debug("Debug to file")
            logger.info("Info to file")
            logger.warning("Warning to file")
            logger.error("Error to file")

            # Verify file was created
            assert Path(log_file).exists()

            # Read log file content
            with open(log_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # All messages should be in the log file (DEBUG level)
            assert "Debug to file" in content
            assert "Info to file" in content
            assert "Warning to file" in content
            assert "Error to file" in content

        finally:
            Path(log_file).unlink(missing_ok=True)

    def test_debug_env_var_enables_debug(self, capsys, monkeypatch):
        """Test DEBUG environment variable enables debug logging."""
        monkeypatch.setenv('DEBUG', 'true')

        configure_logging(verbose=False, quiet=False)

        logger = logging.getLogger("test_logger")
        logger.debug("Debug via env var")

        captured = capsys.readouterr()
        assert "debug via env var" in captured.err.lower()

    def test_debug_env_var_variations(self, capsys, monkeypatch):
        """Test various DEBUG env var values."""
        test_cases = [
            ('true', True),
            ('TRUE', True),
            ('1', True),
            ('yes', True),
            ('YES', True),
            ('false', False),
            ('0', False),
            ('', False),
        ]

        for env_value, should_debug in test_cases:
            monkeypatch.setenv('DEBUG', env_value)
            configure_logging(verbose=False, quiet=False)

            logger = logging.getLogger("test_logger")
            logger.debug(f"Debug test for {env_value}")

            captured = capsys.readouterr()

            if should_debug:
                assert "debug test" in captured.err.lower(), f"Expected debug for DEBUG={env_value}"
            else:
                assert "debug test" not in captured.err.lower(), f"Unexpected debug for DEBUG={env_value}"

    def test_verbose_log_format_includes_function(self, capsys):
        """Test verbose mode includes function name in format."""
        configure_logging(verbose=True)

        logger = logging.getLogger("test_logger")
        logger.debug("Test message")

        captured = capsys.readouterr()
        # Should include timestamp, module name, function name
        assert "test_logger" in captured.err
        assert "test_verbose_log_format_includes_function" in captured.err

    def test_normal_log_format_simple(self, capsys):
        """Test normal mode has simple format."""
        configure_logging(verbose=False, quiet=False)

        logger = logging.getLogger("test_logger")
        logger.warning("Warning message")

        captured = capsys.readouterr()
        # Should be simple format: "WARNING: message"
        assert "WARNING:" in captured.err
        assert "warning message" in captured.err.lower()
        # Should NOT include function name in normal mode
        assert "test_normal_log_format_simple" not in captured.err

    def test_quiet_log_format_simple(self, capsys):
        """Test quiet mode has simple error format."""
        configure_logging(verbose=False, quiet=True)

        logger = logging.getLogger("test_logger")
        logger.error("Error message")

        captured = capsys.readouterr()
        # Should be simple format: "ERROR: message"
        assert "ERROR:" in captured.err
        assert "error message" in captured.err.lower()


class TestLoggingIntegration:
    """Integration tests for logging with actual search operations."""

    def test_normal_search_no_debug_output(self, capsys):
        """Test normal search doesn't show debug/info in output."""
        config = ToolConfig(
            query="AI agents",
            max_results=3,
            format="text",
            verbose=False,
            quiet=False
        )

        configure_logging(verbose=False, quiet=False)
        run_search(config)

        captured = capsys.readouterr()

        # stdout should have results
        assert "result" in captured.out.lower()

        # stderr should NOT have debug/info
        assert "debug" not in captured.err.lower()
        assert "validating query" not in captured.err.lower()

    def test_verbose_search_shows_debug(self, capsys):
        """Test verbose search shows debug messages."""
        config = ToolConfig(
            query="AI agents",
            max_results=3,
            format="text",
            verbose=True,
            quiet=False
        )

        configure_logging(verbose=True, quiet=False)
        run_search(config)

        captured = capsys.readouterr()

        # stdout should have results
        assert "result" in captured.out.lower()

        # stderr should have debug messages
        assert "debug" in captured.err.lower() or "validating query" in captured.err.lower()

    def test_quiet_search_no_info_output(self, capsys):
        """Test quiet search suppresses info output."""
        config = ToolConfig(
            query="Python",
            max_results=2,
            format="text",
            verbose=False,
            quiet=True
        )

        configure_logging(verbose=False, quiet=True)
        run_search(config)

        captured = capsys.readouterr()

        # stdout should have results
        assert "result" in captured.out.lower()

        # stderr should be empty or minimal (no info/debug/warning)
        # Only errors would appear in quiet mode
        stderr_lower = captured.err.lower()
        assert "info" not in stderr_lower
        assert "debug" not in stderr_lower

    def test_error_logged_with_context(self, capsys, caplog):
        """Test errors are logged with context."""
        config = ToolConfig(
            input_file="/tmp/nonexistent_file_for_logging_test.txt",
            format="text",
            verbose=True
        )

        configure_logging(verbose=True, quiet=False)

        with pytest.raises(SystemExit) as exc_info:
            run_search(config)

        assert exc_info.value.code == 1

        # Check error was logged
        captured = capsys.readouterr()
        assert "error" in captured.err.lower()
        assert "not found" in captured.err.lower()

    def test_log_file_captures_all_operations(self):
        """Test log file captures all operations including debug."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
            log_file = f.name

        try:
            Path(log_file).unlink(missing_ok=True)

            config = ToolConfig(
                query="Python CLI",
                max_results=2,
                format="text",
                verbose=False,
                quiet=False,
                log_file=log_file
            )

            configure_logging(verbose=False, quiet=False, log_file=log_file)
            run_search(config)

            # Read log file
            with open(log_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Log file should have debug info even in normal mode
            assert "Validating query" in content or "validating" in content.lower()
            assert "Python CLI" in content

        finally:
            Path(log_file).unlink(missing_ok=True)


class TestCLILoggingFlags:
    """Tests for CLI argument parsing with logging flags."""

    def test_quiet_flag_parsed(self):
        """Test --quiet flag is parsed correctly."""
        config = parse_args(["search", "test", "--quiet"])
        assert config.quiet is True

    def test_quiet_short_flag(self):
        """Test -q flag is parsed correctly."""
        config = parse_args(["search", "test", "-q"])
        assert config.quiet is True

    def test_log_file_flag_parsed(self):
        """Test --log-file flag is parsed correctly."""
        config = parse_args(["search", "test", "--log-file", "/tmp/test.log"])
        assert config.log_file == "/tmp/test.log"

    def test_verbose_and_log_file_combined(self):
        """Test verbose and log-file flags work together."""
        config = parse_args(["search", "test", "--verbose", "--log-file", "/tmp/test.log"])
        assert config.verbose is True
        assert config.log_file == "/tmp/test.log"

    def test_quiet_overrides_verbose(self):
        """Test that quiet and verbose can both be set (quiet takes precedence)."""
        # Note: In the implementation, quiet should take precedence
        config = parse_args(["search", "test", "--verbose", "--quiet"])
        assert config.verbose is True
        assert config.quiet is True

        # When both are set, configure_logging should respect quiet
        # (This is tested in test_configure_logging_both_flags)

    def test_configure_logging_both_flags(self, capsys):
        """Test configure_logging when both verbose and quiet are set."""
        # Quiet should take precedence
        configure_logging(verbose=True, quiet=True)

        logger = logging.getLogger("test_logger")
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")

        captured = capsys.readouterr()

        # Only errors should appear (quiet mode takes precedence)
        assert "debug message" not in captured.err.lower()
        assert "info message" not in captured.err.lower()
        assert "warning message" not in captured.err.lower()
        assert "error message" in captured.err.lower()


class TestLoggingEdgeCases:
    """Edge case tests for logging."""

    def test_log_file_with_nested_directory(self):
        """Test log file creation in nested directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "logs", "nested", "test.log")

            configure_logging(verbose=False, quiet=False, log_file=log_file)

            logger = logging.getLogger("test_logger")
            logger.info("Test message")

            # Directory should be created automatically
            assert Path(log_file).exists()
            assert Path(log_file).parent.exists()

    def test_multiple_configure_logging_calls(self, capsys):
        """Test that multiple configure_logging calls don't duplicate handlers."""
        configure_logging(verbose=True)
        configure_logging(verbose=True)  # Call again

        logger = logging.getLogger("test_logger")
        logger.debug("Single message")

        captured = capsys.readouterr()

        # Message should appear only once (no duplicate handlers)
        count = captured.err.lower().count("single message")
        assert count == 1, f"Expected 1 occurrence, found {count}"

    def test_log_file_encoding_utf8(self):
        """Test log file uses UTF-8 encoding."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
            log_file = f.name

        try:
            Path(log_file).unlink(missing_ok=True)

            configure_logging(verbose=False, quiet=False, log_file=log_file)

            logger = logging.getLogger("test_logger")
            logger.info("Unicode test: 日本語 中文 한글 🎉")

            # Read with UTF-8 encoding
            with open(log_file, 'r', encoding='utf-8') as f:
                content = f.read()

            assert "日本語" in content
            assert "中文" in content
            assert "한글" in content
            assert "🎉" in content

        finally:
            Path(log_file).unlink(missing_ok=True)
