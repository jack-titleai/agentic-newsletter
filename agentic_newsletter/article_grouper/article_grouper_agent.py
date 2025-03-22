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
    
    def group_articles(
        self, 
        articles: List[ParsedArticle],
    ) -> ArticleGroupResult:
        """Group articles by topic.
        
        Args:
            articles (List[ParsedArticle]): List of articles to group.
            
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
                source=article.source,
                parsed_at=article.parsed_at
            ))
        
        # Group the articles
        result = self.openai_client.group_articles(article_data)
        
        logger.info(f"Created {len(result.groups)} article groups")
        
        return result
