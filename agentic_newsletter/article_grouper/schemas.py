"""Schemas for the article grouper module."""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class ArticleData:
    """Data for an article to be grouped."""
    
    id: int
    title: str
    summary: str
    source: str
    parsed_at: datetime


@dataclass
class ArticleGroupData:
    """Data for a group of articles."""
    
    title: str
    summary: str
    article_ids: List[int]


@dataclass
class ArticleGroupResult:
    """Result of the article grouping process."""
    
    groups: List[ArticleGroupData]
    start_date: datetime
    end_date: datetime


# JSON Schema for the OpenAI API
ARTICLE_GROUPING_SCHEMA = {
    "type": "object",
    "required": ["groups"],
    "properties": {
        "groups": {
            "type": "array",
            "description": "List of article groups",
            "items": {
                "type": "object",
                "required": ["title", "summary", "article_ids"],
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "A specific, descriptive title for the group that captures the specific topic shared by these articles"
                    },
                    "summary": {
                        "type": "string",
                        "description": "A 1-3 sentence summary of the specific topic shared by these articles"
                    },
                    "article_ids": {
                        "type": "array",
                        "description": "List of article IDs in this group",
                        "items": {
                            "type": "integer"
                        }
                    }
                }
            }
        }
    }
}
