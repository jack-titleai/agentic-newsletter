"""Bullet point model for Agentic Newsletter."""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from agentic_newsletter.database.base import Base


class BulletPoint(Base):
    """Bullet point model."""

    __tablename__ = "bullet_points"

    id = Column(Integer, primary_key=True)
    bullet_point = Column(String, nullable=False)
    frequency_score = Column(Float, nullable=False)
    impact_score = Column(Float, nullable=False)
    assigned_category = Column(String(255), nullable=False)
    specificity_score = Column(Float, nullable=False)
    source_url = Column(String(512), nullable=True)
    created_at = Column(DateTime, nullable=False)  # When the bullet point was generated
    added_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        """Return a string representation of the bullet point.
        
        Returns:
            str: A string representation of the bullet point.
        """
        return f"<BulletPoint(id={self.id}, category='{self.assigned_category}')>"
