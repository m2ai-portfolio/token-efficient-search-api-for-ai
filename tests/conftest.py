"""Shared test fixtures for the Token-Efficient Search API test suite."""

import pytest
import tempfile
import os
import json


@pytest.fixture
def temp_dir():
    """Provide a temporary directory that is cleaned up after the test."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def sample_queries_txt(temp_dir):
    """Create a sample queries.txt file."""
    path = os.path.join(temp_dir, "queries.txt")
    with open(path, 'w', encoding='utf-8') as f:
        f.write("AI agents\nmachine learning\ntoken optimization\n")
    return path


@pytest.fixture
def sample_queries_json(temp_dir):
    """Create a sample queries.json file."""
    path = os.path.join(temp_dir, "queries.json")
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(["vector database", "python cli", "search API"], f)
    return path


@pytest.fixture
def sample_output_file(temp_dir):
    """Create a path for output file (not yet created)."""
    return os.path.join(temp_dir, "output.txt")
