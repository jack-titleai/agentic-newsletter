"""Article group model for Agentic Newsletter."""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from agentic_newsletter.database.base import Base


class ArticleGroup(Base):
    """Article group model."""

    __tablename__ = "article_groups"

    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    summary = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    added_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    
    # Relationships
    article_group_items = relationship("ArticleGroupItem", back_populates="article_group", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        """Return a string representation of the article group.
        
        Returns:
            str: A string representation of the article group.
        """
        return f"<ArticleGroup(title='{self.title}', created_at='{self.created_at}')>"


class ArticleGroupItem(Base):
    """Article group item model."""

    __tablename__ = "article_group_items"

    id = Column(Integer, primary_key=True)
    article_group_id = Column(Integer, ForeignKey("article_groups.id"), nullable=False)
    article_id = Column(Integer, ForeignKey("parsed_articles.id"), nullable=False)
    
    # Relationships
    article_group = relationship("ArticleGroup", back_populates="article_group_items")
    article = relationship("ParsedArticle")
    
    def __repr__(self) -> str:
        """Return a string representation of the article group item.
        
        Returns:
            str: A string representation of the article group item.
        """
        return f"<ArticleGroupItem(article_group_id={self.article_group_id}, article_id={self.article_id})>"
