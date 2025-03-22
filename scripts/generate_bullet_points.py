#!/usr/bin/env python
"""Script to generate bullet points from categorized articles."""

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

from agentic_newsletter.bullet_point_generator import BulletPointGeneratorAgent
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


def generate_bullet_points(
    db_manager: DatabaseManager,
    generator: BulletPointGeneratorAgent,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    include_other_topics: bool = False,
    dry_run: bool = False
) -> None:
    """Generate bullet points from categorized articles.
    
    Args:
        db_manager (DatabaseManager): Database manager.
        generator (BulletPointGeneratorAgent): Bullet point generator agent.
        start_date (Optional[datetime], optional): Start date. Defaults to None.
        end_date (Optional[datetime], optional): End date. Defaults to None.
        include_other_topics (bool, optional): Whether to include the "other topics" category. Defaults to False.
        dry_run (bool, optional): Whether to run in dry-run mode. Defaults to False.
    """
    # Set end date to now if not provided
    if end_date is None:
        end_date = datetime.now()
    
    # Set start date to 7 days ago if not provided
    if start_date is None:
        start_date = end_date - timedelta(days=7)
    
    logging.info(f"Generating bullet points for articles from {start_date} to {end_date}")
    
    # Get categories with articles in the date range
    categories_with_articles = generator._get_categories_with_articles(start_date, end_date)
    
    # Filter out excluded categories
    excluded = generator.excluded_categories.copy()
    if not include_other_topics:
        excluded.add("other topics")
    
    categories_to_process = [cat for cat in categories_with_articles if cat not in excluded]
    
    # Print categories that would be processed
    print(f"\nFound {len(categories_to_process)} categories with articles in the date range:")
    for category in categories_to_process:
        articles = db_manager.get_articles_by_category(category, start_date, end_date)
        print(f"  - {category}: {len(articles)} articles")
    
    if not categories_to_process:
        print("\nNo categories with articles found in the specified date range.")
        return
    
    # Start the timer
    start_time = time.time()
    
    # Generate bullet points
    if dry_run:
        logging.info("Dry run: Processing articles but not saving to database")
    
    results = generator.generate_bullet_points(
        start_date=start_date,
        end_date=end_date,
        include_other_topics=include_other_topics,
        dry_run=dry_run
    )
    
    # Calculate the time taken
    elapsed_time = time.time() - start_time
    
    # Print results
    total_bullet_points = sum(len(result.bullet_points) for result in results.values())
    print(f"\nGenerated {total_bullet_points} bullet points across {len(results)} categories in {elapsed_time:.2f} seconds")
    
    for category, result in results.items():
        if result.bullet_points:
            print(f"\nCategory: {category}")
            print(f"  Bullet Points: {len(result.bullet_points)}")
            
            # Sort bullet points by impact score (highest first), then frequency score
            sorted_bullet_points = sorted(
                result.bullet_points, 
                key=lambda bp: (bp.impact_score, bp.frequency_score), 
                reverse=True
            )
            
            for i, bp in enumerate(sorted_bullet_points, 1):
                print(f"  {i}. {bp.bullet_point}")
                print(f"     Impact: {bp.impact_score:.1f}, Frequency: {bp.frequency_score:.1f}")


def main():
    """Run the script."""
    parser = argparse.ArgumentParser(description="Generate bullet points from categorized articles")
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
        "--include-other-topics",
        action="store_true",
        help="Include the 'other topics' category",
        default=False
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Don't actually generate bullet points or update the database",
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
    
    # Create database manager and generator agent
    db_manager = DatabaseManager()
    generator = BulletPointGeneratorAgent(db_manager=db_manager)
    
    # Generate bullet points
    generate_bullet_points(
        db_manager=db_manager,
        generator=generator,
        start_date=start_date,
        end_date=end_date,
        include_other_topics=args.include_other_topics,
        dry_run=args.dry_run
    )


if __name__ == "__main__":
    main()
