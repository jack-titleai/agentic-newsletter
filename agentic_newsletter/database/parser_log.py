"""Parser log model for Agentic Newsletter."""

from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, Text

from agentic_newsletter.database.base import Base


class ParserLog(Base):
    """Parser log model."""

    __tablename__ = "parser_logs"

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    duration_seconds = Column(Float, nullable=False)
    articles_found = Column(Integer, nullable=False)
    average_articles_per_email = Column(Float, nullable=False)
    median_articles_per_email = Column(Float, nullable=False)
    error_message = Column(Text, nullable=True)

    def __repr__(self) -> str:
        """Return a string representation of the parser log.
        
        Returns:
            str: A string representation of the parser log.
        """
        return f"<ParserLog(timestamp='{self.timestamp}', articles_found={self.articles_found})>"
