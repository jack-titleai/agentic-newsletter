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


# JSON schema for article grouping
ARTICLE_GROUPING_SCHEMA = {
    "type": "object",
    "required": ["groups"],
    "additionalProperties": False,
    "properties": {
        "groups": {
            "type": "array",
            "description": "List of article groups. Each article must belong to exactly one group.",
            "items": {
                "type": "object",
                "required": ["title", "summary", "article_ids"],
                "additionalProperties": False,
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "A specific, descriptive title for the group."
                    },
                    "summary": {
                        "type": "string",
                        "description": "A summary of what unifies the articles in this group."
                    },
                    "article_ids": {
                        "type": "array",
                        "description": "List of article IDs that belong to this group. Each article must appear in exactly one group.",
                        "items": {
                            "type": "integer"
                        }
                    }
                }
            }
        }
    }
}

# JSON schema for group merging
GROUP_MERGING_SCHEMA = {
    "type": "object",
    "required": ["groups"],
    "additionalProperties": False,
    "properties": {
        "groups": {
            "type": "array",
            "description": "List of merged article groups. Each article must belong to exactly one group.",
            "items": {
                "type": "object",
                "required": ["title", "summary", "article_ids"],
                "additionalProperties": False,
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "A specific, descriptive title for the merged group."
                    },
                    "summary": {
                        "type": "string",
                        "description": "A summary of what unifies the articles in this merged group."
                    },
                    "article_ids": {
                        "type": "array",
                        "description": "List of article IDs that belong to this merged group. Each article must appear in exactly one group.",
                        "items": {
                            "type": "integer"
                        }
                    }
                }
            }
        }
    }
}
