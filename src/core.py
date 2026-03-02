"""Core search functionality for Token-Efficient Search API."""

import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class SearchResult:
    """Represents a single search result optimized for token efficiency."""
    title: str
    snippet: str
    url: str
    relevance: float
    token_count: int

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "title": self.title,
            "snippet": self.snippet,
            "url": self.url,
            "relevance": self.relevance,
            "token_count": self.token_count
        }


# Simulated knowledge base for demonstration
KNOWLEDGE_BASE = [
    {
        "title": "Introduction to Large Language Models",
        "content": "Large language models (LLMs) are AI systems trained on vast amounts of text data. They can generate human-like text, answer questions, and perform various language tasks.",
        "url": "https://example.com/llm-intro",
        "tags": ["ai", "llm", "machine learning", "language model", "deep learning"]
    },
    {
        "title": "Token Optimization Strategies for AI APIs",
        "content": "Reducing token usage in AI API calls is crucial for cost optimization. Strategies include prompt compression, response truncation, and efficient encoding.",
        "url": "https://example.com/token-optimization",
        "tags": ["tokens", "optimization", "api", "cost", "efficiency", "ai"]
    },
    {
        "title": "Building AI Agents with Python",
        "content": "AI agents can be built using Python frameworks. Key components include planning, memory, tool use, and natural language understanding.",
        "url": "https://example.com/ai-agents-python",
        "tags": ["ai", "agents", "python", "automation", "tools"]
    },
    {
        "title": "Web Search API Design Patterns",
        "content": "Designing efficient search APIs requires consideration of relevance ranking, pagination, caching, and rate limiting. REST and GraphQL are common patterns.",
        "url": "https://example.com/search-api-design",
        "tags": ["search", "api", "design", "rest", "web", "patterns"]
    },
    {
        "title": "Natural Language Processing Fundamentals",
        "content": "NLP enables computers to understand human language. Key concepts include tokenization, embedding, parsing, and sentiment analysis.",
        "url": "https://example.com/nlp-fundamentals",
        "tags": ["nlp", "language", "processing", "tokenization", "ai"]
    },
    {
        "title": "Prompt Engineering Best Practices",
        "content": "Effective prompts are clear, specific, and structured. Techniques include few-shot learning, chain-of-thought, and role-based prompting.",
        "url": "https://example.com/prompt-engineering",
        "tags": ["prompts", "engineering", "ai", "llm", "techniques"]
    },
    {
        "title": "Vector Databases for Semantic Search",
        "content": "Vector databases store embeddings for fast similarity search. Popular options include Pinecone, Weaviate, and ChromaDB for AI applications.",
        "url": "https://example.com/vector-databases",
        "tags": ["vectors", "database", "search", "embeddings", "semantic"]
    },
    {
        "title": "Cost Management for AI Infrastructure",
        "content": "Managing AI infrastructure costs involves monitoring API usage, optimizing batch sizes, caching responses, and selecting appropriate model sizes.",
        "url": "https://example.com/ai-cost-management",
        "tags": ["cost", "management", "infrastructure", "ai", "optimization"]
    },
    {
        "title": "Python CLI Development Guide",
        "content": "Building Python CLI tools involves argument parsing, input validation, output formatting, and error handling. Libraries like argparse and click simplify development.",
        "url": "https://example.com/python-cli-guide",
        "tags": ["python", "cli", "development", "argparse", "tools"]
    },
    {
        "title": "RESTful API Authentication Methods",
        "content": "Common API authentication methods include API keys, OAuth 2.0, JWT tokens, and HMAC signatures. Choose based on security requirements and client types.",
        "url": "https://example.com/api-authentication",
        "tags": ["api", "authentication", "security", "oauth", "jwt"]
    }
]


def estimate_tokens(text: str) -> int:
    """
    Estimate token count for a given text.
    Uses a simple approximation: ~4 characters per token (common for English text).

    Args:
        text: Input text to estimate tokens for

    Returns:
        Estimated token count
    """
    if not text:
        return 0
    # Approximate: split by spaces and punctuation, ~4 chars per token
    return max(1, len(text) // 4)


def calculate_relevance(query: str, item: Dict[str, Any]) -> float:
    """
    Calculate relevance score between a query and a knowledge base item.

    Args:
        query: Search query string
        item: Knowledge base item with title, content, and tags

    Returns:
        Relevance score between 0.0 and 1.0
    """
    query_lower = query.lower()
    query_words = set(re.findall(r'\w+', query_lower))

    if not query_words:
        return 0.0

    score = 0.0

    # Title match (weighted heavily)
    title_lower = item["title"].lower()
    title_words = set(re.findall(r'\w+', title_lower))
    title_overlap = len(query_words & title_words) / len(query_words)
    score += title_overlap * 0.4

    # Content match
    content_lower = item["content"].lower()
    content_words = set(re.findall(r'\w+', content_lower))
    content_overlap = len(query_words & content_words) / len(query_words)
    score += content_overlap * 0.3

    # Tag match (check both individual words and full tag phrases)
    tag_words = set()
    for tag in item["tags"]:
        tag_lower = tag.lower()
        # Add the full tag as a phrase
        tag_words.add(tag_lower)
        # Also add individual words from multi-word tags
        tag_words.update(re.findall(r'\w+', tag_lower))
    tag_overlap = len(query_words & tag_words) / len(query_words)
    score += tag_overlap * 0.3

    # Exact phrase bonus
    if query_lower in title_lower or query_lower in content_lower:
        score = min(1.0, score + 0.2)

    return round(min(1.0, score), 4)


def truncate_snippet(content: str, query: str, max_length: int = 150) -> str:
    """
    Create a token-efficient snippet from content, focused around query terms.

    Args:
        content: Full content text
        query: Search query for context
        max_length: Maximum snippet length in characters

    Returns:
        Truncated snippet string
    """
    if len(content) <= max_length:
        return content

    # Try to find query terms in content for context
    query_lower = query.lower()
    content_lower = content.lower()

    # Find the position of the first query term
    pos = content_lower.find(query_lower.split()[0] if query_lower.split() else "")

    if pos > 0:
        # Center the snippet around the found term
        start = max(0, pos - max_length // 4)
        end = min(len(content), start + max_length)
        snippet = content[start:end]
        if start > 0:
            snippet = "..." + snippet
        if end < len(content):
            snippet = snippet + "..."
    else:
        # Default to beginning of content
        snippet = content[:max_length] + "..."

    return snippet


def validate_query(query: str) -> str:
    """
    Validate and sanitize a search query.

    Args:
        query: Raw search query string

    Returns:
        Sanitized query string

    Raises:
        ValueError: If query is empty or invalid
    """
    if not query or not query.strip():
        raise ValueError("Search query cannot be empty")

    # Strip whitespace
    cleaned = query.strip()

    # Check minimum length
    if len(cleaned) < 1:
        raise ValueError("Search query must be at least 1 character")

    # Check maximum length (prevent abuse)
    if len(cleaned) > 500:
        raise ValueError("Search query must be at most 500 characters")

    return cleaned


def search(query: str, max_results: int = 5, knowledge_base: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
    """
    Search for documents matching the query, optimized for token efficiency.

    Args:
        query: The search query string
        max_results: Maximum number of results to return (1-1000)
        knowledge_base: Optional custom knowledge base (uses default if None)

    Returns:
        List of search result dictionaries sorted by relevance

    Raises:
        ValueError: If query is empty or invalid
    """
    # Validate query
    cleaned_query = validate_query(query)

    # Use default knowledge base if none provided
    kb = knowledge_base if knowledge_base is not None else KNOWLEDGE_BASE

    # Calculate relevance for each item
    scored_results = []
    for item in kb:
        relevance = calculate_relevance(cleaned_query, item)
        if relevance > 0.0:
            snippet = truncate_snippet(item["content"], cleaned_query)
            result = SearchResult(
                title=item["title"],
                snippet=snippet,
                url=item["url"],
                relevance=relevance,
                token_count=estimate_tokens(item["title"] + " " + snippet)
            )
            scored_results.append(result)

    # Sort by relevance (descending)
    scored_results.sort(key=lambda x: x.relevance, reverse=True)

    # Limit results
    scored_results = scored_results[:max_results]

    # Convert to dictionaries
    return [r.to_dict() for r in scored_results]
