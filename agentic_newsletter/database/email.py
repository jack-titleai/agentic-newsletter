"""Email model for Agentic Newsletter."""

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from agentic_newsletter.database.base import Base


class Email(Base):
    """Email model."""

    __tablename__ = "emails"

    id = Column(Integer, primary_key=True)
    source_id = Column(Integer, ForeignKey("email_sources.id"), nullable=False)
    sender_email = Column(String(255), nullable=False)
    subject = Column(String(255), nullable=True)
    body = Column(Text, nullable=True)
    received_date = Column(DateTime, nullable=False)
    added_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    message_id = Column(String(255), unique=True, nullable=False)

    source = relationship("EmailSource", back_populates="emails")

    def __repr__(self) -> str:
        """Return a string representation of the email.
        
        Returns:
            str: A string representation of the email.
        """
        return f"<Email(sender='{self.sender_email}', subject='{self.subject}')>"
