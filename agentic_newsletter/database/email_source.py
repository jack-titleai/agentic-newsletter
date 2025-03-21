"""Email source model for Agentic Newsletter."""

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.orm import relationship

from agentic_newsletter.database.base import Base


class EmailSource(Base):
    """Email source model."""

    __tablename__ = "email_sources"

    id = Column(Integer, primary_key=True)
    email_address = Column(String(255), unique=True, nullable=False)
    date_added = Column(DateTime, default=datetime.utcnow, nullable=False)
    active = Column(Boolean, default=True, nullable=False)

    emails = relationship("Email", back_populates="source")

    def __repr__(self) -> str:
        """Return a string representation of the email source.
        
        Returns:
            str: A string representation of the email source.
        """
        return f"<EmailSource(email_address='{self.email_address}', active={self.active})>"
