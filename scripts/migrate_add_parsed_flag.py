#!/usr/bin/env python
"""Migration script to add a 'parsed' column to the emails table."""

import logging
import sys
from pathlib import Path

# Add the parent directory to the Python path if running directly
parent_dir = Path(__file__).parent.parent
if parent_dir not in sys.path:
    sys.path.insert(0, str(parent_dir))

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import Boolean, Column, text, inspect

from agentic_newsletter.database.database_manager import DatabaseManager
from agentic_newsletter.database.email import Email


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


def migrate_add_parsed_flag():
    """Add a 'parsed' column to the emails table and initialize it based on parsed articles."""
    # Create database manager
    db_manager = DatabaseManager()
    
    with db_manager.get_session() as session:
        # Check if the column already exists
        inspector = inspect(db_manager.engine)
        columns = [col["name"] for col in inspector.get_columns("emails")]
        
        if "parsed" not in columns:
            logging.info("Adding 'parsed' column to emails table...")
            
            # Add the column
            session.execute(text("ALTER TABLE emails ADD COLUMN parsed BOOLEAN DEFAULT FALSE NOT NULL"))
            session.commit()
            
            logging.info("Column added successfully.")
        else:
            logging.info("'parsed' column already exists in emails table.")
        
        # Initialize the parsed flag based on existing parsed articles
        logging.info("Initializing 'parsed' flag for emails with parsed articles...")
        
        # Get all emails that have parsed articles
        query = """
        UPDATE emails
        SET parsed = TRUE
        WHERE id IN (
            SELECT DISTINCT email_id
            FROM parsed_articles
        )
        """
        result = session.execute(text(query))
        session.commit()
        
        logging.info(f"Updated {result.rowcount} emails with parsed=TRUE.")
        
        # Log the total number of emails
        total_emails = session.query(Email).count()
        parsed_emails = session.query(Email).filter(Email.parsed == True).count()
        unparsed_emails = session.query(Email).filter(Email.parsed == False).count()
        
        logging.info(f"Total emails: {total_emails}")
        logging.info(f"Emails marked as parsed: {parsed_emails}")
        logging.info(f"Emails marked as unparsed: {unparsed_emails}")


if __name__ == "__main__":
    setup_logging()
    migrate_add_parsed_flag()
