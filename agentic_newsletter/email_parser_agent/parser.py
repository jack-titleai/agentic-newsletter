"""Email parser agent for extracting articles from newsletter emails."""

import logging
import os
from typing import List, Optional, Dict, Any

from agentic_newsletter.email_parser_agent.article import Article
from agentic_newsletter.email_parser_agent.openai_client import OpenAIClient


class EmailParserAgent:
    """Agent for parsing newsletter emails and extracting articles."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o"):
        """Initialize the parser agent.
        
        Args:
            api_key (Optional[str], optional): OpenAI API key. If None, will attempt to read from environment variable.
            model (str, optional): The OpenAI model to use for extraction. Defaults to "gpt-4o".
            
        Raises:
            ValueError: If no API key is provided and OPENAI_API_KEY environment variable is not set.
        """
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key is required. Provide it directly or set OPENAI_API_KEY environment variable.")
        
        self.openai_client = OpenAIClient(api_key=self.api_key, model=model)
        self.logger = logging.getLogger(__name__)
    
    def parse_text(self, text: str) -> List[Article]:
        """Parse text and extract AI-related articles.
        
        Args:
            text (str): The text to parse (e.g., email body).
            
        Returns:
            List[Article]: List of extracted AI-related Article objects.
        """
        self.logger.info("Parsing text to extract AI-related articles")
        
        # Get extraction result from OpenAI
        extraction_result = self.openai_client.extract_articles(text)
        
        # Convert to Article objects
        articles = []
        if "articles" in extraction_result:
            for article_data in extraction_result["articles"]:
                article = Article(
                    title=article_data.get("title", "Untitled"),
                    body=article_data.get("body", ""),
                    url=article_data.get("url"),
                    tags=article_data.get("tags", []),
                    category=article_data.get("category", "other topics")
                )
                articles.append(article)
        
        self.logger.info(f"Extracted {len(articles)} AI-related articles from text")
        
        # Log category counts
        category_counts = {}
        for article in articles:
            category = article.category
            if category in category_counts:
                category_counts[category] += 1
            else:
                category_counts[category] = 1
        
        for category, count in category_counts.items():
            self.logger.info(f"Category '{category}': {count} articles")
        
        return articles
    
    def parse_email(self, email_body: str) -> List[Article]:
        """Parse an email body and extract AI-related articles.
        
        This is an alias for parse_text, specifically for email bodies.
        
        Args:
            email_body (str): The email body to parse.
            
        Returns:
            List[Article]: List of extracted AI-related Article objects.
        """
        return self.parse_text(email_body)
    
    def articles_to_json(self, articles: List[Article]) -> Dict[str, Any]:
        """Convert a list of articles to a JSON-serializable dictionary.
        
        Args:
            articles (List[Article]): List of Article objects.
            
        Returns:
            Dict[str, Any]: JSON-serializable dictionary.
        """
        return {
            "articles": [article.to_dict() for article in articles]
        }
