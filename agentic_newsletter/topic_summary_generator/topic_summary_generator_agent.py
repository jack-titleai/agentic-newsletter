"""Topic summary generator agent for Agentic Newsletter."""

import logging
import os
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from agentic_newsletter.database.database_manager import DatabaseManager
from agentic_newsletter.database.bullet_point import BulletPoint
from agentic_newsletter.database.topic_summary import TopicSummary
from agentic_newsletter.database.topic_summary_log import TopicSummaryLog
from agentic_newsletter.topic_summary_generator.openai_client import OpenAIClient
from agentic_newsletter.topic_summary_generator.schemas import TopicSummaryResult
from agentic_newsletter.config.config_loader import ConfigLoader

logger = logging.getLogger(__name__)


class TopicSummaryGeneratorAgent:
    """Agent for generating topic summaries from bullet points."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o") -> None:
        """Initialize the topic summary generator agent.
        
        Args:
            api_key (Optional[str], optional): OpenAI API key. Defaults to None.
            model (str, optional): OpenAI model to use. Defaults to "gpt-4o".
        """
        # Initialize the OpenAI client
        self.openai_client = OpenAIClient(api_key=api_key, model=model)
        
        # Initialize the database manager
        self.db_manager = DatabaseManager()
        
        # Initialize the config loader
        self.config_loader = ConfigLoader()
    
    def generate_summaries(
        self, 
        bullet_points_by_category: Dict[str, List[BulletPoint]],
        max_bullet_points: int = 5
    ) -> Tuple[Dict[str, str], TopicSummaryLog]:
        """Generate summaries for each topic based on bullet points.
        
        Args:
            bullet_points_by_category (Dict[str, List[BulletPoint]]): Dictionary mapping categories to lists of bullet points.
            max_bullet_points (int, optional): Maximum number of bullet points to use per category. Defaults to 5.
            
        Returns:
            Tuple[Dict[str, str], TopicSummaryLog]: Dictionary mapping categories to summaries and the log of the operation.
        """
        start_time = time.time()
        
        # Track metrics
        topics_processed = 0
        summaries_generated = 0
        bullet_points_processed = 0
        topic_metrics: Dict[str, Dict] = {}
        error_message = None
        
        # Dictionary to store the generated summaries
        summaries: Dict[str, str] = {}
        
        try:
            # Define category mapping for renaming
            category_mapping = {
                "computer vision": "Computer Vision",
                "large language models and/or natural language processing": "LLMs",
                "healthcare AI / healthcare analytics / healthcare technology": "Healthcare AI",
                "hardware for AI and GPUs": "Hardware",
                "AI policy": "AI Policy",
                "other topics": "Miscellaneous"
            }
            
            # Process each category
            for category, bullet_points in bullet_points_by_category.items():
                # Skip empty categories
                if not bullet_points:
                    continue
                
                topics_processed += 1
                
                # Get the display name for the category
                display_category = category_mapping.get(category, category)
                
                # Sort bullet points by combined score (average of impact and frequency)
                bullet_points.sort(
                    key=lambda bp: (bp.impact_score + bp.frequency_score) / 2,
                    reverse=True  # Highest score first
                )
                
                # Limit to the top bullet points
                top_bullet_points = bullet_points[:max_bullet_points]
                bullet_points_processed += len(top_bullet_points)
                
                # Format bullet points for the prompt
                bullet_points_text = "\n\n".join([
                    f"- {bp.bullet_point}" for bp in top_bullet_points
                ])
                
                # Generate the summary
                category_start_time = time.time()
                summary_result = self.openai_client.generate_topic_summary(
                    topic=display_category,
                    bullet_points_text=bullet_points_text
                )
                category_duration = time.time() - category_start_time
                
                # Track metrics for this category
                topic_metrics[display_category] = {
                    "bullet_points_used": len(top_bullet_points),
                    "duration_seconds": category_duration
                }
                
                # Store the summary if it was generated successfully
                if summary_result.summary:
                    summaries[display_category] = summary_result.summary
                    summaries_generated += 1
                    
                    # Save the summary to the database
                    self._save_summary_to_db(display_category, summary_result.summary)
            
        except Exception as e:
            error_message = str(e)
            logger.error(f"Error generating topic summaries: {error_message}")
        
        # Calculate duration
        duration_seconds = time.time() - start_time
        
        # Log the operation
        log = self._log_summary_generation(
            duration_seconds=duration_seconds,
            topics_processed=topics_processed,
            summaries_generated=summaries_generated,
            bullet_points_processed=bullet_points_processed,
            topic_metrics=topic_metrics,
            error_message=error_message
        )
        
        return summaries, log
    
    def _save_summary_to_db(self, topic: str, summary: str) -> TopicSummary:
        """Save a topic summary to the database.
        
        Args:
            topic (str): The topic of the summary.
            summary (str): The summary text.
            
        Returns:
            TopicSummary: The saved topic summary.
        """
        with self.db_manager.get_session() as session:
            topic_summary = TopicSummary(
                topic=topic,
                summary=summary,
                created_at=datetime.utcnow()
            )
            session.add(topic_summary)
            session.commit()
            session.refresh(topic_summary)
            
            logger.info(f"Saved summary for topic '{topic}'")
            return topic_summary
    
    def _log_summary_generation(
        self,
        duration_seconds: float,
        topics_processed: int,
        summaries_generated: int,
        bullet_points_processed: int,
        topic_metrics: Optional[Dict[str, Dict]] = None,
        error_message: Optional[str] = None
    ) -> TopicSummaryLog:
        """Log a summary generation operation.
        
        Args:
            duration_seconds (float): Duration of the operation in seconds.
            topics_processed (int): Number of topics processed.
            summaries_generated (int): Number of summaries generated.
            bullet_points_processed (int): Number of bullet points processed.
            topic_metrics (Optional[Dict[str, Dict]], optional): Metrics per topic. Defaults to None.
            error_message (Optional[str], optional): Error message if an error occurred. Defaults to None.
            
        Returns:
            TopicSummaryLog: The created log.
        """
        with self.db_manager.get_session() as session:
            log = TopicSummaryLog(
                duration_seconds=duration_seconds,
                topics_processed=topics_processed,
                summaries_generated=summaries_generated,
                bullet_points_processed=bullet_points_processed,
                error_message=error_message
            )
            
            if topic_metrics:
                log.set_topic_metrics(topic_metrics)
            
            session.add(log)
            session.commit()
            session.refresh(log)
            
            logger.info(f"Logged topic summary generation: {summaries_generated} summaries for {topics_processed} topics in {duration_seconds:.2f}s")
            return log
