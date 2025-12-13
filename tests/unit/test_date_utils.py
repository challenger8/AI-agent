"""
tests/unit/test_date_utils.py
-----------------------------
Unit tests for DateUtils utility class.
"""

import pytest
from datetime import datetime, timedelta
from utils.date_utils import DateUtils, parse_iso_date, days_since


class TestDateUtils:
    """Tests for DateUtils class"""

    def test_parse_iso_date_with_z_suffix(self):
        """Test parsing ISO date with Z suffix"""
        result = DateUtils.parse_iso_date("2024-01-15T10:30:00Z")
        assert result is not None
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15
        assert result.hour == 10
        assert result.minute == 30

    def test_parse_iso_date_with_timezone(self):
        """Test parsing ISO date with timezone offset"""
        result = DateUtils.parse_iso_date("2024-06-20T15:45:00+03:30")
        assert result is not None
        assert result.year == 2024
        assert result.month == 6
        assert result.day == 20

    def test_parse_iso_date_with_datetime_input(self):
        """Test parse_iso_date passes through datetime objects"""
        input_dt = datetime(2024, 3, 15, 12, 0, 0)
        result = DateUtils.parse_iso_date(input_dt)
        assert result == input_dt

    def test_parse_iso_date_with_none(self):
        """Test parse_iso_date returns None for None input"""
        result = DateUtils.parse_iso_date(None)
        assert result is None

    def test_parse_iso_date_with_default(self):
        """Test parse_iso_date returns default for invalid input"""
        default = datetime(2000, 1, 1)
        result = DateUtils.parse_iso_date("invalid", default=default)
        assert result == default

    def test_parse_iso_date_with_invalid_string(self):
        """Test parse_iso_date returns None for invalid string"""
        result = DateUtils.parse_iso_date("not-a-date")
        assert result is None

    def test_days_between_same_date(self):
        """Test days_between returns 0 for same date"""
        date = datetime(2024, 1, 15)
        result = DateUtils.days_between(date, date)
        assert result == 0

    def test_days_between_different_dates(self):
        """Test days_between calculates correctly"""
        start = datetime(2024, 1, 1)
        end = datetime(2024, 1, 15)
        result = DateUtils.days_between(start, end)
        assert result == 14

    def test_days_between_with_string_dates(self):
        """Test days_between works with string dates"""
        start = "2024-01-01T00:00:00Z"
        end = "2024-01-15T00:00:00Z"
        result = DateUtils.days_between(start, end)
        assert result == 14

    def test_days_between_with_invalid_start(self):
        """Test days_between returns NO_DATE_DAYS for invalid start"""
        result = DateUtils.days_between(None, datetime.now())
        assert result == DateUtils.NO_DATE_DAYS

    def test_days_since_recent_date(self):
        """Test days_since for recent date"""
        recent = datetime.now() - timedelta(days=5)
        result = DateUtils.days_since(recent)
        assert result == 5

    def test_days_since_with_string(self):
        """Test days_since with ISO string"""
        recent = (datetime.now() - timedelta(days=10)).isoformat()
        result = DateUtils.days_since(recent)
        assert 9 <= result <= 11  # Allow for timing variations

    def test_is_within_days_true(self):
        """Test is_within_days returns True for recent date"""
        recent = datetime.now() - timedelta(days=5)
        result = DateUtils.is_within_days(recent, 10)
        assert result is True

    def test_is_within_days_false(self):
        """Test is_within_days returns False for old date"""
        old = datetime.now() - timedelta(days=30)
        result = DateUtils.is_within_days(old, 10)
        assert result is False

    def test_is_within_days_with_none(self):
        """Test is_within_days returns False for None"""
        result = DateUtils.is_within_days(None, 10)
        assert result is False

    def test_get_cutoff_date(self):
        """Test get_cutoff_date calculates correctly"""
        cutoff = DateUtils.get_cutoff_date(30)
        expected = datetime.now() - timedelta(days=30)
        # Allow 1 second difference
        assert abs((cutoff - expected).total_seconds()) < 1

    def test_format_date(self):
        """Test format_date formats correctly"""
        date = datetime(2024, 6, 15, 10, 30)
        result = DateUtils.format_date(date)
        assert result == "2024-06-15"

    def test_format_date_custom_format(self):
        """Test format_date with custom format"""
        date = datetime(2024, 6, 15, 10, 30)
        result = DateUtils.format_date(date, "%d/%m/%Y")
        assert result == "15/06/2024"

    def test_format_date_with_none(self):
        """Test format_date returns None for None input"""
        result = DateUtils.format_date(None)
        assert result is None

    def test_get_date_key(self):
        """Test get_date_key returns YYYY-MM-DD format"""
        date = datetime(2024, 6, 15, 10, 30)
        result = DateUtils.get_date_key(date)
        assert result == "2024-06-15"

    def test_is_past_true(self):
        """Test is_past returns True for past date"""
        past = datetime.now() - timedelta(days=1)
        result = DateUtils.is_past(past)
        assert result is True

    def test_is_past_false_for_future(self):
        """Test is_past returns False for future date"""
        future = datetime.now() + timedelta(days=1)
        result = DateUtils.is_past(future)
        assert result is False

    def test_is_past_with_none(self):
        """Test is_past returns False for None"""
        result = DateUtils.is_past(None)
        assert result is False

    def test_safe_sort_key_with_valid_date(self):
        """Test safe_sort_key with valid date"""
        date = datetime(2024, 6, 15, 10, 30)
        result = DateUtils.safe_sort_key(date)
        assert "2024-06-15" in result

    def test_safe_sort_key_with_invalid(self):
        """Test safe_sort_key returns default for invalid"""
        result = DateUtils.safe_sort_key(None, default='1900-01-01')
        assert result == '1900-01-01'


class TestConvenienceFunctions:
    """Tests for module-level convenience functions"""

    def test_parse_iso_date_function(self):
        """Test parse_iso_date convenience function"""
        result = parse_iso_date("2024-01-15T10:30:00Z")
        assert result is not None
        assert result.year == 2024

    def test_days_since_function(self):
        """Test days_since convenience function"""
        recent = datetime.now() - timedelta(days=5)
        result = days_since(recent)
        assert result == 5
