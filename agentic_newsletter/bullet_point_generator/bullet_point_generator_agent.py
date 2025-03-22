"""Bullet point generator agent for Agentic Newsletter."""

import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set

from agentic_newsletter.bullet_point_generator.openai_client import OpenAIClient
from agentic_newsletter.bullet_point_generator.schemas import BulletPointResult
from agentic_newsletter.config.config_loader import ConfigLoader
from agentic_newsletter.database.database_manager import DatabaseManager
from agentic_newsletter.database.parsed_article import ParsedArticle

logger = logging.getLogger(__name__)


class BulletPointGeneratorAgent:
    """Agent for generating bullet points from categorized articles."""
    
    def __init__(self, openai_client: Optional[OpenAIClient] = None, db_manager: Optional[DatabaseManager] = None) -> None:
        """Initialize the bullet point generator agent.
        
        Args:
            openai_client (Optional[OpenAIClient], optional): OpenAI client. Defaults to None.
            db_manager (Optional[DatabaseManager], optional): Database manager. Defaults to None.
        """
        self.openai_client = openai_client or OpenAIClient()
        self.db_manager = db_manager or DatabaseManager()
        self.config_loader = ConfigLoader()
        self.categories = set(self.config_loader.get_article_categories())
        
        # Categories to exclude
        self.excluded_categories = {"other topics", None}
    
    def generate_bullet_points(
        self, 
        start_date: datetime, 
        end_date: datetime,
        include_other_topics: bool = False,
        dry_run: bool = False
    ) -> Dict[str, BulletPointResult]:
        """Generate bullet points for all categories within a date range.
        
        Args:
            start_date (datetime): Start date for articles.
            end_date (datetime): End date for articles.
            include_other_topics (bool, optional): Whether to include the "other topics" category. 
                Defaults to False.
            dry_run (bool, optional): Whether to run in dry-run mode (don't save to database).
                Defaults to False.
            
        Returns:
            Dict[str, BulletPointResult]: A dictionary mapping categories to their bullet point results.
        """
        logger.info(f"Generating bullet points for articles from {start_date} to {end_date}")
        
        # Start the timer
        start_time = time.time()
        
        # Get all categories that have articles in the date range
        categories_with_articles = self._get_categories_with_articles(start_date, end_date)
        
        # Filter out excluded categories
        excluded = self.excluded_categories.copy()
        if not include_other_topics:
            excluded.add("other topics")
        
        categories_to_process = [cat for cat in categories_with_articles if cat not in excluded]
        
        logger.info(f"Found {len(categories_to_process)} categories with articles to process")
        
        # Generate bullet points for each category
        results = {}
        total_bullet_points = 0
        total_articles_processed = 0
        error_message = None
        
        try:
            for category in categories_to_process:
                # Get articles for this category
                articles = self.db_manager.get_articles_by_category(category, start_date, end_date)
                
                if not articles:
                    logger.warning(f"No articles found for category '{category}' in the specified date range")
                    continue
                
                total_articles_processed += len(articles)
                logger.info(f"Generating bullet points for category '{category}' with {len(articles)} articles")
                
                # Concatenate article content
                articles_text = self._concatenate_articles(articles)
                
                # Generate bullet points
                result = self.openai_client.generate_bullet_points(category, articles_text)
                
                # Save bullet points to the database (unless in dry run mode)
                if not dry_run:
                    self._save_bullet_points(result)
                else:
                    logger.info(f"Dry run: Would save {len(result.bullet_points)} bullet points for category '{category}'")
                
                # Add to results
                results[category] = result
                total_bullet_points += len(result.bullet_points)
        except Exception as e:
            error_message = str(e)
            logger.error(f"Error generating bullet points: {error_message}")
        
        # Calculate the time taken
        elapsed_time = time.time() - start_time
        
        # Log the results (unless in dry run mode)
        if not dry_run:
            self.db_manager.log_bullet_point_generation(
                duration_seconds=elapsed_time,
                categories_processed=len(categories_to_process),
                bullet_points_generated=total_bullet_points,
                articles_processed=total_articles_processed,
                error_message=error_message
            )
        else:
            logger.info(
                f"Dry run: Would log bullet point generation: {total_bullet_points} bullet points "
                f"from {len(categories_to_process)} categories in {elapsed_time:.2f}s"
            )
        
        logger.info(f"Generated {total_bullet_points} bullet points across {len(categories_to_process)} categories in {elapsed_time:.2f} seconds")
        
        return results
    
    def _get_categories_with_articles(self, start_date: datetime, end_date: datetime) -> List[str]:
        """Get all categories that have articles within the date range.
        
        Args:
            start_date (datetime): Start date for articles.
            end_date (datetime): End date for articles.
            
        Returns:
            List[str]: List of categories with articles.
        """
        with self.db_manager.get_session() as session:
            from sqlalchemy import select, distinct
            from agentic_newsletter.database import ParsedArticle, Email
            
            # Join with Email to filter by email's received_date
            query = select(distinct(ParsedArticle.assigned_category)).join(
                Email, ParsedArticle.email_id == Email.id
            ).where(
                ParsedArticle.assigned_category.is_not(None),
                Email.received_date >= start_date,
                Email.received_date <= end_date
            )
            
            categories = [cat for cat in session.execute(query).scalars().all() if cat]
            return categories
    
    def _concatenate_articles(self, articles: List[ParsedArticle]) -> str:
        """Concatenate article content for processing.
        
        Args:
            articles (List[ParsedArticle]): List of articles to concatenate.
            
        Returns:
            str: Concatenated article content.
        """
        article_texts = []
        
        for i, article in enumerate(articles, 1):
            article_text = f"ARTICLE {i}:\n"
            article_text += f"TITLE: {article.title}\n"
            article_text += f"SUMMARY: {article.summary}\n"
            article_text += f"BODY: {article.body}\n\n"
            article_texts.append(article_text)
        
        return "\n".join(article_texts)
    
    def _save_bullet_points(self, result: BulletPointResult) -> None:
        """Save bullet points to the database.
        
        Args:
            result (BulletPointResult): The bullet point result to save.
        """
        for bullet_point_data in result.bullet_points:
            self.db_manager.add_bullet_point(
                bullet_point=bullet_point_data.bullet_point,
                frequency_score=bullet_point_data.frequency_score,
                impact_score=bullet_point_data.impact_score,
                assigned_category=result.category
            )
