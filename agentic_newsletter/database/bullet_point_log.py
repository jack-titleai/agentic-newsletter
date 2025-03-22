"""Bullet point log model for Agentic Newsletter."""

from datetime import datetime
import json
from typing import Dict, Optional

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
    
    # New metrics fields
    avg_frequency_score = Column(Float, nullable=True)
    std_frequency_score = Column(Float, nullable=True)
    avg_impact_score = Column(Float, nullable=True)
    std_impact_score = Column(Float, nullable=True)
    avg_specificity_score = Column(Float, nullable=True)
    std_specificity_score = Column(Float, nullable=True)
    urls_found = Column(Integer, nullable=True)
    
    # Store detailed metrics per category as JSON
    category_metrics = Column(Text, nullable=True)
    
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
    
    def set_category_metrics(self, metrics: Dict[str, Dict]) -> None:
        """Set the category metrics as a JSON string.
        
        Args:
            metrics: Dictionary of category metrics.
        """
        self.category_metrics = json.dumps(metrics)
    
    def get_category_metrics(self) -> Optional[Dict[str, Dict]]:
        """Get the category metrics as a dictionary.
        
        Returns:
            Dictionary of category metrics or None if not set.
        """
        if not self.category_metrics:
            return None
        return json.loads(self.category_metrics)
