# Token-Efficient Search API for AI

A web search API optimized for AI agents that returns the most relevant documents while minimizing token usage.

## Problem

AI agents need to search the web, but standard search APIs return bloated results that waste tokens and context windows. This tool provides search infrastructure specifically optimized for token efficiency and relevance.

## Tech Stack

- Python 3.11+
- argparse (CLI framework)
- pytest (testing)

## Setup

```bash
chmod +x init.sh
./init.sh
```

## Usage

```bash
# Show help
python -m src.cli --help

# Search with a query
python -m src.cli search "your query"

# Search with file input
python -m src.cli search --input queries.txt

# Verbose output
python -m src.cli search "your query" --verbose
```

## Project Structure

```
src/
├── __init__.py        # Package init
├── cli.py             # CLI argument parsing
├── core.py            # Core search functionality
└── utils.py           # Utility functions
tests/
├── __init__.py
├── test_cli.py        # CLI tests
└── test_core.py       # Core function tests
```

## Development

```bash
# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=term-missing
```
