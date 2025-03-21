"""Example script to download emails."""

import logging
import os
import sys
from pathlib import Path

# Add the parent directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agentic_newsletter.email_downloader import EmailDownloader


def main() -> None:
    """Main entry point."""
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler()],
    )
    
    # Create an email downloader
    downloader = EmailDownloader()
    
    # Add email sources
    newsletters = [
        "newsletter@example.com",
        "daily@example.org",
        "weekly@example.net",
    ]
    
    for newsletter in newsletters:
        downloader.add_email_source(newsletter)
        print(f"Added email source: {newsletter}")
    
    # List active email sources
    sources = downloader.get_active_email_sources()
    print(f"Active email sources: {len(sources)}")
    for source in sources:
        print(f"  - {source.email_address}")
    
    # Download emails
    print("Downloading emails...")
    count = downloader.download_emails()
    print(f"Downloaded {count} emails.")


if __name__ == "__main__":
    main()
