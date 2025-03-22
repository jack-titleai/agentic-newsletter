#!/usr/bin/env python
"""Script to group articles by topic."""

import argparse
import logging
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

# Add the parent directory to the Python path if running directly
parent_dir = Path(__file__).parent.parent
if parent_dir not in sys.path:
    sys.path.insert(0, str(parent_dir))

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

from agentic_newsletter.article_grouper import ArticleGrouperAgent
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


def parse_date(date_str: str) -> datetime:
    """Parse a date string.
    
    Args:
        date_str (str): Date string in the format YYYY-MM-DD.
        
    Returns:
        datetime: Parsed date.
    """
    return datetime.strptime(date_str, "%Y-%m-%d")


def group_articles(
    db_manager: DatabaseManager, 
    grouper: ArticleGrouperAgent,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    dry_run: bool = False
) -> None:
    """Group articles by topic.
    
    Args:
        db_manager (DatabaseManager): The database manager.
        grouper (ArticleGrouperAgent): The article grouper agent.
        start_date (Optional[datetime], optional): Start date. Defaults to one week ago.
        end_date (Optional[datetime], optional): End date. Defaults to now.
        dry_run (bool, optional): If True, don't actually add groups to the database.
            Defaults to False.
    """
    # Set default dates if not provided
    if end_date is None:
        end_date = datetime.utcnow()
    if start_date is None:
        start_date = end_date - timedelta(days=7)
    
    logging.info(f"Grouping articles from {start_date} to {end_date}")
    
    # Get articles in the date range
    articles = db_manager.get_articles_by_date_range(start_date, end_date)
    
    if not articles:
        logging.info("No articles found in the specified date range.")
        return
    
    logging.info(f"Found {len(articles)} articles to group.")
    
    # Count the number of unique sources
    sources = set()
    for article in articles:
        sources.add(article.source)
    
    logging.info(f"Articles come from {len(sources)} unique sources.")
    
    # Group the articles
    error_message = None
    articles_per_group = []
    start_time = time.time()
    try:
        result = grouper.group_articles(articles)
        duration = time.time() - start_time
        
        logging.info(f"Created {len(result.groups)} groups in {duration:.2f} seconds.")
        
        # Calculate articles per group
        for group in result.groups:
            articles_per_group.append(len(group.article_ids))
        
        if dry_run:
            # Just print the groups
            for i, group in enumerate(result.groups, 1):
                logging.info(f"Group {i}: {group.title}")
                logging.info(f"Summary: {group.summary}")
                logging.info(f"Articles: {len(group.article_ids)}")
                logging.info("")
        else:
            # Add the groups to the database
            for group in result.groups:
                db_manager.add_article_group(
                    title=group.title,
                    summary=group.summary,
                    article_ids=group.article_ids,
                    start_date=result.start_date,
                    end_date=result.end_date
                )
            
            logging.info(f"Added {len(result.groups)} groups to the database.")
    except Exception as e:
        duration = time.time() - start_time
        error_message = str(e)
        logging.error(f"Error grouping articles: {error_message}")
        result = None
    
    # Log the grouping operation (unless it's a dry run)
    if not dry_run:
        groups_created = len(result.groups) if result else 0
        db_manager.log_grouping(
            duration_seconds=duration,
            articles_processed=len(articles),
            sources_processed=len(sources),
            groups_created=groups_created,
            articles_per_group=articles_per_group,
            error_message=error_message
        )


def main() -> None:
    """Run the script."""
    parser = argparse.ArgumentParser(description="Group articles by topic.")
    parser.add_argument(
        "-s", "--start-date", type=str, help="Start date (YYYY-MM-DD)", default=None
    )
    parser.add_argument(
        "-e", "--end-date", type=str, help="End date (YYYY-MM-DD)", default=None
    )
    parser.add_argument(
        "-d", "--dry-run", action="store_true", help="Don't actually add groups to the database"
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose logging"
    )
    args = parser.parse_args()
    
    # Set up logging
    setup_logging(args.verbose)
    
    # Check for OpenAI API key
    if not os.environ.get("OPENAI_API_KEY"):
        logging.error("OPENAI_API_KEY environment variable not set")
        sys.exit(1)
    
    # Parse dates
    start_date = parse_date(args.start_date) if args.start_date else None
    end_date = parse_date(args.end_date) if args.end_date else None
    
    # Initialize the database manager and grouper
    db_manager = DatabaseManager()
    grouper = ArticleGrouperAgent()
    
    # Group articles
    group_articles(db_manager, grouper, start_date, end_date, args.dry_run)


if __name__ == "__main__":
    main()
