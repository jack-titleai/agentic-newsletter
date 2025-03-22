#!/usr/bin/env python
"""Script to migrate the database to add bullet point tables."""

import argparse
import logging
import os
import sys
from pathlib import Path

# Add the parent directory to the Python path if running directly
parent_dir = Path(__file__).parent.parent
if parent_dir not in sys.path:
    sys.path.insert(0, str(parent_dir))

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine, inspect

from agentic_newsletter.config.config_loader import ConfigLoader
from agentic_newsletter.database import Base, BulletPoint, BulletPointLog


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


def migrate_database(dry_run: bool = False, verbose: bool = False) -> None:
    """Migrate the database to add bullet point tables.
    
    Args:
        dry_run (bool, optional): Whether to run in dry-run mode. Defaults to False.
        verbose (bool, optional): Whether to enable verbose logging. Defaults to False.
    """
    # Set up logging
    setup_logging(verbose)
    
    # Load configuration
    config_loader = ConfigLoader()
    db_path = config_loader.get_database_path()
    db_url = f"sqlite:///{db_path}"
    
    # Create engine
    engine = create_engine(db_url)
    
    # Check if tables already exist
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    
    tables_to_create = []
    if "bullet_points" not in existing_tables:
        tables_to_create.append("bullet_points")
    
    if "bullet_point_logs" not in existing_tables:
        tables_to_create.append("bullet_point_logs")
    
    if not tables_to_create:
        logging.info("All bullet point tables already exist. No migration needed.")
        return
    
    # Create tables
    if dry_run:
        logging.info(f"Dry run: Would create tables: {', '.join(tables_to_create)}")
    else:
        logging.info(f"Creating tables: {', '.join(tables_to_create)}")
        Base.metadata.create_all(engine, checkfirst=True)
        logging.info("Migration completed successfully.")


def main():
    """Run the script."""
    parser = argparse.ArgumentParser(description="Migrate the database to add bullet point tables")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Don't actually create tables, just show what would be done",
        default=False
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
        default=False
    )
    
    args = parser.parse_args()
    
    migrate_database(args.dry_run, args.verbose)


if __name__ == "__main__":
    main()
