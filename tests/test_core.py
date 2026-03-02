"""Tests for core search functionality."""

import pytest
from src.core import search


class TestSearch:
    """Tests for search function."""

    def test_search_returns_list(self):
        """Test that search returns a list."""
        results = search("test query")

        assert isinstance(results, list)

    def test_search_returns_results(self):
        """Test that search returns at least one result."""
        results = search("test query")

        assert len(results) > 0

    def test_search_result_structure(self):
        """Test that search results have correct structure."""
        results = search("test query")

        assert len(results) > 0
        result = results[0]

        assert "title" in result
        assert "snippet" in result
        assert "relevance" in result

    def test_search_with_custom_max_results(self):
        """Test search with custom max_results parameter."""
        results = search("test query", max_results=3)

        assert isinstance(results, list)
        # Note: stub implementation returns 1 result regardless
        # This test will be more meaningful when real search is implemented

    def test_search_includes_query_in_title(self):
        """Test that search result includes query in title."""
        query = "artificial intelligence"
        results = search(query)

        assert len(results) > 0
        assert query in results[0]["title"]
