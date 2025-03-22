#!/usr/bin/env python
"""Download emails from all active email sources."""

import argparse
import logging
import sys
from pathlib import Path
from typing import List, Optional

# Add the parent directory to the Python path if running directly
parent_dir = Path(__file__).parent.parent
if parent_dir not in sys.path:
    sys.path.insert(0, str(parent_dir))

from agentic_newsletter.email_downloader.email_downloader import EmailDownloader


def setup_logging(verbose: bool = False) -> None:
    """Set up logging.
    
    Args:
        verbose (bool, optional): Whether to enable verbose logging. Defaults to False.
    """
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    
    # Reduce verbosity of googleapiclient
    logging.getLogger('googleapiclient').setLevel(logging.WARNING)
    logging.getLogger('google_auth_httplib2').setLevel(logging.WARNING)
    logging.getLogger('httplib2').setLevel(logging.WARNING)


def download_emails(
    max_per_source: Optional[int] = None, 
    verbose: bool = False, 
    force: bool = False,
    specific_sources: Optional[List[str]] = None
) -> None:
    """Download emails from all active email sources.
    
    Args:
        max_per_source (Optional[int], optional): Maximum number of emails to download per source.
            If None, download all available emails. Defaults to None.
        verbose (bool, optional): Whether to enable verbose logging. Defaults to False.
        force (bool, optional): Whether to force download of all emails, even if they already exist.
            Defaults to False.
        specific_sources (Optional[List[str]], optional): List of specific email sources to download from.
            If None, download from all active sources. Defaults to None.
    """
    # Set up logging
    setup_logging(verbose)
    
    # Initialize the email downloader
    downloader = EmailDownloader()
    
    # Get active email sources
    all_sources = downloader.get_active_email_sources()
    
    # Filter sources if specific ones are requested
    if specific_sources:
        sources = [s for s in all_sources if s.email_address in specific_sources]
        if not sources:
            print(f"None of the specified sources {specific_sources} were found in active sources.")
            print("Available active sources:")
            for source in all_sources:
                print(f"  - {source.email_address}")
            sys.exit(1)
    else:
        sources = all_sources
    
    print(f"Active email sources: {len(sources)}")
    for source in sources:
        print(f"  - {source.email_address}")
    
    if not sources:
        print("No active email sources found. Add some using add_email_source.py")
        sys.exit(0)
    
    # Download emails
    print(f"\nDownloading emails from {len(sources)} sources...")
    if max_per_source:
        print(f"Maximum {max_per_source} emails per source")
    if force:
        print("Force mode: downloading all emails, even if they already exist")
    
    count = downloader.download_emails(max_per_source=max_per_source, force=force, specific_sources=sources)
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
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="Force download of all emails, even if they already exist"
    )
    parser.add_argument(
        "-s",
        "--source",
        action="append",
        help="Specific email source to download from (can be used multiple times)"
    )
    
    args = parser.parse_args()
    download_emails(
        max_per_source=args.max, 
        verbose=args.verbose, 
        force=args.force,
        specific_sources=args.source
    )


if __name__ == "__main__":
    main()
