#!/usr/bin/env python
"""Migration script to add specificity_score column to bullet_points table."""

import argparse
import logging
import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from agentic_newsletter.database.database_manager import DatabaseManager
from sqlalchemy import Column, Float, text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def migrate_add_specificity_score(dry_run: bool = False):
    """Add specificity_score column to bullet_points table.
    
    Args:
        dry_run (bool, optional): If True, don't actually make changes. Defaults to False.
    """
    db_manager = DatabaseManager()
    
    with db_manager.engine.connect() as conn:
        # Check if the column already exists
        result = conn.execute(text(
            "SELECT COUNT(*) FROM pragma_table_info('bullet_points') WHERE name='specificity_score'"
        ))
        column_exists = result.scalar() > 0
        
        if column_exists:
            logger.info("specificity_score column already exists in bullet_points table")
            return
        
        logger.info("Adding specificity_score column to bullet_points table")
        
        if not dry_run:
            # Add the column with a default value of 5.0 (middle of the 1-10 range)
            conn.execute(text(
                "ALTER TABLE bullet_points ADD COLUMN specificity_score FLOAT NOT NULL DEFAULT 5.0"
            ))
            conn.commit()
            logger.info("Added specificity_score column to bullet_points table")
        else:
            logger.info("Dry run: Would add specificity_score column to bullet_points table")


def main():
    """Run the migration."""
    parser = argparse.ArgumentParser(description="Add specificity_score column to bullet_points table")
    parser.add_argument("--dry-run", action="store_true", help="Don't actually make changes")
    args = parser.parse_args()
    
    migrate_add_specificity_score(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
