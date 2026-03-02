"""CLI argument parsing for Token-Efficient Search API."""

import argparse
import sys
import logging
from dataclasses import dataclass
from typing import Optional

from .core import search
from .utils import format_results, validate_file_path, check_file_size


@dataclass
class ToolConfig:
    """Configuration for the tool"""
    query: Optional[str] = None
    input_file: Optional[str] = None
    output_file: Optional[str] = None
    verbose: bool = False
    format: str = "text"
    max_results: int = 5


def positive_int(value: str) -> int:
    """
    Validate that a value is a positive integer within acceptable bounds.

    Args:
        value: String value to validate

    Returns:
        Integer value if valid

    Raises:
        argparse.ArgumentTypeError: If value is not a positive integer or out of bounds
    """
    try:
        int_value = int(value)
        if int_value < 1:
            raise argparse.ArgumentTypeError(f"must be a positive integer, got {value}")
        if int_value > 1000:
            raise argparse.ArgumentTypeError(f"must be <= 1000, got {value}")
        return int_value
    except ValueError:
        raise argparse.ArgumentTypeError(f"must be an integer, got {value}")


def parse_args(args: Optional[list] = None) -> ToolConfig:
    """
    Parse command-line arguments.

    Args:
        args: List of argument strings (for testing). If None, uses sys.argv.

    Returns:
        ToolConfig object with parsed arguments

    Raises:
        SystemExit: If argument validation fails
    """
    parser = argparse.ArgumentParser(
        prog="search-api",
        description="Token-Efficient Search API for AI - Optimized search with minimal token usage",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m src.cli search "artificial intelligence"
  python -m src.cli search "machine learning" --max-results 10 --format json
  python -m src.cli search --input queries.txt --output results.json
  python -m src.cli search "AI agents" --verbose --format compact
        """
    )

    # Create subparsers for commands
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Search command
    search_parser = subparsers.add_parser(
        "search",
        help="Search for documents matching a query"
    )

    # Positional argument for query (optional if --input is provided)
    search_parser.add_argument(
        "query",
        nargs="?",
        help="Search query string"
    )

    # Optional arguments
    search_parser.add_argument(
        "-i", "--input",
        dest="input_file",
        help="Input file containing queries (alternative to positional query)"
    )

    search_parser.add_argument(
        "-o", "--output",
        dest="output_file",
        help="Output file to write results to"
    )

    search_parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose/debug logging"
    )

    search_parser.add_argument(
        "-f", "--format",
        choices=["json", "text", "compact"],
        default="text",
        help="Output format (default: text)"
    )

    search_parser.add_argument(
        "-n", "--max-results",
        type=positive_int,
        default=5,
        help="Maximum number of results (default: 5, max: 1000)"
    )

    # Parse arguments
    parsed = parser.parse_args(args)

    # Validate that a command was provided
    if not parsed.command:
        parser.print_help()
        sys.exit(1)

    # Validate that either query or input_file is provided
    if not parsed.query and not parsed.input_file:
        parser.error("Either provide a query or use --input to specify an input file")

    # Create and return ToolConfig
    config = ToolConfig(
        query=parsed.query,
        input_file=parsed.input_file,
        output_file=parsed.output_file,
        verbose=parsed.verbose,
        format=parsed.format,
        max_results=parsed.max_results
    )

    return config


def configure_logging(verbose: bool = False) -> None:
    """
    Configure logging based on verbosity level.

    Args:
        verbose: Enable verbose/debug logging if True
    """
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )


def run_search(config: ToolConfig) -> None:
    """
    Execute the search command.

    Args:
        config: ToolConfig object with parsed arguments
    """
    logger = logging.getLogger(__name__)

    # Determine query source
    if config.input_file:
        logger.debug(f"Reading queries from file: {config.input_file}")
        try:
            # Validate input file path
            input_path = validate_file_path(config.input_file, check_exists=True)

            # Check file size before reading
            check_file_size(input_path)

            with open(input_path, 'r') as f:
                query = f.read().strip()
        except FileNotFoundError:
            logger.error(f"Input file not found: {config.input_file}")
            sys.exit(1)
        except ValueError as e:
            logger.error(f"Invalid input file: {e}")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Error reading input file: {e}")
            sys.exit(1)
    else:
        query = config.query

    logger.debug(f"Searching for: {query}")
    logger.debug(f"Max results: {config.max_results}")
    logger.debug(f"Output format: {config.format}")

    # Perform search
    results = search(query, max_results=config.max_results)
    logger.info(f"Found {len(results)} result(s)")

    # Format results
    formatted_output = format_results(results, format_type=config.format)

    # Output results
    if config.output_file:
        logger.debug(f"Writing results to file: {config.output_file}")
        try:
            # Validate output file path
            output_path = validate_file_path(config.output_file, check_exists=False)

            with open(output_path, 'w') as f:
                f.write(formatted_output)
            logger.info(f"Results written to {config.output_file}")
        except ValueError as e:
            logger.error(f"Invalid output file path: {e}")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Error writing output file: {e}")
            sys.exit(1)
    else:
        print(formatted_output)


def main() -> None:
    """Main entry point for the CLI."""
    try:
        config = parse_args()
        configure_logging(verbose=config.verbose)

        if config.verbose:
            logger = logging.getLogger(__name__)
            logger.debug("Starting Token-Efficient Search API")
            logger.debug(f"Configuration: {config}")

        run_search(config)

    except KeyboardInterrupt:
        print("\nInterrupted by user", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
