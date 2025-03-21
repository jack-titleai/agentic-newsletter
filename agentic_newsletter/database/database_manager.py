"""Database manager for Agentic Newsletter."""

import logging
import statistics
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from agentic_newsletter.config.config_loader import ConfigLoader
from agentic_newsletter.database import Base, DownloadLog, Email, EmailSource, ParsedArticle, ParserLog
from agentic_newsletter.email_parser_agent.article import Article

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Database manager for Agentic Newsletter."""

    def __init__(self) -> None:
        """Initialize the database manager."""
        self.config_loader = ConfigLoader()
        self.db_path = self.config_loader.get_database_path()
        
        # Create database directory if it doesn't exist
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(exist_ok=True, parents=True)
        
        # Create database engine
        self.engine = create_engine(f"sqlite:///{self.db_path}")
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # Create tables
        Base.metadata.create_all(self.engine)
        
        logger.info(f"Database initialized at {self.db_path}")

    def get_session(self) -> Session:
        """Get a database session.
        
        Returns:
            Session: A database session.
        """
        return self.SessionLocal()

    def add_email_source(self, email_address: str, active: bool = True) -> EmailSource:
        """Add an email source to the database.
        
        Args:
            email_address (str): The email address to add.
            active (bool, optional): Whether the email source is active. Defaults to True.
            
        Returns:
            EmailSource: The added email source.
        """
        with self.get_session() as session:
            # Check if email source already exists
            existing_source = session.execute(
                select(EmailSource).where(EmailSource.email_address == email_address)
            ).scalar_one_or_none()
            
            if existing_source:
                # Update existing source if needed
                if existing_source.active != active:
                    existing_source.active = active
                    session.commit()
                return existing_source
            
            # Create new email source
            email_source = EmailSource(email_address=email_address, active=active)
            session.add(email_source)
            session.commit()
            session.refresh(email_source)
            
            logger.info(f"Added email source: {email_address}")
            return email_source

    def get_active_email_sources(self) -> List[EmailSource]:
        """Get all active email sources from the database.
        
        Returns:
            List[EmailSource]: A list of active email sources.
        """
        with self.get_session() as session:
            return list(session.execute(
                select(EmailSource).where(EmailSource.active == True)
            ).scalars().all())

    def update_email_source_status(self, email_address: str, active: bool) -> Optional[EmailSource]:
        """Update the status of an email source.
        
        Args:
            email_address (str): The email address to update.
            active (bool): The new active status.
            
        Returns:
            Optional[EmailSource]: The updated email source, or None if not found.
        """
        with self.get_session() as session:
            email_source = session.execute(
                select(EmailSource).where(EmailSource.email_address == email_address)
            ).scalar_one_or_none()
            
            if not email_source:
                logger.warning(f"Email source not found: {email_address}")
                return None
            
            email_source.active = active
            session.commit()
            session.refresh(email_source)
            
            logger.info(f"Updated email source status: {email_address} -> active={active}")
            return email_source

    def add_email(
        self,
        source_id: int,
        sender_email: str,
        subject: str,
        body: str,
        received_date: datetime,
        message_id: str,
    ) -> Email:
        """Add an email to the database.
        
        Args:
            source_id (int): The ID of the email source.
            sender_email (str): The sender's email address.
            subject (str): The email subject.
            body (str): The email body.
            received_date (datetime): The date the email was received.
            message_id (str): The unique message ID from Gmail.
            
        Returns:
            Email: The added email.
        """
        with self.get_session() as session:
            # Check if email already exists
            existing_email = session.execute(
                select(Email).where(Email.message_id == message_id)
            ).scalar_one_or_none()
            
            if existing_email:
                logger.debug(f"Email already exists: {message_id}")
                return existing_email
            
            # Create new email
            email = Email(
                source_id=source_id,
                sender_email=sender_email,
                subject=subject,
                body=body,
                received_date=received_date,
                message_id=message_id,
            )
            session.add(email)
            session.commit()
            session.refresh(email)
            
            logger.debug(f"Added email: {subject}")
            return email

    def log_download(
        self, duration_seconds: float, emails_downloaded: int, error_message: Optional[str] = None
    ) -> DownloadLog:
        """Log a download operation.
        
        Args:
            duration_seconds (float): The duration of the download operation in seconds.
            emails_downloaded (int): The number of emails downloaded.
            error_message (Optional[str], optional): An error message, if any. Defaults to None.
            
        Returns:
            DownloadLog: The created download log.
        """
        with self.get_session() as session:
            download_log = DownloadLog(
                duration_seconds=duration_seconds,
                emails_downloaded=emails_downloaded,
                error_message=error_message,
            )
            session.add(download_log)
            session.commit()
            session.refresh(download_log)
            
            logger.info(f"Logged download: {emails_downloaded} emails in {duration_seconds:.2f}s")
            return download_log
    
    def log_parsing(
        self, duration_seconds: float, articles_found: int, 
        articles_per_email: List[int], error_message: Optional[str] = None
    ) -> ParserLog:
        """Log a parsing operation.
        
        Args:
            duration_seconds (float): The duration of the parsing operation in seconds.
            articles_found (int): The number of articles found.
            articles_per_email (List[int]): List of article counts per email.
            error_message (Optional[str], optional): An error message, if any. Defaults to None.
            
        Returns:
            ParserLog: The created parser log.
        """
        with self.get_session() as session:
            # Calculate statistics
            avg_articles = sum(articles_per_email) / len(articles_per_email) if articles_per_email else 0
            median_articles = statistics.median(articles_per_email) if articles_per_email else 0
            
            parser_log = ParserLog(
                duration_seconds=duration_seconds,
                articles_found=articles_found,
                average_articles_per_email=avg_articles,
                median_articles_per_email=median_articles,
                error_message=error_message,
            )
            session.add(parser_log)
            session.commit()
            session.refresh(parser_log)
            
            logger.info(f"Logged parsing: {articles_found} articles in {duration_seconds:.2f}s")
            return parser_log

    def get_email_by_message_id(self, message_id: str) -> Optional[Email]:
        """Get an email by its message ID.
        
        Args:
            message_id (str): The message ID to look for.
            
        Returns:
            Optional[Email]: The email, or None if not found.
        """
        with self.get_session() as session:
            return session.execute(
                select(Email).where(Email.message_id == message_id)
            ).scalar_one_or_none()
    
    def add_parsed_article(self, article: Article, email_id: int, sender: str) -> ParsedArticle:
        """Add a parsed article to the database.
        
        Args:
            article (Article): The article to add.
            email_id (int): The ID of the email the article was parsed from.
            sender (str): The sender of the email.
            
        Returns:
            ParsedArticle: The added parsed article.
        """
        with self.get_session() as session:
            parsed_article = ParsedArticle.from_article(article, email_id, sender)
            session.add(parsed_article)
            session.commit()
            session.refresh(parsed_article)
            
            logger.debug(f"Added parsed article: {parsed_article.title}")
            return parsed_article
    
    def get_unparsed_emails(self) -> List[Email]:
        """Get all emails that have not been parsed yet.
        
        Returns:
            List[Email]: A list of unparsed emails.
        """
        with self.get_session() as session:
            # Query for emails that don't have any parsed articles
            query = select(Email).outerjoin(ParsedArticle).where(ParsedArticle.id == None)
            return list(session.execute(query).scalars().all())
    
    def is_email_parsed(self, email_id: int) -> bool:
        """Check if an email has been parsed.
        
        Args:
            email_id (int): The ID of the email to check.
            
        Returns:
            bool: True if the email has been parsed, False otherwise.
        """
        with self.get_session() as session:
            # Check if there are any parsed articles for this email
            count = session.execute(
                select(ParsedArticle).where(ParsedArticle.email_id == email_id)
            ).first() is not None
            return count

    def get_download_logs(self, limit: int = 10) -> List[DownloadLog]:
        """Get the most recent download logs.
        
        Args:
            limit (int, optional): The maximum number of logs to retrieve. Defaults to 10.
            
        Returns:
            List[DownloadLog]: A list of download logs.
        """
        with self.get_session() as session:
            return list(session.execute(
                select(DownloadLog).order_by(DownloadLog.timestamp.desc()).limit(limit)
            ).scalars().all())
