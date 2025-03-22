#!/usr/bin/env python
"""
Script to analyze the consistency of the article grouper by running it multiple times
and tracking the number of groups produced in each stage.
"""

import argparse
import logging
import sys
import time
import numpy as np
from datetime import datetime, timedelta
from typing import List, Tuple

from agentic_newsletter.article_grouper.article_grouper_agent import ArticleGrouperAgent
from agentic_newsletter.database.database_manager import DatabaseManager
from agentic_newsletter.database.models import ParsedArticle


def setup_logging(verbose: bool = False) -> None:
    """Set up logging configuration."""
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)]
    )


def run_grouper_once(
    db_manager: DatabaseManager,
    start_date: datetime,
    end_date: datetime,
    verbose: bool = False
) -> Tuple[int, int]:
    """
    Run the article grouper once and return the number of groups at each stage.
    
    Args:
        db_manager: Database manager instance
        start_date: Start date for article selection
        end_date: End date for article selection
        verbose: Whether to print verbose output
        
    Returns:
        Tuple of (initial_group_count, merged_group_count)
    """
    # Get articles from the database
    articles = db_manager.get_parsed_articles(
        start_date=start_date,
        end_date=end_date,
        order_by="created_at",
        order_direction="asc"
    )
    
    if not articles:
        logging.error(f"No articles found between {start_date} and {end_date}")
        return (0, 0)
    
    # Create an article grouper agent
    agent = ArticleGrouperAgent()
    
    # Group the articles
    result = agent.group_articles(articles)
    
    # Get the counts
    initial_group_count = agent.initial_group_count
    merged_group_count = len(result.groups)
    
    if verbose:
        logging.info(f"Run completed: {initial_group_count} initial groups, {merged_group_count} merged groups")
    
    return (initial_group_count, merged_group_count)


def analyze_results(initial_counts: List[int], merged_counts: List[int]) -> None:
    """
    Analyze and print statistics about the group counts.
    
    Args:
        initial_counts: List of initial group counts
        merged_counts: List of merged group counts
    """
    # Calculate statistics
    initial_avg = np.mean(initial_counts)
    initial_std = np.std(initial_counts)
    initial_median = np.median(initial_counts)
    
    merged_avg = np.mean(merged_counts)
    merged_std = np.std(merged_counts)
    merged_median = np.median(merged_counts)
    
    # Print results
    print("\n=== ANALYSIS RESULTS ===")
    
    print("\nInitial Group Counts:")
    for i, count in enumerate(initial_counts, 1):
        print(f"Run {i}: {count}")
    
    print(f"\nInitial Groups Statistics:")
    print(f"Average: {initial_avg:.2f}")
    print(f"Standard Deviation: {initial_std:.2f}")
    print(f"Median: {initial_median:.2f}")
    
    print("\nMerged Group Counts:")
    for i, count in enumerate(merged_counts, 1):
        print(f"Run {i}: {count}")
    
    print(f"\nMerged Groups Statistics:")
    print(f"Average: {merged_avg:.2f}")
    print(f"Standard Deviation: {merged_std:.2f}")
    print(f"Median: {merged_median:.2f}")


def main():
    """Main function to run the analysis."""
    parser = argparse.ArgumentParser(description="Analyze article grouper consistency")
    parser.add_argument(
        "--start-date",
        type=str,
        help="Start date for articles (YYYY-MM-DD)",
        required=True
    )
    parser.add_argument(
        "--end-date",
        type=str,
        help="End date for articles (YYYY-MM-DD), defaults to current date",
        default=None
    )
    parser.add_argument(
        "--runs",
        type=int,
        help="Number of times to run the grouper",
        default=15
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    
    args = parser.parse_args()
    
    # Set up logging
    setup_logging(args.verbose)
    
    # Parse dates
    start_date = datetime.strptime(args.start_date, "%Y-%m-%d")
    
    if args.end_date:
        end_date = datetime.strptime(args.end_date, "%Y-%m-%d")
    else:
        end_date = datetime.now()
    
    # Initialize database
    db_manager = DatabaseManager()
    logging.info(f"Analyzing grouper consistency from {start_date} to {end_date}")
    
    # Get article count
    articles = db_manager.get_parsed_articles(
        start_date=start_date,
        end_date=end_date
    )
    article_count = len(articles)
    logging.info(f"Found {article_count} articles to analyze.")
    
    if article_count == 0:
        logging.error("No articles found for the specified date range.")
        return
    
    # Run the grouper multiple times
    initial_counts = []
    merged_counts = []
    
    for run in range(1, args.runs + 1):
        logging.info(f"Starting run {run}/{args.runs}")
        start_time = time.time()
        
        initial_count, merged_count = run_grouper_once(
            db_manager=db_manager,
            start_date=start_date,
            end_date=end_date,
            verbose=args.verbose
        )
        
        initial_counts.append(initial_count)
        merged_counts.append(merged_count)
        
        end_time = time.time()
        logging.info(f"Run {run}/{args.runs} completed in {end_time - start_time:.2f} seconds")
    
    # Analyze and print results
    analyze_results(initial_counts, merged_counts)


if __name__ == "__main__":
    main()
