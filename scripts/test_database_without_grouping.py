#!/usr/bin/env python
"""Test script to verify database functionality without grouping."""

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
from agentic_newsletter.email_parser_agent.article import Article


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


def test_database_functionality():
    """Test database functionality without grouping."""
    # Create database manager
    db_manager = DatabaseManager()
    
    # Test database session
    print("Testing database session...")
    with db_manager.get_session() as session:
        print("Database session created successfully")
    
    # Test getting articles by category
    print("\nTesting get_articles_by_category...")
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    # Get all categories with articles
    categories = db_manager._get_categories_with_articles(start_date, end_date)
    print(f"Found {len(categories)} categories with articles")
    
    if categories:
        # Test getting articles for the first category
        category = categories[0]
        articles = db_manager.get_articles_by_category(category, start_date, end_date)
        print(f"Found {len(articles)} articles in category '{category}'")
        
        if articles:
            # Print details of the first article
            article = articles[0]
            print(f"Sample article: {article.title}")
            print(f"  Category: {article.assigned_category}")
            print(f"  URL: {article.url}")
            print(f"  Parsed at: {article.parsed_at}")
    
    # Test adding a new article
    print("\nTesting adding a new article...")
    # Create a test article
    test_article = Article(
        title="Test Article",
        body="This is a test article body.",
        category="test_category",
        url="https://example.com/test",
        tags=["test", "database"]
    )
    
    # Get the latest email ID for testing
    with db_manager.get_session() as session:
        from agentic_newsletter.database import Email
        latest_email = session.query(Email).order_by(Email.id.desc()).first()
    
    if latest_email:
        # Add the article to the database
        parsed_article = db_manager.add_parsed_article(
            article=test_article,
            email_id=latest_email.id,
            sender=latest_email.sender
        )
        print(f"Added test article with ID {parsed_article.id}")
        
        # Verify the article was added correctly
        with db_manager.get_session() as session:
            from agentic_newsletter.database import ParsedArticle
            retrieved_article = session.query(ParsedArticle).filter(
                ParsedArticle.id == parsed_article.id
            ).first()
            
            if retrieved_article:
                print("Test article retrieved successfully:")
                print(f"  Title: {retrieved_article.title}")
                print(f"  Category: {retrieved_article.assigned_category}")
                
                # Clean up the test article
                session.delete(retrieved_article)
                session.commit()
                print("Test article deleted")
    else:
        print("No emails found in the database to test with")
    
    print("\nAll database tests completed successfully!")


if __name__ == "__main__":
    setup_logging(verbose=True)
    test_database_functionality()
