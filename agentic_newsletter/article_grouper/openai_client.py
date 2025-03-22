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
        """Group articles by topic using the OpenAI API.
        
        Args:
            articles (List[ArticleData]): List of articles to group.
            
        Returns:
            ArticleGroupResult: Result of the grouping process.
            
        Raises:
            Exception: If there's an error grouping articles after max_retries attempts.
        """
        if not articles:
            logger.warning("No articles provided for grouping")
            return ArticleGroupResult(groups=[], start_date=None, end_date=None)
        
        # Convert ArticleData objects to dictionaries
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
        
        # Send the request to OpenAI with retry logic
        attempts = 0
        last_error = None
        backoff_time = self.retry_delay  # Start with the base delay
        
        while attempts < self.max_retries:
            attempts += 1
            try:
                logger.debug(f"Attempt {attempts}/{self.max_retries}: Sending request to OpenAI API using model {self.model}")
                
                # Try with json_schema format first
                try:
                    response = self.client.chat.completions.create(
                        model=self.model,
                        messages=[
                            {"role": "system", "content": prompt},
                        ],
                        response_format={
                            "type": "json_schema",
                            "json_schema": {
                                "name": "article_grouping",
                                "schema": ARTICLE_GROUPING_SCHEMA,
                                "strict": True
                            }
                        },
                        temperature=0.2,
                    )
                except openai.RateLimitError as e:
                    # Handle rate limit errors with exponential backoff
                    last_error = f"Rate limit exceeded: {e}"
                    logger.warning(f"Rate limit error: {e}")
                    if attempts < self.max_retries:
                        logger.info(f"Rate limited. Backing off for {backoff_time} seconds... (Attempt {attempts}/{self.max_retries})")
                        time.sleep(backoff_time)
                        # Exponential backoff: double the wait time for the next attempt
                        backoff_time *= 2
                        continue
                    else:
                        raise Exception(last_error)
                except Exception as e:
                    # If json_schema format fails, fall back to basic json_object format
                    logger.warning(f"Failed to use json_schema format: {e}. Falling back to json_object format.")
                    response = self.client.chat.completions.create(
                        model=self.model,
                        messages=[
                            {"role": "system", "content": prompt},
                        ],
                        response_format={"type": "json_object"},
                        temperature=0.2,
                    )
                
                logger.debug("Received response from OpenAI API")
                
                # Parse the response
                response_content = response.choices[0].message.content
                response_json = json.loads(response_content)
                
                # Convert the response to ArticleGroupData objects
                groups = []
                for group in response_json.get("groups", []):
                    groups.append(ArticleGroupData(
                        title=group.get("title", ""),
                        summary=group.get("summary", ""),
                        article_ids=group.get("article_ids", [])
                    ))
                
                # Get the earliest and latest parsed_at dates
                start_date = min(article.parsed_at for article in articles) if articles else None
                end_date = max(article.parsed_at for article in articles) if articles else None
                
                return ArticleGroupResult(
                    groups=groups,
                    start_date=start_date,
                    end_date=end_date
                )
                
            except Exception as e:
                last_error = str(e)
                logger.warning(f"Error in attempt {attempts}/{self.max_retries}: {last_error}")
                
                if attempts < self.max_retries:
                    logger.info(f"Retrying in {backoff_time} seconds...")
                    time.sleep(backoff_time)
                    # Exponential backoff: double the wait time for the next attempt
                    backoff_time *= 2
                else:
                    logger.error(f"Failed after {self.max_retries} attempts. Last error: {last_error}")
                    raise Exception(f"Error grouping articles: {last_error}")
    
    def merge_groups(self, group_result: ArticleGroupResult) -> ArticleGroupResult:
        """Merge similar groups using the OpenAI API.
        
        Args:
            group_result (ArticleGroupResult): Initial grouping result to merge.
            
        Returns:
            ArticleGroupResult: Result of the merging process with consolidated groups.
            
        Raises:
            Exception: If there's an error merging groups after max_retries attempts.
        """
        if not group_result.groups:
            logger.warning("No groups provided for merging")
            return group_result
        
        # Convert ArticleGroupData objects to dictionaries
        group_data = []
        for group in group_result.groups:
            group_data.append({
                "title": group.title,
                "summary": group.summary,
                "article_ids": group.article_ids
            })
        
        # Create the prompt
        prompt = GROUP_MERGING_PROMPT.format(groups=json.dumps(group_data, indent=2))
        
        # Send the request to OpenAI with retry logic
        attempts = 0
        last_error = None
        backoff_time = self.retry_delay  # Start with the base delay
        
        while attempts < self.max_retries:
            attempts += 1
            try:
                logger.debug(f"Attempt {attempts}/{self.max_retries}: Sending request to OpenAI API for group merging using model {self.model}")
                
                # Try with json_schema format first
                try:
                    response = self.client.chat.completions.create(
                        model=self.model,
                        messages=[
                            {"role": "system", "content": prompt},
                        ],
                        response_format={
                            "type": "json_schema",
                            "json_schema": {
                                "name": "group_merging",
                                "schema": GROUP_MERGING_SCHEMA,
                                "strict": True
                            }
                        },
                        temperature=0.2,
                    )
                except openai.RateLimitError as e:
                    # Handle rate limit errors with exponential backoff
                    last_error = f"Rate limit exceeded: {e}"
                    logger.warning(f"Rate limit error: {e}")
                    if attempts < self.max_retries:
                        logger.info(f"Rate limited. Backing off for {backoff_time} seconds... (Attempt {attempts}/{self.max_retries})")
                        time.sleep(backoff_time)
                        # Exponential backoff: double the wait time for the next attempt
                        backoff_time *= 2
                        continue
                    else:
                        raise Exception(last_error)
                except Exception as e:
                    # If json_schema format fails, fall back to basic json_object format
                    logger.warning(f"Failed to use json_schema format for merging: {e}. Falling back to json_object format.")
                    response = self.client.chat.completions.create(
                        model=self.model,
                        messages=[
                            {"role": "system", "content": prompt},
                        ],
                        response_format={"type": "json_object"},
                        temperature=0.2,
                    )
                
                logger.debug("Received response from OpenAI API for group merging")
                
                # Parse the response
                response_content = response.choices[0].message.content
                response_json = json.loads(response_content)
                
                # Convert the response to ArticleGroupData objects
                merged_groups = []
                for group in response_json.get("groups", []):
                    merged_groups.append(ArticleGroupData(
                        title=group.get("title", ""),
                        summary=group.get("summary", ""),
                        article_ids=group.get("article_ids", [])
                    ))
                
                return ArticleGroupResult(
                    groups=merged_groups,
                    start_date=group_result.start_date,
                    end_date=group_result.end_date
                )
                
            except Exception as e:
                last_error = str(e)
                logger.warning(f"Error in attempt {attempts}/{self.max_retries}: {last_error}")
                
                if attempts < self.max_retries:
                    logger.info(f"Retrying in {backoff_time} seconds...")
                    time.sleep(backoff_time)
                    # Exponential backoff: double the wait time for the next attempt
                    backoff_time *= 2
                else:
                    logger.error(f"Failed after {self.max_retries} attempts. Last error: {last_error}")
                    raise Exception(f"Error merging groups: {last_error}")
