"""Utility functions for the search API tool."""

import json
from pathlib import Path
from typing import List, Dict, Any

# Security constants
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB limit
FORBIDDEN_DIRECTORIES = {'/etc', '/proc', '/sys', '/dev', '/root', '/boot'}


def validate_file_path(file_path: str, check_exists: bool = False) -> Path:
    """
    Validate and sanitize a file path to prevent path traversal attacks.

    Args:
        file_path: The file path to validate
        check_exists: If True, check that the file exists

    Returns:
        Normalized Path object

    Raises:
        ValueError: If the path is invalid or points to a forbidden directory
        FileNotFoundError: If check_exists is True and file doesn't exist
    """
    try:
        # Convert to Path and resolve to absolute path
        path = Path(file_path).resolve()

        # Check if path points to or is within forbidden system directories
        for forbidden_dir in FORBIDDEN_DIRECTORIES:
            forbidden_path = Path(forbidden_dir).resolve()
            try:
                # Check if path is the forbidden directory or a subdirectory
                path.relative_to(forbidden_path)
                raise ValueError(
                    f"Access to system directory '{forbidden_dir}' is forbidden"
                )
            except ValueError as e:
                # If relative_to raises ValueError, path is NOT under forbidden_path
                # Re-raise only if it's our security error, not the relative_to error
                if "forbidden" in str(e):
                    raise
                # Otherwise continue checking other forbidden dirs
                continue

        # Check existence if required
        if check_exists and not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        return path

    except Exception as e:
        if isinstance(e, (ValueError, FileNotFoundError)):
            raise
        raise ValueError(f"Invalid file path: {file_path}") from e


def check_file_size(file_path: Path, max_size: int = MAX_FILE_SIZE) -> None:
    """
    Check if a file size is within acceptable limits.

    Args:
        file_path: Path object to check
        max_size: Maximum allowed file size in bytes

    Raises:
        ValueError: If file exceeds maximum size
        FileNotFoundError: If file doesn't exist
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    file_size = file_path.stat().st_size
    if file_size > max_size:
        raise ValueError(
            f"File size ({file_size} bytes) exceeds maximum allowed "
            f"size ({max_size} bytes / {max_size // (1024*1024)} MB)"
        )


def read_queries_from_file(file_path: str) -> list[str]:
    """
    Read queries from a file, one query per line.
    Supports .txt files (one query per line) and .json files (array of strings).

    Args:
        file_path: Path to the input file

    Returns:
        List of query strings

    Raises:
        ValueError: If path is invalid or file format unsupported
        FileNotFoundError: If file doesn't exist
    """
    # Validate path
    validated_path = validate_file_path(file_path, check_exists=True)
    # Check file size
    check_file_size(validated_path)

    suffix = validated_path.suffix.lower()

    with open(validated_path, 'r', encoding='utf-8') as f:
        if suffix == '.json':
            data = json.load(f)
            if not isinstance(data, list):
                raise ValueError("JSON input file must contain an array of query strings")
            return [str(q).strip() for q in data if str(q).strip()]
        else:
            # Default: treat as text, one query per line
            lines = f.readlines()
            return [line.strip() for line in lines if line.strip()]


def write_results_to_file(results_text: str, file_path: str) -> str:
    """
    Write formatted results to a file.

    Args:
        results_text: Formatted results string
        file_path: Path to write to

    Returns:
        Absolute path of the written file

    Raises:
        ValueError: If path is invalid
        IOError: If file cannot be written
    """
    validated_path = validate_file_path(file_path, check_exists=False)

    # Ensure parent directory exists
    validated_path.parent.mkdir(parents=True, exist_ok=True)

    with open(validated_path, 'w', encoding='utf-8') as f:
        f.write(results_text)

    return str(validated_path)


def detect_file_format(file_path: str) -> str:
    """
    Detect the format of an input file based on extension.

    Args:
        file_path: Path to the file

    Returns:
        Format string: 'json', 'txt', or 'unknown'
    """
    suffix = Path(file_path).suffix.lower()
    format_map = {
        '.json': 'json',
        '.txt': 'txt',
        '.text': 'txt',
        '.csv': 'csv',
    }
    return format_map.get(suffix, 'txt')  # Default to txt


def format_results(results: List[Dict[str, Any]], format_type: str = "text") -> str:
    """
    Format search results based on the specified format.

    Args:
        results: List of search result dictionaries
        format_type: Output format ("text", "json", or "compact")

    Returns:
        Formatted string representation of results
    """
    if format_type == "json":
        return json.dumps(results, indent=2)

    elif format_type == "compact":
        # Single-line compact format
        compact_results = []
        for i, result in enumerate(results, 1):
            title = result.get("title", "No title")
            url = result.get("url", "N/A")
            relevance = result.get("relevance", 0.0)
            compact_results.append(f"{i}. {title} [{url}] ({relevance:.2f})")
        return " | ".join(compact_results)

    else:  # text format (default)
        output = []
        output.append(f"\n{'='*60}")
        output.append(f"Found {len(results)} result(s)")
        output.append(f"{'='*60}\n")

        total_tokens = 0
        for i, result in enumerate(results, 1):
            output.append(f"Result #{i}")
            output.append(f"  Title: {result.get('title', 'No title')}")
            output.append(f"  URL: {result.get('url', 'N/A')}")
            output.append(f"  Snippet: {result.get('snippet', 'No snippet')}")
            output.append(f"  Relevance: {result.get('relevance', 0.0):.2f}")
            output.append(f"  Tokens: {result.get('token_count', 0)}")
            output.append("")
            total_tokens += result.get('token_count', 0)

        output.append(f"{'='*60}")
        output.append(f"Total tokens: {total_tokens}")
        output.append(f"{'='*60}\n")

        return "\n".join(output)
