"""GA4 client wrapper for analytics data retrieval."""

from typing import Dict, Any, List, Optional
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.admin_v1beta import AnalyticsAdminServiceClient
from google.analytics.admin_v1beta.types import ListPropertiesRequest
from google.oauth2.credentials import Credentials

from ..utils.errors import GA4APIError, AuthenticationError
from ..utils.logging import get_logger
from ..utils.validation import DataValidator
from .report_builder import ReportBuilder
from .data_formatter import DataFormatter

logger = get_logger(__name__)


class GA4Client:
    """Wrapper for Google Analytics 4 API clients."""
    
    def __init__(self, credentials: Optional[Credentials] = None):
        """
        Initialize GA4 client.
        
        Args:
            credentials: Google OAuth2 credentials
        """
        self._credentials = credentials
        self._analytics_client: Optional[BetaAnalyticsDataClient] = None
        self._admin_client: Optional[AnalyticsAdminServiceClient] = None
        
        if credentials:
            self._initialize_clients()
    
    def _initialize_clients(self) -> None:
        """Initialize GA4 API clients with credentials."""
        if not self._credentials:
            raise AuthenticationError("No credentials provided for GA4 client initialization")
        
        try:
            self._analytics_client = BetaAnalyticsDataClient(credentials=self._credentials)
            self._admin_client = AnalyticsAdminServiceClient(credentials=self._credentials)
            logger.info("GA4 clients initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize GA4 clients: {e}")
            raise GA4APIError(f"Failed to initialize GA4 clients: {e}")
    
    def update_credentials(self, credentials: Credentials) -> None:
        """
        Update credentials and reinitialize clients.
        
        Args:
            credentials: New Google OAuth2 credentials
        """
        self._credentials = credentials
        self._initialize_clients()
    
    @property
    def is_authenticated(self) -> bool:
        """Check if client is properly authenticated."""
        return (
            self._credentials is not None and
            not self._credentials.expired and
            self._analytics_client is not None and
            self._admin_client is not None
        )
    
    def _ensure_authenticated(self) -> None:
        """Ensure client is authenticated before API calls."""
        if not self.is_authenticated:
            raise AuthenticationError(
                "Not authenticated. Please authenticate before making API calls."
            )
    
    def get_standard_report(
        self,
        property_id: str,
        start_date: str = "7daysAgo",
        end_date: str = "today",
        metrics: str = "sessions,users,pageviews",
        dimensions: str = "date",
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Get a standard GA4 report.
        
        Args:
            property_id: GA4 property ID
            start_date: Start date for the report
            end_date: End date for the report
            metrics: Comma-separated list of metrics
            dimensions: Comma-separated list of dimensions
            limit: Maximum number of rows to return
            
        Returns:
            Formatted report data
            
        Raises:
            GA4APIError: If API call fails
        """
        self._ensure_authenticated()
        
        try:
            # Validate inputs
            property_id = DataValidator.validate_property_id(property_id)
            start_date, end_date = DataValidator.validate_date_range(start_date, end_date)
            DataValidator.validate_metrics(metrics)
            DataValidator.validate_dimensions(dimensions)
            limit = DataValidator.validate_limit(limit)
            
            request = ReportBuilder.build_standard_report_request(
                property_id, start_date, end_date, metrics, dimensions, limit
            )
            
            response = self._analytics_client.run_report(request=request)
            formatted_response = DataFormatter.format_report_response(response)
            
            logger.info(f"Retrieved standard report for property {property_id}")
            return formatted_response
            
        except Exception as e:
            logger.error(f"Failed to get standard report: {e}")
            raise GA4APIError(f"Failed to get standard report: {e}", e)
    
    def get_realtime_data(
        self,
        property_id: str,
        metrics: str = "activeUsers",
        dimensions: str = "country",
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Get realtime GA4 data.
        
        Args:
            property_id: GA4 property ID
            metrics: Comma-separated list of realtime metrics
            dimensions: Comma-separated list of dimensions
            limit: Maximum number of rows to return
            
        Returns:
            Formatted realtime data
            
        Raises:
            GA4APIError: If API call fails
        """
        self._ensure_authenticated()
        
        try:
            request = ReportBuilder.build_realtime_report_request(
                property_id, metrics, dimensions, limit
            )
            
            response = self._analytics_client.run_realtime_report(request=request)
            formatted_response = DataFormatter.format_realtime_response(response)
            
            logger.info(f"Retrieved realtime data for property {property_id}")
            return formatted_response
            
        except Exception as e:
            logger.error(f"Failed to get realtime data: {e}")
            raise GA4APIError(f"Failed to get realtime data: {e}", e)
    
    def get_audience_data(
        self,
        property_id: str,
        start_date: str = "30daysAgo",
        end_date: str = "today",
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        Get audience insights from GA4.
        
        Args:
            property_id: GA4 property ID
            start_date: Start date for the report
            end_date: End date for the report
            limit: Maximum number of rows to return
            
        Returns:
            Formatted audience data
            
        Raises:
            GA4APIError: If API call fails
        """
        self._ensure_authenticated()
        
        try:
            request = ReportBuilder.build_audience_report_request(
                property_id, start_date, end_date, limit
            )
            
            response = self._analytics_client.run_report(request=request)
            formatted_response = DataFormatter.format_report_response(response)
            
            logger.info(f"Retrieved audience data for property {property_id}")
            return formatted_response
            
        except Exception as e:
            logger.error(f"Failed to get audience data: {e}")
            raise GA4APIError(f"Failed to get audience data: {e}", e)
    
    def get_popular_pages(
        self,
        property_id: str,
        start_date: str = "7daysAgo",
        end_date: str = "today",
        limit: int = 15
    ) -> Dict[str, Any]:
        """
        Get popular pages from GA4.
        
        Args:
            property_id: GA4 property ID
            start_date: Start date for the report
            end_date: End date for the report
            limit: Maximum number of rows to return
            
        Returns:
            Formatted popular pages data
            
        Raises:
            GA4APIError: If API call fails
        """
        self._ensure_authenticated()
        
        try:
            request = ReportBuilder.build_popular_pages_request(
                property_id, start_date, end_date, limit
            )
            
            response = self._analytics_client.run_report(request=request)
            formatted_response = DataFormatter.format_report_response(response)
            
            logger.info(f"Retrieved popular pages for property {property_id}")
            return formatted_response
            
        except Exception as e:
            logger.error(f"Failed to get popular pages: {e}")
            raise GA4APIError(f"Failed to get popular pages: {e}", e)
    
    def list_properties(self) -> Dict[str, Any]:
        """
        List all accessible GA4 properties.
        
        Returns:
            Formatted properties data
            
        Raises:
            GA4APIError: If API call fails
        """
        self._ensure_authenticated()
        
        if not self._admin_client:
            raise GA4APIError("Admin client not initialized for property listing")
        
        try:
            # Get all accounts first
            accounts_request = self._admin_client.list_accounts()
            accounts_data = []
            
            for account in accounts_request:
                account_data = {
                    "account_id": account.name.split('/')[-1],
                    "account_name": account.display_name,
                    "account_resource_name": account.name,
                    "properties": []
                }
                
                # List properties for this account
                try:
                    filter_string = f"parent:{account.name}"
                    request = ListPropertiesRequest(filter=filter_string)
                    properties_response = self._admin_client.list_properties(request=request)
                    
                    for property in properties_response:
                        property_data = {
                            "property_id": property.name.split('/')[-1],
                            "property_name": property.display_name,
                            "property_resource_name": property.name,
                            "currency_code": getattr(property, 'currency_code', None),
                            "time_zone": getattr(property, 'time_zone', None),
                            "create_time": (
                                property.create_time.isoformat() 
                                if hasattr(property, 'create_time') and property.create_time 
                                else None
                            ),
                            "parent": account.name
                        }
                        account_data["properties"].append(property_data)
                        
                except Exception as e:
                    account_data["properties_error"] = f"Could not list properties: {str(e)}"
                
                accounts_data.append(account_data)
            
            formatted_response = DataFormatter.format_properties_response(accounts_data)
            logger.info(f"Listed {formatted_response['total_properties']} properties from {formatted_response['total_accounts']} accounts")
            return formatted_response
            
        except Exception as e:
            logger.error(f"Failed to list properties: {e}")
            raise GA4APIError(f"Failed to list properties: {e}", e)