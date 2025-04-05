"""Topic summary log model for Agentic Newsletter."""

from datetime import datetime
import json
from typing import Dict, Optional

from sqlalchemy import Column, DateTime, Float, Integer, Text

from agentic_newsletter.database.base import Base


class TopicSummaryLog(Base):
    """Topic summary log model for tracking API calls to the topic summary generator."""

    __tablename__ = "topic_summary_logs"

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    duration_seconds = Column(Float, nullable=False)
    topics_processed = Column(Integer, nullable=False)
    summaries_generated = Column(Integer, nullable=False)
    bullet_points_processed = Column(Integer, nullable=False)
    
    # Store detailed metrics per topic as JSON
    topic_metrics = Column(Text, nullable=True)
    
    error_message = Column(Text, nullable=True)

    def __repr__(self) -> str:
        """Return a string representation of the topic summary log.
        
        Returns:
            str: A string representation of the topic summary log.
        """
        return (
            f"<TopicSummaryLog(timestamp='{self.timestamp}', "
            f"topics_processed={self.topics_processed}, "
            f"summaries_generated={self.summaries_generated})>"
        )
    
    def set_topic_metrics(self, metrics: Dict[str, Dict]) -> None:
        """Set the topic metrics as a JSON string.
        
        Args:
            metrics: Dictionary of topic metrics.
        """
        self.topic_metrics = json.dumps(metrics)
    
    def get_topic_metrics(self) -> Optional[Dict[str, Dict]]:
        """Get the topic metrics as a dictionary.
        
        Returns:
            Dictionary of topic metrics or None if not set.
        """
        if not self.topic_metrics:
            return None
        return json.loads(self.topic_metrics)
