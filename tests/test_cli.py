"""Tests for CLI argument parsing."""

import sys
import pytest
from io import StringIO
from pathlib import Path
import tempfile
import json

from src.cli import parse_args, ToolConfig, run_search, configure_logging


class TestParseArgs:
    """Tests for argument parsing."""

    def test_help_flag(self, capsys):
        """Test that --help flag displays usage information."""
        with pytest.raises(SystemExit) as exc_info:
            parse_args(["--help"])

        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "usage:" in captured.out.lower()
        assert "Token-Efficient Search API" in captured.out

    def test_search_with_query(self):
        """Test search command with a query."""
        config = parse_args(["search", "test query"])

        assert isinstance(config, ToolConfig)
        assert config.query == "test query"
        assert config.max_results == 5
        assert config.format == "text"
        assert config.verbose is False

    def test_verbose_flag(self):
        """Test --verbose flag."""
        config = parse_args(["search", "test", "--verbose"])

        assert config.verbose is True

    def test_format_options(self):
        """Test --format options."""
        # Test JSON format
        config = parse_args(["search", "test", "--format", "json"])
        assert config.format == "json"

        # Test text format
        config = parse_args(["search", "test", "--format", "text"])
        assert config.format == "text"

        # Test compact format
        config = parse_args(["search", "test", "--format", "compact"])
        assert config.format == "compact"

    def test_max_results_flag(self):
        """Test --max-results flag."""
        config = parse_args(["search", "test", "--max-results", "10"])

        assert config.max_results == 10

    def test_short_flags(self):
        """Test short flag versions."""
        config = parse_args(["search", "test", "-v", "-f", "json", "-n", "3"])

        assert config.verbose is True
        assert config.format == "json"
        assert config.max_results == 3

    def test_missing_command(self, capsys):
        """Test that missing command shows error."""
        with pytest.raises(SystemExit) as exc_info:
            parse_args([])

        assert exc_info.value.code == 1

    def test_missing_query_and_input(self, capsys):
        """Test that missing query and input file shows error."""
        with pytest.raises(SystemExit) as exc_info:
            parse_args(["search"])

        assert exc_info.value.code == 2
        captured = capsys.readouterr()
        assert "Either provide a query or use --input" in captured.err

    def test_input_flag(self):
        """Test --input flag."""
        config = parse_args(["search", "--input", "queries.txt"])

        assert config.input_file == "queries.txt"
        assert config.query is None

    def test_output_flag(self):
        """Test --output flag."""
        config = parse_args(["search", "test", "--output", "results.json"])

        assert config.output_file == "results.json"

    def test_combined_flags(self):
        """Test multiple flags together."""
        config = parse_args([
            "search", "AI agents",
            "--verbose",
            "--format", "compact",
            "--max-results", "8",
            "--output", "out.txt"
        ])

        assert config.query == "AI agents"
        assert config.verbose is True
        assert config.format == "compact"
        assert config.max_results == 8
        assert config.output_file == "out.txt"


class TestRunSearch:
    """Tests for search execution."""

    def test_search_with_query(self, capsys):
        """Test search execution with a direct query."""
        config = ToolConfig(
            query="AI agents",
            max_results=5,
            format="text"
        )

        configure_logging(verbose=False)
        run_search(config)

        captured = capsys.readouterr()
        assert "result(s)" in captured.out
        assert "Relevance:" in captured.out

    def test_search_with_json_format(self, capsys):
        """Test search with JSON output format."""
        config = ToolConfig(
            query="Python",
            format="json"
        )

        configure_logging(verbose=False)
        run_search(config)

        captured = capsys.readouterr()
        # Verify it's valid JSON
        results = json.loads(captured.out)
        assert isinstance(results, list)
        assert len(results) > 0

    def test_search_with_compact_format(self, capsys):
        """Test search with compact output format."""
        config = ToolConfig(
            query="Python",
            format="compact"
        )

        configure_logging(verbose=False)
        run_search(config)

        captured = capsys.readouterr()
        assert "|" in captured.out or "." in captured.out  # Compact format uses pipes or dots

    def test_search_with_output_file(self):
        """Test search with output file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            output_file = f.name

        try:
            config = ToolConfig(
                query="Python",
                output_file=output_file,
                format="text"
            )

            configure_logging(verbose=False)
            run_search(config)

            # Verify file was created and contains results
            with open(output_file, 'r', encoding='utf-8') as f:
                content = f.read()
                assert "result(s)" in content
                assert "Relevance:" in content
        finally:
            Path(output_file).unlink(missing_ok=True)

    def test_search_with_input_file(self, capsys):
        """Test search with input file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("AI agents Python")
            input_file = f.name

        try:
            config = ToolConfig(
                input_file=input_file,
                format="text"
            )

            configure_logging(verbose=False)
            run_search(config)

            captured = capsys.readouterr()
            assert "result(s)" in captured.out
            assert "Relevance:" in captured.out
        finally:
            Path(input_file).unlink(missing_ok=True)

    def test_search_with_missing_input_file(self, capsys):
        """Test search with non-existent input file."""
        config = ToolConfig(
            input_file="/nonexistent/file.txt",
            format="text"
        )

        configure_logging(verbose=False)

        with pytest.raises(SystemExit) as exc_info:
            run_search(config)

        assert exc_info.value.code == 1

    def test_search_with_invalid_query(self, capsys):
        """Test search with invalid (empty) query."""
        config = ToolConfig(
            query="",
            format="text"
        )

        configure_logging(verbose=False, quiet=False)

        with pytest.raises(SystemExit) as exc_info:
            run_search(config)

        assert exc_info.value.code == 1
        # Check that error was logged
        captured = capsys.readouterr()
        assert "Invalid query" in captured.err or "cannot be empty" in captured.err

    def test_search_with_stdin(self, monkeypatch, capsys):
        """Test search with stdin input."""
        from io import StringIO
        stdin_input = StringIO("AI agents")
        monkeypatch.setattr('sys.stdin', stdin_input)

        config = ToolConfig(query="-", format="text")
        configure_logging(verbose=False)
        run_search(config)

        captured = capsys.readouterr()
        assert "result(s)" in captured.out.lower() or "Result" in captured.out


class TestConfigureLogging:
    """Tests for logging configuration."""

    def test_configure_logging_normal(self):
        """Test logging configuration in normal mode."""
        configure_logging(verbose=False)
        # No assertions needed - just verify it doesn't crash

    def test_configure_logging_verbose(self):
        """Test logging configuration in verbose mode."""
        configure_logging(verbose=True)
        # No assertions needed - just verify it doesn't crash
