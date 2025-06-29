"""OAuth2 flow management for Google Analytics authentication."""

import json
import os
from typing import Tuple
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials

from ..config.settings import Settings
from ..config.constants import GA4_SCOPES, OAUTH_REDIRECT_URI, OAUTH_FLOW_STATE_FILE
from ..utils.errors import AuthenticationError
from ..utils.logging import get_logger
from .credentials_manager import CredentialsManager

logger = get_logger(__name__)


class OAuthManager:
    """Manages OAuth2 authentication flow for Google Analytics."""
    
    def __init__(self, settings: Settings, credentials_manager: CredentialsManager):
        """
        Initialize OAuth manager.
        
        Args:
            settings: Application settings instance
            credentials_manager: Credentials manager instance
        """
        self.settings = settings
        self.credentials_manager = credentials_manager
        self.flow_state_file = OAUTH_FLOW_STATE_FILE
    
    def start_oauth_flow(self) -> str:
        """
        Start OAuth2 authorization flow.
        
        Returns:
            Authorization URL for user to visit
            
        Raises:
            AuthenticationError: If OAuth flow cannot be started
        """
        try:
            client_config = self.settings.get_oauth_client_config()
            flow = Flow.from_client_config(
                client_config,
                scopes=GA4_SCOPES,
                redirect_uri=OAUTH_REDIRECT_URI
            )
            
            auth_url, state = flow.authorization_url(prompt='consent')
            
            # Store flow state for completion
            flow_state = {
                'client_config': client_config,
                'state': state
            }
            
            with open(self.flow_state_file, 'w') as f:
                json.dump(flow_state, f)
            
            logger.info("OAuth flow started successfully")
            return auth_url
            
        except Exception as e:
            logger.error(f"Failed to start OAuth flow: {e}")
            raise AuthenticationError(f"Failed to start OAuth flow: {e}")
    
    def complete_oauth_flow(self, authorization_code: str) -> Credentials:
        """
        Complete OAuth2 flow with authorization code.
        
        Args:
            authorization_code: Authorization code from OAuth callback
            
        Returns:
            Google OAuth2 credentials
            
        Raises:
            AuthenticationError: If OAuth flow completion fails
        """
        try:
            # Load flow state
            if not os.path.exists(self.flow_state_file):
                raise AuthenticationError(
                    "No OAuth flow state found. Please start OAuth flow first."
                )
            
            with open(self.flow_state_file, 'r') as f:
                flow_state = json.load(f)
            
            flow = Flow.from_client_config(
                flow_state['client_config'],
                scopes=GA4_SCOPES,
                redirect_uri=OAUTH_REDIRECT_URI,
                state=flow_state['state']
            )
            
            # Exchange authorization code for tokens
            flow.fetch_token(code=authorization_code)
            credentials = flow.credentials
            
            # Save credentials
            self.credentials_manager.save_credentials(credentials)
            
            # Clean up flow state
            self._cleanup_flow_state()
            
            logger.info("OAuth flow completed successfully")
            return credentials
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid flow state file: {e}")
            raise AuthenticationError(f"Invalid flow state file: {e}")
        except Exception as e:
            logger.error(f"Failed to complete OAuth flow: {e}")
            raise AuthenticationError(f"Failed to complete OAuth flow: {e}")
    
    def load_saved_credentials(self) -> Credentials:
        """
        Load previously saved credentials.
        
        Returns:
            Google OAuth2 credentials
            
        Raises:
            AuthenticationError: If loading credentials fails
        """
        try:
            return self.credentials_manager.load_credentials()
        except Exception as e:
            logger.error(f"Failed to load saved credentials: {e}")
            raise AuthenticationError(f"Failed to load saved credentials: {e}")
    
    def check_auth_status(self) -> Tuple[bool, str]:
        """
        Check current authentication status.
        
        Returns:
            Tuple of (is_authenticated, status_message)
        """
        if not self.credentials_manager.is_authenticated:
            return False, "Not authenticated. Use start_oauth_flow or load_saved_credentials first."
        
        if self.credentials_manager.is_expired:
            return False, "Credentials expired. Please re-authenticate using start_oauth_flow."
        
        return True, "Authenticated and ready to access Google Analytics 4 data."
    
    def get_auth_info(self) -> dict:
        """
        Get detailed authentication information.
        
        Returns:
            Dictionary with authentication details
        """
        is_auth, status = self.check_auth_status()
        creds_info = self.credentials_manager.get_credentials_info()
        
        return {
            "authenticated": is_auth,
            "status": status,
            "credentials_info": creds_info,
            "required_scopes": GA4_SCOPES,
            "has_required_config": self.settings.has_required_credentials
        }
    
    def _cleanup_flow_state(self) -> None:
        """Clean up OAuth flow state file."""
        if os.path.exists(self.flow_state_file):
            try:
                os.remove(self.flow_state_file)
                logger.debug("OAuth flow state cleaned up")
            except Exception as e:
                logger.warning(f"Failed to clean up flow state: {e}")
    
    def reset_authentication(self) -> None:
        """Reset authentication by clearing all stored credentials."""
        try:
            self.credentials_manager.clear_credentials()
            self._cleanup_flow_state()
            logger.info("Authentication reset successfully")
        except Exception as e:
            logger.error(f"Failed to reset authentication: {e}")
            raise AuthenticationError(f"Failed to reset authentication: {e}")