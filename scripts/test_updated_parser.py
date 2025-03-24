#!/usr/bin/env python
"""Script to test the updated email parser with direct category assignment."""

import argparse
import logging
import os
import sys
from pathlib import Path
from collections import Counter

# Add the parent directory to the Python path if running directly
parent_dir = Path(__file__).parent.parent
if parent_dir not in sys.path:
    sys.path.insert(0, str(parent_dir))

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

from agentic_newsletter.config.config_loader import ConfigLoader
from agentic_newsletter.database.database_manager import DatabaseManager
from agentic_newsletter.email_parser_agent import EmailParserAgent

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

def main() -> None:
    """Run the test script."""
    parser = argparse.ArgumentParser(description="Test the updated email parser with direct category assignment.")
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose logging"
    )
    parser.add_argument(
        "-t", "--text", type=str, help="Test with a specific text input instead of from the database"
    )
    parser.add_argument(
        "-f", "--file", type=str, help="Test with text from a file instead of from the database"
    )
    parser.add_argument(
        "-e", "--email-id", type=int, help="Test with a specific email ID from the database"
    )
    
    args = parser.parse_args()
    setup_logging(args.verbose)
    
    # Initialize components
    config_loader = ConfigLoader()
    db_manager = DatabaseManager()
    email_parser = EmailParserAgent()
    
    # Get the valid categories from config
    categories = config_loader.get_article_categories()
    logging.info(f"Valid categories: {categories}")
    
    # Determine the input text to parse
    input_text = None
    
    if args.text:
        # Use the provided text
        input_text = args.text
        logging.info("Using provided text input")
    elif args.file:
        # Read text from file
        try:
            with open(args.file, 'r', encoding='utf-8') as f:
                input_text = f.read()
            logging.info(f"Read {len(input_text)} characters from file: {args.file}")
        except Exception as e:
            logging.error(f"Error reading file: {e}")
            sys.exit(1)
    elif args.email_id:
        # Get email from database
        email = db_manager.get_email_by_id(args.email_id)
        if not email:
            logging.error(f"Email with ID {args.email_id} not found")
            sys.exit(1)
        input_text = email.body
        logging.info(f"Using email from {email.sender_email} with subject: {email.subject}")
    else:
        # Get the most recent unparsed email
        unparsed_emails = db_manager.get_unparsed_emails()
        if not unparsed_emails:
            logging.error("No unparsed emails found in the database")
            sys.exit(1)
        email = unparsed_emails[0]
        input_text = email.body
        logging.info(f"Using most recent unparsed email from {email.sender_email} with subject: {email.subject}")
    
    # Parse the text
    logging.info("Parsing text with updated parser...")
    articles = email_parser.parse_text(input_text)
    
    # Display results
    logging.info(f"Extracted {len(articles)} AI-related articles")
    
    # Count categories
    category_counter = Counter()
    for article in articles:
        category_counter[article.category] += 1
    
    # Display category counts
    logging.info("Category distribution:")
    for category, count in category_counter.items():
        logging.info(f"  - {category}: {count} articles")
    
    # Display article details
    for i, article in enumerate(articles, 1):
        logging.info(f"\nArticle {i}:")
        logging.info(f"  Title: {article.title}")
        logging.info(f"  Category: {article.category}")
        logging.info(f"  URL: {article.url}")
        logging.info(f"  Tags: {', '.join(article.tags) if article.tags else 'None'}")
        # Truncate body for display
        body_preview = article.body[:100] + "..." if len(article.body) > 100 else article.body
        logging.info(f"  Body preview: {body_preview}")
    
    logging.info("\nTest completed successfully")

if __name__ == "__main__":
    main()
