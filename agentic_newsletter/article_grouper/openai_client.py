"""OpenAI client for the article grouper module."""

import json
import logging
import os
import time
from datetime import datetime
from typing import Dict, List, Any

from openai import OpenAI
import openai

from agentic_newsletter.article_grouper.prompts import ARTICLE_GROUPING_PROMPT, GROUP_MERGING_PROMPT
from agentic_newsletter.article_grouper.schemas import (
    ArticleData, 
    ArticleGroupData, 
    ArticleGroupResult, 
    ARTICLE_GROUPING_SCHEMA,
    GROUP_MERGING_SCHEMA
)

logger = logging.getLogger(__name__)


class OpenAIClient:
    """Client for interacting with OpenAI's API."""
    
    def __init__(self, api_key: str = None, model: str = "gpt-4o", max_retries: int = 5, retry_delay: float = 1.0) -> None:
        """Initialize the OpenAI client.
        
        Args:
            api_key (str, optional): OpenAI API key. Defaults to None.
            model (str, optional): OpenAI model to use. Defaults to "gpt-4o".
            max_retries (int, optional): Maximum number of retries for API calls. Defaults to 5.
            retry_delay (float, optional): Initial delay between retries in seconds. Defaults to 1.0.
        """
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.max_retries = max_retries
        self.retry_delay = retry_delay
    
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
        
        # Prepare the input for the OpenAI API
        article_json = json.dumps([{
            "id": article.id,
            "title": article.title,
            "summary": article.summary,
            "source": article.source
        } for article in articles])
        
        # Prepare the messages for the chat completion
        messages = [
            {"role": "system", "content": ARTICLE_GROUPING_PROMPT},
            {"role": "user", "content": f"Here are the articles to group:\n\n{article_json}"}
        ]
        
        # Use the schema format if possible, otherwise fall back to json_object
        use_schema_format = True
        
        # Get the start and end dates
        dates = [article.parsed_at for article in articles if article.parsed_at]
        start_date = min(dates) if dates else None
        end_date = max(dates) if dates else None
        
        # Try to get a response from the OpenAI API with retries
        for attempt in range(1, self.max_retries + 1):
            try:
                if use_schema_format:
                    try:
                        response = self.client.chat.completions.create(
                            model=self.model,
                            messages=messages,
                            response_format={
                                "type": "json_schema",
                                "json_schema": {
                                    "name": "article_grouping",
                                    "schema": ARTICLE_GROUPING_SCHEMA,
                                    "strict": True
                                }
                            },
                            temperature=0.05,  # Lower temperature for more deterministic results
                        )
                    except openai.BadRequestError as e:
                        logger.warning(f"Failed to use json_schema format: Error code: {e.status_code} - {e}. Falling back to json_object format.")
                        use_schema_format = False
                        continue
                else:
                    response = self.client.chat.completions.create(
                        model=self.model,
                        messages=messages,
                        response_format={"type": "json_object"},
                        temperature=0.05,  # Lower temperature for more deterministic results
                    )
                
                logger.debug("Received response from OpenAI API")
                
                # Parse the response
                response_content = response.choices[0].message.content
                result = json.loads(response_content)
                
                # Convert the response to ArticleGroupData objects
                groups = []
                for group in result.get("groups", []):
                    groups.append(ArticleGroupData(
                        title=group.get("title", ""),
                        summary=group.get("summary", ""),
                        article_ids=group.get("article_ids", [])
                    ))
                
                return ArticleGroupResult(
                    groups=groups,
                    start_date=start_date,
                    end_date=end_date
                )
                
            except Exception as e:
                logger.warning(f"Error in attempt {attempt}/{self.max_retries}: {e}")
                
                if attempt < self.max_retries:
                    logger.info(f"Retrying in {self.retry_delay} seconds...")
                    time.sleep(self.retry_delay)
                    # Exponential backoff: double the wait time for the next attempt
                    self.retry_delay *= 2
                else:
                    logger.error(f"Failed after {self.max_retries} attempts. Last error: {e}")
                    raise Exception(f"Error grouping articles: {e}")
    
    def merge_groups(self, initial_result: ArticleGroupResult) -> ArticleGroupResult:
        """Merge similar groups from the initial grouping.
        
        Args:
            initial_result (ArticleGroupResult): Result of the initial grouping process.
            
        Returns:
            ArticleGroupResult: Result of the merging process.
        """
        if not initial_result.groups:
            logger.warning("No groups provided for merging")
            return initial_result
        
        # Prepare the input for the OpenAI API
        groups_json = json.dumps([{
            "title": group.title,
            "summary": group.summary,
            "article_ids": group.article_ids
        } for group in initial_result.groups])
        
        # Prepare the messages for the chat completion
        messages = [
            {"role": "system", "content": GROUP_MERGING_PROMPT},
            {"role": "user", "content": f"Here are the groups to merge:\n\n{groups_json}"}
        ]
        
        # Use the schema format if possible, otherwise fall back to json_object
        use_schema_format = True
        
        # Try to get a response from the OpenAI API with retries
        for attempt in range(1, self.max_retries + 1):
            try:
                if use_schema_format:
                    try:
                        response = self.client.chat.completions.create(
                            model=self.model,
                            messages=messages,
                            response_format={
                                "type": "json_schema",
                                "json_schema": {
                                    "name": "group_merging",
                                    "schema": GROUP_MERGING_SCHEMA,
                                    "strict": True
                                }
                            },
                            temperature=0.05,  # Lower temperature for more deterministic results
                        )
                    except openai.BadRequestError as e:
                        logger.warning(f"Failed to use json_schema format for merging: Error code: {e.status_code} - {e}. Falling back to json_object format.")
                        use_schema_format = False
                        continue
                else:
                    response = self.client.chat.completions.create(
                        model=self.model,
                        messages=messages,
                        response_format={"type": "json_object"},
                        temperature=0.05,  # Lower temperature for more deterministic results
                    )
                
                logger.debug("Received response from OpenAI API for group merging")
                
                # Parse the response
                response_content = response.choices[0].message.content
                result = json.loads(response_content)
                
                # Convert the response to ArticleGroupData objects
                merged_groups = []
                for group in result.get("groups", []):
                    merged_groups.append(ArticleGroupData(
                        title=group.get("title", ""),
                        summary=group.get("summary", ""),
                        article_ids=group.get("article_ids", [])
                    ))
                
                return ArticleGroupResult(
                    groups=merged_groups,
                    start_date=initial_result.start_date,
                    end_date=initial_result.end_date
                )
                
            except Exception as e:
                logger.warning(f"Error in attempt {attempt}/{self.max_retries}: {e}")
                
                if attempt < self.max_retries:
                    logger.info(f"Retrying in {self.retry_delay} seconds...")
                    time.sleep(self.retry_delay)
                    # Exponential backoff: double the wait time for the next attempt
                    self.retry_delay *= 2
                else:
                    logger.error(f"Failed after {self.max_retries} attempts. Last error: {e}")
                    raise Exception(f"Error merging groups: {e}")
