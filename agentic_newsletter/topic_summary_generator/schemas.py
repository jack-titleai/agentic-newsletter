"""Schemas for the topic summary generator module."""

from dataclasses import dataclass
from typing import Dict, List, Optional

# JSON schema for topic summary generation
TOPIC_SUMMARY_SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {
            "type": "string",
            "description": "A concise summary of the key developments from the bullet points"
        }
    },
    "required": ["summary"],
    "additionalProperties": False
}


@dataclass
class TopicSummaryData:
    """Data class for a topic summary."""
    
    summary: str


@dataclass
class TopicSummaryResult:
    """Result of a topic summary generation."""
    
    summary: str
    topic: str
