"""Configuration settings management."""

import os
from typing import Optional
from dotenv import load_dotenv
from ..utils.errors import ConfigurationError

# Load environment variables from .env file
load_dotenv()


class Settings:
    """Centralized configuration management for GA4 MCP Server."""
    
    def __init__(self):
        """Initialize settings and validate required environment variables."""
        self._client_id: Optional[str] = None
        self._client_secret: Optional[str] = None
        self._property_id: Optional[str] = None
        self._load_env_vars()
    
    def _load_env_vars(self) -> None:
        """Load and cache environment variables."""
        self._client_id = os.getenv('GA4_CLIENT_ID')
        self._client_secret = os.getenv('GA4_CLIENT_SECRET')
        self._property_id = os.getenv('GA4_PROPERTY_ID')
    
    @property
    def client_id(self) -> str:
        """Get GA4 client ID."""
        if not self._client_id:
            raise ConfigurationError(
                "GA4_CLIENT_ID environment variable is required. "
                "Please set it in your .env file or environment."
            )
        return self._client_id
    
    @property
    def client_secret(self) -> str:
        """Get GA4 client secret."""
        if not self._client_secret:
            raise ConfigurationError(
                "GA4_CLIENT_SECRET environment variable is required. "
                "Please set it in your .env file or environment."
            )
        return self._client_secret
    
    @property
    def property_id(self) -> Optional[str]:
        """Get GA4 property ID (optional)."""
        return self._property_id
    
    @property
    def has_required_credentials(self) -> bool:
        """Check if all required credentials are available."""
        return bool(self._client_id and self._client_secret)
    
    def get_oauth_client_config(self) -> dict:
        """Get OAuth client configuration dictionary."""
        return {
            "web": {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": ["http://localhost:8080"]
            }
        }
    
    def get_debug_info(self) -> dict:
        """Get debug information about configuration state."""
        return {
            "env_file_exists": os.path.exists('.env'),
            "variables": {
                "GA4_CLIENT_ID": "[SET]" if self._client_id else "[NOT SET]",
                "GA4_CLIENT_SECRET": "[SET]" if self._client_secret else "[NOT SET]", 
                "GA4_PROPERTY_ID": self._property_id if self._property_id else "[NOT SET]"
            },
            "GA4_CLIENT_ID_preview": f"{self._client_id[:10]}..." if self._client_id else None
        }