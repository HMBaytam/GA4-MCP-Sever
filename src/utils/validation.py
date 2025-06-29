"""Data validation utilities for GA4 MCP Server."""

import re
from typing import List, Any, Optional
from datetime import datetime, timedelta

from .errors import GA4ServerError
from .logging import get_logger

logger = get_logger(__name__)


class ValidationError(GA4ServerError):
    """Raised when validation fails."""
    
    def __init__(self, message: str):
        super().__init__(message, "VALIDATION_ERROR")


class DataValidator:
    """Validates input data for GA4 API requests."""
    
    # Valid GA4 metrics (common ones)
    VALID_METRICS = {
        # Basic metrics
        'sessions', 'users', 'newUsers', 'pageviews', 'screenPageViews',
        'bounceRate', 'averageSessionDuration', 'sessionDuration',
        # Engagement metrics
        'engagedSessions', 'engagementRate', 'engagedSessionsPerUser',
        # Conversion metrics
        'conversions', 'totalRevenue', 'purchaseRevenue',
        # Real-time metrics
        'activeUsers', 'active1DayUsers', 'active7DayUsers', 'active28DayUsers'
    }
    
    # Valid GA4 dimensions (common ones)
    VALID_DIMENSIONS = {
        # Time dimensions
        'date', 'year', 'month', 'week', 'day', 'hour',
        # Geographic dimensions
        'country', 'region', 'city', 'continent', 'subContinent',
        # Technology dimensions
        'deviceCategory', 'operatingSystem', 'browser', 'platform',
        # Traffic dimensions
        'source', 'medium', 'campaign', 'channelGroup',
        # Page dimensions
        'pageTitle', 'pagePath', 'pageLocation', 'landingPage'
    }
    
    @staticmethod
    def validate_property_id(property_id: str) -> str:
        """
        Validate and format GA4 property ID.
        
        Args:
            property_id: GA4 property ID to validate
            
        Returns:
            Formatted property ID
            
        Raises:
            ValidationError: If property ID is invalid
        """
        if not property_id:
            raise ValidationError("Property ID cannot be empty")
        
        # Remove 'properties/' prefix if present for validation
        clean_id = property_id.replace('properties/', '')
        
        # Check if it's a valid numeric ID
        if not clean_id.isdigit():
            raise ValidationError(
                f"Invalid property ID: {property_id}. "
                f"Expected numeric ID or 'properties/123456789' format"
            )
        
        # Ensure it has proper format
        formatted_id = f"properties/{clean_id}" if not property_id.startswith('properties/') else property_id
        
        logger.debug(f"Validated property ID: {formatted_id}")
        return formatted_id
    
    @staticmethod
    def validate_date_range(start_date: str, end_date: str) -> tuple[str, str]:
        """
        Validate GA4 date range.
        
        Args:
            start_date: Start date string
            end_date: End date string
            
        Returns:
            Tuple of validated start and end dates
            
        Raises:
            ValidationError: If date range is invalid
        """
        # Relative date patterns
        relative_pattern = re.compile(r'^\d+(daysAgo|weeksAgo|monthsAgo|yearsAgo)$|^(today|yesterday)$')
        # Absolute date pattern (YYYY-MM-DD)
        absolute_pattern = re.compile(r'^\d{4}-\d{2}-\d{2}$')
        
        def validate_single_date(date_str: str, date_type: str) -> str:
            if not date_str:
                raise ValidationError(f"{date_type} cannot be empty")
            
            # Check relative date format
            if relative_pattern.match(date_str):
                return date_str
            
            # Check absolute date format
            if absolute_pattern.match(date_str):
                try:
                    # Validate that it's a real date
                    datetime.strptime(date_str, '%Y-%m-%d')
                    return date_str
                except ValueError:
                    raise ValidationError(f"Invalid {date_type.lower()}: {date_str}")
            
            raise ValidationError(
                f"Invalid {date_type.lower()} format: {date_str}. "
                f"Use YYYY-MM-DD or relative format like '7daysAgo', 'today'"
            )
        
        validated_start = validate_single_date(start_date, "Start date")
        validated_end = validate_single_date(end_date, "End date")
        
        logger.debug(f"Validated date range: {validated_start} to {validated_end}")
        return validated_start, validated_end
    
    @staticmethod
    def validate_metrics(metrics: str, allow_realtime: bool = False) -> List[str]:
        """
        Validate GA4 metrics list.
        
        Args:
            metrics: Comma-separated metrics string
            allow_realtime: Whether to allow real-time only metrics
            
        Returns:
            List of validated metric names
            
        Raises:
            ValidationError: If any metric is invalid
        """
        if not metrics:
            raise ValidationError("Metrics cannot be empty")
        
        metric_list = [metric.strip() for metric in metrics.split(',')]
        
        if not metric_list:
            raise ValidationError("At least one metric must be specified")
        
        valid_metrics = DataValidator.VALID_METRICS.copy()
        if allow_realtime:
            valid_metrics.update({'activeUsers'})
        
        for metric in metric_list:
            if not metric:
                raise ValidationError("Empty metric name found")
            
            # Basic validation - check against known metrics (non-exhaustive)
            # GA4 has many metrics, so we only validate common ones
            if metric not in valid_metrics:
                logger.warning(f"Unknown metric '{metric}' - proceeding anyway")
        
        logger.debug(f"Validated metrics: {metric_list}")
        return metric_list
    
    @staticmethod
    def validate_dimensions(dimensions: str) -> List[str]:
        """
        Validate GA4 dimensions list.
        
        Args:
            dimensions: Comma-separated dimensions string
            
        Returns:
            List of validated dimension names
            
        Raises:
            ValidationError: If any dimension is invalid
        """
        if not dimensions:
            raise ValidationError("Dimensions cannot be empty")
        
        dimension_list = [dim.strip() for dim in dimensions.split(',')]
        
        if not dimension_list:
            raise ValidationError("At least one dimension must be specified")
        
        for dimension in dimension_list:
            if not dimension:
                raise ValidationError("Empty dimension name found")
            
            # Basic validation - check against known dimensions (non-exhaustive)
            if dimension not in DataValidator.VALID_DIMENSIONS:
                logger.warning(f"Unknown dimension '{dimension}' - proceeding anyway")
        
        logger.debug(f"Validated dimensions: {dimension_list}")
        return dimension_list
    
    @staticmethod
    def validate_limit(limit: int, max_limit: int = 100000) -> int:
        """
        Validate report limit parameter.
        
        Args:
            limit: Row limit to validate
            max_limit: Maximum allowed limit
            
        Returns:
            Validated limit value
            
        Raises:
            ValidationError: If limit is invalid
        """
        if not isinstance(limit, int):
            raise ValidationError(f"Limit must be an integer, got {type(limit)}")
        
        if limit < 1:
            raise ValidationError("Limit must be at least 1")
        
        if limit > max_limit:
            raise ValidationError(f"Limit cannot exceed {max_limit}")
        
        logger.debug(f"Validated limit: {limit}")
        return limit
    
    @staticmethod
    def sanitize_string_input(input_str: str, max_length: int = 1000) -> str:
        """
        Sanitize string input for security.
        
        Args:
            input_str: String to sanitize
            max_length: Maximum allowed length
            
        Returns:
            Sanitized string
            
        Raises:
            ValidationError: If input is invalid
        """
        if not isinstance(input_str, str):
            raise ValidationError(f"Expected string input, got {type(input_str)}")
        
        if len(input_str) > max_length:
            raise ValidationError(f"Input too long: {len(input_str)} > {max_length}")
        
        # Remove any potential injection characters
        sanitized = re.sub(r'[<>"\']', '', input_str.strip())
        
        return sanitized