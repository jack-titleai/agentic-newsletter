#!/usr/bin/env python
"""Migration script to remove the summary and grouping_datetime columns from the parsed_articles table."""

import argparse
import logging
import sys
from pathlib import Path

# Add the parent directory to the path so we can import the package
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

from agentic_newsletter.config.config_loader import ConfigLoader
from agentic_newsletter.database.base import Base
from agentic_newsletter.database.database_manager import DatabaseManager
from agentic_newsletter.database.parsed_article import ParsedArticle

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Migrate the database to remove summary and grouping_datetime columns")
    parser.add_argument("--dry-run", action="store_true", help="Perform a dry run without making changes")
    return parser.parse_args()

def main():
    """Run the migration."""
    args = parse_args()
    
    # Load database configuration
    config_loader = ConfigLoader()
    db_path = config_loader.get_database_path()
    
    logger.info(f"Using database at {db_path}")
    
    # Create engine and connect to the database
    engine = create_engine(f"sqlite:///{db_path}")
    
    try:
        # Check if the columns exist before attempting to drop them
        with engine.connect() as conn:
            # Get column info
            result = conn.execute(text("PRAGMA table_info(parsed_articles)"))
            columns = {row[1]: row for row in result}
            
            if "summary" not in columns and "grouping_datetime" not in columns:
                logger.info("Columns 'summary' and 'grouping_datetime' do not exist. No migration needed.")
                return
            
            if args.dry_run:
                logger.info("Dry run: Would drop 'summary' and 'grouping_datetime' columns from parsed_articles table")
                return
            
            # SQLite doesn't support DROP COLUMN directly, so we need to:
            # 1. Create a new table without the columns
            # 2. Copy the data
            # 3. Drop the old table
            # 4. Rename the new table
            
            # Create a temporary table without the columns
            logger.info("Creating temporary table without the columns to be dropped")
            conn.execute(text("""
                CREATE TABLE parsed_articles_new (
                    id INTEGER PRIMARY KEY,
                    email_id INTEGER NOT NULL,
                    sender VARCHAR(255) NOT NULL,
                    title VARCHAR(255) NOT NULL,
                    body TEXT NOT NULL,
                    url VARCHAR(512),
                    tags JSON,
                    assigned_category VARCHAR(255),
                    parsed_at DATETIME NOT NULL,
                    added_at DATETIME NOT NULL,
                    FOREIGN KEY (email_id) REFERENCES emails (id)
                )
            """))
            
            # Copy data to the new table
            logger.info("Copying data to the new table")
            conn.execute(text("""
                INSERT INTO parsed_articles_new
                SELECT id, email_id, sender, title, body, url, tags, assigned_category, parsed_at, added_at
                FROM parsed_articles
            """))
            
            # Drop the old table
            logger.info("Dropping the old table")
            conn.execute(text("DROP TABLE parsed_articles"))
            
            # Rename the new table
            logger.info("Renaming the new table")
            conn.execute(text("ALTER TABLE parsed_articles_new RENAME TO parsed_articles"))
            
            # Commit the transaction
            conn.commit()
            
            logger.info("Migration completed successfully")
    
    except SQLAlchemyError as e:
        logger.error(f"Database error: {e}")
        return
    
    logger.info("Database migration completed")

if __name__ == "__main__":
    main()
