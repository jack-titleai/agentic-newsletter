"""OpenAI client for the topic summary generator module."""

import json
import logging
import time
from typing import Dict, List, Any

from openai import OpenAI
import openai

from agentic_newsletter.topic_summary_generator.prompts import (
    TOPIC_SUMMARY_GENERATION_PROMPT,
    TOPIC_SUMMARY_RETRY_PROMPT
)
from agentic_newsletter.topic_summary_generator.schemas import (
    TopicSummaryData,
    TopicSummaryResult,
    TOPIC_SUMMARY_SCHEMA
)
from agentic_newsletter.config.config_loader import ConfigLoader

logger = logging.getLogger(__name__)


class OpenAIClient:
    """Client for interacting with OpenAI's API for topic summary generation."""
    
    def __init__(self, api_key: str = None, model: str = None, max_retries: int = 5, retry_delay: float = 1.0) -> None:
        """Initialize the OpenAI client.
        
        Args:
            api_key (str, optional): OpenAI API key. Defaults to None.
            model (str, optional): OpenAI model to use. If None, uses the model from config.
            max_retries (int, optional): Maximum number of retries for API calls. Defaults to 5.
            retry_delay (float, optional): Initial delay between retries in seconds. Defaults to 1.0.
        """
        self.client = OpenAI(api_key=api_key)
        self.config_loader = ConfigLoader()
        self.model = model if model is not None else self.config_loader.get_openai_model()
        self.max_retries = max_retries
        self.retry_delay = retry_delay
    
    def generate_topic_summary(self, topic: str, bullet_points_text: str) -> TopicSummaryResult:
        """Generate a summary for a topic based on bullet point content.
        
        Args:
            topic (str): The topic to generate a summary for.
            bullet_points_text (str): Concatenated text of bullet points for this topic.
            
        Returns:
            TopicSummaryResult: The generated topic summary.
        """
        if not bullet_points_text.strip():
            logger.warning(f"No bullet point content provided for topic '{topic}'")
            return TopicSummaryResult(summary="", topic=topic)
        
        # Create the prompt
        prompt = TOPIC_SUMMARY_GENERATION_PROMPT.format(
            topic=topic,
            bullet_points=bullet_points_text
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
                logger.info(f"Generating summary for topic '{topic}' (attempt {attempt})")
                
                # If this is a retry, add the retry prompt with error information
                if attempt > 1 and previous_errors:
                    error_feedback = "\n\n".join(previous_errors)
                    retry_message = TOPIC_SUMMARY_RETRY_PROMPT.format(
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
                                    "name": "topic_summary_generation",
                                    "schema": TOPIC_SUMMARY_SCHEMA,
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
                    if "summary" not in result:
                        error_msg = "Response does not contain 'summary' field"
                        logger.error(error_msg)
                        previous_errors.append(f"ERROR: {error_msg}")
                        if attempt < self.max_retries:
                            logger.info(f"Retrying ({attempt}/{self.max_retries})...")
                            time.sleep(self.retry_delay * (2 ** (attempt - 1)))  # Exponential backoff
                            continue
                        else:
                            logger.error("Maximum retries reached. Returning empty result.")
                            return TopicSummaryResult(summary="", topic=topic)
                    
                    summary = result["summary"]
                    
                    if not summary and attempt < self.max_retries:
                        logger.warning("Empty summary found. Retrying...")
                        time.sleep(self.retry_delay * (2 ** (attempt - 1)))
                        continue
                    
                    logger.info(f"Generated summary for topic '{topic}'")
                    
                    return TopicSummaryResult(
                        summary=summary,
                        topic=topic
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
                logger.warning(f"Error generating topic summary (attempt {attempt}): {error_msg}")
                previous_errors.append(f"ERROR: {error_msg}")
                
                if attempt < self.max_retries:
                    logger.info(f"Retrying ({attempt}/{self.max_retries})...")
                    time.sleep(self.retry_delay * (2 ** (attempt - 1)))
                    continue
        
        # If we get here, all attempts failed
        logger.error(f"Failed to generate summary for topic '{topic}' after {self.max_retries} attempts")
        return TopicSummaryResult(summary="", topic=topic)
