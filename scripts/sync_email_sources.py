#!/usr/bin/env python
"""Sync email sources from config file to database."""

import argparse
import logging
import sys
from pathlib import Path

# Add the parent directory to the Python path if running directly
parent_dir = Path(__file__).parent.parent
if parent_dir not in sys.path:
    sys.path.insert(0, str(parent_dir))

from agentic_newsletter.config.config_loader import ConfigLoader
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


def sync_email_sources(verbose: bool = False, dry_run: bool = False) -> None:
    """Sync email sources from config file to database.
    
    Args:
        verbose (bool, optional): Whether to enable verbose logging. Defaults to False.
        dry_run (bool, optional): If True, don't actually modify the database.
            Defaults to False.
    """
    # Set up logging
    setup_logging(verbose)
    
    # Initialize the email downloader and config loader
    downloader = EmailDownloader()
    config_loader = ConfigLoader()
    
    # Get email sources from config
    config_sources = config_loader.get_email_sources()
    print(f"Found {len(config_sources)} email sources in config:")
    for source in config_sources:
        print(f"  - {source}")
    
    if not config_sources:
        print("No email sources found in config. Add some to the 'email_sources' field in config.json")
        sys.exit(0)
    
    # Get active email sources from database
    db_sources = downloader.get_active_email_sources()
    db_source_emails = [source.email_address for source in db_sources]
    
    print(f"\nFound {len(db_sources)} active email sources in database:")
    for source in db_sources:
        print(f"  - {source.email_address}")
    
    # Find sources to add
    sources_to_add = [s for s in config_sources if s not in db_source_emails]
    
    if not sources_to_add:
        print("\nAll config sources are already in the database.")
    else:
        print(f"\nAdding {len(sources_to_add)} new sources to database:")
        for source in sources_to_add:
            print(f"  - {source}")
            
            if not dry_run:
                downloader.add_email_source(source)
    
    # Find sources to activate
    inactive_sources = downloader.db_manager.get_inactive_email_sources()
    inactive_source_emails = [source.email_address for source in inactive_sources]
    
    sources_to_activate = [s for s in config_sources if s in inactive_source_emails]
    
    if sources_to_activate:
        print(f"\nActivating {len(sources_to_activate)} inactive sources:")
        for source in sources_to_activate:
            print(f"  - {source}")
            
            if not dry_run:
                downloader.update_email_source_status(source, active=True)
    
    # Find sources to deactivate
    sources_to_deactivate = [s for s in db_source_emails if s not in config_sources]
    
    if sources_to_deactivate:
        print(f"\nDeactivating {len(sources_to_deactivate)} sources not in config:")
        for source in sources_to_deactivate:
            print(f"  - {source}")
            
            if not dry_run:
                downloader.update_email_source_status(source, active=False)
    
    if dry_run:
        print("\nDry run, no changes made to database.")
    else:
        print("\nEmail sources synced successfully.")


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Sync email sources from config file to database"
    )
    parser.add_argument(
        "-v", 
        "--verbose", 
        action="store_true", 
        help="Enable verbose logging"
    )
    parser.add_argument(
        "-d",
        "--dry-run",
        action="store_true",
        help="Don't actually modify the database"
    )
    
    args = parser.parse_args()
    sync_email_sources(verbose=args.verbose, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
