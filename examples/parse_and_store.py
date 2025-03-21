#!/usr/bin/env python
"""Example script to parse a newsletter and store the results in the database."""

import os
import sys
import time
from pathlib import Path

# Add the parent directory to the Python path if running directly
parent_dir = Path(__file__).parent.parent
if parent_dir not in sys.path:
    sys.path.insert(0, str(parent_dir))

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

from agentic_newsletter.database.database_manager import DatabaseManager
from agentic_newsletter.email_parser_agent import EmailParserAgent


def main():
    """Run the example."""
    # Check for OpenAI API key
    if not os.environ.get("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY environment variable not set")
        sys.exit(1)
    
    # Initialize the database manager and parser
    db_manager = DatabaseManager()
    parser = EmailParserAgent()
    
    # Get the path to the test email
    test_email_path = Path(parent_dir) / "data" / "test_email.txt"
    
    if not test_email_path.exists():
        print(f"Error: Test email not found at {test_email_path}")
        sys.exit(1)
    
    # Read the test email
    with open(test_email_path, "r", encoding="utf-8") as f:
        email_text = f.read()
    
    print(f"Parsing test email...")
    
    # Parse the email
    start_time = time.time()
    articles = parser.parse_text(email_text)
    duration = time.time() - start_time
    
    print(f"Extracted {len(articles)} articles in {duration:.2f} seconds")
    
    # Add a test email to the database if it doesn't exist
    test_email = db_manager.get_email_by_message_id("test_email_id")
    if not test_email:
        print("Adding test email to database...")
        test_email = db_manager.add_email(
            source_id=1,  # Assuming source ID 1 exists
            sender_email="test@example.com",
            subject="Test Newsletter",
            body=email_text,
            received_date=time.time(),
            message_id="test_email_id"
        )
    
    # Add the parsed articles to the database
    print("Adding parsed articles to database...")
    for article in articles:
        db_manager.add_parsed_article(article, test_email.id, test_email.sender_email)
    
    # Log the parsing operation
    db_manager.log_parsing(
        duration_seconds=duration,
        articles_found=len(articles),
        articles_per_email=[len(articles)],
        error_message=None
    )
    
    print(f"Successfully added {len(articles)} articles to the database")
    
    # Print article titles
    print("\nExtracted articles:")
    for i, article in enumerate(articles, 1):
        print(f"{i}. {article.title}")


if __name__ == "__main__":
    main()
