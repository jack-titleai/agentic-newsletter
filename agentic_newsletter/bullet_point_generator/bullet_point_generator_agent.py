"""Bullet point generator agent for Agentic Newsletter."""

import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
import numpy as np

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
            start_date (datetime): Start date for articles to process.
            end_date (datetime): End date for articles to process.
            include_other_topics (bool, optional): Whether to include articles in the 'other_topics' category. Defaults to False.
            dry_run (bool, optional): If True, don't save bullet points to the database. Defaults to False.
            
        Returns:
            Dict[str, BulletPointResult]: Dictionary mapping category names to BulletPointResult objects.
        """
        start_time = time.time()
        results: Dict[str, BulletPointResult] = {}
        total_bullet_points = 0
        total_articles = 0
        error_message = None
        
        # Metrics tracking
        all_frequency_scores = []
        all_impact_scores = []
        all_specificity_scores = []
        total_urls_found = 0
        category_metrics = {}
        
        try:
            # Get all articles within the date range
            articles_by_category = self._get_articles_by_category(start_date, end_date, include_other_topics)
            
            if not articles_by_category:
                logger.info("No articles found in the date range")
                return {}
            
            logger.info(f"Found {len(articles_by_category)} categories with articles to process")
            
            # Process each category
            for category, articles in articles_by_category.items():
                total_articles += len(articles)
                logger.info(f"Generating bullet points for category '{category}' with {len(articles)} articles")
                
                # Concatenate article content
                articles_text = self._concatenate_articles(articles)
                
                # Generate bullet points
                result = self.openai_client.generate_bullet_points(category, articles_text)
                results[category] = result
                
                # Track metrics for this category
                category_frequency_scores = [bp.frequency_score for bp in result.bullet_points]
                category_impact_scores = [bp.impact_score for bp in result.bullet_points]
                category_specificity_scores = [bp.specificity_score for bp in result.bullet_points]
                category_urls_found = sum(1 for bp in result.bullet_points if bp.source_url)
                
                # Add to overall metrics
                all_frequency_scores.extend(category_frequency_scores)
                all_impact_scores.extend(category_impact_scores)
                all_specificity_scores.extend(category_specificity_scores)
                total_urls_found += category_urls_found
                
                # Store category metrics
                category_metrics[category] = {
                    "bullet_points": len(result.bullet_points),
                    "articles": len(articles),
                    "avg_frequency_score": np.mean(category_frequency_scores) if category_frequency_scores else None,
                    "std_frequency_score": np.std(category_frequency_scores) if category_frequency_scores else None,
                    "avg_impact_score": np.mean(category_impact_scores) if category_impact_scores else None,
                    "std_impact_score": np.std(category_impact_scores) if category_impact_scores else None,
                    "avg_specificity_score": np.mean(category_specificity_scores) if category_specificity_scores else None,
                    "std_specificity_score": np.std(category_specificity_scores) if category_specificity_scores else None,
                    "urls_found": category_urls_found,
                    "urls_percentage": (category_urls_found / len(result.bullet_points)) * 100 if result.bullet_points else 0
                }
                
                # Display metrics for this category
                print(f"\nCategory: {category}")
                print(f"  Articles processed: {len(articles)}")
                print(f"  Bullet points generated: {len(result.bullet_points)}")
                if category_frequency_scores:
                    print(f"  Frequency score: avg={np.mean(category_frequency_scores):.2f}, std={np.std(category_frequency_scores):.2f}")
                if category_impact_scores:
                    print(f"  Impact score: avg={np.mean(category_impact_scores):.2f}, std={np.std(category_impact_scores):.2f}")
                if category_specificity_scores:
                    print(f"  Specificity score: avg={np.mean(category_specificity_scores):.2f}, std={np.std(category_specificity_scores):.2f}")
                print(f"  URLs found: {category_urls_found}/{len(result.bullet_points)} ({(category_urls_found / len(result.bullet_points)) * 100:.1f}%)")
                
                if not dry_run:
                    self._save_bullet_points(result)
                else:
                    logger.info(f"Dry run: Would save {len(result.bullet_points)} bullet points for category '{category}'")
                
                total_bullet_points += len(result.bullet_points)
        
        except Exception as e:
            logger.error(f"Error generating bullet points: {str(e)}")
            error_message = str(e)
        
        duration = time.time() - start_time
        
        # Calculate overall metrics
        avg_frequency_score = np.mean(all_frequency_scores) if all_frequency_scores else None
        std_frequency_score = np.std(all_frequency_scores) if all_frequency_scores else None
        avg_impact_score = np.mean(all_impact_scores) if all_impact_scores else None
        std_impact_score = np.std(all_impact_scores) if all_impact_scores else None
        avg_specificity_score = np.mean(all_specificity_scores) if all_specificity_scores else None
        std_specificity_score = np.std(all_specificity_scores) if all_specificity_scores else None
        
        # Display overall metrics
        print("\nOverall Metrics:")
        print(f"  Categories processed: {len(results)}")
        print(f"  Articles processed: {total_articles}")
        print(f"  Bullet points generated: {total_bullet_points}")
        if all_frequency_scores:
            print(f"  Frequency score: avg={avg_frequency_score:.2f}, std={std_frequency_score:.2f}")
        if all_impact_scores:
            print(f"  Impact score: avg={avg_impact_score:.2f}, std={std_impact_score:.2f}")
        if all_specificity_scores:
            print(f"  Specificity score: avg={avg_specificity_score:.2f}, std={std_specificity_score:.2f}")
        print(f"  URLs found: {total_urls_found}/{total_bullet_points} ({(total_urls_found / total_bullet_points) * 100 if total_bullet_points else 0:.1f}%)")
        print(f"  Duration: {duration:.2f} seconds")
        
        # Save metrics to database
        if not dry_run:
            self.db_manager.log_bullet_point_generation(
                duration_seconds=duration,
                categories_processed=len(results),
                bullet_points_generated=total_bullet_points,
                articles_processed=total_articles,
                category_metrics=category_metrics,
                avg_frequency_score=avg_frequency_score,
                std_frequency_score=std_frequency_score,
                avg_impact_score=avg_impact_score,
                std_impact_score=std_impact_score,
                avg_specificity_score=avg_specificity_score,
                std_specificity_score=std_specificity_score,
                urls_found=total_urls_found,
                error_message=error_message
            )
        
        logger.info(f"Generated {total_bullet_points} bullet points across {len(results)} categories in {duration:.2f} seconds")
        
        return results
    
    def _get_articles_by_category(self, start_date: datetime, end_date: datetime, include_other_topics: bool = False) -> Dict[str, List[ParsedArticle]]:
        """Get articles by category within a date range.
        
        Args:
            start_date (datetime): Start date for articles to process.
            end_date (datetime): End date for articles to process.
            include_other_topics (bool, optional): Whether to include articles in the 'other_topics' category. Defaults to False.
            
        Returns:
            Dict[str, List[ParsedArticle]]: Dictionary mapping category names to lists of articles.
        """
        logger.info(f"Generating bullet points for articles from {start_date} to {end_date}")
        
        # Get all categories that have articles in the date range
        categories_with_articles = self._get_categories_with_articles(start_date, end_date)
        
        # Filter out excluded categories
        excluded = self.excluded_categories.copy()
        if not include_other_topics:
            excluded.add("other topics")
        
        categories_to_process = [cat for cat in categories_with_articles if cat not in excluded]
        
        # Get articles for each category
        articles_by_category = {}
        for category in categories_to_process:
            articles = self.db_manager.get_articles_by_category(category, start_date, end_date)
            
            if not articles:
                logger.warning(f"No articles found for category '{category}' in the specified date range")
                continue
            
            articles_by_category[category] = articles
        
        return articles_by_category
    
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
            article_text += f"BODY: {article.body}\n"
            if article.url:
                article_text += f"URL: {article.url}\n"
            article_text += "\n"
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
                category=result.category,
                frequency_score=bullet_point_data.frequency_score,
                impact_score=bullet_point_data.impact_score,
                specificity_score=bullet_point_data.specificity_score,
                source_url=bullet_point_data.source_url
            )
