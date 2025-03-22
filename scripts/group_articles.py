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
        db_manager (DatabaseManager): Database manager.
        grouper (ArticleGrouperAgent): Article grouper agent.
        start_date (Optional[datetime], optional): Start date. Defaults to None.
        end_date (Optional[datetime], optional): End date. Defaults to None.
        dry_run (bool, optional): Whether to run in dry-run mode. Defaults to False.
    """
    # Set end date to now if not provided
    if end_date is None:
        end_date = datetime.now()
    
    # Set start date to 7 days ago if not provided
    if start_date is None:
        start_date = end_date - timedelta(days=7)
    
    logging.info(f"Categorizing articles from {start_date} to {end_date}")
    
    # Get articles to categorize
    articles = db_manager.get_articles_by_date_range(start_date, end_date)
    
    # Log information about the articles
    logging.info(f"Found {len(articles)} articles to categorize.")
    
    if not articles:
        logging.warning("No articles found in the specified date range.")
        return
    
    # Log some information about the articles
    article_ids = [article.id for article in articles]
    logging.info(f"Article ID range: {min(article_ids)} to {max(article_ids)}")
    logging.info(f"Article IDs length: {len(article_ids)}")
    logging.info(f"Article IDs: {article_ids[:10]}... (showing first 10)")
    
    # Log the number of unique sources
    unique_sources = set(article.sender for article in articles)
    logging.info(f"Articles come from {len(unique_sources)} unique sources.")
    
    # Start the timer
    start_time = time.time()
    
    # Group the articles
    result = grouper.group_articles(articles)
    
    # Calculate the time taken
    elapsed_time = time.time() - start_time
    
    # Log the results
    logging.info(f"Categorized articles into {len(result.groups)} categories in {elapsed_time:.2f} seconds.")
    
    # Count the total number of articles assigned
    total_articles = sum(len(group.article_ids) for group in result.groups)
    logging.info(f"Total articles assigned to categories: {total_articles}")
    
    # Output the number of articles assigned to each category
    if not dry_run:
        print("\nArticles assigned to each category:")
        for group in result.groups:
            article_count = len(group.article_ids)
            if article_count > 0:
                print(f"Category: {group.title}")
                print(f"  Articles: {article_count}")
                print(f"  Summary: {group.summary}")
                print(f"  Grouping Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}")
                print()
    
    # Log the update to the database
    if dry_run:
        logging.info("Dry run: Not updating assigned_category in the database.")
    else:
        logging.info(f"Updated assigned_category for articles in {len(result.groups)} categories.")
        
        # Get the article counts per category
        articles_per_category = [len(group.article_ids) for group in result.groups]
        
        # Log the grouping
        db_manager.log_grouping(
            duration_seconds=elapsed_time,
            articles_processed=len(articles),
            categories_used=len(result.groups),
            sources_processed=len(unique_sources),
            articles_per_category=articles_per_category,
            error_message=None
        )


def main():
    """Run the script."""
    parser = argparse.ArgumentParser(description="Group articles by topic")
    parser.add_argument(
        "--start-date",
        type=str,
        help="Start date (YYYY-MM-DD)",
        default=None
    )
    parser.add_argument(
        "--end-date",
        type=str,
        help="End date (YYYY-MM-DD)",
        default=None
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Don't actually update categories in the database",
        default=False
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
        default=False
    )
    
    args = parser.parse_args()
    
    # Set up logging
    setup_logging(args.verbose)
    
    # Parse dates
    start_date = parse_date(args.start_date) if args.start_date else None
    end_date = parse_date(args.end_date) if args.end_date else None
    
    # Create database manager and grouper agent
    db_manager = DatabaseManager()
    grouper = ArticleGrouperAgent(db_manager=db_manager)
    
    # Group articles
    group_articles(
        db_manager=db_manager,
        grouper=grouper,
        start_date=start_date,
        end_date=end_date,
        dry_run=args.dry_run
    )


if __name__ == "__main__":
    main()
