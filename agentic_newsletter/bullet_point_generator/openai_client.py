"""OpenAI client for the bullet point generator module."""

import json
import logging
import time
from typing import Dict, List, Any

from openai import OpenAI
import openai

from agentic_newsletter.bullet_point_generator.prompts import (
    BULLET_POINT_GENERATION_PROMPT,
    BULLET_POINT_RETRY_PROMPT
)
from agentic_newsletter.bullet_point_generator.schemas import (
    BulletPointData,
    BulletPointResult,
    BULLET_POINT_SCHEMA
)
from agentic_newsletter.config.config_loader import ConfigLoader

logger = logging.getLogger(__name__)


class OpenAIClient:
    """Client for interacting with OpenAI's API for bullet point generation."""
    
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
        self.config_loader = ConfigLoader()
    
    def generate_bullet_points(self, category: str, articles_text: str) -> BulletPointResult:
        """Generate bullet points for a category based on article content.
        
        Args:
            category (str): The category to generate bullet points for.
            articles_text (str): Concatenated text of all articles in this category.
            
        Returns:
            BulletPointResult: The generated bullet points.
        """
        if not articles_text.strip():
            logger.warning(f"No article content provided for category '{category}'")
            return BulletPointResult(bullet_points=[], category=category)
        
        # Create the prompt
        prompt = BULLET_POINT_GENERATION_PROMPT.format(
            category=category,
            articles=articles_text
        )
        
        # Create the messages for the API call
        messages = [
            {"role": "system", "content": prompt}
        ]
        
        # Track errors for retry prompts
        previous_errors = []
        
        # Use the schema format if possible, otherwise fall back to json_object
        use_schema_format = True
        
        # Try to get a response with the JSON schema format
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"Generating bullet points for category '{category}' (attempt {attempt})")
                
                # If this is a retry, add the retry prompt with error information
                if attempt > 1 and previous_errors:
                    error_feedback = "\n\n".join(previous_errors)
                    retry_message = BULLET_POINT_RETRY_PROMPT.format(
                        error_message=error_feedback
                    )
                    messages.append({"role": "user", "content": retry_message})
                
                # Make the API call with the appropriate format
                if use_schema_format:
                    try:
                        # Make the API call with JSON schema validation
                        response = self.client.chat.completions.create(
                            model=self.model,
                            messages=messages,
                            response_format={
                                "type": "json_schema",
                                "json_schema": {
                                    "name": "bullet_point_generation",
                                    "schema": BULLET_POINT_SCHEMA,
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
                    # Fall back to simple JSON object format
                    response = self.client.chat.completions.create(
                        model=self.model,
                        messages=messages,
                        response_format={"type": "json_object"},
                        temperature=0.1,
                    )
                
                # Parse the response
                response_content = response.choices[0].message.content
                try:
                    result = json.loads(response_content)
                    
                    # Validate that the result has the expected structure
                    if "bullet_points" not in result:
                        error_msg = "Response does not contain 'bullet_points' field"
                        logger.error(error_msg)
                        previous_errors.append(f"ERROR: {error_msg}")
                        if attempt < self.max_retries:
                            logger.info(f"Retrying ({attempt}/{self.max_retries})...")
                            time.sleep(self.retry_delay * (2 ** (attempt - 1)))  # Exponential backoff
                            continue
                        else:
                            logger.error("Maximum retries reached. Returning empty result.")
                            return BulletPointResult(bullet_points=[], category=category)
                    
                    # Create the bullet points
                    bullet_points = []
                    for item in result["bullet_points"]:
                        try:
                            bullet_points.append(
                                BulletPointData(
                                    bullet_point=item["bullet_point"],
                                    frequency_score=float(item["frequency_score"]),
                                    impact_score=float(item["impact_score"]),
                                    specificity_score=float(item["specificity_score"]),
                                    source_url=item.get("source_url")
                                )
                            )
                        except (KeyError, ValueError, TypeError) as e:
                            error_msg = f"Invalid bullet point data: {str(e)}"
                            logger.warning(error_msg)
                            previous_errors.append(f"ERROR: {error_msg}")
                            if attempt < self.max_retries:
                                continue
                    
                    if not bullet_points and attempt < self.max_retries:
                        logger.warning("No valid bullet points found. Retrying...")
                        time.sleep(self.retry_delay * (2 ** (attempt - 1)))
                        continue
                    
                    logger.info(f"Generated {len(bullet_points)} bullet points for category '{category}'")
                    
                    return BulletPointResult(
                        bullet_points=bullet_points,
                        category=category
                    )
                except json.JSONDecodeError as e:
                    error_msg = f"Failed to parse JSON response: {str(e)}"
                    logger.warning(error_msg)
                    previous_errors.append(f"ERROR: {error_msg}")
                    if attempt < self.max_retries:
                        logger.info(f"Retrying ({attempt}/{self.max_retries})...")
                        time.sleep(self.retry_delay * (2 ** (attempt - 1)))
                        continue
                    
            except openai.OpenAIError as e:
                error_msg = f"OpenAI API error: {str(e)}"
                logger.warning(f"Error generating bullet points (attempt {attempt}): {error_msg}")
                previous_errors.append(f"ERROR: {error_msg}")
                
                if attempt < self.max_retries:
                    logger.info(f"Retrying ({attempt}/{self.max_retries})...")
                    time.sleep(self.retry_delay * (2 ** (attempt - 1)))
                    continue
        
        # If we get here, all attempts failed
        logger.error(f"Failed to generate bullet points for category '{category}' after {self.max_retries} attempts")
        return BulletPointResult(bullet_points=[], category=category)
