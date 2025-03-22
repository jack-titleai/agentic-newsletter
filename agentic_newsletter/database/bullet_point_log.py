"""Bullet point log model for Agentic Newsletter."""

from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, Text

from agentic_newsletter.database.base import Base


class BulletPointLog(Base):
    """Bullet point log model for tracking API calls to the bullet point generator."""

    __tablename__ = "bullet_point_logs"

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    duration_seconds = Column(Float, nullable=False)
    categories_processed = Column(Integer, nullable=False)
    bullet_points_generated = Column(Integer, nullable=False)
    articles_processed = Column(Integer, nullable=False)
    error_message = Column(Text, nullable=True)

    def __repr__(self) -> str:
        """Return a string representation of the bullet point log.
        
        Returns:
            str: A string representation of the bullet point log.
        """
        return (
            f"<BulletPointLog(timestamp='{self.timestamp}', "
            f"categories_processed={self.categories_processed}, "
            f"bullet_points_generated={self.bullet_points_generated})>"
        )
