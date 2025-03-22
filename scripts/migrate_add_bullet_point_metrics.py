#!/usr/bin/env python
"""Migration script to add metrics columns to bullet_point_logs table."""

import argparse
import logging
import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from agentic_newsletter.database.database_manager import DatabaseManager
from sqlalchemy import text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def migrate_add_bullet_point_metrics(dry_run: bool = False):
    """Add metrics columns to bullet_point_logs table.
    
    Args:
        dry_run (bool, optional): If True, don't actually make changes. Defaults to False.
    """
    db_manager = DatabaseManager()
    
    with db_manager.engine.connect() as conn:
        # Check if the table exists
        result = conn.execute(text(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='bullet_point_logs'"
        ))
        table_exists = result.scalar() is not None
        
        if not table_exists:
            logger.info("bullet_point_logs table doesn't exist yet, no migration needed")
            return
        
        # Check if the columns already exist
        result = conn.execute(text(
            "SELECT COUNT(*) FROM pragma_table_info('bullet_point_logs') WHERE name='avg_frequency_score'"
        ))
        column_exists = result.scalar() > 0
        
        if column_exists:
            logger.info("Metrics columns already exist in bullet_point_logs table")
            return
        
        logger.info("Adding metrics columns to bullet_point_logs table")
        
        if not dry_run:
            # Add the columns
            conn.execute(text("ALTER TABLE bullet_point_logs ADD COLUMN avg_frequency_score FLOAT"))
            conn.execute(text("ALTER TABLE bullet_point_logs ADD COLUMN std_frequency_score FLOAT"))
            conn.execute(text("ALTER TABLE bullet_point_logs ADD COLUMN avg_impact_score FLOAT"))
            conn.execute(text("ALTER TABLE bullet_point_logs ADD COLUMN std_impact_score FLOAT"))
            conn.execute(text("ALTER TABLE bullet_point_logs ADD COLUMN avg_specificity_score FLOAT"))
            conn.execute(text("ALTER TABLE bullet_point_logs ADD COLUMN std_specificity_score FLOAT"))
            conn.execute(text("ALTER TABLE bullet_point_logs ADD COLUMN urls_found INTEGER"))
            conn.execute(text("ALTER TABLE bullet_point_logs ADD COLUMN category_metrics TEXT"))
            conn.commit()
            logger.info("Added metrics columns to bullet_point_logs table")
        else:
            logger.info("Dry run: Would add metrics columns to bullet_point_logs table")


def main():
    """Run the migration."""
    parser = argparse.ArgumentParser(description="Add metrics columns to bullet_point_logs table")
    parser.add_argument("--dry-run", action="store_true", help="Don't actually make changes")
    args = parser.parse_args()
    
    migrate_add_bullet_point_metrics(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
