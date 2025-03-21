#!/usr/bin/env python
"""Example script to parse newsletter text and extract articles."""

import argparse
import json
import logging
import os
import sys
from pathlib import Path

# Add the parent directory to the Python path if running directly
parent_dir = Path(__file__).parent.parent
if parent_dir not in sys.path:
    sys.path.insert(0, str(parent_dir))

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

from agentic_newsletter.email_parser_agent import EmailParserAgent


def setup_logging(verbose: bool = False) -> None:
    """Set up logging.
    
    Args:
        verbose (bool, optional): Whether to enable verbose logging. Defaults to False.
    """
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler()],
    )


def parse_newsletter(file_path: str, output_file: str = None, verbose: bool = False) -> None:
    """Parse a newsletter file and extract articles.
    
    Args:
        file_path (str): Path to the file containing newsletter text.
        output_file (str, optional): Path where to save the JSON output. If None, prints to stdout.
        verbose (bool, optional): Whether to enable verbose logging. Defaults to False.
    """
    setup_logging(verbose)
    
    # Read input file
    with open(file_path, 'r', encoding='utf-8') as f:
        newsletter_text = f.read()
    
    # Initialize the parser
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY environment variable not set")
        sys.exit(1)
    
    parser = EmailParserAgent(api_key=api_key)
    
    # Parse the newsletter
    articles = parser.parse_text(newsletter_text)
    
    # Convert to JSON
    articles_json = parser.articles_to_json(articles)
    
    # Output results
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(articles_json, f, indent=2)
        print(f"Extracted {len(articles)} articles. Results saved to {output_file}")
    else:
        print(json.dumps(articles_json, indent=2))
        print(f"\nExtracted {len(articles)} articles.")


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Parse newsletter text and extract articles"
    )
    parser.add_argument(
        "file", help="Path to file containing newsletter text"
    )
    parser.add_argument(
        "-o", "--output", help="Path where to save the JSON output"
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    parse_newsletter(args.file, args.output, args.verbose)


if __name__ == "__main__":
    main()
