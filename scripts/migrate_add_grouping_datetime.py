#!/usr/bin/env python
"""Migration script to add grouping_datetime column to parsed_articles table."""

import logging
import os
import sys
from datetime import datetime
from pathlib import Path

# Add the parent directory to the Python path if running directly
parent_dir = Path(__file__).parent.parent
if parent_dir not in sys.path:
    sys.path.insert(0, str(parent_dir))

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine, text
from agentic_newsletter.config.config_loader import ConfigLoader

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

def run_migration():
    """Run the migration to add the grouping_datetime column."""
    # Get database path from config
    config_loader = ConfigLoader()
    db_path = config_loader.get_database_path()
    
    logger.info(f"Running migration on database at {db_path}")
    
    # Create database engine
    engine = create_engine(f"sqlite:///{db_path}")
    
    # Check if column already exists
    with engine.connect() as conn:
        result = conn.execute(text("PRAGMA table_info(parsed_articles)"))
        columns = [row[1] for row in result.fetchall()]
        
        if "grouping_datetime" in columns:
            logger.info("Column 'grouping_datetime' already exists. Skipping migration.")
            return
    
    # Add the column
    with engine.begin() as conn:
        logger.info("Adding 'grouping_datetime' column to parsed_articles table")
        conn.execute(text("ALTER TABLE parsed_articles ADD COLUMN grouping_datetime TIMESTAMP"))
        
        # Update existing records with assigned categories to have a grouping_datetime
        logger.info("Setting grouping_datetime for articles with existing categories")
        conn.execute(text(
            "UPDATE parsed_articles SET grouping_datetime = :now "
            "WHERE assigned_category IS NOT NULL AND grouping_datetime IS NULL"
        ), {"now": datetime.utcnow()})
    
    logger.info("Migration completed successfully")

if __name__ == "__main__":
    run_migration()
