"""Database manager for Agentic Newsletter."""

import logging
import os
from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple, Union
from pathlib import Path
from typing import List, Optional, Tuple

from sqlalchemy import create_engine, func, select, update
from sqlalchemy.orm import Session, sessionmaker

from agentic_newsletter.config.config_loader import ConfigLoader
from agentic_newsletter.database import (
    Base, DownloadLog, Email, EmailSource, 
    ParsedArticle, ParserLog, BulletPoint, BulletPointLog,
    TopicSummary, TopicSummaryLog
)
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

    def get_inactive_email_sources(self) -> List[EmailSource]:
        """Get all inactive email sources from the database.
        
        Returns:
            List[EmailSource]: A list of inactive email sources.
        """
        with self.get_session() as session:
            return list(session.execute(
                select(EmailSource).where(EmailSource.active == False)
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
            parser_log = ParserLog(
                duration_seconds=duration_seconds,
                articles_found=articles_found,
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
    
    def add_parsed_article(self, email_id: int, sender: str, article: Article) -> ParsedArticle:
        """Add a parsed article to the database.
        
        Args:
            email_id (int): ID of the email that contained the article.
            sender (str): Sender of the email.
            article (Article): Article to add.
            
        Returns:
            ParsedArticle: The added parsed article.
        """
        with self.get_session() as session:
            parsed_article = ParsedArticle.from_article(article, email_id, sender)
            session.add(parsed_article)
            session.commit()
            session.refresh(parsed_article)
            return parsed_article
    
    def get_unparsed_emails(self, start_date: Optional[datetime] = None) -> List[Email]:
        """Get all emails that have not been parsed yet.
        
        Args:
            start_date (Optional[datetime], optional): If provided, only return emails received
                on or after this date. Defaults to None.
        
        Returns:
            List[Email]: A list of unparsed emails.
        """
        with self.get_session() as session:
            query = select(Email).where(Email.parsed == False)
            
            if start_date:
                query = query.where(Email.received_date >= start_date)
            
            # Order by received date (oldest first)
            query = query.order_by(Email.received_date)
            
            emails = session.execute(query).scalars().all()
            return emails

    def is_email_parsed(self, email_id: int) -> bool:
        """Check if an email has been parsed.
        
        Args:
            email_id (int): The ID of the email to check.
            
        Returns:
            bool: True if the email has been parsed, False otherwise.
        """
        with self.get_session() as session:
            email = session.execute(
                select(Email).where(Email.id == email_id)
            ).scalar_one_or_none()
            
            if not email:
                return False
                
            return email.parsed

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

    def get_articles_by_date_range(
        self, start_date: datetime, end_date: datetime, active_sources_only: bool = True
    ) -> List[ParsedArticle]:
        """Get articles by date range of the source emails.
        
        Args:
            start_date (datetime): Start date for email received_date.
            end_date (datetime): End date for email received_date.
            active_sources_only (bool, optional): Whether to only include articles from active sources.
                Defaults to True.
                
        Returns:
            List[ParsedArticle]: List of articles from emails received within the specified date range.
        """
        with self.get_session() as session:
            # Join with Email to filter by email's received_date date
            query = select(ParsedArticle).join(
                Email, ParsedArticle.email_id == Email.id
            ).where(
                Email.received_date >= start_date,
                Email.received_date <= end_date
            )
            
            if active_sources_only:
                # Join with EmailSource to filter by active sources
                query = query.join(
                    EmailSource, Email.source_id == EmailSource.id
                ).where(EmailSource.active == True)
            
            articles = session.execute(query).scalars().all()
            return articles
    
    def update_article_categories(self, article_categories: Dict[int, str]) -> None:
        """Update the assigned_category field for multiple articles.
        
        Args:
            article_categories (Dict[int, str]): Dictionary mapping article IDs to categories.
        """
        if not article_categories:
            self.logger.warning("No article categories provided for update")
            return
        
        self.logger.info(f"Updating assigned_category for {len(article_categories)} articles")
        
        with self.get_session() as session:
            for article_id, category in article_categories.items():
                article = session.query(ParsedArticle).filter(ParsedArticle.id == article_id).first()
                if article:
                    article.assigned_category = category
                    self.logger.debug(f"Updated article {article_id} with category '{category}'")
                else:
                    self.logger.warning(f"Article with ID {article_id} not found")
            
            session.commit()
            self.logger.info("Article categories updated successfully")
    
    def get_articles_by_category(self, category: str, start_date: datetime, end_date: datetime) -> List[ParsedArticle]:
        """Get articles with a specific assigned category within a date range.
        
        Args:
            category (str): The category to filter by.
            start_date (datetime): Start date for email received_date.
            end_date (datetime): End date for email received_date.
                
        Returns:
            List[ParsedArticle]: List of articles with the specified category.
        """
        with self.get_session() as session:
            # Join with Email to filter by email's received_date
            query = select(ParsedArticle).join(
                Email, ParsedArticle.email_id == Email.id
            ).where(
                ParsedArticle.assigned_category == category,
                Email.received_date >= start_date,
                Email.received_date <= end_date
            ).order_by(Email.received_date.desc())  # Order by email received date, newest first
            
            articles = session.execute(query).scalars().all()
            return articles

    def log_grouping(
        self, duration_seconds: float, articles_processed: int, categories_used: int, 
        sources_processed: int, articles_per_category: Optional[List[int]] = None,
        error_message: Optional[str] = None
    ) -> None:
        """Log a grouping operation.
        
        Args:
            duration_seconds (float): The duration of the grouping operation in seconds.
            articles_processed (int): The number of articles processed.
            categories_used (int): The number of categories used.
            sources_processed (int): The number of email sources processed.
            articles_per_category (Optional[List[int]], optional): List of article counts per category.
                Used to calculate statistics. Defaults to None.
            error_message (Optional[str], optional): An error message, if any. Defaults to None.
        """
        # Calculate statistics if articles_per_category is provided
        avg_articles = None
        median_articles = None
        max_articles = None
        min_articles = None
        
        if articles_per_category and len(articles_per_category) > 0:
            avg_articles = sum(articles_per_category) / len(articles_per_category)
            
            # Calculate median
            sorted_counts = sorted(articles_per_category)
            mid = len(sorted_counts) // 2
            if len(sorted_counts) % 2 == 0:
                median_articles = (sorted_counts[mid - 1] + sorted_counts[mid]) / 2
            else:
                median_articles = sorted_counts[mid]
            
            max_articles = max(articles_per_category) if articles_per_category else None
            min_articles = min(articles_per_category) if articles_per_category else None
        
        with self.get_session() as session:
            logger.info(f"Logged grouping: {categories_used} categories from {articles_processed} articles in {duration_seconds:.2f}s")
    
    def add_bullet_point(
        self, 
        bullet_point: str, 
        category: str, 
        frequency_score: float, 
        impact_score: float, 
        specificity_score: float,
        source_url: Optional[str] = None
    ) -> BulletPoint:
        """Add a bullet point to the database.
        
        Args:
            bullet_point (str): The bullet point text.
            category (str): The category of the bullet point.
            frequency_score (float): The frequency score of the bullet point.
            impact_score (float): The impact score of the bullet point.
            specificity_score (float): The specificity score of the bullet point.
            source_url (Optional[str], optional): The source URL of the bullet point. Defaults to None.
            
        Returns:
            BulletPoint: The added bullet point.
        """
        with self.get_session() as session:
            bullet_point_obj = BulletPoint(
                bullet_point=bullet_point,
                assigned_category=category,
                frequency_score=frequency_score,
                impact_score=impact_score,
                specificity_score=specificity_score,
                source_url=source_url,
                created_at=datetime.utcnow()
            )
            session.add(bullet_point_obj)
            session.commit()
            session.refresh(bullet_point_obj)
            
            logger.info(f"Added bullet point for category '{category}'")
            return bullet_point_obj
    
    def get_bullet_points_by_category(
        self, 
        category: str, 
        start_date: Optional[datetime] = None, 
        end_date: Optional[datetime] = None
    ) -> List[BulletPoint]:
        """Get bullet points for a specific category within a date range.
        
        Args:
            category (str): The category to filter by.
            start_date (Optional[datetime], optional): Start date for created_at. Defaults to None.
            end_date (Optional[datetime], optional): End date for created_at. Defaults to None.
                
        Returns:
            List[BulletPoint]: List of bullet points for the specified category.
        """
        with self.get_session() as session:
            query = select(BulletPoint).where(BulletPoint.assigned_category == category)
            
            if start_date:
                query = query.where(BulletPoint.created_at >= start_date)
            
            if end_date:
                query = query.where(BulletPoint.created_at <= end_date)
            
            # Order by impact score (highest first), then frequency score
            query = query.order_by(BulletPoint.impact_score.desc(), BulletPoint.frequency_score.desc())
            
            bullet_points = session.execute(query).scalars().all()
            return bullet_points
    
    def log_bullet_point_generation(
        self,
        duration_seconds: float,
        categories_processed: int,
        bullet_points_generated: int,
        articles_processed: int,
        error_message: Optional[str] = None,
        category_metrics: Optional[Dict[str, Dict]] = None,
        avg_frequency_score: Optional[float] = None,
        std_frequency_score: Optional[float] = None,
        avg_impact_score: Optional[float] = None,
        std_impact_score: Optional[float] = None,
        avg_specificity_score: Optional[float] = None,
        std_specificity_score: Optional[float] = None,
        urls_found: Optional[int] = None
    ) -> BulletPointLog:
        """Log a bullet point generation run.
        
        Args:
            duration_seconds: Duration of the bullet point generation in seconds.
            categories_processed: Number of categories processed.
            bullet_points_generated: Number of bullet points generated.
            articles_processed: Number of articles processed.
            error_message: Error message if an error occurred.
            category_metrics: Dictionary of metrics per category.
            avg_frequency_score: Average frequency score across all bullet points.
            std_frequency_score: Standard deviation of frequency scores.
            avg_impact_score: Average impact score across all bullet points.
            std_impact_score: Standard deviation of impact scores.
            avg_specificity_score: Average specificity score across all bullet points.
            std_specificity_score: Standard deviation of specificity scores.
            urls_found: Number of URLs found in bullet points.
            
        Returns:
            BulletPointLog: The added bullet point log.
        """
        return self.add_bullet_point_log(
            duration_seconds=duration_seconds,
            categories_processed=categories_processed,
            bullet_points_generated=bullet_points_generated,
            articles_processed=articles_processed,
            error_message=error_message,
            category_metrics=category_metrics,
            avg_frequency_score=avg_frequency_score,
            std_frequency_score=std_frequency_score,
            avg_impact_score=avg_impact_score,
            std_impact_score=std_impact_score,
            avg_specificity_score=avg_specificity_score,
            std_specificity_score=std_specificity_score,
            urls_found=urls_found
        )
    
    def add_bullet_point_log(
        self,
        duration_seconds: float,
        categories_processed: int,
        bullet_points_generated: int,
        articles_processed: int,
        category_metrics: Optional[Dict[str, Dict]] = None,
        avg_frequency_score: Optional[float] = None,
        std_frequency_score: Optional[float] = None,
        avg_impact_score: Optional[float] = None,
        std_impact_score: Optional[float] = None,
        avg_specificity_score: Optional[float] = None,
        std_specificity_score: Optional[float] = None,
        urls_found: Optional[int] = None,
        error_message: Optional[str] = None
    ) -> BulletPointLog:
        """Add a bullet point log to the database.
        
        Args:
            duration_seconds: Duration of the bullet point generation in seconds.
            categories_processed: Number of categories processed.
            bullet_points_generated: Number of bullet points generated.
            articles_processed: Number of articles processed.
            category_metrics: Dictionary of metrics per category.
            avg_frequency_score: Average frequency score across all bullet points.
            std_frequency_score: Standard deviation of frequency scores.
            avg_impact_score: Average impact score across all bullet points.
            std_impact_score: Standard deviation of impact scores.
            avg_specificity_score: Average specificity score across all bullet points.
            std_specificity_score: Standard deviation of specificity scores.
            urls_found: Number of URLs found in bullet points.
            error_message: Error message if an error occurred.
            
        Returns:
            BulletPointLog: The added bullet point log.
        """
        with self.get_session() as session:
            log = BulletPointLog(
                duration_seconds=duration_seconds,
                categories_processed=categories_processed,
                bullet_points_generated=bullet_points_generated,
                articles_processed=articles_processed,
                avg_frequency_score=avg_frequency_score,
                std_frequency_score=std_frequency_score,
                avg_impact_score=avg_impact_score,
                std_impact_score=std_impact_score,
                avg_specificity_score=avg_specificity_score,
                std_specificity_score=std_specificity_score,
                urls_found=urls_found,
                error_message=error_message
            )
            
            if category_metrics:
                log.set_category_metrics(category_metrics)
                
            session.add(log)
            session.commit()
            session.refresh(log)
            
            return log

    def get_parsed_articles_by_email(self, email_id: int) -> List[ParsedArticle]:
        """Get all parsed articles for a specific email.
        
        Args:
            email_id (int): The ID of the email.
            
        Returns:
            List[ParsedArticle]: A list of parsed articles for the email.
        """
        with self.get_session() as session:
            parsed_articles = session.execute(
                select(ParsedArticle).where(ParsedArticle.email_id == email_id)
            ).scalars().all()
            
            return parsed_articles

    def mark_email_as_parsed(self, email_id: int) -> bool:
        """Mark an email as parsed.
        
        Args:
            email_id (int): The ID of the email to mark as parsed.
            
        Returns:
            bool: True if the email was successfully marked as parsed, False otherwise.
        """
        with self.get_session() as session:
            email = session.execute(
                select(Email).where(Email.id == email_id)
            ).scalar_one_or_none()
            
            if not email:
                logger.warning(f"Email with ID {email_id} not found")
                return False
                
            email.parsed = True
            session.commit()
            logger.debug(f"Email with ID {email_id} marked as parsed")
            return True
            
    def add_topic_summary(self, topic: str, summary: str) -> TopicSummary:
        """Add a topic summary to the database.
        
        Args:
            topic (str): The topic of the summary.
            summary (str): The summary text.
            
        Returns:
            TopicSummary: The added topic summary.
        """
        with self.get_session() as session:
            topic_summary = TopicSummary(
                topic=topic,
                summary=summary,
                created_at=datetime.utcnow()
            )
            session.add(topic_summary)
            session.commit()
            session.refresh(topic_summary)
            
            logger.info(f"Added topic summary for '{topic}'")
            return topic_summary
    
    def get_topic_summaries_by_date_range(
        self, 
        start_date: Optional[datetime] = None, 
        end_date: Optional[datetime] = None
    ) -> List[TopicSummary]:
        """Get topic summaries within a date range.
        
        Args:
            start_date (Optional[datetime], optional): Start date for created_at. Defaults to None.
            end_date (Optional[datetime], optional): End date for created_at. Defaults to None.
                
        Returns:
            List[TopicSummary]: List of topic summaries within the date range.
        """
        with self.get_session() as session:
            query = select(TopicSummary)
            
            if start_date:
                query = query.where(TopicSummary.created_at >= start_date)
            
            if end_date:
                query = query.where(TopicSummary.created_at <= end_date)
            
            # Order by creation date (newest first)
            query = query.order_by(TopicSummary.created_at.desc())
            
            summaries = session.execute(query).scalars().all()
            return summaries
    
    def get_most_recent_topic_summaries(self) -> Dict[str, TopicSummary]:
        """Get the most recent topic summaries for each topic.
        
        Returns:
            Dict[str, TopicSummary]: Dictionary mapping topics to their most recent summaries.
        """
        with self.get_session() as session:
            # Get all topic summaries ordered by creation date (newest first)
            query = select(TopicSummary).order_by(TopicSummary.created_at.desc())
            all_summaries = session.execute(query).scalars().all()
            
            # Keep only the most recent summary for each topic
            topic_to_summary: Dict[str, TopicSummary] = {}
            for summary in all_summaries:
                if summary.topic not in topic_to_summary:
                    topic_to_summary[summary.topic] = summary
            
            return topic_to_summary
    
    def add_topic_summary_log(
        self,
        duration_seconds: float,
        topics_processed: int,
        summaries_generated: int,
        bullet_points_processed: int,
        topic_metrics: Optional[Dict[str, Dict]] = None,
        error_message: Optional[str] = None
    ) -> TopicSummaryLog:
        """Log a topic summary generation operation.
        
        Args:
            duration_seconds (float): Duration of the operation in seconds.
            topics_processed (int): Number of topics processed.
            summaries_generated (int): Number of summaries generated.
            bullet_points_processed (int): Number of bullet points processed.
            topic_metrics (Optional[Dict[str, Dict]], optional): Metrics per topic. Defaults to None.
            error_message (Optional[str], optional): Error message if an error occurred. Defaults to None.
            
        Returns:
            TopicSummaryLog: The created log.
        """
        with self.get_session() as session:
            log = TopicSummaryLog(
                duration_seconds=duration_seconds,
                topics_processed=topics_processed,
                summaries_generated=summaries_generated,
                bullet_points_processed=bullet_points_processed,
                error_message=error_message
            )
            
            if topic_metrics:
                log.set_topic_metrics(topic_metrics)
            
            session.add(log)
            session.commit()
            session.refresh(log)
            
            logger.info(f"Logged topic summary generation: {summaries_generated} summaries for {topics_processed} topics in {duration_seconds:.2f}s")
            return log
    
    def get_most_recent_topic_summary_log(self) -> Optional[TopicSummaryLog]:
        """Get the most recent topic summary log.
        
        Returns:
            Optional[TopicSummaryLog]: The most recent topic summary log, or None if no logs exist.
        """
        with self.get_session() as session:
            query = select(TopicSummaryLog).order_by(TopicSummaryLog.timestamp.desc()).limit(1)
            log = session.execute(query).scalar_one_or_none()
            return log
