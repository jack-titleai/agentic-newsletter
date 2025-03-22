"""OpenAI client for the email parser agent."""

import json
import logging
import time
from typing import Dict, Any, Optional

import openai
from openai import OpenAI

from agentic_newsletter.email_parser_agent.prompts import ARTICLE_EXTRACTION_PROMPT
from agentic_newsletter.email_parser_agent.schema import ARTICLE_EXTRACTION_SCHEMA


class OpenAIClient:
    """Client for interacting with OpenAI's API."""
    
    def __init__(self, api_key: str, model: str = "gpt-4o", max_retries: int = 5, retry_delay: float = 1.0):
        """Initialize the OpenAI client.
        
        Args:
            api_key (str): OpenAI API key.
            model (str, optional): OpenAI model to use. Defaults to "gpt-4o".
            max_retries (int, optional): Maximum number of retries for API calls. Defaults to 5.
            retry_delay (float, optional): Delay between retries in seconds. Defaults to 1.0.
        """
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.logger = logging.getLogger(__name__)
    
    def extract_articles(self, text: str) -> Dict[str, Any]:
        """Extract articles from text using the OpenAI API.
        
        Args:
            text (str): Text to extract articles from.
            
        Returns:
            Dict[str, Any]: Extracted articles in JSON format.
            
        Raises:
            Exception: If there's an error extracting articles after max_retries attempts.
        """
        attempts = 0
        last_error = None
        backoff_time = self.retry_delay  # Start with the base delay
        
        while attempts < self.max_retries:
            attempts += 1
            try:
                self.logger.debug(f"Attempt {attempts}/{self.max_retries}: Sending request to OpenAI API using model {self.model}")
                
                # Use json_schema format with our updated schema
                try:
                    response = self.client.chat.completions.create(
                        model=self.model,
                        response_format={
                            "type": "json_schema",
                            "json_schema": {
                                "name": "article_extraction",
                                "schema": ARTICLE_EXTRACTION_SCHEMA,
                                "strict": True
                            }
                        },
                        messages=[
                            {"role": "system", "content": ARTICLE_EXTRACTION_PROMPT},
                            {"role": "user", "content": text}
                        ],
                        temperature=0.1,  # Lower temperature for more deterministic output
                    )
                except openai.RateLimitError as e:
                    # Handle rate limit errors with exponential backoff
                    last_error = f"Rate limit exceeded: {e}"
                    self.logger.warning(f"Rate limit error: {e}")
                    if attempts < self.max_retries:
                        self.logger.info(f"Rate limited. Backing off for {backoff_time} seconds... (Attempt {attempts}/{self.max_retries})")
                        time.sleep(backoff_time)
                        # Exponential backoff: double the wait time for the next attempt
                        backoff_time *= 2
                        continue
                    else:
                        raise Exception(last_error)
                except Exception as e:
                    # If json_schema format fails, fall back to basic json_object format
                    self.logger.warning(f"Failed to use json_schema format: {e}. Falling back to json_object format.")
                    try:
                        response = self.client.chat.completions.create(
                            model=self.model,
                            response_format={"type": "json_object"},
                            messages=[
                                {"role": "system", "content": ARTICLE_EXTRACTION_PROMPT},
                                {"role": "user", "content": text}
                            ],
                            temperature=0.1,  # Lower temperature for more deterministic output
                        )
                    except openai.RateLimitError as e:
                        # Handle rate limit errors with exponential backoff
                        last_error = f"Rate limit exceeded: {e}"
                        self.logger.warning(f"Rate limit error: {e}")
                        if attempts < self.max_retries:
                            self.logger.info(f"Rate limited. Backing off for {backoff_time} seconds... (Attempt {attempts}/{self.max_retries})")
                            time.sleep(backoff_time)
                            # Exponential backoff: double the wait time for the next attempt
                            backoff_time *= 2
                            continue
                        else:
                            raise Exception(last_error)
                
                # Extract and parse JSON response
                content = response.choices[0].message.content
                self.logger.debug("Received response from OpenAI API")
                
                try:
                    result = json.loads(content)
                    # An empty articles list is a valid result, not an error
                    if "articles" in result:
                        return result
                    else:
                        # If the response doesn't have an articles key, add an empty one
                        self.logger.info("Response doesn't contain 'articles' key, returning empty articles list")
                        return {"articles": []}
                except json.JSONDecodeError as e:
                    last_error = f"Failed to parse JSON response: {e}"
                    self.logger.error(f"Error parsing JSON response: {e}")
                    if attempts < self.max_retries:
                        self.logger.info(f"Retrying in {backoff_time} seconds... (Attempt {attempts}/{self.max_retries})")
                        time.sleep(backoff_time)
                        # Increase backoff time for next attempt
                        backoff_time *= 2
                        continue
                    else:
                        raise Exception(last_error)
                        
            except Exception as e:
                last_error = f"Failed to extract articles: {e}"
                self.logger.error(f"Error extracting articles: {e}")
                if attempts < self.max_retries:
                    self.logger.info(f"Retrying in {backoff_time} seconds... (Attempt {attempts}/{self.max_retries})")
                    time.sleep(backoff_time)
                    # Increase backoff time for next attempt
                    backoff_time *= 2
                    continue
                else:
                    raise Exception(last_error)
        
        # If we've exhausted all retries
        raise Exception(last_error or "Failed to extract articles after multiple attempts")
