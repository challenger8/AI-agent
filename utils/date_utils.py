"""
utils/date_utils.py
-------------------
Centralized date parsing and manipulation utilities.
DRY: Eliminates duplicate datetime.fromisoformat() calls across the codebase.
"""

from datetime import datetime, timedelta
from typing import Optional, Union
import logging

logger = logging.getLogger(__name__)


class DateUtils:
    """
    Utility class for date parsing and manipulation.

    Centralizes all date-related operations to eliminate code duplication.
    """

    # Sentinel value for "no date found" cases
    NO_DATE_DAYS = 999

    @staticmethod
    def parse_iso_date(
        date_value: Union[str, datetime, None],
        default: Optional[datetime] = None
    ) -> Optional[datetime]:
        """
        Parse ISO format date string to datetime object.

        Handles:
        - ISO strings with 'Z' suffix
        - ISO strings with timezone offset
        - Already-parsed datetime objects
        - None values

        Args:
            date_value: Date string, datetime object, or None
            default: Default value if parsing fails

        Returns:
            Parsed datetime or default value

        Examples:
            >>> DateUtils.parse_iso_date("2024-01-15T10:30:00Z")
            datetime(2024, 1, 15, 10, 30, 0, tzinfo=...)

            >>> DateUtils.parse_iso_date(None)
            None
        """
        if date_value is None:
            return default

        if isinstance(date_value, datetime):
            return date_value

        if isinstance(date_value, str):
            try:
                # Handle 'Z' suffix (UTC)
                normalized = date_value.replace('Z', '+00:00')
                return datetime.fromisoformat(normalized)
            except (ValueError, AttributeError) as e:
                logger.debug(f"Failed to parse date '{date_value}': {e}")
                return default

        return default

    @staticmethod
    def days_between(
        start: Union[str, datetime, None],
        end: Union[str, datetime, None] = None
    ) -> int:
        """
        Calculate days between two dates.

        Args:
            start: Start date (string or datetime)
            end: End date (defaults to now)

        Returns:
            Number of days, or NO_DATE_DAYS if dates invalid
        """
        start_dt = DateUtils.parse_iso_date(start)
        end_dt = DateUtils.parse_iso_date(end) or datetime.now()

        if start_dt is None:
            return DateUtils.NO_DATE_DAYS

        # Remove timezone info for comparison if needed
        if start_dt.tzinfo is not None and end_dt.tzinfo is None:
            start_dt = start_dt.replace(tzinfo=None)
        elif start_dt.tzinfo is None and end_dt.tzinfo is not None:
            end_dt = end_dt.replace(tzinfo=None)

        return max(0, (end_dt - start_dt).days)

    @staticmethod
    def days_since(date_value: Union[str, datetime, None]) -> int:
        """
        Calculate days since a given date until now.

        Args:
            date_value: Date to calculate from

        Returns:
            Number of days since date, or NO_DATE_DAYS if invalid
        """
        return DateUtils.days_between(date_value, datetime.now())

    @staticmethod
    def is_within_days(
        date_value: Union[str, datetime, None],
        days: int
    ) -> bool:
        """
        Check if date is within specified number of days from now.

        Args:
            date_value: Date to check
            days: Number of days threshold

        Returns:
            True if date is within threshold
        """
        days_since = DateUtils.days_since(date_value)
        return days_since != DateUtils.NO_DATE_DAYS and days_since <= days

    @staticmethod
    def get_cutoff_date(days: int) -> datetime:
        """
        Get a cutoff date (now - days).

        Args:
            days: Number of days back

        Returns:
            Cutoff datetime
        """
        return datetime.now() - timedelta(days=days)

    @staticmethod
    def format_date(
        date_value: Union[str, datetime, None],
        format_str: str = "%Y-%m-%d"
    ) -> Optional[str]:
        """
        Format a date value to string.

        Args:
            date_value: Date to format
            format_str: Output format (default: YYYY-MM-DD)

        Returns:
            Formatted date string or None
        """
        parsed = DateUtils.parse_iso_date(date_value)
        if parsed:
            return parsed.strftime(format_str)
        return None

    @staticmethod
    def get_date_key(date_value: Union[str, datetime, None]) -> Optional[str]:
        """
        Get date as YYYY-MM-DD string for grouping/keying.

        Args:
            date_value: Date value

        Returns:
            Date string in YYYY-MM-DD format or None
        """
        return DateUtils.format_date(date_value, "%Y-%m-%d")

    @staticmethod
    def is_past(date_value: Union[str, datetime, None]) -> bool:
        """
        Check if date is in the past.

        Args:
            date_value: Date to check

        Returns:
            True if date is before now
        """
        parsed = DateUtils.parse_iso_date(date_value)
        if parsed is None:
            return False

        now = datetime.now()
        if parsed.tzinfo is not None:
            parsed = parsed.replace(tzinfo=None)

        return parsed <= now

    @staticmethod
    def safe_sort_key(
        date_value: Union[str, datetime, None],
        default: str = '1900-01-01'
    ) -> str:
        """
        Get a safe sort key for date values.

        Args:
            date_value: Date to convert
            default: Default for None/invalid dates

        Returns:
            ISO format string suitable for sorting
        """
        parsed = DateUtils.parse_iso_date(date_value)
        if parsed:
            return parsed.isoformat()
        return default


# Convenience functions for backward compatibility
def parse_iso_date(date_value, default=None):
    """Convenience wrapper for DateUtils.parse_iso_date"""
    return DateUtils.parse_iso_date(date_value, default)


def days_since(date_value):
    """Convenience wrapper for DateUtils.days_since"""
    return DateUtils.days_since(date_value)
