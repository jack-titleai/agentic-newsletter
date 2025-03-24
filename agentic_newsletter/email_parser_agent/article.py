"""Article data model for the email parser agent."""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Article:
    """Represents an article extracted from a newsletter email."""
    
    title: str
    body: str
    url: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    category: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Convert the article to a dictionary.
        
        Returns:
            dict: Dictionary representation of the article.
        """
        return {
            "title": self.title,
            "body": self.body,
            "url": self.url,
            "tags": self.tags,
            "category": self.category
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Article":
        """Create an Article from a dictionary.
        
        Args:
            data (dict): Dictionary containing article data.
            
        Returns:
            Article: New Article instance.
        """
        return cls(
            title=data.get("title", "Untitled"),
            body=data.get("body", ""),
            url=data.get("url"),
            tags=data.get("tags", []),
            category=data.get("category")
        )
