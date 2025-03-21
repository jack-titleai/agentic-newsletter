#!/usr/bin/env python
"""Script to migrate the parser_logs table by removing average and median columns."""

import argparse
import logging
import sqlite3
import sys
from pathlib import Path

# Add the parent directory to the Python path if running directly
parent_dir = Path(__file__).parent.parent
if parent_dir not in sys.path:
    sys.path.insert(0, str(parent_dir))

from agentic_newsletter.config.config_loader import ConfigLoader


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


def migrate_parser_logs(db_path: str, dry_run: bool = False) -> None:
    """Migrate the parser_logs table by removing average and median columns.
    
    Args:
        db_path (str): Path to the SQLite database.
        dry_run (bool, optional): If True, don't actually modify the database.
            Defaults to False.
    """
    logging.info(f"Migrating parser_logs table in database: {db_path}")
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if the table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='parser_logs'")
        if not cursor.fetchone():
            logging.info("parser_logs table does not exist. No migration needed.")
            return
        
        # Check if the columns exist
        cursor.execute("PRAGMA table_info(parser_logs)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'average_articles_per_email' not in columns and 'median_articles_per_email' not in columns:
            logging.info("Columns already removed. No migration needed.")
            return
        
        if dry_run:
            logging.info("Dry run: Would migrate parser_logs table.")
            return
        
        # Create a new table without the columns
        logging.info("Creating new table without average and median columns...")
        cursor.execute("""
        CREATE TABLE parser_logs_new (
            id INTEGER PRIMARY KEY,
            timestamp DATETIME NOT NULL,
            duration_seconds FLOAT NOT NULL,
            articles_found INTEGER NOT NULL,
            error_message TEXT
        )
        """)
        
        # Copy data from the old table to the new table
        logging.info("Copying data to new table...")
        cursor.execute("""
        INSERT INTO parser_logs_new (id, timestamp, duration_seconds, articles_found, error_message)
        SELECT id, timestamp, duration_seconds, articles_found, error_message FROM parser_logs
        """)
        
        # Drop the old table
        logging.info("Dropping old table...")
        cursor.execute("DROP TABLE parser_logs")
        
        # Rename the new table
        logging.info("Renaming new table...")
        cursor.execute("ALTER TABLE parser_logs_new RENAME TO parser_logs")
        
        # Commit the changes
        conn.commit()
        logging.info("Migration completed successfully.")
        
    except Exception as e:
        conn.rollback()
        logging.error(f"Error migrating database: {e}")
        raise
    finally:
        conn.close()


def main() -> None:
    """Run the script."""
    parser = argparse.ArgumentParser(description="Migrate the parser_logs table by removing average and median columns.")
    parser.add_argument(
        "-d", "--dry-run", action="store_true", help="Don't actually modify the database"
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose logging"
    )
    args = parser.parse_args()
    
    # Set up logging
    setup_logging(args.verbose)
    
    # Get the database path
    config_loader = ConfigLoader()
    db_path = config_loader.get_database_path()
    
    # Migrate the database
    migrate_parser_logs(db_path, args.dry_run)


if __name__ == "__main__":
    main()
