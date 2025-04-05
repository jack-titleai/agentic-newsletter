"""Topic summary model for Agentic Newsletter."""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime, Float, Integer, String, Text

from agentic_newsletter.database.base import Base


class TopicSummary(Base):
    """Topic summary model."""

    __tablename__ = "topic_summaries"

    id = Column(Integer, primary_key=True)
    topic = Column(String(255), nullable=False)
    summary = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    added_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        """Return a string representation of the topic summary.
        
        Returns:
            str: A string representation of the topic summary.
        """
        return f"<TopicSummary(id={self.id}, topic='{self.topic}')>"
