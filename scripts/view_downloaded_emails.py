#!/usr/bin/env python
"""Script to view downloaded emails."""

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional

# Add the parent directory to the Python path if running directly
parent_dir = Path(__file__).parent.parent
if parent_dir not in sys.path:
    sys.path.insert(0, str(parent_dir))

from agentic_newsletter.database.database_manager import DatabaseManager
from agentic_newsletter.database.email import Email
from agentic_newsletter.database.email_source import EmailSource


def setup_logging(verbose: bool = False) -> None:
    """Set up logging.
    
    Args:
        verbose (bool, optional): Whether to enable verbose logging. Defaults to False.
    """
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler()],
    )


def view_emails(source_email: Optional[str] = None, limit: Optional[int] = None, verbose: bool = False) -> None:
    """View downloaded emails.
    
    Args:
        source_email (Optional[str], optional): Filter emails by source email address.
            If None, show emails from all sources. Defaults to None.
        limit (Optional[int], optional): Maximum number of emails to display.
            If None, display all emails. Defaults to None.
        verbose (bool, optional): Whether to enable verbose logging. Defaults to False.
    """
    setup_logging(verbose)
    
    # Create a database manager
    db_manager = DatabaseManager()
    
    # Get email sources
    with db_manager.get_session() as session:
        if source_email:
            # Get emails from a specific source
            source = session.query(EmailSource).filter(EmailSource.email_address == source_email).first()
            if not source:
                print(f"Error: Email source not found: {source_email}")
                sys.exit(1)
            
            emails = session.query(Email).filter(Email.source_id == source.id)
            print(f"Emails from {source_email}:")
        else:
            # Get all emails
            emails = session.query(Email).join(EmailSource)
            print("All downloaded emails:")
        
        # Apply limit
        if limit:
            emails = emails.limit(limit)
        
        # Count total emails
        total_count = emails.count()
        if total_count == 0:
            print("No emails found.")
            sys.exit(0)
        
        # Display emails
        for i, email in enumerate(emails.all(), 1):
            source = session.query(EmailSource).filter(EmailSource.id == email.source_id).first()
            print(f"\n{i}. From: {source.email_address}")
            print(f"   Subject: {email.subject}")
            print(f"   Date: {email.date}")
            print(f"   ID: {email.message_id}")
            
            if verbose:
                # Show snippet in verbose mode
                snippet = email.body[:150] + "..." if len(email.body) > 150 else email.body
                print(f"   Snippet: {snippet}")
        
        print(f"\nTotal: {total_count} emails")


def list_sources(verbose: bool = False) -> None:
    """List all email sources.
    
    Args:
        verbose (bool, optional): Whether to enable verbose logging. Defaults to False.
    """
    setup_logging(verbose)
    
    # Create a database manager
    db_manager = DatabaseManager()
    
    # Get email sources
    with db_manager.get_session() as session:
        sources = session.query(EmailSource).all()
        
        print("Email sources:")
        for i, source in enumerate(sources, 1):
            status = "Active" if source.active else "Inactive"
            print(f"{i}. {source.email_address} ({status})")
            
            if verbose:
                # Show email count in verbose mode
                email_count = session.query(Email).filter(Email.source_id == source.id).count()
                print(f"   Emails: {email_count}")
        
        print(f"\nTotal: {len(sources)} sources")


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="View downloaded emails"
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # View emails command
    view_parser = subparsers.add_parser("view", help="View downloaded emails")
    view_parser.add_argument(
        "-s", 
        "--source", 
        help="Filter emails by source email address"
    )
    view_parser.add_argument(
        "-l", 
        "--limit", 
        type=int, 
        help="Maximum number of emails to display"
    )
    
    # List sources command
    list_parser = subparsers.add_parser("sources", help="List all email sources")
    
    # Common arguments
    parser.add_argument(
        "-v", 
        "--verbose", 
        action="store_true", 
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    if args.command == "view":
        view_emails(source_email=args.source, limit=args.limit, verbose=args.verbose)
    elif args.command == "sources":
        list_sources(verbose=args.verbose)
    else:
        # Default to viewing emails if no command is specified
        view_emails(verbose=args.verbose)


if __name__ == "__main__":
    main()
