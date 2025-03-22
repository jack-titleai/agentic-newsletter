"""Gmail client for Agentic Newsletter."""

import base64
import json
import logging
import os.path
import time
from datetime import datetime
from email.utils import parsedate_to_datetime
from typing import Any, Dict, List, Optional, Tuple

import google.auth.exceptions
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from agentic_newsletter.config.config_loader import ConfigLoader

logger = logging.getLogger(__name__)


class GmailClient:
    """Gmail client for Agentic Newsletter."""

    def __init__(self) -> None:
        """Initialize the Gmail client."""
        self.config_loader = ConfigLoader()
        self.scopes = self.config_loader.get_gmail_scopes()
        self.credentials_file = self.config_loader.get_gmail_credentials_file()
        self.token_file = self.config_loader.get_gmail_token_file()
        self.max_results = self.config_loader.get_gmail_max_results()
        self.service = self._get_gmail_service()

    def _get_gmail_service(self) -> Any:
        """Get the Gmail service.
        
        Returns:
            Any: The Gmail service.
            
        Raises:
            FileNotFoundError: If the credentials file is not found.
            Exception: If authentication fails.
        """
        creds = None
        
        # Check if token file exists
        if os.path.exists(self.token_file):
            try:
                creds = Credentials.from_authorized_user_info(
                    json.loads(open(self.token_file).read()), self.scopes
                )
            except Exception as e:
                logger.warning(f"Error loading token file: {e}")
        
        # If there are no valid credentials, let the user log in
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except google.auth.exceptions.RefreshError:
                    logger.warning("Token refresh failed, need to re-authenticate")
                    creds = None
            
            if not creds:
                if not os.path.exists(self.credentials_file):
                    raise FileNotFoundError(
                        f"Credentials file not found: {self.credentials_file}. "
                        "Please download it from the Google Cloud Console."
                    )
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, self.scopes
                )
                creds = flow.run_local_server(port=0)
            
            # Save the credentials for the next run
            with open(self.token_file, "w") as token:
                token.write(creds.to_json())
        
        return build("gmail", "v1", credentials=creds)

    def get_emails_from_sender(
        self, sender_email: str, max_results: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get emails from a specific sender.
        
        Args:
            sender_email (str): The sender's email address.
            max_results (Optional[int], optional): The maximum number of results to return.
                If None, all available emails will be retrieved using pagination.
                
        Returns:
            List[Dict[str, Any]]: A list of email messages.
        """
        query = f"from:{sender_email}"
        
        try:
            detailed_messages = []
            page_token = None
            
            # If max_results is None, we'll retrieve all emails using pagination
            # If max_results is specified, we'll limit to that number
            remaining = max_results if max_results is not None else float('inf')
            
            while remaining > 0:
                # Determine how many results to request in this page
                page_size = min(self.max_results, remaining) if max_results is not None else self.max_results
                
                # Request messages
                results = self.service.users().messages().list(
                    userId="me", 
                    q=query, 
                    maxResults=page_size,
                    pageToken=page_token
                ).execute()
                
                # Get messages from this page
                messages = results.get("messages", [])
                if not messages:
                    break
                
                # Get full message details for each message
                for message in messages:
                    if len(detailed_messages) >= max_results if max_results is not None else False:
                        break
                    
                    msg = self.service.users().messages().get(
                        userId="me", id=message["id"], format="full"
                    ).execute()
                    detailed_messages.append(msg)
                
                # Update remaining count
                if max_results is not None:
                    remaining -= len(messages)
                
                # Get next page token
                page_token = results.get("nextPageToken")
                if not page_token:
                    break
            
            return detailed_messages
        except Exception as e:
            logger.error(f"Error getting emails from {sender_email}: {e}")
            return []

    def parse_email_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Parse an email message from the Gmail API.
        
        Args:
            message (Dict[str, Any]): The email message from the Gmail API.
            
        Returns:
            Dict[str, Any]: The parsed email message.
        """
        headers = {header["name"]: header["value"] for header in message["payload"]["headers"]}
        
        # Get sender email
        sender = headers.get("From", "")
        sender_email = sender.split("<")[-1].split(">")[0] if "<" in sender else sender
        
        # Get subject
        subject = headers.get("Subject", "")
        
        # Get received date
        date_str = headers.get("Date", "")
        try:
            received_date = parsedate_to_datetime(date_str)
        except Exception:
            received_date = datetime.utcnow()
        
        # Get message ID
        message_id = message["id"]
        
        # Get body
        body = self._get_email_body(message["payload"])
        
        return {
            "sender_email": sender_email,
            "subject": subject,
            "body": body,
            "received_date": received_date,
            "message_id": message_id,
        }

    def _get_email_body(self, payload: Dict[str, Any]) -> str:
        """Get the email body from the payload.
        
        Args:
            payload (Dict[str, Any]): The email payload.
            
        Returns:
            str: The email body.
        """
        if "parts" in payload:
            # Multipart message
            for part in payload["parts"]:
                if part["mimeType"] == "text/plain":
                    if "data" in part["body"]:
                        return base64.urlsafe_b64decode(
                            part["body"]["data"].encode("ASCII")
                        ).decode("utf-8")
                elif "parts" in part:
                    # Recursive call for nested parts
                    body = self._get_email_body(part)
                    if body:
                        return body
        elif payload["mimeType"] == "text/plain":
            # Plain text message
            if "data" in payload["body"]:
                return base64.urlsafe_b64decode(
                    payload["body"]["data"].encode("ASCII")
                ).decode("utf-8")
        
        # If we couldn't find a plain text part, try to get HTML
        if "parts" in payload:
            for part in payload["parts"]:
                if part["mimeType"] == "text/html":
                    if "data" in part["body"]:
                        return base64.urlsafe_b64decode(
                            part["body"]["data"].encode("ASCII")
                        ).decode("utf-8")
        elif payload["mimeType"] == "text/html":
            if "data" in payload["body"]:
                return base64.urlsafe_b64decode(
                    payload["body"]["data"].encode("ASCII")
                ).decode("utf-8")
        
        return ""
