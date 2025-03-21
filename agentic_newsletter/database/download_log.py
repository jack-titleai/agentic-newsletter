"""Download log model for Agentic Newsletter."""

from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, Text

from agentic_newsletter.database.base import Base


class DownloadLog(Base):
    """Download log model."""

    __tablename__ = "download_logs"

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    duration_seconds = Column(Float, nullable=False)
    emails_downloaded = Column(Integer, nullable=False)
    error_message = Column(Text, nullable=True)

    def __repr__(self) -> str:
        """Return a string representation of the download log.
        
        Returns:
            str: A string representation of the download log.
        """
        return f"<DownloadLog(timestamp='{self.timestamp}', emails_downloaded={self.emails_downloaded})>"
