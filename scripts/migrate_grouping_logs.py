#!/usr/bin/env python
"""Script to migrate grouping_logs and article_groups tables."""

import argparse
import logging
import sys
from pathlib import Path

# Add the parent directory to the Python path if running directly
parent_dir = Path(__file__).parent.parent
if parent_dir not in sys.path:
    sys.path.insert(0, str(parent_dir))

import sqlite3

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


def migrate_grouping_logs(db_path: str, dry_run: bool = False) -> None:
    """Migrate grouping_logs table.
    
    Args:
        db_path (str): Path to the database file.
        dry_run (bool, optional): If True, don't actually modify the database.
            Defaults to False.
    """
    logging.info(f"Migrating grouping_logs table in {db_path}")
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if the table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='grouping_logs'")
    if not cursor.fetchone():
        logging.info("grouping_logs table does not exist, no migration needed")
        conn.close()
        return
    
    # Get the current columns
    cursor.execute("PRAGMA table_info(grouping_logs)")
    columns = [row[1] for row in cursor.fetchall()]
    
    # Check if the new columns already exist
    new_columns = [
        "sources_processed",
        "average_articles_per_group",
        "median_articles_per_group",
        "max_articles_per_group",
        "min_articles_per_group"
    ]
    
    columns_to_add = [col for col in new_columns if col not in columns]
    
    if not columns_to_add:
        logging.info("All columns already exist in grouping_logs, no migration needed")
        conn.close()
        return
    
    logging.info(f"Adding columns to grouping_logs: {', '.join(columns_to_add)}")
    
    if dry_run:
        logging.info("Dry run, not modifying the database")
        conn.close()
        return
    
    # Add the new columns
    for column in columns_to_add:
        if column == "sources_processed":
            # This is a non-nullable column, so we need to set a default value
            cursor.execute(f"ALTER TABLE grouping_logs ADD COLUMN {column} INTEGER NOT NULL DEFAULT 0")
        else:
            cursor.execute(f"ALTER TABLE grouping_logs ADD COLUMN {column} FLOAT")
    
    # Commit the changes
    conn.commit()
    conn.close()
    
    logging.info("grouping_logs migration completed successfully")


def migrate_article_groups(db_path: str, dry_run: bool = False) -> None:
    """Migrate article_groups table.
    
    Args:
        db_path (str): Path to the database file.
        dry_run (bool, optional): If True, don't actually modify the database.
            Defaults to False.
    """
    logging.info(f"Migrating article_groups table in {db_path}")
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if the table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='article_groups'")
    if not cursor.fetchone():
        logging.info("article_groups table does not exist, no migration needed")
        conn.close()
        return
    
    # Get the current columns
    cursor.execute("PRAGMA table_info(article_groups)")
    columns = [row[1] for row in cursor.fetchall()]
    
    # Check if the added_at column already exists
    if "added_at" in columns:
        logging.info("added_at column already exists in article_groups, no migration needed")
        conn.close()
        return
    
    logging.info("Adding added_at column to article_groups")
    
    if dry_run:
        logging.info("Dry run, not modifying the database")
        conn.close()
        return
    
    # Add the added_at column with a default value of created_at
    cursor.execute("ALTER TABLE article_groups ADD COLUMN added_at DATETIME DEFAULT NULL")
    cursor.execute("UPDATE article_groups SET added_at = created_at")
    
    # Commit the changes
    conn.commit()
    conn.close()
    
    logging.info("article_groups migration completed successfully")


def main() -> None:
    """Run the script."""
    parser = argparse.ArgumentParser(description="Migrate grouping_logs and article_groups tables.")
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
    
    # Migrate the tables
    migrate_grouping_logs(db_path, args.dry_run)
    migrate_article_groups(db_path, args.dry_run)


if __name__ == "__main__":
    main()
