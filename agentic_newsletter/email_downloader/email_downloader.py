"""Email downloader for Agentic Newsletter."""

import logging
import time
from datetime import datetime
from typing import List, Optional

from agentic_newsletter.database.database_manager import DatabaseManager
from agentic_newsletter.database import Email, EmailSource
from agentic_newsletter.email_downloader.gmail_client import GmailClient

logger = logging.getLogger(__name__)


class EmailDownloader:
    """Email downloader for Agentic Newsletter."""

    def __init__(self) -> None:
        """Initialize the email downloader."""
        self.db_manager = DatabaseManager()
        self.gmail_client = GmailClient()
        logger.info("Email downloader initialized")

    def add_email_source(self, email_address: str, active: bool = True) -> EmailSource:
        """Add an email source to download from.
        
        Args:
            email_address (str): The email address to add.
            active (bool, optional): Whether the email source is active. Defaults to True.
            
        Returns:
            EmailSource: The added email source.
        """
        return self.db_manager.add_email_source(email_address, active)

    def update_email_source_status(self, email_address: str, active: bool) -> Optional[EmailSource]:
        """Update the status of an email source.
        
        Args:
            email_address (str): The email address to update.
            active (bool): The new active status.
            
        Returns:
            Optional[EmailSource]: The updated email source, or None if not found.
        """
        return self.db_manager.update_email_source_status(email_address, active)

    def get_active_email_sources(self) -> List[EmailSource]:
        """Get all active email sources.
        
        Returns:
            List[EmailSource]: A list of active email sources.
        """
        return self.db_manager.get_active_email_sources()

    def download_emails(
        self, 
        max_per_source: Optional[int] = None, 
        force: bool = False,
        specific_sources: Optional[List[EmailSource]] = None
    ) -> int:
        """Download emails from all active email sources.
        
        Args:
            max_per_source (Optional[int], optional): The maximum number of emails to download per source.
                Defaults to None, which uses the configured max_results.
            force (bool, optional): Whether to force download of all emails, even if they already exist.
                Defaults to False.
            specific_sources (Optional[List[EmailSource]], optional): List of specific email sources to download from.
                If None, download from all active sources. Defaults to None.
                
        Returns:
            int: The total number of emails downloaded.
        """
        start_time = time.time()
        total_downloaded = 0
        error_message = None
        
        try:
            # Get active email sources if not specified
            sources = specific_sources if specific_sources is not None else self.get_active_email_sources()
            logger.info(f"Downloading emails from {len(sources)} sources")
            
            for source in sources:
                # Download emails from this source
                source_downloaded = self._download_emails_from_source(source, max_per_source, force)
                total_downloaded += source_downloaded
                logger.info(f"Downloaded {source_downloaded} emails from {source.email_address}")
        except Exception as e:
            error_message = str(e)
            logger.error(f"Error downloading emails: {e}")
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Log the download
        self.db_manager.log_download(duration, total_downloaded, error_message)
        
        logger.info(f"Downloaded {total_downloaded} emails in {duration:.2f}s")
        return total_downloaded

    def _download_emails_from_source(
        self, source: EmailSource, max_results: Optional[int] = None, force: bool = False
    ) -> int:
        """Download emails from a specific source.
        
        Args:
            source (EmailSource): The email source to download from.
            max_results (Optional[int], optional): The maximum number of emails to download.
                Defaults to None, which uses the configured max_results.
            force (bool, optional): Whether to force download of all emails, even if they already exist.
                Defaults to False.
                
        Returns:
            int: The number of emails downloaded.
        """
        # Get emails from Gmail
        logger.info(f"Retrieving emails from {source.email_address}...")
        messages = self.gmail_client.get_emails_from_sender(source.email_address, max_results)
        logger.info(f"Found {len(messages)} emails from {source.email_address} in Gmail")
        
        # Count new emails
        new_emails = 0
        skipped_emails = 0
        
        # Process each message
        for message in messages:
            # Parse the message
            parsed_message = self.gmail_client.parse_email_message(message)
            
            # Check if the email already exists
            existing_email = self.db_manager.get_email_by_message_id(parsed_message["message_id"])
            if existing_email and not force:
                skipped_emails += 1
                continue
            
            # Add the email to the database
            self.db_manager.add_email(
                source_id=source.id,
                sender_email=parsed_message["sender_email"],
                subject=parsed_message["subject"],
                body=parsed_message["body"],
                received_date=parsed_message["received_date"],
                message_id=parsed_message["message_id"],
            )
            
            new_emails += 1
        
        logger.info(f"Downloaded {new_emails} new emails from {source.email_address} (skipped {skipped_emails} existing emails)")
        return new_emails
