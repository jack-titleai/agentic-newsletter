#!/usr/bin/env python
"""Clear parsed articles and parser logs from the database."""

import argparse
import logging
import sys
from pathlib import Path

# Add the parent directory to the Python path if running directly
parent_dir = Path(__file__).parent.parent
if parent_dir not in sys.path:
    sys.path.insert(0, str(parent_dir))

from agentic_newsletter.database.database_manager import DatabaseManager
from agentic_newsletter.database.parsed_article import ParsedArticle
from agentic_newsletter.database.parser_log import ParserLog


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


def clear_parsed_data(dry_run: bool = False, verbose: bool = False) -> None:
    """Clear parsed articles and parser logs from the database.
    
    Args:
        dry_run (bool, optional): If True, don't actually delete anything. Defaults to False.
        verbose (bool, optional): Whether to enable verbose logging. Defaults to False.
    """
    # Set up logging
    setup_logging(verbose)
    
    # Initialize the database manager
    db_manager = DatabaseManager()
    
    # Get session
    with db_manager.get_session() as session:
        # Count records before deletion
        parsed_article_count = session.query(ParsedArticle).count()
        parser_log_count = session.query(ParserLog).count()
        
        print(f"Found {parsed_article_count} parsed articles and {parser_log_count} parser logs in the database.")
        
        if dry_run:
            print("Dry run, not deleting anything.")
            return
        
        # Delete all parsed articles
        session.query(ParsedArticle).delete()
        print(f"Deleted {parsed_article_count} parsed articles.")
        
        # Delete all parser logs
        session.query(ParserLog).delete()
        print(f"Deleted {parser_log_count} parser logs.")
        
        # Commit the changes
        session.commit()
        
        print("Successfully cleared parsed data from the database.")


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Clear parsed articles and parser logs from the database"
    )
    parser.add_argument(
        "-d", 
        "--dry-run", 
        action="store_true", 
        help="Don't actually delete anything"
    )
    parser.add_argument(
        "-v", 
        "--verbose", 
        action="store_true", 
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    clear_parsed_data(dry_run=args.dry_run, verbose=args.verbose)


if __name__ == "__main__":
    main()
