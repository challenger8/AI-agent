"""
utils/deal_status_detector.py
-----------------------------
Centralized deal status detection logic.
DRY: Eliminates duplicate status detection across deal_service.py and health_calculator.py.
SRP: Single responsibility - only deals with status detection.
"""

from datetime import datetime
from typing import Any, Dict, Optional, Tuple
from enum import Enum
import logging

from utils.date_utils import DateUtils
from config.settings import AnalysisSettings

logger = logging.getLogger(__name__)


class DealStatus(Enum):
    """Enumeration of deal statuses"""
    WON = 'won'
    LOST = 'lost'
    OPEN = 'open'
    UNKNOWN = 'unknown'


class DealStatusDetector:
    """
    Utility class for detecting deal status.

    Centralizes deal status detection logic that was duplicated in:
    - services/deal_service.py (detect_deal_status)
    - services/analytics/health_calculator.py (_detect_deal_status)

    SOLID Principles Applied:
    - SRP: Only handles status detection
    - OCP: New statuses can be added via configuration
    - DIP: Depends on abstractions (AnalysisSettings) not concrete implementations
    """

    # Field name mappings for case-insensitive lookup
    WON_TIME_FIELDS = ['change_to_won_time', 'ChangeToWonTime', 'won_time']
    LOST_TIME_FIELDS = ['change_to_loss_time', 'ChangeToLossTime', 'lost_time']
    STATUS_FIELDS = ['Status', 'status', 'DealStatus', 'deal_status', 'deal_state']
    REGISTER_TIME_FIELDS = ['RegisterTime', 'register_time', 'created_at']

    @classmethod
    def detect(cls, deal: Dict[str, Any]) -> DealStatus:
        """
        Detect deal status from deal data.

        Priority:
        1. Timestamp fields (most reliable)
        2. Status text field

        Args:
            deal: Deal dictionary

        Returns:
            DealStatus enum value
        """
        if not deal:
            return DealStatus.UNKNOWN

        # Priority 1: Check transition timestamps (most reliable)
        if cls._has_valid_timestamp(deal, cls.WON_TIME_FIELDS):
            return DealStatus.WON

        if cls._has_valid_timestamp(deal, cls.LOST_TIME_FIELDS):
            return DealStatus.LOST

        # Priority 2: Check status text field
        status_text = cls._get_status_text(deal)
        if status_text:
            return cls._parse_status_text(status_text)

        return DealStatus.UNKNOWN

    @classmethod
    def detect_string(cls, deal: Dict[str, Any]) -> str:
        """
        Detect deal status and return as string.

        Convenience method for backward compatibility.

        Args:
            deal: Deal dictionary

        Returns:
            Status as string ('won', 'lost', 'open', 'unknown')
        """
        return cls.detect(deal).value

    @classmethod
    def _has_valid_timestamp(cls, deal: Dict[str, Any], field_names: list) -> bool:
        """
        Check if deal has a valid (past) timestamp for given fields.

        Args:
            deal: Deal dictionary
            field_names: List of possible field names

        Returns:
            True if valid timestamp exists
        """
        for field in field_names:
            value = deal.get(field)
            if value:
                parsed = DateUtils.parse_iso_date(value)
                if parsed and DateUtils.is_past(parsed):
                    return True
        return False

    @classmethod
    def _get_status_text(cls, deal: Dict[str, Any]) -> Optional[str]:
        """
        Extract status text from deal.

        Args:
            deal: Deal dictionary

        Returns:
            Status text or None
        """
        for field in cls.STATUS_FIELDS:
            value = deal.get(field)
            if value and isinstance(value, str):
                return value.strip().lower()
        return None

    @classmethod
    def _parse_status_text(cls, status_text: str) -> DealStatus:
        """
        Parse status text to DealStatus enum.

        Args:
            status_text: Status string (lowercase)

        Returns:
            DealStatus enum value
        """
        # Check WON statuses
        for won_status in AnalysisSettings.DEAL_STATUS_WON:
            if won_status.lower() in status_text:
                return DealStatus.WON

        # Check LOST statuses
        for lost_status in AnalysisSettings.DEAL_STATUS_LOST:
            if lost_status.lower() in status_text:
                return DealStatus.LOST

        # Check OPEN statuses
        for open_status in AnalysisSettings.DEAL_STATUS_OPEN:
            if open_status.lower() in status_text:
                return DealStatus.OPEN

        logger.debug(f"Unknown status text: {status_text}")
        return DealStatus.UNKNOWN

    @classmethod
    def get_status_change_date(cls, deal: Dict[str, Any]) -> Optional[datetime]:
        """
        Get the date when deal status changed (won or lost).

        Args:
            deal: Deal dictionary

        Returns:
            Status change datetime or None
        """
        # Check won timestamp
        for field in cls.WON_TIME_FIELDS:
            value = deal.get(field)
            if value:
                parsed = DateUtils.parse_iso_date(value)
                if parsed:
                    return parsed

        # Check lost timestamp
        for field in cls.LOST_TIME_FIELDS:
            value = deal.get(field)
            if value:
                parsed = DateUtils.parse_iso_date(value)
                if parsed:
                    return parsed

        return None

    @classmethod
    def get_days_since_status_change(cls, deal: Dict[str, Any]) -> Optional[int]:
        """
        Get days since deal status changed.

        Args:
            deal: Deal dictionary

        Returns:
            Days since change or None if still open
        """
        change_date = cls.get_status_change_date(deal)
        if change_date:
            return DateUtils.days_since(change_date)
        return None

    @classmethod
    def get_deal_age_days(cls, deal: Dict[str, Any]) -> int:
        """
        Calculate deal age in days.

        For closed deals: from creation to close date
        For open deals: from creation to now

        Args:
            deal: Deal dictionary

        Returns:
            Age in days, or NO_DATE_DAYS if no creation date
        """
        # Get register time
        register_time = None
        for field in cls.REGISTER_TIME_FIELDS:
            if deal.get(field):
                register_time = DateUtils.parse_iso_date(deal[field])
                if register_time:
                    break

        if not register_time:
            return DateUtils.NO_DATE_DAYS

        # Determine end date
        status_change = cls.get_status_change_date(deal)
        end_date = status_change or datetime.now()

        return DateUtils.days_between(register_time, end_date)

    @classmethod
    def is_won(cls, deal: Dict[str, Any]) -> bool:
        """Check if deal is won"""
        return cls.detect(deal) == DealStatus.WON

    @classmethod
    def is_lost(cls, deal: Dict[str, Any]) -> bool:
        """Check if deal is lost"""
        return cls.detect(deal) == DealStatus.LOST

    @classmethod
    def is_open(cls, deal: Dict[str, Any]) -> bool:
        """Check if deal is open"""
        return cls.detect(deal) == DealStatus.OPEN

    @classmethod
    def is_closed(cls, deal: Dict[str, Any]) -> bool:
        """Check if deal is closed (won or lost)"""
        status = cls.detect(deal)
        return status in (DealStatus.WON, DealStatus.LOST)

    @classmethod
    def get_status_with_details(cls, deal: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get comprehensive status information.

        Args:
            deal: Deal dictionary

        Returns:
            Dictionary with status details
        """
        status = cls.detect(deal)
        change_date = cls.get_status_change_date(deal)
        days_since_change = cls.get_days_since_status_change(deal)
        deal_age = cls.get_deal_age_days(deal)

        return {
            'status': status.value,
            'is_closed': status in (DealStatus.WON, DealStatus.LOST),
            'status_change_date': change_date.isoformat() if change_date else None,
            'days_since_status_change': days_since_change,
            'deal_age_days': deal_age if deal_age != DateUtils.NO_DATE_DAYS else None
        }


# Convenience functions for backward compatibility
def detect_deal_status(deal: Dict[str, Any]) -> str:
    """Convenience wrapper for DealStatusDetector.detect_string"""
    return DealStatusDetector.detect_string(deal)


def is_deal_won(deal: Dict[str, Any]) -> bool:
    """Convenience wrapper for DealStatusDetector.is_won"""
    return DealStatusDetector.is_won(deal)


def is_deal_lost(deal: Dict[str, Any]) -> bool:
    """Convenience wrapper for DealStatusDetector.is_lost"""
    return DealStatusDetector.is_lost(deal)


def is_deal_open(deal: Dict[str, Any]) -> bool:
    """Convenience wrapper for DealStatusDetector.is_open"""
    return DealStatusDetector.is_open(deal)
