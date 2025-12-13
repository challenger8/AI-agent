"""
utils/activity_utils.py
-----------------------
Centralized activity analysis utilities.
DRY: Eliminates duplicate _days_since_last_activity() implementations.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from collections import Counter
import logging

from utils.date_utils import DateUtils

logger = logging.getLogger(__name__)


class ActivityUtils:
    """
    Utility class for activity analysis operations.

    Centralizes activity-related calculations that were duplicated across:
    - services/deal_service.py
    - services/analytics/health_calculator.py
    - services/analytics/risk_analyzer.py
    - services/moe/experts/activity_expert.py
    """

    # Sentinel value for "no activities" case
    NO_ACTIVITY_DAYS = 999

    @staticmethod
    def get_activity_date(activity: Any) -> Optional[datetime]:
        """
        Extract date from an activity object.

        Handles both object attributes and dictionary keys.

        Args:
            activity: Activity object or dictionary

        Returns:
            Activity datetime or None
        """
        # Try object attributes first
        date_attrs = ['registerdate', 'register_date', 'add_time', 'created_at']
        for attr in date_attrs:
            if hasattr(activity, attr):
                value = getattr(activity, attr)
                if value:
                    return DateUtils.parse_iso_date(value)

        # Try dictionary keys
        if isinstance(activity, dict):
            for key in date_attrs:
                if key in activity and activity[key]:
                    return DateUtils.parse_iso_date(activity[key])

        return None

    @staticmethod
    def get_latest_activity_date(activities: List[Any]) -> Optional[datetime]:
        """
        Get the most recent activity date from a list.

        Args:
            activities: List of activity objects/dicts

        Returns:
            Most recent datetime or None
        """
        if not activities:
            return None

        latest = None
        for activity in activities:
            activity_date = ActivityUtils.get_activity_date(activity)
            if activity_date and (latest is None or activity_date > latest):
                latest = activity_date

        return latest

    @staticmethod
    def days_since_last_activity(activities: List[Any]) -> int:
        """
        Calculate days since the last activity.

        This is the DRY replacement for multiple implementations across the codebase.

        Args:
            activities: List of activity objects/dicts

        Returns:
            Days since last activity, or NO_ACTIVITY_DAYS if none found
        """
        if not activities:
            return ActivityUtils.NO_ACTIVITY_DAYS

        latest = ActivityUtils.get_latest_activity_date(activities)
        if latest is None:
            return ActivityUtils.NO_ACTIVITY_DAYS

        return DateUtils.days_since(latest)

    @staticmethod
    def has_recent_activity(activities: List[Any], days: int = 30) -> bool:
        """
        Check if there's activity within specified days.

        Args:
            activities: List of activities
            days: Number of days to check

        Returns:
            True if activity found within timeframe
        """
        days_since = ActivityUtils.days_since_last_activity(activities)
        return days_since != ActivityUtils.NO_ACTIVITY_DAYS and days_since <= days

    @staticmethod
    def count_activities_after(
        activities: List[Any],
        after_date: Union[str, datetime, None]
    ) -> int:
        """
        Count activities after a given date.

        Args:
            activities: List of activities
            after_date: Date threshold

        Returns:
            Count of activities after the date
        """
        if not activities or not after_date:
            return 0

        threshold = DateUtils.parse_iso_date(after_date)
        if threshold is None:
            return 0

        # Normalize timezone
        if threshold.tzinfo is not None:
            threshold = threshold.replace(tzinfo=None)

        count = 0
        for activity in activities:
            activity_date = ActivityUtils.get_activity_date(activity)
            if activity_date:
                # Normalize timezone for comparison
                if activity_date.tzinfo is not None:
                    activity_date = activity_date.replace(tzinfo=None)
                if activity_date > threshold:
                    count += 1

        return count

    @staticmethod
    def count_activities_in_period(
        activities: List[Any],
        days: int = 30
    ) -> int:
        """
        Count activities within a period.

        Args:
            activities: List of activities
            days: Period in days

        Returns:
            Count of activities in period
        """
        cutoff = DateUtils.get_cutoff_date(days)
        return ActivityUtils.count_activities_after(activities, cutoff)

    @staticmethod
    def calculate_frequency(activities: List[Any]) -> Dict[str, Any]:
        """
        Calculate activity frequency statistics.

        Args:
            activities: List of activities

        Returns:
            Dictionary with frequency statistics
        """
        if not activities:
            return {'status': 'no_data', 'average_per_day': 0}

        # Count by day
        daily_counts: Dict[str, int] = {}
        for activity in activities:
            activity_date = ActivityUtils.get_activity_date(activity)
            if activity_date:
                date_key = activity_date.strftime('%Y-%m-%d')
                daily_counts[date_key] = daily_counts.get(date_key, 0) + 1

        if not daily_counts:
            return {'status': 'no_dated_activities', 'average_per_day': 0}

        avg_per_day = sum(daily_counts.values()) / len(daily_counts)
        max_day = max(daily_counts.items(), key=lambda x: x[1])

        return {
            'status': 'ok',
            'average_per_day': round(avg_per_day, 2),
            'busiest_day': max_day[0],
            'busiest_day_count': max_day[1],
            'total_days_with_activity': len(daily_counts),
            'total_activities': sum(daily_counts.values())
        }

    @staticmethod
    def count_by_type(activities: List[Any]) -> Dict[str, int]:
        """
        Count activities by type.

        Args:
            activities: List of activities

        Returns:
            Dictionary of type -> count
        """
        type_counts: Dict[str, int] = {}

        for activity in activities:
            # Try to get activity type
            activity_type = None

            if hasattr(activity, 'activitytypeid'):
                activity_type = activity.activitytypeid
            elif hasattr(activity, 'type'):
                activity_type = activity.type
            elif isinstance(activity, dict):
                activity_type = activity.get('activitytypeid') or activity.get('type')

            activity_type = activity_type or 'unknown'
            type_counts[str(activity_type)] = type_counts.get(str(activity_type), 0) + 1

        return type_counts

    @staticmethod
    def get_activity_text(activity: Any) -> str:
        """
        Get combined text from activity for analysis.

        Args:
            activity: Activity object or dict

        Returns:
            Combined text string
        """
        texts = []

        # Text fields to extract
        text_fields = ['title', 'note', 'resultnote', 'result_note', 'description']

        for field in text_fields:
            value = None
            if hasattr(activity, field):
                value = getattr(activity, field)
            elif isinstance(activity, dict):
                value = activity.get(field)

            if value and isinstance(value, str):
                texts.append(value.strip())

        return " ".join(texts)

    @staticmethod
    def to_dict(activity: Any) -> Dict[str, Any]:
        """
        Convert activity to dictionary.

        Args:
            activity: Activity object

        Returns:
            Dictionary representation
        """
        if isinstance(activity, dict):
            return activity

        if hasattr(activity, 'to_dict'):
            return activity.to_dict()

        # Manual extraction
        result = {}
        common_fields = [
            'id', 'title', 'note', 'resultnote', 'activitytypeid',
            'registerdate', 'dealid', 'creatorid', 'ownerid'
        ]

        for field in common_fields:
            if hasattr(activity, field):
                value = getattr(activity, field)
                if isinstance(value, datetime):
                    result[field] = value.isoformat()
                else:
                    result[field] = value

        return result


# Convenience functions for backward compatibility
def days_since_last_activity(activities: List[Any]) -> int:
    """Convenience wrapper for ActivityUtils.days_since_last_activity"""
    return ActivityUtils.days_since_last_activity(activities)


def has_recent_activity(activities: List[Any], days: int = 30) -> bool:
    """Convenience wrapper for ActivityUtils.has_recent_activity"""
    return ActivityUtils.has_recent_activity(activities, days)
