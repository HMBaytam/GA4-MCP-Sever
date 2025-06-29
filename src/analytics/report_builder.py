"""Report building utilities for GA4 API requests."""

from typing import List, Dict, Any, Optional
from google.analytics.data_v1beta.types import (
    RunReportRequest,
    RunRealtimeReportRequest,
    Dimension,
    Metric,
    DateRange,
    OrderBy
)

from ..config.constants import (
    DEFAULT_REPORT_LIMIT,
    DEFAULT_REALTIME_LIMIT,
    DEFAULT_START_DATE,
    DEFAULT_END_DATE,
    DEFAULT_METRICS,
    DEFAULT_DIMENSIONS,
    DEFAULT_REALTIME_METRICS,
    DEFAULT_REALTIME_DIMENSIONS
)
from ..utils.logging import get_logger

logger = get_logger(__name__)


class ReportBuilder:
    """Builds GA4 API requests for different types of reports."""
    
    @staticmethod
    def build_standard_report_request(
        property_id: str,
        start_date: str = DEFAULT_START_DATE,
        end_date: str = DEFAULT_END_DATE,
        metrics: str = DEFAULT_METRICS,
        dimensions: str = DEFAULT_DIMENSIONS,
        limit: int = DEFAULT_REPORT_LIMIT
    ) -> RunReportRequest:
        """
        Build a standard GA4 report request.
        
        Args:
            property_id: GA4 property ID
            start_date: Start date for the report
            end_date: End date for the report
            metrics: Comma-separated list of metrics
            dimensions: Comma-separated list of dimensions
            limit: Maximum number of rows to return
            
        Returns:
            RunReportRequest object
        """
        try:
            # Ensure property_id has correct format
            if not property_id.startswith('properties/'):
                property_id = f"properties/{property_id}"
            
            # Parse metrics and dimensions
            metric_list = [Metric(name=metric.strip()) for metric in metrics.split(',')]
            dimension_list = [Dimension(name=dim.strip()) for dim in dimensions.split(',')]
            
            # Create date range
            date_range = DateRange(start_date=start_date, end_date=end_date)
            
            request = RunReportRequest(
                property=property_id,
                dimensions=dimension_list,
                metrics=metric_list,
                date_ranges=[date_range],
                limit=limit
            )
            
            logger.debug(f"Built standard report request for property {property_id}")
            return request
            
        except Exception as e:
            logger.error(f"Failed to build standard report request: {e}")
            raise
    
    @staticmethod
    def build_realtime_report_request(
        property_id: str,
        metrics: str = DEFAULT_REALTIME_METRICS,
        dimensions: str = DEFAULT_REALTIME_DIMENSIONS,
        limit: int = DEFAULT_REALTIME_LIMIT
    ) -> RunRealtimeReportRequest:
        """
        Build a realtime GA4 report request.
        
        Args:
            property_id: GA4 property ID
            metrics: Comma-separated list of realtime metrics
            dimensions: Comma-separated list of dimensions
            limit: Maximum number of rows to return
            
        Returns:
            RunRealtimeReportRequest object
        """
        try:
            # Ensure property_id has correct format
            if not property_id.startswith('properties/'):
                property_id = f"properties/{property_id}"
            
            # Parse metrics and dimensions
            metric_list = [Metric(name=metric.strip()) for metric in metrics.split(',')]
            dimension_list = [Dimension(name=dim.strip()) for dim in dimensions.split(',')]
            
            request = RunRealtimeReportRequest(
                property=property_id,
                dimensions=dimension_list,
                metrics=metric_list,
                limit=limit
            )
            
            logger.debug(f"Built realtime report request for property {property_id}")
            return request
            
        except Exception as e:
            logger.error(f"Failed to build realtime report request: {e}")
            raise
    
    @staticmethod
    def build_audience_report_request(
        property_id: str,
        start_date: str = "30daysAgo",
        end_date: str = "today",
        limit: int = 20
    ) -> RunReportRequest:
        """
        Build an audience insights report request.
        
        Args:
            property_id: GA4 property ID
            start_date: Start date for the report
            end_date: End date for the report
            limit: Maximum number of rows to return
            
        Returns:
            RunReportRequest object
        """
        try:
            # Ensure property_id has correct format
            if not property_id.startswith('properties/'):
                property_id = f"properties/{property_id}"
            
            # Define audience-focused metrics and dimensions
            metrics = [
                Metric(name="users"),
                Metric(name="newUsers"),
                Metric(name="sessions"),
                Metric(name="engagedSessions"),
                Metric(name="averageSessionDuration")
            ]
            
            dimensions = [
                Dimension(name="country"),
                Dimension(name="city"),
                Dimension(name="deviceCategory"),
                Dimension(name="operatingSystem")
            ]
            
            # Create date range
            date_range = DateRange(start_date=start_date, end_date=end_date)
            
            request = RunReportRequest(
                property=property_id,
                dimensions=dimensions,
                metrics=metrics,
                date_ranges=[date_range],
                limit=limit,
                order_bys=[OrderBy(metric=OrderBy.MetricOrderBy(metric_name="users"), desc=True)]
            )
            
            logger.debug(f"Built audience report request for property {property_id}")
            return request
            
        except Exception as e:
            logger.error(f"Failed to build audience report request: {e}")
            raise
    
    @staticmethod
    def build_popular_pages_request(
        property_id: str,
        start_date: str = DEFAULT_START_DATE,
        end_date: str = DEFAULT_END_DATE,
        limit: int = 15
    ) -> RunReportRequest:
        """
        Build a popular pages report request.
        
        Args:
            property_id: GA4 property ID
            start_date: Start date for the report
            end_date: End date for the report
            limit: Maximum number of rows to return
            
        Returns:
            RunReportRequest object
        """
        try:
            # Ensure property_id has correct format
            if not property_id.startswith('properties/'):
                property_id = f"properties/{property_id}"
            
            # Define page-focused metrics and dimensions
            metrics = [
                Metric(name="screenPageViews"),
                Metric(name="users"),
                Metric(name="sessions"),
                Metric(name="averageSessionDuration"),
                Metric(name="bounceRate")
            ]
            
            dimensions = [
                Dimension(name="pageTitle"),
                Dimension(name="pagePath")
            ]
            
            # Create date range
            date_range = DateRange(start_date=start_date, end_date=end_date)
            
            request = RunReportRequest(
                property=property_id,
                dimensions=dimensions,
                metrics=metrics,
                date_ranges=[date_range],
                limit=limit,
                order_bys=[OrderBy(metric=OrderBy.MetricOrderBy(metric_name="screenPageViews"), desc=True)]
            )
            
            logger.debug(f"Built popular pages request for property {property_id}")
            return request
            
        except Exception as e:
            logger.error(f"Failed to build popular pages request: {e}")
            raise