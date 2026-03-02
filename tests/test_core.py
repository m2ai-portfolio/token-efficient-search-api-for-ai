"""Tests for core search functionality."""

import pytest
from src.core import (
    search,
    SearchResult,
    calculate_relevance,
    estimate_tokens,
    truncate_snippet,
    validate_query,
    KNOWLEDGE_BASE
)


class TestSearchResult:
    """Tests for SearchResult dataclass."""

    def test_search_result_creation(self):
        """Test creating a SearchResult instance."""
        result = SearchResult(
            title="Test Title",
            snippet="Test snippet",
            url="https://example.com",
            relevance=0.95,
            token_count=10
        )

        assert result.title == "Test Title"
        assert result.snippet == "Test snippet"
        assert result.url == "https://example.com"
        assert result.relevance == 0.95
        assert result.token_count == 10

    def test_search_result_to_dict(self):
        """Test converting SearchResult to dictionary."""
        result = SearchResult(
            title="Test Title",
            snippet="Test snippet",
            url="https://example.com",
            relevance=0.85,
            token_count=15
        )

        result_dict = result.to_dict()

        assert isinstance(result_dict, dict)
        assert result_dict["title"] == "Test Title"
        assert result_dict["snippet"] == "Test snippet"
        assert result_dict["url"] == "https://example.com"
        assert result_dict["relevance"] == 0.85
        assert result_dict["token_count"] == 15


class TestEstimateTokens:
    """Tests for estimate_tokens function."""

    def test_estimate_tokens_with_text(self):
        """Test estimating tokens for normal text."""
        text = "This is a test sentence with some words."
        tokens = estimate_tokens(text)

        assert tokens > 0
        assert isinstance(tokens, int)

    def test_estimate_tokens_with_empty_string(self):
        """Test estimating tokens for empty string."""
        tokens = estimate_tokens("")

        assert tokens == 0

    def test_estimate_tokens_approximation(self):
        """Test that token estimation is approximately 4 chars per token."""
        text = "a" * 100  # 100 characters
        tokens = estimate_tokens(text)

        # Should be around 25 tokens (100 / 4)
        assert 20 <= tokens <= 30


class TestCalculateRelevance:
    """Tests for calculate_relevance function."""

    def test_calculate_relevance_exact_title_match(self):
        """Test relevance calculation with exact title match."""
        item = {
            "title": "AI Agents",
            "content": "Some content about other topics.",
            "tags": ["other"]
        }

        relevance = calculate_relevance("AI Agents", item)

        assert relevance > 0.0
        assert relevance <= 1.0

    def test_calculate_relevance_content_match(self):
        """Test relevance calculation with content match."""
        item = {
            "title": "Something else",
            "content": "This is about Python programming and development.",
            "tags": ["other"]
        }

        relevance = calculate_relevance("Python programming", item)

        assert relevance > 0.0
        assert relevance <= 1.0

    def test_calculate_relevance_tag_match(self):
        """Test relevance calculation with tag match."""
        item = {
            "title": "Some title",
            "content": "Some content.",
            "tags": ["ai", "machine learning", "python"]
        }

        relevance = calculate_relevance("machine learning", item)

        assert relevance > 0.0
        assert relevance <= 1.0

    def test_calculate_relevance_no_match(self):
        """Test relevance calculation with no match."""
        item = {
            "title": "Completely Different",
            "content": "Nothing related to the query here.",
            "tags": ["unrelated"]
        }

        relevance = calculate_relevance("xyz123abc", item)

        assert relevance == 0.0

    def test_calculate_relevance_with_empty_query(self):
        """Test relevance calculation with empty query."""
        item = {
            "title": "Test",
            "content": "Test content",
            "tags": ["test"]
        }

        relevance = calculate_relevance("", item)

        assert relevance == 0.0


class TestTruncateSnippet:
    """Tests for truncate_snippet function."""

    def test_truncate_snippet_short_content(self):
        """Test truncating snippet when content is short."""
        content = "This is a short snippet."
        snippet = truncate_snippet(content, "query", max_length=100)

        assert snippet == content

    def test_truncate_snippet_long_content(self):
        """Test truncating snippet when content is long."""
        content = "a" * 200
        snippet = truncate_snippet(content, "query", max_length=100)

        assert len(snippet) <= 103  # 100 + "..."
        assert snippet.endswith("...")

    def test_truncate_snippet_with_query_term(self):
        """Test truncating snippet centers around query term."""
        content = "The beginning is not important. The middle has Python code. The end doesn't matter."
        snippet = truncate_snippet(content, "Python", max_length=50)

        assert "Python" in snippet

    def test_truncate_snippet_custom_max_length(self):
        """Test truncating snippet with custom max length."""
        content = "a" * 300
        snippet = truncate_snippet(content, "query", max_length=50)

        assert len(snippet) <= 53  # 50 + "..."


class TestValidateQuery:
    """Tests for validate_query function."""

    def test_validate_query_valid(self):
        """Test validating a valid query."""
        query = "artificial intelligence"
        validated = validate_query(query)

        assert validated == query

    def test_validate_query_strips_whitespace(self):
        """Test that validation strips whitespace."""
        query = "  test query  "
        validated = validate_query(query)

        assert validated == "test query"

    def test_validate_query_empty_raises_error(self):
        """Test that empty query raises ValueError."""
        with pytest.raises(ValueError, match="cannot be empty"):
            validate_query("")

    def test_validate_query_whitespace_only_raises_error(self):
        """Test that whitespace-only query raises ValueError."""
        with pytest.raises(ValueError, match="cannot be empty"):
            validate_query("   ")

    def test_validate_query_too_long_raises_error(self):
        """Test that too-long query raises ValueError."""
        long_query = "a" * 501
        with pytest.raises(ValueError, match="at most 500 characters"):
            validate_query(long_query)

    def test_validate_query_max_length_allowed(self):
        """Test that max length query is allowed."""
        query = "a" * 500
        validated = validate_query(query)

        assert validated == query


class TestSearch:
    """Tests for search function."""

    def test_search_returns_list(self):
        """Test that search returns a list."""
        results = search("AI agents")

        assert isinstance(results, list)

    def test_search_returns_results(self):
        """Test that search returns at least one result for a valid query."""
        results = search("AI agents")

        assert len(results) > 0

    def test_search_result_structure(self):
        """Test that search results have correct structure."""
        results = search("Python")

        assert len(results) > 0
        result = results[0]

        assert "title" in result
        assert "snippet" in result
        assert "url" in result
        assert "relevance" in result
        assert "token_count" in result

    def test_search_with_custom_max_results(self):
        """Test search with custom max_results parameter."""
        results = search("AI", max_results=3)

        assert len(results) <= 3

    def test_search_empty_query_raises_error(self):
        """Test that empty query raises ValueError."""
        with pytest.raises(ValueError, match="cannot be empty"):
            search("")

    def test_search_whitespace_query_raises_error(self):
        """Test that whitespace-only query raises ValueError."""
        with pytest.raises(ValueError, match="cannot be empty"):
            search("   ")

    def test_search_too_long_query_raises_error(self):
        """Test that too-long query raises ValueError."""
        long_query = "a" * 501
        with pytest.raises(ValueError, match="at most 500 characters"):
            search(long_query)

    def test_search_results_sorted_by_relevance(self):
        """Test that search results are sorted by relevance (descending)."""
        results = search("AI agents Python")

        if len(results) > 1:
            for i in range(len(results) - 1):
                assert results[i]["relevance"] >= results[i + 1]["relevance"]

    def test_search_relevance_in_range(self):
        """Test that relevance scores are between 0.0 and 1.0."""
        results = search("machine learning")

        for result in results:
            assert 0.0 <= result["relevance"] <= 1.0

    def test_search_token_count_present(self):
        """Test that all results have token_count field."""
        results = search("API")

        for result in results:
            assert "token_count" in result
            assert result["token_count"] > 0

    def test_search_with_custom_knowledge_base(self):
        """Test search with custom knowledge base."""
        custom_kb = [
            {
                "title": "Custom Result",
                "content": "This is custom content about testing.",
                "url": "https://custom.com",
                "tags": ["testing", "custom"]
            }
        ]

        results = search("testing", knowledge_base=custom_kb)

        assert len(results) > 0
        assert results[0]["title"] == "Custom Result"

    def test_search_no_matches_returns_empty_list(self):
        """Test that search with no matches returns empty list."""
        results = search("xyzabc123nonexistent")

        assert isinstance(results, list)
        assert len(results) == 0

    def test_search_specific_topics(self):
        """Test search for specific topics in knowledge base."""
        # Test for AI agents
        results = search("AI agents")
        assert any("agent" in r["title"].lower() for r in results)

        # Test for token optimization
        results = search("token optimization")
        assert any("token" in r["title"].lower() for r in results)

        # Test for Python CLI
        results = search("Python CLI")
        assert any("cli" in r["title"].lower() or "python" in r["title"].lower() for r in results)

    def test_search_max_results_limit(self):
        """Test that max_results properly limits output."""
        results_2 = search("AI", max_results=2)
        results_5 = search("AI", max_results=5)
        results_10 = search("AI", max_results=10)

        assert len(results_2) <= 2
        assert len(results_5) <= 5
        assert len(results_10) <= 10

    def test_search_url_field_present(self):
        """Test that all results have URL field."""
        results = search("search")

        for result in results:
            assert "url" in result
            assert result["url"].startswith("https://")
