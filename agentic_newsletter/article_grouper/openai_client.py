"""OpenAI client for the article grouper module."""

import json
import logging
import os
from typing import Dict, List

from openai import OpenAI

from agentic_newsletter.article_grouper.prompts import ARTICLE_GROUPING_PROMPT
from agentic_newsletter.article_grouper.schemas import ArticleData, ArticleGroupData, ArticleGroupResult, ARTICLE_GROUPING_SCHEMA

logger = logging.getLogger(__name__)


class OpenAIClient:
    """OpenAI client for the article grouper module."""
    
    def __init__(self, api_key: str = None, model: str = "gpt-4o") -> None:
        """Initialize the OpenAI client.
        
        Args:
            api_key (str, optional): OpenAI API key. Defaults to None.
            model (str, optional): OpenAI model to use. Defaults to "gpt-4o".
        """
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key not provided")
        
        self.model = model
        self.client = OpenAI(api_key=self.api_key)
    
    def group_articles(self, articles: List[ArticleData]) -> ArticleGroupResult:
        """Group articles by topic.
        
        Args:
            articles (List[ArticleData]): List of articles to group.
            
        Returns:
            ArticleGroupResult: Result of the grouping process.
        """
        if not articles:
            logger.warning("No articles provided for grouping")
            return ArticleGroupResult(groups=[], start_date=None, end_date=None)
        
        # Prepare the article data for the prompt
        article_data = []
        for article in articles:
            article_data.append({
                "id": article.id,
                "title": article.title,
                "summary": article.summary,
                "source": article.source
            })
        
        # Create the prompt
        prompt = ARTICLE_GROUPING_PROMPT.format(articles=json.dumps(article_data, indent=2))
        
        # Send the request to OpenAI
        logger.debug(f"Sending request to OpenAI API using model {self.model}")
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": prompt},
                ],
                response_format={"type": "json_schema", "schema": ARTICLE_GROUPING_SCHEMA},
                temperature=0.2,
            )
            
            logger.debug("Received response from OpenAI API")
            
            # Parse the response
            response_content = response.choices[0].message.content
            response_json = json.loads(response_content)
            
            # Create the result
            groups = []
            for group_data in response_json["groups"]:
                group = ArticleGroupData(
                    title=group_data["title"],
                    summary=group_data["summary"],
                    article_ids=group_data["article_ids"]
                )
                groups.append(group)
            
            # Determine the date range
            start_date = min(article.parsed_at for article in articles)
            end_date = max(article.parsed_at for article in articles)
            
            return ArticleGroupResult(
                groups=groups,
                start_date=start_date,
                end_date=end_date
            )
            
        except Exception as e:
            logger.error(f"Error grouping articles: {e}")
            raise
