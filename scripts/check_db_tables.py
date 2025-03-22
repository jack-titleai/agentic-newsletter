#!/usr/bin/env python
"""Script to check database tables."""

import argparse
import logging
import sys
from pathlib import Path

# Add the parent directory to the Python path if running directly
parent_dir = Path(__file__).parent.parent
if parent_dir not in sys.path:
    sys.path.insert(0, str(parent_dir))

from sqlalchemy import inspect, text

from agentic_newsletter.database.database_manager import DatabaseManager


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


def check_tables(db_manager: DatabaseManager, table_name: str = None) -> None:
    """Check database tables.
    
    Args:
        db_manager (DatabaseManager): The database manager.
        table_name (str, optional): The name of a specific table to check. Defaults to None.
    """
    with db_manager.get_session() as session:
        inspector = inspect(db_manager.engine)
        
        # Get all table names
        table_names = inspector.get_table_names()
        
        if table_name:
            if table_name not in table_names:
                logging.error(f"Table '{table_name}' not found in database")
                return
            table_names = [table_name]
        
        # Print table information
        for table in table_names:
            logging.info(f"Table: {table}")
            
            # Get columns
            columns = inspector.get_columns(table)
            logging.info("  Columns:")
            for column in columns:
                logging.info(f"    {column['name']} ({column['type']})")
            
            # Get primary key
            pk = inspector.get_pk_constraint(table)
            logging.info(f"  Primary Key: {pk['constrained_columns']}")
            
            # Get foreign keys
            fks = inspector.get_foreign_keys(table)
            if fks:
                logging.info("  Foreign Keys:")
                for fk in fks:
                    logging.info(f"    {fk['constrained_columns']} -> {fk['referred_table']}.{fk['referred_columns']}")
            
            # Get row count
            count = session.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
            logging.info(f"  Row Count: {count}")
            
            logging.info("")


def main() -> None:
    """Run the script."""
    parser = argparse.ArgumentParser(description="Check database tables.")
    parser.add_argument(
        "-t", "--table", type=str, help="Name of a specific table to check", default=None
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose logging"
    )
    args = parser.parse_args()
    
    # Set up logging
    setup_logging(args.verbose)
    
    # Initialize the database manager
    db_manager = DatabaseManager()
    
    # Check tables
    check_tables(db_manager, args.table)


if __name__ == "__main__":
    main()
