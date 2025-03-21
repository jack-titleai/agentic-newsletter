"""OpenAI client for the email parser agent."""

import json
import logging
from typing import Dict, Any, Optional

import openai
from openai import OpenAI

from agentic_newsletter.email_parser_agent.prompts import ARTICLE_EXTRACTION_PROMPT
from agentic_newsletter.email_parser_agent.schema import ARTICLE_EXTRACTION_SCHEMA


class OpenAIClient:
    """Client for interacting with OpenAI's API."""
    
    def __init__(self, api_key: str, model: str = "gpt-4o"):
        """Initialize the OpenAI client.
        
        Args:
            api_key (str): OpenAI API key.
            model (str, optional): OpenAI model to use. Defaults to "gpt-4o".
        """
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.logger = logging.getLogger(__name__)
    
    def extract_articles(self, text: str) -> Dict[str, Any]:
        """Extract articles from text using the OpenAI API.
        
        Args:
            text (str): Text to extract articles from.
            
        Returns:
            Dict[str, Any]: Extracted articles in JSON format.
            
        Raises:
            Exception: If there's an error extracting articles.
        """
        try:
            self.logger.debug(f"Sending request to OpenAI API using model {self.model}")
            
            # First try with json_schema format
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
            except Exception as e:
                # If json_schema format fails, fall back to basic json_object format
                self.logger.warning(f"Failed to use json_schema format: {e}. Falling back to json_object format.")
                response = self.client.chat.completions.create(
                    model=self.model,
                    response_format={"type": "json_object"},
                    messages=[
                        {"role": "system", "content": ARTICLE_EXTRACTION_PROMPT},
                        {"role": "user", "content": text}
                    ],
                    temperature=0.1,  # Lower temperature for more deterministic output
                )
            
            # Extract and parse JSON response
            content = response.choices[0].message.content
            self.logger.debug("Received response from OpenAI API")
            
            try:
                return json.loads(content)
            except json.JSONDecodeError as e:
                self.logger.error(f"Error parsing JSON response: {e}")
                self.logger.error(f"Response content: {content}")
                raise ValueError(f"Invalid JSON response from OpenAI API: {e}")
                
        except Exception as e:
            self.logger.error(f"Error extracting articles: {e}")
            raise
