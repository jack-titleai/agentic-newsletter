#!/usr/bin/env python
"""Script to check if any parsed articles exist in the database."""

import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add the parent directory to the Python path if running directly
parent_dir = Path(__file__).parent.parent
if parent_dir not in sys.path:
    sys.path.insert(0, str(parent_dir))

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

from agentic_newsletter.database.database_manager import DatabaseManager


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


def check_parsed_articles():
    """Check if any parsed articles exist in the database."""
    # Create database manager
    db_manager = DatabaseManager()
    
    # Get the current time
    now = datetime.now()
    
    # Check for articles parsed in the last hour
    one_hour_ago = now - timedelta(hours=1)
    
    with db_manager.get_session() as session:
        from agentic_newsletter.database import ParsedArticle
        
        # Count total parsed articles
        total_count = session.query(ParsedArticle).count()
        print(f"Total parsed articles in database: {total_count}")
        
        # Count recently parsed articles
        recent_count = session.query(ParsedArticle).filter(
            ParsedArticle.parsed_at >= one_hour_ago
        ).count()
        print(f"Articles parsed in the last hour: {recent_count}")
        
        # Get the most recent parsed article
        most_recent = session.query(ParsedArticle).order_by(
            ParsedArticle.parsed_at.desc()
        ).first()
        
        if most_recent:
            print("\nMost recent parsed article:")
            print(f"  ID: {most_recent.id}")
            print(f"  Title: {most_recent.title}")
            print(f"  Category: {most_recent.assigned_category}")
            print(f"  Parsed at: {most_recent.parsed_at}")
            
            # Calculate time since parsing
            time_since = now - most_recent.parsed_at
            print(f"  Time since parsing: {time_since}")
        else:
            print("\nNo parsed articles found in the database.")


if __name__ == "__main__":
    setup_logging()
    check_parsed_articles()
