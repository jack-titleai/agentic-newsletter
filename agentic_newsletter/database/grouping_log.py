"""Grouping log model for Agentic Newsletter."""

from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, Text

from agentic_newsletter.database.base import Base


class GroupingLog(Base):
    """Grouping log model."""

    __tablename__ = "grouping_logs"

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    duration_seconds = Column(Float, nullable=False)
    articles_processed = Column(Integer, nullable=False)
    sources_processed = Column(Integer, nullable=False)
    groups_created = Column(Integer, nullable=False)
    average_articles_per_group = Column(Float, nullable=True)
    median_articles_per_group = Column(Float, nullable=True)
    max_articles_per_group = Column(Integer, nullable=True)
    min_articles_per_group = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)

    def __repr__(self) -> str:
        """Return a string representation of the grouping log.
        
        Returns:
            str: A string representation of the grouping log.
        """
        return f"<GroupingLog(timestamp='{self.timestamp}', groups_created={self.groups_created})>"
