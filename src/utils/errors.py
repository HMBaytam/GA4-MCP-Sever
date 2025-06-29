"""Custom exception classes for GA4 MCP Server."""


class GA4ServerError(Exception):
    """Base exception for GA4 MCP Server errors."""
    
    def __init__(self, message: str, error_code: str = None):
        super().__init__(message)
        self.error_code = error_code
        self.message = message


class AuthenticationError(GA4ServerError):
    """Raised when authentication-related errors occur."""
    
    def __init__(self, message: str):
        super().__init__(message, "AUTH_ERROR")


class ConfigurationError(GA4ServerError):
    """Raised when configuration is invalid or missing."""
    
    def __init__(self, message: str):
        super().__init__(message, "CONFIG_ERROR")


class GA4APIError(GA4ServerError):
    """Raised when GA4 API calls fail."""
    
    def __init__(self, message: str, api_error: Exception = None):
        super().__init__(message, "API_ERROR")
        self.api_error = api_error


class CredentialsError(AuthenticationError):
    """Raised when credential operations fail."""
    
    def __init__(self, message: str):
        super().__init__(message)