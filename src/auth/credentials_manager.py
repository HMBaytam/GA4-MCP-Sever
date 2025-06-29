"""Credentials management for OAuth2 authentication."""

import json
import os
from typing import Optional, Dict, Any
from google.oauth2.credentials import Credentials

from ..utils.errors import CredentialsError
from ..utils.logging import get_logger
from ..config.constants import GA4_CREDENTIALS_FILE

logger = get_logger(__name__)


class CredentialsManager:
    """Manages OAuth2 credentials storage and retrieval."""
    
    def __init__(self, credentials_file: str = GA4_CREDENTIALS_FILE):
        """
        Initialize credentials manager.
        
        Args:
            credentials_file: Path to credentials file
        """
        self.credentials_file = credentials_file
        self._credentials: Optional[Credentials] = None
    
    def save_credentials(self, credentials: Credentials) -> None:
        """
        Save OAuth2 credentials to file.
        
        Args:
            credentials: Google OAuth2 credentials object
            
        Raises:
            CredentialsError: If saving credentials fails
        """
        try:
            creds_data = {
                'token': credentials.token,
                'refresh_token': credentials.refresh_token,
                'token_uri': credentials.token_uri,
                'client_id': credentials.client_id,
                'client_secret': credentials.client_secret,
                'scopes': credentials.scopes
            }
            
            with open(self.credentials_file, 'w') as f:
                json.dump(creds_data, f)
            
            self._credentials = credentials
            logger.info("Credentials saved successfully")
            
        except Exception as e:
            logger.error(f"Failed to save credentials: {e}")
            raise CredentialsError(f"Failed to save credentials: {e}")
    
    def load_credentials(self) -> Credentials:
        """
        Load OAuth2 credentials from file.
        
        Returns:
            Google OAuth2 credentials object
            
        Raises:
            CredentialsError: If loading credentials fails
        """
        if not os.path.exists(self.credentials_file):
            raise CredentialsError(
                "No saved credentials found. Please authenticate first."
            )
        
        try:
            with open(self.credentials_file, 'r') as f:
                creds_data = json.load(f)
            
            self._credentials = Credentials(
                token=creds_data.get('token'),
                refresh_token=creds_data.get('refresh_token'),
                token_uri=creds_data.get('token_uri'),
                client_id=creds_data.get('client_id'),
                client_secret=creds_data.get('client_secret'),
                scopes=creds_data.get('scopes')
            )
            
            logger.info("Credentials loaded successfully")
            return self._credentials
            
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Invalid credentials file format: {e}")
            raise CredentialsError(f"Invalid credentials file format: {e}")
        except Exception as e:
            logger.error(f"Failed to load credentials: {e}")
            raise CredentialsError(f"Failed to load credentials: {e}")
    
    @property
    def credentials(self) -> Optional[Credentials]:
        """Get current credentials without loading from file."""
        return self._credentials
    
    @property
    def is_authenticated(self) -> bool:
        """Check if valid credentials are available."""
        return (
            self._credentials is not None and 
            not self.is_expired
        )
    
    @property
    def is_expired(self) -> bool:
        """Check if current credentials are expired."""
        if not self._credentials:
            return True
        return self._credentials.expired
    
    def clear_credentials(self) -> None:
        """Clear stored credentials and remove file."""
        self._credentials = None
        if os.path.exists(self.credentials_file):
            try:
                os.remove(self.credentials_file)
                logger.info("Credentials cleared successfully")
            except Exception as e:
                logger.error(f"Failed to remove credentials file: {e}")
                raise CredentialsError(f"Failed to clear credentials: {e}")
    
    def get_credentials_info(self) -> Dict[str, Any]:
        """
        Get information about current credentials.
        
        Returns:
            Dictionary with credentials information
        """
        if not self._credentials:
            return {
                "authenticated": False,
                "expired": True,
                "scopes": [],
                "client_id": None
            }
        
        return {
            "authenticated": True,
            "expired": self._credentials.expired,
            "scopes": self._credentials.scopes or [],
            "client_id": self._credentials.client_id,
            "has_refresh_token": bool(self._credentials.refresh_token)
        }