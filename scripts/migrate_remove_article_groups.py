#!/usr/bin/env python
"""Migration script to remove the article_groups and article_group_items tables."""

import argparse
import logging
import sys
from pathlib import Path

# Add the parent directory to the path so we can import the package
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

from agentic_newsletter.config.config_loader import ConfigLoader

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Migrate the database to remove article_groups and article_group_items tables")
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
        # Check if the tables exist before attempting to drop them
        with engine.connect() as conn:
            # Check if article_group_items table exists
            result = conn.execute(text(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='article_group_items'"
            ))
            article_group_items_exists = result.fetchone() is not None
            
            # Check if article_groups table exists
            result = conn.execute(text(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='article_groups'"
            ))
            article_groups_exists = result.fetchone() is not None
            
            # Check if grouper_logs table exists
            result = conn.execute(text(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='grouper_logs'"
            ))
            grouper_logs_exists = result.fetchone() is not None
            
            if not article_group_items_exists and not article_groups_exists and not grouper_logs_exists:
                logger.info("Tables 'article_group_items', 'article_groups', and 'grouper_logs' do not exist. No migration needed.")
                return
            
            if args.dry_run:
                if article_group_items_exists:
                    logger.info("Dry run: Would drop 'article_group_items' table")
                if article_groups_exists:
                    logger.info("Dry run: Would drop 'article_groups' table")
                if grouper_logs_exists:
                    logger.info("Dry run: Would drop 'grouper_logs' table")
                return
            
            # Drop the tables in the correct order (due to foreign key constraints)
            if article_group_items_exists:
                logger.info("Dropping 'article_group_items' table")
                conn.execute(text("DROP TABLE article_group_items"))
            
            if article_groups_exists:
                logger.info("Dropping 'article_groups' table")
                conn.execute(text("DROP TABLE article_groups"))
            
            if grouper_logs_exists:
                logger.info("Dropping 'grouper_logs' table")
                conn.execute(text("DROP TABLE grouper_logs"))
            
            # Commit the transaction
            conn.commit()
            
            logger.info("Migration completed successfully")
    
    except SQLAlchemyError as e:
        logger.error(f"Database error: {e}")
        return
    
    logger.info("Database migration completed")

if __name__ == "__main__":
    main()
