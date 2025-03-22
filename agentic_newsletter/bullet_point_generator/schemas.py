"""Schemas for the bullet point generator module."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, validator

# JSON Schema for bullet point generation
BULLET_POINT_SCHEMA = {
    "type": "object",
    "required": ["bullet_points"],
    "additionalProperties": False,
    "properties": {
        "bullet_points": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["bullet_point", "frequency_score", "impact_score", "specificity_score"],
                "additionalProperties": False,
                "properties": {
                    "bullet_point": {
                        "type": "string",
                        "description": "A 1-2 sentence bullet point about a specific topic or event"
                    },
                    "frequency_score": {
                        "type": "number",
                        "description": "Score from 1-10 indicating how frequently this topic appears in the articles"
                    },
                    "impact_score": {
                        "type": "number",
                        "description": "Score from 1-10 indicating how impactful this topic is to the AI community"
                    },
                    "specificity_score": {
                        "type": "number",
                        "description": "Score from 1-10 indicating how specific and detailed the bullet point is"
                    }
                }
            }
        }
    }
}


class BulletPointData(BaseModel):
    """Data model for a bullet point."""
    
    bullet_point: str = Field(
        ..., 
        description="A 1-2 sentence bullet point about a specific topic or event"
    )
    frequency_score: float = Field(
        ..., 
        description="Score from 1-10 indicating how frequently this topic appears in the articles",
        ge=1.0,
        le=10.0
    )
    impact_score: float = Field(
        ..., 
        description="Score from 1-10 indicating how impactful this topic is to the AI community",
        ge=1.0,
        le=10.0
    )
    specificity_score: float = Field(
        ..., 
        description="Score from 1-10 indicating how specific and detailed the bullet point is",
        ge=1.0,
        le=10.0
    )
    
    @validator('frequency_score', 'impact_score', 'specificity_score')
    def validate_score(cls, v):
        """Validate that scores are between 1 and 10."""
        if v < 1 or v > 10:
            raise ValueError(f"Score must be between 1 and 10, got {v}")
        return v


class BulletPointResult(BaseModel):
    """Result of bullet point generation for a category."""
    
    bullet_points: List[BulletPointData]
    category: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
