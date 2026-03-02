"""Integration tests for the Token-Efficient Search API CLI."""

import subprocess
import sys
import os
import json
import tempfile
import pytest
from pathlib import Path

# Project root for consistent path handling across all tests
PROJECT_ROOT = str(Path(__file__).parent.parent.resolve())


def run_cli(args, stdin_input=None, env=None):
    """Helper to run CLI via subprocess."""
    cmd = [sys.executable, "-m", "src.cli"] + args
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT,
        input=stdin_input,
        env={**os.environ, **(env or {})},
        timeout=30
    )
    return result


class TestCLIEndToEnd:
    """End-to-end tests using subprocess to test actual CLI invocations."""

    def test_help_flag(self):
        """Test --help returns usage info."""
        result = run_cli(["--help"])
        assert result.returncode == 0
        assert "search" in result.stdout.lower()

    def test_search_help(self):
        """Test search --help returns detailed help."""
        result = run_cli(["search", "--help"])
        assert result.returncode == 0
        assert "--format" in result.stdout
        assert "--max-results" in result.stdout

    def test_basic_search(self):
        """Test basic search returns results."""
        result = run_cli(["search", "AI agents"])
        assert result.returncode == 0
        assert "result" in result.stdout.lower()

    def test_json_output(self):
        """Test JSON output is valid."""
        result = run_cli(["search", "AI agents", "--format", "json"])
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert isinstance(data, list)
        assert len(data) > 0
        assert "title" in data[0]

    def test_compact_output(self):
        """Test compact format output."""
        result = run_cli(["search", "AI agents", "--format", "compact"])
        assert result.returncode == 0
        assert "|" in result.stdout

    def test_max_results(self):
        """Test max results limits output."""
        result = run_cli(["search", "AI", "--format", "json", "--max-results", "2"])
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert len(data) <= 2

    def test_verbose_mode(self):
        """Test verbose shows debug output."""
        result = run_cli(["search", "AI agents", "--verbose"])
        assert result.returncode == 0
        assert "DEBUG" in result.stderr

    def test_quiet_mode(self):
        """Test quiet suppresses non-error output."""
        result = run_cli(["search", "AI agents", "--quiet"])
        assert result.returncode == 0
        # In quiet mode, stderr should have no DEBUG or INFO messages
        assert "DEBUG" not in result.stderr
        assert "INFO" not in result.stderr

    def test_debug_env_var(self):
        """Test DEBUG env var enables debug mode."""
        result = run_cli(["search", "AI agents"], env={"DEBUG": "true"})
        assert result.returncode == 0
        assert "DEBUG" in result.stderr

    def test_stdin_input(self):
        """Test stdin input with '-' query."""
        result = run_cli(["search", "-"], stdin_input="machine learning\n")
        assert result.returncode == 0
        assert "result" in result.stdout.lower()

    def test_file_input_txt(self):
        """Test reading queries from a .txt file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write("AI agents\nmachine learning\n")
            f.flush()
            input_file = f.name
        try:
            result = run_cli(["search", "--input", input_file])
            assert result.returncode == 0
            assert "result" in result.stdout.lower()
        finally:
            os.unlink(input_file)

    def test_file_input_json(self):
        """Test reading queries from a .json file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            json.dump(["vector database", "python cli"], f)
            f.flush()
            input_file = f.name
        try:
            result = run_cli(["search", "--input", input_file, "--format", "json"])
            assert result.returncode == 0
            data = json.loads(result.stdout)
            assert isinstance(data, list)
        finally:
            os.unlink(input_file)

    def test_file_output(self):
        """Test writing results to output file."""
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
            output_path = f.name
        try:
            result = run_cli(["search", "AI agents", "--output", output_path])
            assert result.returncode == 0
            with open(output_path, 'r', encoding='utf-8') as f:
                content = f.read()
            assert "result" in content.lower()
        finally:
            os.unlink(output_path)

    def test_full_pipeline(self):
        """Test complete pipeline: file input → search → file output."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as fin:
            fin.write("token optimization\nlanguage models\n")
            input_path = fin.name
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as fout:
            output_path = fout.name

        try:
            result = run_cli([
                "search", "--input", input_path,
                "--output", output_path,
                "--format", "json", "--max-results", "3"
            ])

            assert result.returncode == 0
            with open(output_path, 'r', encoding='utf-8') as f:
                data = json.loads(f.read())

            assert isinstance(data, list)
        finally:
            os.unlink(input_path)
            os.unlink(output_path)

    def test_log_file_creation(self):
        """Test log file is created with debug content."""
        with tempfile.NamedTemporaryFile(suffix='.log', delete=False) as f:
            log_path = f.name
        try:
            result = run_cli(["search", "AI agents", "--log-file", log_path])
            assert result.returncode == 0
            with open(log_path, 'r', encoding='utf-8') as f:
                content = f.read()
            assert "DEBUG" in content or "INFO" in content
        finally:
            os.unlink(log_path)

    def test_short_flags(self):
        """Test short flags work correctly."""
        result = run_cli(["search", "AI", "-v", "-f", "json", "-n", "3"])
        assert result.returncode == 0
        assert "DEBUG" in result.stderr
        data = json.loads(result.stdout)
        assert len(data) <= 3


class TestErrorHandling:
    """Test error conditions produce clear messages."""

    def test_no_command(self):
        """Test missing command shows help."""
        result = run_cli([])
        assert result.returncode != 0

    def test_no_query(self):
        """Test missing query shows error."""
        result = run_cli(["search"])
        assert result.returncode != 0

    def test_missing_input_file(self):
        """Test missing input file shows error."""
        result = run_cli(["search", "--input", "/tmp/nonexistent_file_xyz123.txt"])
        assert result.returncode != 0

    def test_forbidden_input_path(self):
        """Test path traversal blocked."""
        result = run_cli(["search", "--input", "/etc/passwd"])
        assert result.returncode != 0
        assert "forbidden" in result.stderr.lower()

    def test_invalid_max_results_negative(self):
        """Test negative max results rejected."""
        result = run_cli(["search", "test", "--max-results", "-1"])
        assert result.returncode != 0

    def test_invalid_max_results_zero(self):
        """Test zero max results rejected."""
        result = run_cli(["search", "test", "--max-results", "0"])
        assert result.returncode != 0

    def test_invalid_format(self):
        """Test invalid format rejected."""
        result = run_cli(["search", "test", "--format", "xml"])
        assert result.returncode != 0

    def test_invalid_max_results_string(self):
        """Test non-numeric max results rejected."""
        result = run_cli(["search", "test", "--max-results", "abc"])
        assert result.returncode != 0

    def test_invalid_max_results_too_large(self):
        """Test max results > 1000 rejected."""
        result = run_cli(["search", "test", "--max-results", "1001"])
        assert result.returncode != 0

    def test_empty_stdin(self):
        """Test empty stdin input shows error."""
        result = run_cli(["search", "-"], stdin_input="")
        assert result.returncode != 0


class TestSearchRelevance:
    """Integration tests for search quality and relevance."""

    def test_exact_match_high_relevance(self):
        """Test exact title match returns highest relevance."""
        result = run_cli(["search", "large language models", "--format", "json"])
        data = json.loads(result.stdout)
        if data:
            assert data[0]["relevance"] >= 0.5
            # Check that results have language-related terms
            assert any("language" in r["title"].lower() or "llm" in r["title"].lower() or "ai" in r["title"].lower() for r in data)

    def test_no_results_for_unrelated_query(self):
        """Test unrelated query returns few or no high-relevance results."""
        result = run_cli(["search", "underwater basket weaving xyz123", "--format", "json"])
        data = json.loads(result.stdout)
        # All results should have low relevance or be empty
        if data:
            assert all(r["relevance"] < 0.5 for r in data)

    def test_results_sorted_by_relevance(self):
        """Test results are sorted highest to lowest relevance."""
        result = run_cli(["search", "AI search optimization", "--format", "json"])
        data = json.loads(result.stdout)
        if len(data) > 1:
            for i in range(len(data) - 1):
                assert data[i]["relevance"] >= data[i+1]["relevance"]

    def test_token_counts_present(self):
        """Test all results include token counts."""
        result = run_cli(["search", "python", "--format", "json"])
        data = json.loads(result.stdout)
        for r in data:
            assert "token_count" in r
            assert r["token_count"] > 0

    def test_all_required_fields_present(self):
        """Test all results have required fields."""
        result = run_cli(["search", "API", "--format", "json"])
        data = json.loads(result.stdout)
        for r in data:
            assert "title" in r
            assert "snippet" in r
            assert "url" in r
            assert "relevance" in r
            assert "token_count" in r

    def test_relevance_scores_in_range(self):
        """Test relevance scores are between 0.0 and 1.0."""
        result = run_cli(["search", "machine learning", "--format", "json"])
        data = json.loads(result.stdout)
        for r in data:
            assert 0.0 <= r["relevance"] <= 1.0


class TestFileFormats:
    """Test different input and output file formats."""

    def test_json_input_file(self):
        """Test JSON input file with array of queries."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            json.dump(["AI agents", "neural networks"], f)
            input_file = f.name
        try:
            result = run_cli(["search", "--input", input_file, "--format", "json"])
            assert result.returncode == 0
            data = json.loads(result.stdout)
            assert isinstance(data, list)
            assert len(data) > 0
        finally:
            os.unlink(input_file)

    def test_txt_input_file_multiline(self):
        """Test text input file with multiple queries."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write("query one\nquery two\nquery three\n")
            input_file = f.name
        try:
            result = run_cli(["search", "--input", input_file, "--format", "json"])
            assert result.returncode == 0
            data = json.loads(result.stdout)
            assert isinstance(data, list)
        finally:
            os.unlink(input_file)

    def test_json_output_file(self):
        """Test JSON output is valid when written to file."""
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            output_file = f.name
        try:
            result = run_cli(["search", "Python", "--output", output_file, "--format", "json"])
            assert result.returncode == 0
            with open(output_file, 'r', encoding='utf-8') as f:
                data = json.loads(f.read())
            assert isinstance(data, list)
        finally:
            os.unlink(output_file)

    def test_text_output_file(self):
        """Test text output is properly formatted when written to file."""
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
            output_file = f.name
        try:
            result = run_cli(["search", "Python", "--output", output_file, "--format", "text"])
            assert result.returncode == 0
            with open(output_file, 'r', encoding='utf-8') as f:
                content = f.read()
            assert "result" in content.lower()
            assert "relevance" in content.lower()
        finally:
            os.unlink(output_file)

    def test_compact_output_file(self):
        """Test compact output format in file."""
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
            output_file = f.name
        try:
            result = run_cli(["search", "AI", "--output", output_file, "--format", "compact"])
            assert result.returncode == 0
            with open(output_file, 'r', encoding='utf-8') as f:
                content = f.read()
            assert "|" in content
        finally:
            os.unlink(output_file)


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_max_results_boundary(self):
        """Test max results at boundary (1000)."""
        result = run_cli(["search", "AI", "--max-results", "1000"])
        assert result.returncode == 0

    def test_single_character_query(self):
        """Test single character query is accepted."""
        result = run_cli(["search", "A"])
        assert result.returncode == 0

    def test_query_with_special_characters(self):
        """Test query with special characters."""
        result = run_cli(["search", "AI & ML: The Future!"])
        assert result.returncode == 0

    def test_query_with_unicode(self):
        """Test query with unicode characters."""
        result = run_cli(["search", "AI 人工智能 🤖"])
        assert result.returncode == 0

    def test_empty_input_file(self):
        """Test empty input file shows error."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            # Write nothing (empty file)
            input_file = f.name
        try:
            result = run_cli(["search", "--input", input_file])
            assert result.returncode != 0
        finally:
            os.unlink(input_file)

    def test_input_file_with_blank_lines(self):
        """Test input file with blank lines skips them."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write("\n\nAI agents\n\n\nmachine learning\n\n")
            input_file = f.name
        try:
            result = run_cli(["search", "--input", input_file, "--format", "json"])
            assert result.returncode == 0
            data = json.loads(result.stdout)
            assert isinstance(data, list)
        finally:
            os.unlink(input_file)

    def test_combined_verbose_and_quiet_flags(self):
        """Test that quiet takes precedence over verbose."""
        result = run_cli(["search", "AI", "--verbose", "--quiet"])
        assert result.returncode == 0
        # Quiet should suppress DEBUG output
        assert "DEBUG" not in result.stderr or result.stderr == ""

    def test_log_file_in_subdirectory(self):
        """Test log file creation in subdirectory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = os.path.join(tmpdir, "logs", "test.log")
            result = run_cli(["search", "AI", "--log-file", log_path])
            assert result.returncode == 0
            assert os.path.exists(log_path)
            with open(log_path, 'r', encoding='utf-8') as f:
                content = f.read()
            assert len(content) > 0
