#!/usr/bin/env python
"""Script to migrate from article_groups to assigned_category in parsed_articles."""

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

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


def add_assigned_category_column(db_path: str, dry_run: bool = False) -> None:
    """Add assigned_category column to parsed_articles table.
    
    Args:
        db_path (str): Path to the database file.
        dry_run (bool, optional): If True, don't actually modify the database.
            Defaults to False.
    """
    logging.info(f"Adding assigned_category column to parsed_articles table in {db_path}")
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if the table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='parsed_articles'")
    if not cursor.fetchone():
        logging.error("parsed_articles table does not exist")
        conn.close()
        return
    
    # Get the current columns
    cursor.execute("PRAGMA table_info(parsed_articles)")
    columns = [row[1] for row in cursor.fetchall()]
    
    # Check if the assigned_category column already exists
    if "assigned_category" in columns:
        logging.info("assigned_category column already exists in parsed_articles, no migration needed")
        conn.close()
        return
    
    logging.info("Adding assigned_category column to parsed_articles")
    
    if dry_run:
        logging.info("Dry run, not modifying the database")
        conn.close()
        return
    
    # Add the assigned_category column
    cursor.execute("ALTER TABLE parsed_articles ADD COLUMN assigned_category TEXT")
    
    # Commit the changes
    conn.commit()
    conn.close()
    
    logging.info("parsed_articles migration completed successfully")


def migrate_article_groups_to_categories(db_path: str, dry_run: bool = False) -> None:
    """Migrate data from article_groups to assigned_category in parsed_articles.
    
    Args:
        db_path (str): Path to the database file.
        dry_run (bool, optional): If True, don't actually modify the database.
            Defaults to False.
    """
    logging.info(f"Migrating data from article_groups to assigned_category in {db_path}")
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if both tables exist
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='article_groups'")
    article_groups_exists = cursor.fetchone() is not None
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='article_group_items'")
    article_group_items_exists = cursor.fetchone() is not None
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='parsed_articles'")
    parsed_articles_exists = cursor.fetchone() is not None
    
    if not (article_groups_exists and article_group_items_exists and parsed_articles_exists):
        logging.info("One or more required tables don't exist, skipping data migration")
        conn.close()
        return
    
    # Check if the assigned_category column exists in parsed_articles
    cursor.execute("PRAGMA table_info(parsed_articles)")
    columns = [row[1] for row in cursor.fetchall()]
    
    if "assigned_category" not in columns:
        logging.error("assigned_category column doesn't exist in parsed_articles, run add_assigned_category_column first")
        conn.close()
        return
    
    # Get the article groups and their items
    cursor.execute("""
        SELECT ag.id, ag.title, agi.article_id
        FROM article_groups ag
        JOIN article_group_items agi ON ag.id = agi.article_group_id
    """)
    
    group_data = cursor.fetchall()
    
    if not group_data:
        logging.info("No article groups found, nothing to migrate")
        conn.close()
        return
    
    # Organize the data by article ID
    article_categories: Dict[int, str] = {}
    for group_id, group_title, article_id in group_data:
        article_categories[article_id] = group_title
    
    logging.info(f"Found {len(article_categories)} articles with assigned categories")
    
    if dry_run:
        logging.info("Dry run, not modifying the database")
        conn.close()
        return
    
    # Update the parsed_articles table
    for article_id, category in article_categories.items():
        cursor.execute(
            "UPDATE parsed_articles SET assigned_category = ? WHERE id = ?",
            (category, article_id)
        )
    
    # Commit the changes
    conn.commit()
    
    logging.info(f"Updated assigned_category for {len(article_categories)} articles")
    conn.close()


def drop_article_groups_tables(db_path: str, dry_run: bool = False) -> None:
    """Drop article_groups and article_group_items tables.
    
    Args:
        db_path (str): Path to the database file.
        dry_run (bool, optional): If True, don't actually modify the database.
            Defaults to False.
    """
    logging.info(f"Dropping article_groups and article_group_items tables in {db_path}")
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if the tables exist
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='article_groups'")
    article_groups_exists = cursor.fetchone() is not None
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='article_group_items'")
    article_group_items_exists = cursor.fetchone() is not None
    
    if not (article_groups_exists or article_group_items_exists):
        logging.info("Article groups tables don't exist, nothing to drop")
        conn.close()
        return
    
    if dry_run:
        logging.info("Dry run, not modifying the database")
        conn.close()
        return
    
    # Drop the tables
    if article_group_items_exists:
        cursor.execute("DROP TABLE article_group_items")
        logging.info("Dropped article_group_items table")
    
    if article_groups_exists:
        cursor.execute("DROP TABLE article_groups")
        logging.info("Dropped article_groups table")
    
    # Commit the changes
    conn.commit()
    conn.close()
    
    logging.info("Article groups tables dropped successfully")


def main() -> None:
    """Run the script."""
    parser = argparse.ArgumentParser(
        description="Migrate from article_groups to assigned_category in parsed_articles."
    )
    parser.add_argument(
        "-d", "--dry-run", action="store_true", 
        help="Don't actually modify the database"
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", 
        help="Enable verbose logging"
    )
    parser.add_argument(
        "--skip-data-migration", action="store_true",
        help="Skip migrating data from article_groups to assigned_category"
    )
    parser.add_argument(
        "--skip-drop-tables", action="store_true",
        help="Skip dropping article_groups and article_group_items tables"
    )
    args = parser.parse_args()
    
    # Set up logging
    setup_logging(args.verbose)
    
    # Get the database path
    config_loader = ConfigLoader()
    db_path = config_loader.get_database_path()
    
    # Run the migrations
    add_assigned_category_column(db_path, args.dry_run)
    
    if not args.skip_data_migration:
        migrate_article_groups_to_categories(db_path, args.dry_run)
    
    if not args.skip_drop_tables:
        drop_article_groups_tables(db_path, args.dry_run)


if __name__ == "__main__":
    main()
