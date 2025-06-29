"""Data formatting utilities for GA4 API responses."""

from typing import Dict, Any, List
from google.analytics.data_v1beta.types import RunReportResponse, RunRealtimeReportResponse

from ..utils.logging import get_logger

logger = get_logger(__name__)


class DataFormatter:
    """Formats GA4 API responses into structured data."""
    
    @staticmethod
    def format_report_response(response: RunReportResponse) -> Dict[str, Any]:
        """
        Format GA4 report response into a readable dictionary.
        
        Args:
            response: GA4 RunReportResponse object
            
        Returns:
            Formatted response dictionary
        """
        try:
            result = {
                "row_count": response.row_count,
                "metadata": DataFormatter._extract_metadata(response),
                "dimension_headers": [header.name for header in response.dimension_headers],
                "metric_headers": [
                    {
                        "name": header.name, 
                        "type": header.type_.name
                    } 
                    for header in response.metric_headers
                ],
                "rows": []
            }
            
            for row in response.rows:
                row_data = {
                    "dimensions": [dim.value for dim in row.dimension_values],
                    "metrics": [metric.value for metric in row.metric_values]
                }
                result["rows"].append(row_data)
            
            logger.debug(f"Formatted report response with {result['row_count']} rows")
            return result
            
        except Exception as e:
            logger.error(f"Failed to format report response: {e}")
            raise
    
    @staticmethod
    def format_realtime_response(response: RunRealtimeReportResponse) -> Dict[str, Any]:
        """
        Format GA4 realtime response into a readable dictionary.
        
        Args:
            response: GA4 RunRealtimeReportResponse object
            
        Returns:
            Formatted response dictionary
        """
        try:
            result = {
                "row_count": response.row_count,
                "dimension_headers": [header.name for header in response.dimension_headers],
                "metric_headers": [
                    {
                        "name": header.name, 
                        "type": header.type_.name
                    } 
                    for header in response.metric_headers
                ],
                "rows": []
            }
            
            for row in response.rows:
                row_data = {
                    "dimensions": [dim.value for dim in row.dimension_values],
                    "metrics": [metric.value for metric in row.metric_values]
                }
                result["rows"].append(row_data)
            
            logger.debug(f"Formatted realtime response with {result['row_count']} rows")
            return result
            
        except Exception as e:
            logger.error(f"Failed to format realtime response: {e}")
            raise
    
    @staticmethod
    def _extract_metadata(response: RunReportResponse) -> Dict[str, Any]:
        """
        Extract metadata from GA4 response.
        
        Args:
            response: GA4 RunReportResponse object
            
        Returns:
            Metadata dictionary
        """
        if not response.metadata:
            return {
                "data_loss_from_other_row": False,
                "schema_restriction_response": None,
                "currency_code": None,
                "time_zone": None
            }
        
        return {
            "data_loss_from_other_row": response.metadata.data_loss_from_other_row,
            "schema_restriction_response": (
                response.metadata.schema_restriction_response.name 
                if response.metadata.schema_restriction_response 
                else None
            ),
            "currency_code": response.metadata.currency_code,
            "time_zone": response.metadata.time_zone
        }
    
    @staticmethod
    def format_properties_response(accounts_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Format properties list response.
        
        Args:
            accounts_data: List of account data dictionaries
            
        Returns:
            Formatted properties response
        """
        total_accounts = len(accounts_data)
        total_properties = sum(
            len(account.get("properties", [])) 
            for account in accounts_data
        )
        
        return {
            "accounts": accounts_data,
            "total_accounts": total_accounts,
            "total_properties": total_properties
        }
    
    @staticmethod
    def format_error_response(error: Exception, context: str = "") -> str:
        """
        Format error response for MCP tools.
        
        Args:
            error: Exception that occurred
            context: Additional context about the error
            
        Returns:
            Formatted error message
        """
        if context:
            return f"Error {context}: {str(error)}"
        return f"Error: {str(error)}"