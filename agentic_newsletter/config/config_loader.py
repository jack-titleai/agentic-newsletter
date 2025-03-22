"""Configuration loader for Agentic Newsletter."""

import json
import os
from pathlib import Path
from typing import Any, Dict

import dotenv


class ConfigLoader:
    """Configuration loader for Agentic Newsletter."""

    def __init__(self) -> None:
        """Initialize the configuration loader."""
        # Load environment variables from .env file
        dotenv.load_dotenv()
        
        # Load config from JSON file
        config_path = Path(__file__).parent / "config.json"
        with open(config_path, "r") as f:
            self.config = json.load(f)
        
        # Create data directory if it doesn't exist
        data_dir = Path(self.get_project_root()) / self.config["database"]["path"].split("/")[0]
        data_dir.mkdir(exist_ok=True)

    def get_config(self) -> Dict[str, Any]:
        """Get the configuration dictionary.
        
        Returns:
            Dict[str, Any]: The configuration dictionary.
        """
        return self.config
    
    def get_database_path(self) -> str:
        """Get the database path.
        
        Returns:
            str: The database path.
        """
        db_path = self.config["database"]["path"]
        return str(Path(self.get_project_root()) / db_path)
    
    def get_gmail_credentials_file(self) -> str:
        """Get the Gmail credentials file path.
        
        Returns:
            str: The Gmail credentials file path.
        """
        return os.environ.get("GMAIL_CREDENTIALS_FILE", "credentials.json")
    
    def get_gmail_token_file(self) -> str:
        """Get the Gmail token file path.
        
        Returns:
            str: The Gmail token file path.
        """
        token_file = self.config["gmail"]["token_file"]
        return str(Path(self.get_project_root()) / token_file)
    
    def get_gmail_scopes(self) -> list[str]:
        """Get the Gmail API scopes.
        
        Returns:
            list[str]: The Gmail API scopes.
        """
        return self.config["gmail"]["scopes"]
    
    def get_gmail_max_results(self) -> int:
        """Get the maximum number of results per Gmail API request.
        
        Returns:
            int: The maximum number of results.
        """
        return self.config["gmail"]["max_results_per_request"]
    
    def get_email_sources(self) -> list[str]:
        """Get the list of email sources from the config.
        
        Returns:
            list[str]: List of email addresses to use as sources.
        """
        return self.config.get("email_sources", [])
    
    def get_article_categories(self) -> list[str]:
        """Get the list of article categories from the config.
        
        Returns:
            list[str]: List of article categories to filter by.
        """
        return self.config.get("article_categories", [])
    
    @staticmethod
    def get_project_root() -> Path:
        """Get the project root directory.
        
        Returns:
            Path: The project root directory.
        """
        # This assumes the package is installed in development mode
        # or that the current working directory is the project root
        return Path.cwd()
