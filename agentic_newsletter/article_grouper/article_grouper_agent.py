"""Article grouper agent for Agentic Newsletter."""

import logging
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Set

from agentic_newsletter.article_grouper.openai_client import OpenAIClient
from agentic_newsletter.article_grouper.schemas import ArticleData, ArticleGroupResult, ArticleGroupData
from agentic_newsletter.config.config_loader import ConfigLoader
from agentic_newsletter.database.database_manager import DatabaseManager
from agentic_newsletter.database.parsed_article import ParsedArticle

logger = logging.getLogger(__name__)


class ArticleGrouperAgent:
    """Agent for grouping articles by topic."""
    
    def __init__(self, openai_client: Optional[OpenAIClient] = None, db_manager: Optional[DatabaseManager] = None) -> None:
        """Initialize the article grouper agent.
        
        Args:
            openai_client (Optional[OpenAIClient], optional): OpenAI client. Defaults to None.
            db_manager (Optional[DatabaseManager], optional): Database manager. Defaults to None.
        """
        self.openai_client = openai_client or OpenAIClient()
        self.db_manager = db_manager or DatabaseManager()
        self.config_loader = ConfigLoader()
        self.valid_categories = set(self.config_loader.get_article_categories())
    
    def group_articles(
        self, 
        articles: List[ParsedArticle]
    ) -> ArticleGroupResult:
        """Group articles into predefined categories from the config file.
        
        Args:
            articles (List[ParsedArticle]): List of articles to categorize.
            
        Returns:
            ArticleGroupResult: Result of the categorization process.
        """
        if not articles:
            logger.warning("No articles provided for categorization")
            return ArticleGroupResult(groups=[], start_date=None, end_date=None)
        
        logger.info(f"Categorizing {len(articles)} articles into predefined categories")
        
        # Create a mapping from original article IDs to consecutive IDs starting from 1
        id_mapping, reverse_mapping = self._create_id_mapping([article.id for article in articles])
        
        # Log the mapping
        logger.info(f"Created ID mapping for {len(id_mapping)} articles")
        logger.info(f"Original ID range: {min(id_mapping.keys())} to {max(id_mapping.keys())}")
        logger.info(f"Remapped ID range: 1 to {len(id_mapping)}")
        
        # Show a sample of the mapping
        sample_mapping = {k: id_mapping[k] for k in sorted(id_mapping.keys())[:5]}
        logger.info(f"Sample mapping (first 5): {sample_mapping}")
        
        # Convert ParsedArticle objects to ArticleData objects with remapped IDs
        article_data = []
        for article in articles:
            article_data.append(ArticleData(
                id=id_mapping[article.id],  # Use the remapped ID
                title=article.title,
                summary=article.summary,
                source=article.sender,
                parsed_at=article.parsed_at
            ))
        
        logger.info(f"Sending {len(article_data)} articles with remapped IDs to OpenAI")
        
        # Categorize articles using the OpenAI client
        result = self.openai_client.group_articles(article_data)
        
        # Map the article IDs back to the original IDs
        logger.info(f"Remapping {len(result.groups)} groups back to original article IDs")
        
        remapped_groups = []
        article_categories = {}  # Dictionary to store article ID -> category mappings
        
        for group in result.groups:
            # Ensure the category name matches exactly one of the predefined categories (case sensitive)
            if group.title not in self.valid_categories:
                logger.warning(f"Category '{group.title}' is not in the list of valid categories. Using lowercase version if available.")
                # Try to find a case-insensitive match
                for valid_category in self.valid_categories:
                    if valid_category.lower() == group.title.lower():
                        logger.info(f"Matched '{group.title}' to valid category '{valid_category}'")
                        group.title = valid_category
                        break
                else:
                    logger.error(f"Could not match '{group.title}' to any valid category. Using as is.")
            
            # Map each article ID back to its original ID
            original_article_ids = []
            for remapped_id in group.article_ids:
                if remapped_id in reverse_mapping:
                    original_id = reverse_mapping[remapped_id]
                    original_article_ids.append(original_id)
                    # Store the category for each article using the ORIGINAL article ID
                    article_categories[original_id] = group.title
                else:
                    logger.warning(f"Remapped ID {remapped_id} not found in reverse mapping. Skipping.")
            
            logger.info(f"Group '{group.title}': Remapped {len(group.article_ids)} articles from consecutive IDs to original IDs")
            
            remapped_groups.append(ArticleGroupData(
                title=group.title,
                summary=group.summary,
                article_ids=original_article_ids
            ))
        
        # Update the assigned_category field in the database using the ORIGINAL article IDs
        logger.info(f"Updating assigned_category for {len(article_categories)} articles")
        self.db_manager.update_article_categories(article_categories)
        
        # Create a new result with the remapped article IDs
        remapped_result = ArticleGroupResult(
            groups=remapped_groups,
            start_date=result.start_date,
            end_date=result.end_date
        )
        
        logger.info(f"Categorized articles into {len(remapped_result.groups)} categories")
        
        return remapped_result
    
    def _create_id_mapping(self, original_ids: List[int]) -> Tuple[Dict[int, int], Dict[int, int]]:
        """Create a mapping from original article IDs to consecutive IDs starting from 1.
        
        Args:
            original_ids (List[int]): List of original article IDs.
            
        Returns:
            Tuple[Dict[int, int], Dict[int, int]]: A tuple containing:
                - A mapping from original IDs to consecutive IDs
                - A mapping from consecutive IDs back to original IDs
        """
        # Create a mapping from original IDs to consecutive IDs starting from 1
        id_mapping = {}
        for i, original_id in enumerate(original_ids, start=1):
            id_mapping[original_id] = i
        
        # Create a reverse mapping from consecutive IDs back to original IDs
        reverse_mapping = {v: k for k, v in id_mapping.items()}
        
        return id_mapping, reverse_mapping
