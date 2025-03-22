"""Article grouper agent for Agentic Newsletter."""

import logging
from datetime import datetime, timedelta
from typing import List, Optional

from agentic_newsletter.article_grouper.openai_client import OpenAIClient
from agentic_newsletter.article_grouper.schemas import ArticleData, ArticleGroupResult
from agentic_newsletter.database.parsed_article import ParsedArticle

logger = logging.getLogger(__name__)


class ArticleGrouperAgent:
    """Agent for grouping articles by topic."""
    
    def __init__(self, openai_client: Optional[OpenAIClient] = None) -> None:
        """Initialize the article grouper agent.
        
        Args:
            openai_client (Optional[OpenAIClient], optional): OpenAI client. Defaults to None.
        """
        self.openai_client = openai_client or OpenAIClient()
        self.initial_group_count = 0
    
    def group_articles(
        self, 
        articles: List[ParsedArticle],
        merge_groups: bool = True
    ) -> ArticleGroupResult:
        """Group articles by topic using a two-stage process.
        
        Args:
            articles (List[ParsedArticle]): List of articles to group.
            merge_groups (bool, optional): Whether to perform the second stage of merging similar groups. Defaults to True.
            
        Returns:
            ArticleGroupResult: Result of the grouping process.
        """
        if not articles:
            logger.warning("No articles provided for grouping")
            return ArticleGroupResult(groups=[], start_date=None, end_date=None)
        
        logger.info(f"Grouping {len(articles)} articles by topic")
        
        # Convert ParsedArticle objects to ArticleData objects
        article_data = []
        for article in articles:
            article_data.append(ArticleData(
                id=article.id,
                title=article.title,
                summary=article.summary,
                source=article.sender,
                parsed_at=article.parsed_at
            ))
        
        # Stage 1: Initial specific grouping
        initial_result = self.openai_client.group_articles(article_data)
        
        # Store the initial group count
        self.initial_group_count = len(initial_result.groups)
        
        logger.info(f"Stage 1: Created {self.initial_group_count} initial article groups")
        
        # If merge_groups is False or there's only one group, return the initial result
        if not merge_groups or self.initial_group_count <= 1:
            return initial_result
        
        # Stage 2: Merge similar groups
        logger.info("Stage 2: Merging similar groups")
        merged_result = self.openai_client.merge_groups(initial_result)
        
        logger.info(f"Stage 2: Created {len(merged_result.groups)} merged article groups")
        
        return merged_result
