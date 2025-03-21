#!/usr/bin/env python
"""Script to add email sources from a text file."""

import argparse
import logging
import sys
from pathlib import Path

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


def add_emails_from_file(file_path: str, verbose: bool = False) -> None:
    """Add email sources from a text file.
    
    Args:
        file_path (str): Path to the text file containing email addresses.
        verbose (bool, optional): Whether to enable verbose logging. Defaults to False.
    """
    setup_logging(verbose)
    
    # Create an email downloader
    downloader = EmailDownloader()
    
    # Read email addresses from the file
    try:
        with open(file_path, 'r') as f:
            emails = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"Error: File not found: {file_path}")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading file: {e}")
        sys.exit(1)
    
    if not emails:
        print("No email addresses found in the file.")
        sys.exit(0)
    
    print(f"Found {len(emails)} email addresses in the file.")
    
    # Add each email as a source
    added_count = 0
    for email in emails:
        try:
            # Basic validation
            if '@' not in email:
                print(f"Skipping invalid email address: {email}")
                continue
            
            downloader.add_email_source(email)
            added_count += 1
            print(f"Added email source: {email}")
        except Exception as e:
            print(f"Error adding email source {email}: {e}")
    
    # List active email sources
    sources = downloader.get_active_email_sources()
    print(f"\nActive email sources: {len(sources)}")
    for source in sources:
        print(f"  - {source.email_address}")
    
    print(f"\nSuccessfully added {added_count} email sources.")


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Add email sources from a text file (one email per line)"
    )
    parser.add_argument(
        "file", help="Path to the text file containing email addresses (one per line)"
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    add_emails_from_file(args.file, args.verbose)


if __name__ == "__main__":
    main()
