"""Command-line interface for Agentic Newsletter."""

import argparse
import logging
import sys
from typing import List, Optional

from agentic_newsletter.email_downloader import EmailDownloader


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


def download_emails(args: argparse.Namespace) -> None:
    """Download emails command.
    
    Args:
        args (argparse.Namespace): Command-line arguments.
    """
    downloader = EmailDownloader()
    
    if args.add_source:
        for source in args.add_source:
            downloader.add_email_source(source)
            print(f"Added email source: {source}")
    
    if args.list_sources:
        sources = downloader.get_active_email_sources()
        if sources:
            print("Active email sources:")
            for source in sources:
                print(f"  - {source.email_address}")
        else:
            print("No active email sources found.")
    
    if args.download:
        print("Downloading emails...")
        count = downloader.download_emails(args.max_emails)
        print(f"Downloaded {count} emails.")


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Agentic Newsletter CLI")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging")
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Download emails command
    download_parser = subparsers.add_parser("download", help="Download emails")
    download_parser.add_argument(
        "--add-source", action="append", help="Add an email source to download from"
    )
    download_parser.add_argument(
        "--list-sources", action="store_true", help="List active email sources"
    )
    download_parser.add_argument(
        "--download", action="store_true", help="Download emails from active sources"
    )
    download_parser.add_argument(
        "--max-emails", type=int, help="Maximum number of emails to download per source"
    )
    
    args = parser.parse_args()
    setup_logging(args.verbose)
    
    if args.command == "download":
        download_emails(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
