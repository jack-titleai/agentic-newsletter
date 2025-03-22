"""OpenAI client for the article grouper module."""

import json
import logging
import os
import time
from datetime import datetime
from typing import Dict, List, Any, Set

from openai import OpenAI
import openai

from agentic_newsletter.article_grouper.prompts import ARTICLE_GROUPING_PROMPT, ARTICLE_GROUPING_RETRY_PROMPT
from agentic_newsletter.article_grouper.schemas import (
    ArticleData, 
    ArticleGroupData, 
    ArticleGroupResult, 
    ARTICLE_GROUPING_SCHEMA
)
from agentic_newsletter.config.config_loader import ConfigLoader

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
        config_loader = ConfigLoader()
        self.config = config_loader.get_config()
        self.categories = self.config.get("article_categories", [])
    
    def group_articles(self, articles: List[ArticleData]) -> ArticleGroupResult:
        """Group articles into predefined categories from the config file.
        
        Args:
            articles (List[ArticleData]): List of articles to categorize.
            
        Returns:
            ArticleGroupResult: Result of the categorization process.
        """
        if not articles:
            logger.warning("No articles provided for categorization")
            # Return empty groups for all categories
            empty_groups = []
            for category in self.categories:
                empty_groups.append(ArticleGroupData(
                    title=category,
                    summary=f"No articles were found for the {category} category in the specified date range.",
                    article_ids=[]
                ))
            return ArticleGroupResult(groups=empty_groups, start_date=None, end_date=None)
        
        # Format the articles as a string
        articles_str = json.dumps([{
            "id": article.id,
            "title": article.title,
            "summary": article.summary,
            "source": article.source
        } for article in articles], indent=2)
        
        # Format the categories as a string
        categories_str = "\n".join([f"- {category}" for category in self.categories])
        
        # Get the list of valid article IDs for validation
        valid_article_ids = [article.id for article in articles]
        
        # Create a more explicit list of valid article IDs
        valid_ids_list = ", ".join(str(id) for id in sorted(valid_article_ids))
        
        # Add a note about the valid article IDs to the prompt
        valid_ids_note = f"IMPORTANT: Only categorize the {len(valid_article_ids)} articles provided in the input. The ONLY valid article IDs are: [{valid_ids_list}]. DO NOT include any article IDs that are not in this list."
        
        # Create the prompt
        prompt = ARTICLE_GROUPING_PROMPT.format(
            categories=categories_str,
            articles=articles_str,
            valid_ids_note=valid_ids_note
        )
        
        # Create the messages for the API call
        messages = [
            {"role": "system", "content": prompt}
        ]
        
        # Extract dates for the result
        dates = [article.parsed_at for article in articles if article.parsed_at]
        start_date = min(dates) if dates else None
        end_date = max(dates) if dates else None
        
        # Use the schema format if possible, otherwise fall back to json_object
        use_schema_format = True
        
        # Track errors for retry prompts
        previous_errors = []
        
        # Try to get a response from the OpenAI API with retries
        for attempt in range(1, self.max_retries + 1):
            try:
                # If this is a retry, update the prompt with error information
                if attempt > 1 and previous_errors:
                    error_feedback = "\n\n".join(previous_errors)
                    retry_prompt = ARTICLE_GROUPING_RETRY_PROMPT.format(
                        categories=categories_str,
                        articles=articles_str,
                        valid_ids_note=valid_ids_note,
                        error_feedback=error_feedback,
                        valid_ids_list=valid_ids_list
                    )
                    messages = [
                        {"role": "system", "content": retry_prompt}
                    ]
                    logger.info(f"Using retry prompt with error feedback for attempt {attempt}")
                
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
                            temperature=0.1,  # Lower temperature for more deterministic results
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
                        temperature=0.1,  # Lower temperature for more deterministic results
                    )
                
                logger.debug("Received response from OpenAI API")
                
                # Parse the response
                response_content = response.choices[0].message.content
                try:
                    result = json.loads(response_content)
                    
                    # Validate that the result has the expected structure
                    if "groups" not in result:
                        error_msg = "Response does not contain 'groups' field"
                        logger.error(error_msg)
                        previous_errors.append(f"ERROR: {error_msg}")
                        if attempt < self.max_retries:
                            logger.info(f"Retrying ({attempt}/{self.max_retries})...")
                            time.sleep(self.retry_delay * (2 ** (attempt - 1)))  # Exponential backoff
                            continue
                        else:
                            logger.error("Maximum retries reached. Returning empty result.")
                            return self._create_empty_result(start_date, end_date)
                    
                    # Validate that all articles are assigned to exactly one category
                    assigned_articles: Set[int] = set()
                    all_article_ids: Set[int] = set(valid_article_ids)  # Use the list of valid IDs we created
                    
                    # First pass: validate that all article IDs in the response are valid
                    invalid_article_ids = []
                    for group in result["groups"]:
                        for article_id in group["article_ids"]:
                            if article_id not in all_article_ids:
                                invalid_article_ids.append(article_id)
                    
                    if invalid_article_ids:
                        error_msg = f"Response contains invalid article IDs: {invalid_article_ids[:10]}... (showing first 10)"
                        logger.error(error_msg)
                        previous_errors.append(f"ERROR: {error_msg}\nThe only valid article IDs are: [{valid_ids_list}]")
                        if attempt < self.max_retries:
                            logger.info(f"Retrying ({attempt}/{self.max_retries})...")
                            time.sleep(self.retry_delay * (2 ** (attempt - 1)))  # Exponential backoff
                            continue
                        else:
                            logger.error("Maximum retries reached. Returning empty result.")
                            return self._create_empty_result(start_date, end_date)
                    
                    # Second pass: check for duplicate assignments
                    duplicate_article_ids = []
                    for group in result["groups"]:
                        for article_id in group["article_ids"]:
                            if article_id in assigned_articles:
                                duplicate_article_ids.append(article_id)
                            assigned_articles.add(article_id)
                    
                    if duplicate_article_ids:
                        error_msg = f"Articles {duplicate_article_ids[:10]}... are assigned to multiple categories"
                        logger.error(error_msg)
                        previous_errors.append(f"ERROR: {error_msg}\nEach article must be assigned to EXACTLY ONE category.")
                        if attempt < self.max_retries:
                            logger.info(f"Retrying ({attempt}/{self.max_retries})...")
                            time.sleep(self.retry_delay * (2 ** (attempt - 1)))  # Exponential backoff
                            continue
                        else:
                            logger.error("Maximum retries reached. Returning empty result.")
                            return self._create_empty_result(start_date, end_date)
                    
                    # Check if any articles are missing
                    missing_articles = all_article_ids - assigned_articles
                    if missing_articles:
                        error_msg = f"Articles {list(missing_articles)[:10]}... (showing first 10) are not assigned to any category"
                        logger.error(error_msg)
                        previous_errors.append(f"ERROR: {error_msg}\nEach article must be assigned to EXACTLY ONE category.")
                        if attempt < self.max_retries:
                            logger.info(f"Retrying ({attempt}/{self.max_retries})...")
                            time.sleep(self.retry_delay * (2 ** (attempt - 1)))  # Exponential backoff
                            continue
                        else:
                            logger.error("Maximum retries reached. Returning empty result.")
                            return self._create_empty_result(start_date, end_date)
                    
                    # Create ArticleGroupData objects
                    groups = []
                    
                    # Create a map of category titles to their corresponding groups
                    category_to_group = {group["title"]: group for group in result["groups"]}
                    
                    # Ensure all categories are included in the output
                    for category in self.categories:
                        if category in category_to_group:
                            group = category_to_group[category]
                            groups.append(ArticleGroupData(
                                title=category,
                                summary=group["summary"],
                                article_ids=group["article_ids"]
                            ))
                        else:
                            # Add empty group for this category
                            groups.append(ArticleGroupData(
                                title=category,
                                summary=f"No articles were found for the {category} category in the specified date range.",
                                article_ids=[]
                            ))
                    
                    # Create and return the result
                    return ArticleGroupResult(
                        groups=groups,
                        start_date=start_date,
                        end_date=end_date
                    )
                
                except json.JSONDecodeError as e:
                    error_msg = f"Failed to parse response as JSON: {e}"
                    logger.error(error_msg)
                    previous_errors.append(f"ERROR: {error_msg}")
                    if attempt < self.max_retries:
                        logger.info(f"Retrying ({attempt}/{self.max_retries})...")
                        time.sleep(self.retry_delay * (2 ** (attempt - 1)))  # Exponential backoff
                        continue
                    else:
                        logger.error("Maximum retries reached. Returning empty result.")
                        return self._create_empty_result(start_date, end_date)
            
            except openai.RateLimitError as e:
                logger.warning(f"Rate limit error: {e}")
                if attempt < self.max_retries:
                    wait_time = self.retry_delay * (2 ** (attempt - 1))  # Exponential backoff
                    logger.info(f"Waiting {wait_time} seconds before retrying...")
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error("Maximum retries reached. Returning empty result.")
                    return self._create_empty_result(start_date, end_date)
            
            except Exception as e:
                error_msg = f"Error calling OpenAI API: {e}"
                logger.error(error_msg)
                previous_errors.append(f"ERROR: {error_msg}")
                if attempt < self.max_retries:
                    logger.info(f"Retrying ({attempt}/{self.max_retries})...")
                    time.sleep(self.retry_delay * (2 ** (attempt - 1)))  # Exponential backoff
                    continue
                else:
                    logger.error("Maximum retries reached. Returning empty result.")
                    return self._create_empty_result(start_date, end_date)
    
    def _create_empty_result(self, start_date: datetime = None, end_date: datetime = None) -> ArticleGroupResult:
        """Create an empty result with all categories included.
        
        Args:
            start_date (datetime, optional): Start date. Defaults to None.
            end_date (datetime, optional): End date. Defaults to None.
            
        Returns:
            ArticleGroupResult: Empty result with all categories.
        """
        empty_groups = []
        for category in self.categories:
            empty_groups.append(ArticleGroupData(
                title=category,
                summary=f"No articles were found for the {category} category in the specified date range.",
                article_ids=[]
            ))
        return ArticleGroupResult(groups=empty_groups, start_date=start_date, end_date=end_date)
