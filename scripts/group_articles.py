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
    """Group articles into predefined categories.
    
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
    
    # Debug: Log article IDs to understand what's being processed
    article_ids = [article.id for article in articles]
    logging.info(f"Article ID range: {min(article_ids)} to {max(article_ids)}")
    logging.info(f"Article IDs length: {len(article_ids)}")
    logging.info(f"Article IDs: {sorted(article_ids)[:10]}... (showing first 10)")
    
    # Count the number of unique sources
    sources = set()
    for article in articles:
        sources.add(article.sender)
    
    logging.info(f"Articles come from {len(sources)} unique sources.")
    
    # Group the articles
    error_message = None
    articles_per_group = []
    start_time = time.time()
    try:
        result = grouper.group_articles(articles)
        duration = time.time() - start_time
        
        # Print group counts
        logging.info(f"Categorized articles into {len(result.groups)} categories in {duration:.2f} seconds.")
        
        # Calculate articles per group
        total_assigned = 0
        for group in result.groups:
            group_count = len(group.article_ids)
            articles_per_group.append(group_count)
            total_assigned += group_count
        
        # Debug: Check if all articles are accounted for
        logging.info(f"Total articles assigned to groups: {total_assigned}")
        if total_assigned != len(articles):
            logging.warning(f"Mismatch between input articles ({len(articles)}) and assigned articles ({total_assigned})")
            
            # Debug: Check which article IDs are in the result vs. input
            all_result_ids = []
            for group in result.groups:
                all_result_ids.extend(group.article_ids)
            
            # Find articles that are in the result but not in the input
            extra_ids = set(all_result_ids) - set(article_ids)
            if extra_ids:
                logging.warning(f"Found {len(extra_ids)} article IDs in result that weren't in input: {sorted(list(extra_ids))[:10]}... (showing first 10)")
                
                # Remove invalid article IDs from the result
                for group in result.groups:
                    group.article_ids = [id for id in group.article_ids if id in article_ids]
                
                # Recalculate total assigned after removing invalid IDs
                total_assigned = sum(len(group.article_ids) for group in result.groups)
                logging.info(f"After removing invalid IDs, total articles assigned: {total_assigned}")
            
            # Find articles that are in the input but not in the result
            missing_ids = set(article_ids) - set(all_result_ids)
            if missing_ids:
                logging.warning(f"Found {len(missing_ids)} article IDs in input that aren't in result: {sorted(list(missing_ids))[:10]}... (showing first 10)")
                
                # Add missing articles to the "other topics" category if it exists
                other_topics_group = next((group for group in result.groups if group.title == "other topics"), None)
                if other_topics_group:
                    other_topics_group.article_ids.extend(missing_ids)
                    logging.info(f"Added {len(missing_ids)} missing articles to 'other topics' category")
                    
                    # Recalculate total assigned after adding missing IDs
                    total_assigned = sum(len(group.article_ids) for group in result.groups)
                    logging.info(f"After adding missing IDs, total articles assigned: {total_assigned}")
        
        if dry_run:
            # Just print the groups
            for i, group in enumerate(result.groups, 1):
                logging.info(f"Category {i}: {group.title}")
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
            
            logging.info(f"Added {len(result.groups)} categories to the database.")
    except Exception as e:
        duration = time.time() - start_time
        error_message = str(e)
        logging.error(f"Error categorizing articles: {error_message}")
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
        help="Don't actually add groups to the database"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
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
    
    # Initialize the database manager and article grouper
    db_manager = DatabaseManager()
    grouper = ArticleGrouperAgent()
    
    # Group the articles
    group_articles(
        db_manager=db_manager,
        grouper=grouper,
        start_date=start_date,
        end_date=end_date,
        dry_run=args.dry_run
    )


if __name__ == "__main__":
    main()
