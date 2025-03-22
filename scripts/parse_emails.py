#!/usr/bin/env python
"""Script to parse unparsed emails and add them to the database."""

import argparse
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import List, Optional

# Add the parent directory to the Python path if running directly
parent_dir = Path(__file__).parent.parent
if parent_dir not in sys.path:
    sys.path.insert(0, str(parent_dir))

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

from agentic_newsletter.database.database_manager import DatabaseManager
from agentic_newsletter.email_parser_agent import EmailParserAgent, Article


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


def parse_emails(
    db_manager: DatabaseManager, 
    parser: EmailParserAgent, 
    limit: int = None, 
    dry_run: bool = False,
    start_date: Optional[datetime] = None,
    delay_between_emails: float = 0.0
) -> None:
    """Parse unparsed emails and add them to the database.
    
    Args:
        db_manager (DatabaseManager): The database manager.
        parser (EmailParserAgent): The email parser agent.
        limit (int, optional): Maximum number of emails to parse. Defaults to None (all).
        dry_run (bool, optional): If True, don't actually add parsed articles to the database.
            Defaults to False.
        start_date (Optional[datetime], optional): If provided, only parse emails received
            on or after this date. Defaults to None.
        delay_between_emails (float, optional): Delay in seconds between processing emails.
            Useful to avoid rate limiting. Defaults to 0.0 (no delay).
    """
    # Get unparsed emails
    unparsed_emails = db_manager.get_unparsed_emails(start_date)
    
    if limit is not None:
        unparsed_emails = unparsed_emails[:limit]
    
    if not unparsed_emails:
        logging.info("No unparsed emails found.")
        return
    
    if start_date:
        logging.info(f"Found {len(unparsed_emails)} unparsed emails from {start_date.strftime('%Y-%m-%d')}.")
    else:
        logging.info(f"Found {len(unparsed_emails)} unparsed emails.")
    
    # Track statistics for logging
    total_articles = 0
    articles_per_email = []
    emails_processed = 0
    emails_with_errors = 0
    start_time = time.time()
    error_message = None
    
    for i, email in enumerate(unparsed_emails):
        # Double-check if the email has already been parsed
        if db_manager.is_email_parsed(email.id):
            logging.info(f"Skipping already parsed email from {email.sender_email}: {email.subject}")
            continue
            
        logging.info(f"Parsing email from {email.sender_email} with subject: {email.subject}")
        
        try:
            # Parse the email
            articles = parser.parse_text(email.body)
            articles_count = len(articles)
            articles_per_email.append(articles_count)
            total_articles += articles_count
            emails_processed += 1
            
            logging.info(f"Extracted {articles_count} AI-related articles from email.")
            
            if not dry_run:
                # Add parsed articles to the database
                for article in articles:
                    db_manager.add_parsed_article(article, email.id, email.sender_email)
                
                logging.info(f"Added {articles_count} articles to the database.")
        except Exception as e:
            emails_with_errors += 1
            error_msg = f"Error processing email from {email.sender_email} with subject '{email.subject}': {e}"
            logging.error(error_msg)
            if not error_message:  # Store the first error for logging
                error_message = error_msg
            # Continue with the next email
        
        # Add delay between emails if specified and not the last email
        if delay_between_emails > 0 and i < len(unparsed_emails) - 1:
            logging.debug(f"Waiting {delay_between_emails} seconds before processing next email...")
            time.sleep(delay_between_emails)
    
    # Calculate duration
    duration = time.time() - start_time
    
    # Log the parsing operation
    if not dry_run:
        db_manager.log_parsing(
            duration_seconds=duration,
            articles_found=total_articles,
            articles_per_email=articles_per_email,
            error_message=error_message
        )
    
    logging.info(f"Parsing completed in {duration:.2f} seconds.")
    logging.info(f"Emails processed successfully: {emails_processed}")
    if emails_with_errors > 0:
        logging.info(f"Emails with errors (skipped): {emails_with_errors}")
    logging.info(f"Total AI-related articles extracted: {total_articles}")


def main() -> None:
    """Run the script."""
    parser = argparse.ArgumentParser(description="Parse unparsed emails and add them to the database.")
    parser.add_argument(
        "-l", "--limit", type=int, help="Maximum number of emails to parse", default=None
    )
    parser.add_argument(
        "-d", "--dry-run", action="store_true", help="Don't actually add parsed articles to the database"
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose logging"
    )
    parser.add_argument(
        "--start-date", type=str, help="Only parse emails received on or after this date (format: YYYY-MM-DD)",
        default=None
    )
    parser.add_argument(
        "--delay-between-emails", type=float, help="Delay in seconds between processing emails", default=0.0
    )
    args = parser.parse_args()
    
    # Set up logging
    setup_logging(args.verbose)
    
    # Check for OpenAI API key
    if not os.environ.get("OPENAI_API_KEY"):
        logging.error("OPENAI_API_KEY environment variable not set")
        sys.exit(1)
    
    # Parse start date if provided
    start_date = None
    if args.start_date:
        try:
            start_date = datetime.strptime(args.start_date, "%Y-%m-%d")
            logging.info(f"Only parsing emails from {args.start_date} onwards")
        except ValueError:
            logging.error(f"Invalid date format: {args.start_date}. Use YYYY-MM-DD format.")
            sys.exit(1)
    
    # Initialize the database manager and parser
    db_manager = DatabaseManager()
    parser_agent = EmailParserAgent()
    
    logging.info("Parser will only extract AI-related articles")
    
    # Parse emails
    parse_emails(db_manager, parser_agent, args.limit, args.dry_run, start_date, args.delay_between_emails)


if __name__ == "__main__":
    main()
