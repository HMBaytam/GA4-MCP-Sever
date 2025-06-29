"""Application constants and configuration values."""

from typing import List

# OAuth2 Configuration
GA4_SCOPES: List[str] = [
    'https://www.googleapis.com/auth/analytics.readonly',
    'https://www.googleapis.com/auth/analytics.manage.users.readonly'
]

OAUTH_REDIRECT_URI: str = 'http://localhost:8080'

# File paths
OAUTH_FLOW_STATE_FILE: str = '.oauth_flow_state.json'
GA4_CREDENTIALS_FILE: str = '.ga4_credentials.json'

# Google OAuth URLs
GOOGLE_AUTH_URI: str = "https://accounts.google.com/o/oauth2/auth"
GOOGLE_TOKEN_URI: str = "https://oauth2.googleapis.com/token"

# Default request limits
DEFAULT_REPORT_LIMIT: int = 10
MAX_REPORT_LIMIT: int = 100000
DEFAULT_REALTIME_LIMIT: int = 10
DEFAULT_AUDIENCE_LIMIT: int = 20
DEFAULT_PAGES_LIMIT: int = 15

# Default date ranges
DEFAULT_START_DATE: str = "7daysAgo"
DEFAULT_END_DATE: str = "today"
DEFAULT_AUDIENCE_START_DATE: str = "30daysAgo"

# Default metrics and dimensions
DEFAULT_METRICS: str = "sessions,users,pageviews"
DEFAULT_DIMENSIONS: str = "date"
DEFAULT_REALTIME_METRICS: str = "activeUsers"
DEFAULT_REALTIME_DIMENSIONS: str = "country"