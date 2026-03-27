# Token-Efficient Search API for AI

A search tool optimized for AI agents that returns relevant documents while minimizing token usage. Results include relevance scores and token counts so agents can make cost-aware decisions about which content to consume.

## Problem

AI agents need to search for information, but standard search APIs return bloated results that waste tokens and context windows. This tool scores and ranks results by relevance, truncates snippets to the minimum useful length, and reports token counts per result.

## How It Works

The search engine scores documents against a query using a weighted formula:

- **Title match** (40%) -- word overlap between query and document title
- **Content match** (30%) -- word overlap between query and document body
- **Tag match** (30%) -- word overlap between query and document tags
- **Exact phrase bonus** (+20%) -- if the full query appears verbatim in title or content

Results are sorted by relevance score (0.0-1.0), truncated to token-efficient snippets centered around query terms, and limited to the requested count.

## Tech Stack

- Python 3.11+
- argparse (CLI framework)
- pytest + pytest-cov (testing)
- No external runtime dependencies

## Setup

### Quick Start

```bash
chmod +x init.sh
./init.sh
```

### Manual Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt   # pytest, pytest-cov (dev only)
```

No runtime dependencies beyond the Python standard library.

## Usage

### Basic Search

```bash
# Search with a query
python -m src.cli search "token optimization"

# Limit number of results
python -m src.cli search "AI agents" --max-results 3
```

### Output Formats

```bash
# Default human-readable text format
python -m src.cli search "large language models"

# JSON (structured, machine-parseable)
python -m src.cli search "large language models" --format json

# Compact (single-line, minimal tokens)
python -m src.cli search "large language models" --format compact
```

### File I/O

```bash
# Read queries from a file (one per line, or JSON array)
python -m src.cli search --input queries.txt

# Write results to a file
python -m src.cli search "AI agents" --output results.json --format json

# Read from stdin
echo "vector databases" | python -m src.cli search -
```

### Logging and Debugging

```bash
# Verbose output (debug-level logging to stderr)
python -m src.cli search "AI agents" --verbose

# Quiet mode (errors only)
python -m src.cli search "AI agents" --quiet

# Log to file
python -m src.cli search "AI agents" --log-file search.log
```

## Output Formats

### Text (default)

```
============================================================
Found 3 result(s)
============================================================

Result #1
  Title: Token Optimization Strategies for AI APIs
  URL: https://example.com/token-optimization
  Snippet: Reducing token usage in AI API calls is crucial for cost optimization...
  Relevance: 0.70
  Tokens: 28

Result #2
  ...

============================================================
Total tokens: 76
============================================================
```

### JSON

```json
[
  {
    "title": "Token Optimization Strategies for AI APIs",
    "snippet": "Reducing token usage in AI API calls is crucial...",
    "url": "https://example.com/token-optimization",
    "relevance": 0.7,
    "token_count": 28
  }
]
```

### Compact

```
1. Token Optimization Strategies for AI APIs [https://example.com/token-optimization] (0.70) | 2. ...
```

## CLI Reference

```
python -m src.cli search [QUERY] [OPTIONS]

Positional:
  QUERY                    Search query string (use "-" for stdin)

Options:
  -i, --input FILE         Read queries from file (.txt or .json)
  -o, --output FILE        Write results to file
  -f, --format FORMAT      Output format: text (default), json, compact
  -n, --max-results N      Max results to return (default: 5, max: 1000)
  -v, --verbose            Enable debug logging
  -q, --quiet              Suppress all output except errors
  --log-file FILE          Write logs to file
```

## Security

- File paths are validated against path traversal attacks
- System directories (`/etc`, `/proc`, `/sys`, `/dev`, `/root`, `/boot`) are blocked
- Input files are capped at 10 MB
- Queries are limited to 500 characters
- Max results capped at 1000

## Project Structure

```
src/
  __init__.py        # Package init
  cli.py             # CLI argument parsing and execution
  core.py            # Search engine: scoring, relevance, snippets
  utils.py           # File I/O, formatting, path validation
tests/
  conftest.py        # Test fixtures
  test_cli.py        # CLI argument parsing tests
  test_core.py       # Core search function tests
  test_file_io.py    # File read/write tests
  test_security.py   # Path traversal and input validation tests
  test_logging.py    # Logging configuration tests
  test_integration.py # End-to-end integration tests
```

## Development

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=term-missing

# Run a specific test file
pytest tests/test_core.py -v
```

## License

MIT
