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
            "description": "List of article groups. Each article must be assigned to exactly one group.",
            "items": {
                "type": "object",
                "required": ["title", "summary", "article_ids"],
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "A highly specific, descriptive title for the group that includes company names, product names, or event details. Avoid general categories like 'AI in Healthcare' - instead use specific titles like 'Google's Gemini AI Model for Japanese Hospitals'."
                    },
                    "summary": {
                        "type": "string",
                        "description": "A 1-3 sentence summary that explains the specific topic, event, or announcement shared by these articles. Include specific details when available."
                    },
                    "article_ids": {
                        "type": "array",
                        "description": "List of article IDs in this group. Each article ID should appear in exactly one group.",
                        "items": {
                            "type": "integer"
                        }
                    }
                },
                "additionalProperties": False
            }
        }
    },
    "additionalProperties": False
}

# JSON Schema for the group merging process
GROUP_MERGING_SCHEMA = {
    "type": "object",
    "required": ["groups"],
    "properties": {
        "groups": {
            "type": "array",
            "description": "List of merged article groups. Each article must be assigned to exactly one group.",
            "items": {
                "type": "object",
                "required": ["title", "summary", "article_ids"],
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "A specific but comprehensive title for the merged group that captures the broader topic while still being descriptive. Include company names and key details."
                    },
                    "summary": {
                        "type": "string",
                        "description": "A comprehensive summary that incorporates the key points from all merged groups. Should explain the broader topic while maintaining specific details."
                    },
                    "article_ids": {
                        "type": "array",
                        "description": "List of all article IDs from the merged groups. Each article ID should appear in exactly one group after merging.",
                        "items": {
                            "type": "integer"
                        }
                    }
                },
                "additionalProperties": False
            }
        }
    },
    "additionalProperties": False
}
