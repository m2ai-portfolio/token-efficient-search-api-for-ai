"""Tests for file I/O operations."""

import pytest
import json
import tempfile
from pathlib import Path

from src.utils import read_queries_from_file, write_results_to_file, detect_file_format
from src.cli import run_search, ToolConfig, configure_logging


class TestReadQueriesFromFile:
    """Tests for reading queries from files."""

    def test_read_txt_file_multiple_queries(self):
        """Test reading multiple queries from a .txt file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt', encoding='utf-8') as f:
            f.write("AI agents\n")
            f.write("machine learning\n")
            f.write("token optimization\n")
            input_file = f.name

        try:
            queries = read_queries_from_file(input_file)
            assert len(queries) == 3
            assert queries[0] == "AI agents"
            assert queries[1] == "machine learning"
            assert queries[2] == "token optimization"
        finally:
            Path(input_file).unlink(missing_ok=True)

    def test_read_txt_file_with_empty_lines(self):
        """Test reading from .txt file with empty lines (should skip them)."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt', encoding='utf-8') as f:
            f.write("query one\n")
            f.write("\n")
            f.write("   \n")
            f.write("query two\n")
            input_file = f.name

        try:
            queries = read_queries_from_file(input_file)
            assert len(queries) == 2
            assert queries[0] == "query one"
            assert queries[1] == "query two"
        finally:
            Path(input_file).unlink(missing_ok=True)

    def test_read_json_file_array_of_strings(self):
        """Test reading queries from a .json file with array of strings."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json', encoding='utf-8') as f:
            json.dump(["vector database", "python cli", "REST API"], f)
            input_file = f.name

        try:
            queries = read_queries_from_file(input_file)
            assert len(queries) == 3
            assert queries[0] == "vector database"
            assert queries[1] == "python cli"
            assert queries[2] == "REST API"
        finally:
            Path(input_file).unlink(missing_ok=True)

    def test_read_json_file_invalid_format(self):
        """Test reading from .json file with invalid format (not an array)."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json', encoding='utf-8') as f:
            json.dump({"query": "test"}, f)
            input_file = f.name

        try:
            with pytest.raises(ValueError, match="JSON input file must contain an array"):
                read_queries_from_file(input_file)
        finally:
            Path(input_file).unlink(missing_ok=True)

    def test_read_missing_file(self):
        """Test reading from a file that doesn't exist."""
        with pytest.raises(FileNotFoundError):
            read_queries_from_file("/nonexistent/file.txt")

    def test_read_empty_txt_file(self):
        """Test reading from an empty .txt file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt', encoding='utf-8') as f:
            input_file = f.name

        try:
            queries = read_queries_from_file(input_file)
            assert len(queries) == 0
        finally:
            Path(input_file).unlink(missing_ok=True)

    def test_read_empty_json_array(self):
        """Test reading from .json file with empty array."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json', encoding='utf-8') as f:
            json.dump([], f)
            input_file = f.name

        try:
            queries = read_queries_from_file(input_file)
            assert len(queries) == 0
        finally:
            Path(input_file).unlink(missing_ok=True)


class TestWriteResultsToFile:
    """Tests for writing results to files."""

    def test_write_to_file(self):
        """Test writing results to a file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            output_file = f.name

        try:
            results_text = "Test results\nLine 2\nLine 3"
            output_path = write_results_to_file(results_text, output_file)

            assert Path(output_path).exists()
            with open(output_path, 'r', encoding='utf-8') as f:
                content = f.read()
                assert content == results_text
        finally:
            Path(output_file).unlink(missing_ok=True)

    def test_write_to_nonexistent_directory(self):
        """Test writing to a file in a non-existent directory (should create it)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = Path(tmpdir) / "subdir" / "nested" / "output.txt"
            results_text = "Test output"

            output_path = write_results_to_file(results_text, str(output_file))

            assert Path(output_path).exists()
            with open(output_path, 'r', encoding='utf-8') as f:
                content = f.read()
                assert content == results_text

    def test_write_empty_string(self):
        """Test writing an empty string to a file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            output_file = f.name

        try:
            output_path = write_results_to_file("", output_file)
            assert Path(output_path).exists()
            with open(output_path, 'r', encoding='utf-8') as f:
                content = f.read()
                assert content == ""
        finally:
            Path(output_file).unlink(missing_ok=True)


class TestDetectFileFormat:
    """Tests for file format detection."""

    def test_detect_json_format(self):
        """Test detecting JSON format."""
        assert detect_file_format("file.json") == "json"
        assert detect_file_format("FILE.JSON") == "json"

    def test_detect_txt_format(self):
        """Test detecting text format."""
        assert detect_file_format("file.txt") == "txt"
        assert detect_file_format("file.text") == "txt"

    def test_detect_csv_format(self):
        """Test detecting CSV format."""
        assert detect_file_format("file.csv") == "csv"

    def test_detect_unknown_format(self):
        """Test detecting unknown format (defaults to txt)."""
        assert detect_file_format("file.xyz") == "txt"
        assert detect_file_format("file") == "txt"


class TestFullPipeline:
    """Tests for full input -> search -> output pipeline."""

    def test_txt_input_to_txt_output(self):
        """Test reading from .txt input, searching, and writing to .txt output."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt', encoding='utf-8') as f:
            f.write("AI agents\n")
            f.write("Python\n")
            input_file = f.name

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            output_file = f.name

        try:
            config = ToolConfig(
                input_file=input_file,
                output_file=output_file,
                format="text"
            )

            configure_logging(verbose=False)
            run_search(config)

            # Verify output file was created and contains results
            assert Path(output_file).exists()
            with open(output_file, 'r', encoding='utf-8') as f:
                content = f.read()
                assert "result(s)" in content.lower()
                # Should have processed 2 queries
                assert "Result" in content
        finally:
            Path(input_file).unlink(missing_ok=True)
            Path(output_file).unlink(missing_ok=True)

    def test_json_input_to_json_output(self):
        """Test reading from .json input, searching, and writing to .json output."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json', encoding='utf-8') as f:
            json.dump(["vector database", "token optimization"], f)
            input_file = f.name

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            output_file = f.name

        try:
            config = ToolConfig(
                input_file=input_file,
                output_file=output_file,
                format="json"
            )

            configure_logging(verbose=False)
            run_search(config)

            # Verify output file was created and contains valid JSON
            assert Path(output_file).exists()
            with open(output_file, 'r', encoding='utf-8') as f:
                results = json.load(f)
                assert isinstance(results, list)
                # Should have results from both queries
                assert len(results) > 0
        finally:
            Path(input_file).unlink(missing_ok=True)
            Path(output_file).unlink(missing_ok=True)

    def test_multiple_queries_aggregate_results(self, capsys):
        """Test that multiple queries produce aggregated results."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt', encoding='utf-8') as f:
            f.write("AI\n")
            f.write("Python\n")
            f.write("API\n")
            input_file = f.name

        try:
            config = ToolConfig(
                input_file=input_file,
                format="text",
                max_results=3
            )

            configure_logging(verbose=False)
            run_search(config)

            captured = capsys.readouterr()
            # Should have multiple results from 3 queries
            assert "Result" in captured.out
            # Results should be aggregated, not separate
            assert "result(s)" in captured.out.lower()
        finally:
            Path(input_file).unlink(missing_ok=True)
