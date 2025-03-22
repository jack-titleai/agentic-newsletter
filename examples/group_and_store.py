#!/usr/bin/env python
"""Example script to group articles and store the results in the database."""

import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

# Add the parent directory to the Python path if running directly
parent_dir = Path(__file__).parent.parent
if parent_dir not in sys.path:
    sys.path.insert(0, str(parent_dir))

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

from agentic_newsletter.article_grouper import ArticleGrouperAgent
from agentic_newsletter.database.database_manager import DatabaseManager


def main():
    """Run the example."""
    # Check for OpenAI API key
    if not os.environ.get("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY environment variable not set")
        sys.exit(1)
    
    # Initialize the database manager and grouper
    db_manager = DatabaseManager()
    grouper = ArticleGrouperAgent()
    
    # Set date range (last 7 days)
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=7)
    
    print(f"Grouping articles from {start_date} to {end_date}")
    
    # Get articles in the date range
    articles = db_manager.get_articles_by_date_range(start_date, end_date)
    
    if not articles:
        print("No articles found in the specified date range.")
        return
    
    print(f"Found {len(articles)} articles to group.")
    
    # Count the number of unique sources
    sources = set()
    for article in articles:
        sources.add(article.source)
    
    print(f"Articles come from {len(sources)} unique sources.")
    
    # Group the articles
    error_message = None
    articles_per_group = []
    start_time = time.time()
    try:
        result = grouper.group_articles(articles)
        duration = time.time() - start_time
        
        print(f"Created {len(result.groups)} groups in {duration:.2f} seconds.")
        
        # Calculate articles per group
        for group in result.groups:
            articles_per_group.append(len(group.article_ids))
        
        # Add the groups to the database
        now = datetime.utcnow()
        for group in result.groups:
            db_manager.add_article_group(
                title=group.title,
                summary=group.summary,
                article_ids=group.article_ids,
                start_date=result.start_date,
                end_date=result.end_date,
                added_at=now
            )
        
        print(f"Added {len(result.groups)} groups to the database.")
        
        # Log the grouping operation
        db_manager.log_grouping(
            duration_seconds=duration,
            articles_processed=len(articles),
            sources_processed=len(sources),
            groups_created=len(result.groups),
            articles_per_group=articles_per_group,
            error_message=None
        )
        
        # Print group details
        print("\nGroup details:")
        for i, group in enumerate(result.groups, 1):
            print(f"\nGroup {i}: {group.title}")
            print(f"Summary: {group.summary}")
            print(f"Articles ({len(group.article_ids)}):")
            
            # Get the articles in this group
            group_articles = []
            for article_id in group.article_ids:
                for article in articles:
                    if article.id == article_id:
                        group_articles.append(article)
                        break
            
            # Print article titles
            for j, article in enumerate(group_articles, 1):
                print(f"  {j}. {article.title} (from {article.source})")
    except Exception as e:
        duration = time.time() - start_time
        error_message = str(e)
        print(f"Error grouping articles: {error_message}")
        
        # Log the error
        db_manager.log_grouping(
            duration_seconds=duration,
            articles_processed=len(articles),
            sources_processed=len(sources),
            groups_created=0,
            articles_per_group=[],
            error_message=error_message
        )


if __name__ == "__main__":
    main()
