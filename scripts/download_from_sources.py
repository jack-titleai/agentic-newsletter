#!/usr/bin/env python
"""Script to download emails from all active email sources."""

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional

# Add the parent directory to the Python path if running directly
parent_dir = Path(__file__).parent.parent
if parent_dir not in sys.path:
    sys.path.insert(0, str(parent_dir))

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


def download_emails(max_per_source: Optional[int] = None, verbose: bool = False) -> None:
    """Download emails from all active email sources.
    
    Args:
        max_per_source (Optional[int], optional): Maximum number of emails to download per source.
            If None, download all available emails. Defaults to None.
        verbose (bool, optional): Whether to enable verbose logging. Defaults to False.
    """
    setup_logging(verbose)
    
    # Create an email downloader
    downloader = EmailDownloader()
    
    # List active email sources
    sources = downloader.get_active_email_sources()
    print(f"Active email sources: {len(sources)}")
    for source in sources:
        print(f"  - {source.email_address}")
    
    if not sources:
        print("No active email sources found. Add sources first using add_email_sources.py")
        sys.exit(0)
    
    # Download emails
    print(f"\nDownloading emails from {len(sources)} sources...")
    if max_per_source:
        print(f"Maximum {max_per_source} emails per source")
    
    count = downloader.download_emails(max_per_source=max_per_source)
    print(f"\nSuccessfully downloaded {count} emails.")


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Download emails from all active email sources"
    )
    parser.add_argument(
        "-m", 
        "--max", 
        type=int, 
        help="Maximum number of emails to download per source"
    )
    parser.add_argument(
        "-v", 
        "--verbose", 
        action="store_true", 
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    download_emails(max_per_source=args.max, verbose=args.verbose)


if __name__ == "__main__":
    main()
