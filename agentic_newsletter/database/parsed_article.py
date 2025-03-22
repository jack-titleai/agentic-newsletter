"""Parsed article model for Agentic Newsletter."""

from datetime import datetime
from typing import List

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.orm import relationship

from agentic_newsletter.database.base import Base


class ParsedArticle(Base):
    """Parsed article model."""

    __tablename__ = "parsed_articles"

    id = Column(Integer, primary_key=True)
    email_id = Column(Integer, ForeignKey("emails.id"), nullable=False)
    sender = Column(String(255), nullable=False)
    title = Column(String(255), nullable=False)
    summary = Column(Text, nullable=False)
    body = Column(Text, nullable=False)
    url = Column(String(512), nullable=True)
    tags = Column(JSON, nullable=True)  # Store tags as JSON array
    assigned_category = Column(String(255), nullable=True)  # Category assigned by the grouper agent
    grouping_datetime = Column(DateTime, nullable=True)  # When the article was assigned to a category
    parsed_at = Column(DateTime, nullable=False)
    added_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationship with Email
    email = relationship("Email", back_populates="parsed_articles")

    def __repr__(self) -> str:
        """Return a string representation of the parsed article.
        
        Returns:
            str: A string representation of the parsed article.
        """
        return f"<ParsedArticle(title='{self.title}', email_id={self.email_id})>"
    
    def to_article(self) -> 'Article':
        """Convert to an Article object.
        
        Returns:
            Article: The Article object.
        """
        from agentic_newsletter.email_parser_agent.article import Article
        
        return Article(
            title=self.title,
            summary=self.summary,
            body=self.body,
            url=self.url,
            tags=self.tags if self.tags else []
        )
    
    @classmethod
    def from_article(cls, article: 'Article', email_id: int, sender: str) -> 'ParsedArticle':
        """Create a ParsedArticle from an Article.
        
        Args:
            article (Article): The Article object.
            email_id (int): The ID of the email.
            sender (str): The sender of the email.
            
        Returns:
            ParsedArticle: The ParsedArticle object.
        """
        return cls(
            email_id=email_id,
            sender=sender,
            title=article.title,
            summary=article.summary,
            body=article.body,
            url=article.url,
            tags=article.tags,
            assigned_category=None,  # Explicitly set to None for new articles
            grouping_datetime=None,  # Explicitly set to None for new articles
            parsed_at=datetime.utcnow()
        )
