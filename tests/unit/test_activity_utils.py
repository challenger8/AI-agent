"""
tests/unit/test_activity_utils.py
---------------------------------
Unit tests for ActivityUtils utility class.
"""

import pytest
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Optional
from utils.activity_utils import (
    ActivityUtils,
    days_since_last_activity,
    has_recent_activity
)


@dataclass
class MockActivity:
    """Mock activity object for testing"""
    id: str = "1"
    title: str = "Test Activity"
    note: str = "Test note"
    registerdate: Optional[str] = None
    activitytypeid: str = "call"


class TestActivityUtils:
    """Tests for ActivityUtils class"""

    def test_get_activity_date_from_object(self):
        """Test getting date from activity object attribute"""
        activity = MockActivity(
            registerdate=(datetime.now() - timedelta(days=5)).isoformat()
        )
        result = ActivityUtils.get_activity_date(activity)
        assert result is not None
        assert (datetime.now() - result).days == 5

    def test_get_activity_date_from_dict(self):
        """Test getting date from activity dictionary"""
        activity = {
            'id': '1',
            'registerdate': (datetime.now() - timedelta(days=3)).isoformat()
        }
        result = ActivityUtils.get_activity_date(activity)
        assert result is not None
        assert (datetime.now() - result).days == 3

    def test_get_activity_date_none_activity(self):
        """Test get_activity_date with None date"""
        activity = MockActivity(registerdate=None)
        result = ActivityUtils.get_activity_date(activity)
        assert result is None

    def test_get_latest_activity_date_empty_list(self):
        """Test get_latest_activity_date with empty list"""
        result = ActivityUtils.get_latest_activity_date([])
        assert result is None

    def test_get_latest_activity_date_single_activity(self):
        """Test get_latest_activity_date with single activity"""
        activity = MockActivity(
            registerdate=(datetime.now() - timedelta(days=5)).isoformat()
        )
        result = ActivityUtils.get_latest_activity_date([activity])
        assert result is not None
        assert (datetime.now() - result).days == 5

    def test_get_latest_activity_date_multiple_activities(self):
        """Test get_latest_activity_date returns most recent"""
        activities = [
            MockActivity(registerdate=(datetime.now() - timedelta(days=10)).isoformat()),
            MockActivity(registerdate=(datetime.now() - timedelta(days=2)).isoformat()),
            MockActivity(registerdate=(datetime.now() - timedelta(days=5)).isoformat()),
        ]
        result = ActivityUtils.get_latest_activity_date(activities)
        assert result is not None
        assert (datetime.now() - result).days == 2

    def test_days_since_last_activity_empty_list(self):
        """Test days_since_last_activity with empty list"""
        result = ActivityUtils.days_since_last_activity([])
        assert result == ActivityUtils.NO_ACTIVITY_DAYS

    def test_days_since_last_activity_recent(self):
        """Test days_since_last_activity with recent activity"""
        activities = [
            MockActivity(registerdate=(datetime.now() - timedelta(days=3)).isoformat())
        ]
        result = ActivityUtils.days_since_last_activity(activities)
        assert result == 3

    def test_days_since_last_activity_old(self):
        """Test days_since_last_activity with old activity"""
        activities = [
            MockActivity(registerdate=(datetime.now() - timedelta(days=100)).isoformat())
        ]
        result = ActivityUtils.days_since_last_activity(activities)
        assert result == 100

    def test_has_recent_activity_true(self):
        """Test has_recent_activity returns True for recent activity"""
        activities = [
            MockActivity(registerdate=(datetime.now() - timedelta(days=5)).isoformat())
        ]
        result = ActivityUtils.has_recent_activity(activities, days=30)
        assert result is True

    def test_has_recent_activity_false(self):
        """Test has_recent_activity returns False for old activity"""
        activities = [
            MockActivity(registerdate=(datetime.now() - timedelta(days=60)).isoformat())
        ]
        result = ActivityUtils.has_recent_activity(activities, days=30)
        assert result is False

    def test_has_recent_activity_empty_list(self):
        """Test has_recent_activity returns False for empty list"""
        result = ActivityUtils.has_recent_activity([])
        assert result is False

    def test_count_activities_after(self):
        """Test count_activities_after"""
        cutoff = datetime.now() - timedelta(days=30)
        activities = [
            MockActivity(registerdate=(datetime.now() - timedelta(days=10)).isoformat()),
            MockActivity(registerdate=(datetime.now() - timedelta(days=20)).isoformat()),
            MockActivity(registerdate=(datetime.now() - timedelta(days=50)).isoformat()),
        ]
        result = ActivityUtils.count_activities_after(activities, cutoff)
        assert result == 2

    def test_count_activities_after_empty(self):
        """Test count_activities_after with empty list"""
        result = ActivityUtils.count_activities_after([], datetime.now())
        assert result == 0

    def test_count_activities_in_period(self):
        """Test count_activities_in_period"""
        activities = [
            MockActivity(registerdate=(datetime.now() - timedelta(days=5)).isoformat()),
            MockActivity(registerdate=(datetime.now() - timedelta(days=15)).isoformat()),
            MockActivity(registerdate=(datetime.now() - timedelta(days=45)).isoformat()),
        ]
        result = ActivityUtils.count_activities_in_period(activities, days=30)
        assert result == 2

    def test_calculate_frequency_empty(self):
        """Test calculate_frequency with empty list"""
        result = ActivityUtils.calculate_frequency([])
        assert result['status'] == 'no_data'

    def test_calculate_frequency_with_activities(self):
        """Test calculate_frequency with activities"""
        activities = [
            MockActivity(registerdate=(datetime.now() - timedelta(days=1)).isoformat()),
            MockActivity(registerdate=(datetime.now() - timedelta(days=1)).isoformat()),
            MockActivity(registerdate=(datetime.now() - timedelta(days=2)).isoformat()),
        ]
        result = ActivityUtils.calculate_frequency(activities)
        assert result['status'] == 'ok'
        assert result['total_activities'] == 3
        assert 'average_per_day' in result

    def test_count_by_type_empty(self):
        """Test count_by_type with empty list"""
        result = ActivityUtils.count_by_type([])
        assert result == {}

    def test_count_by_type_with_activities(self):
        """Test count_by_type with activities"""
        activities = [
            MockActivity(activitytypeid='call'),
            MockActivity(activitytypeid='call'),
            MockActivity(activitytypeid='email'),
        ]
        result = ActivityUtils.count_by_type(activities)
        assert result['call'] == 2
        assert result['email'] == 1

    def test_get_activity_text(self):
        """Test get_activity_text combines text fields"""
        activity = MockActivity(
            title="Call with client",
            note="Discussed pricing"
        )
        result = ActivityUtils.get_activity_text(activity)
        assert "Call with client" in result
        assert "Discussed pricing" in result

    def test_get_activity_text_from_dict(self):
        """Test get_activity_text from dictionary"""
        activity = {
            'title': 'Email sent',
            'note': 'Follow up required'
        }
        result = ActivityUtils.get_activity_text(activity)
        assert "Email sent" in result
        assert "Follow up required" in result

    def test_to_dict_already_dict(self):
        """Test to_dict passes through dictionaries"""
        activity = {'id': '1', 'title': 'Test'}
        result = ActivityUtils.to_dict(activity)
        assert result == activity

    def test_to_dict_from_object(self):
        """Test to_dict converts object to dict"""
        activity = MockActivity(id='123', title='Test Activity')
        result = ActivityUtils.to_dict(activity)
        assert result['id'] == '123'
        assert result['title'] == 'Test Activity'


class TestConvenienceFunctions:
    """Tests for module-level convenience functions"""

    def test_days_since_last_activity_function(self):
        """Test days_since_last_activity convenience function"""
        activities = [
            MockActivity(registerdate=(datetime.now() - timedelta(days=7)).isoformat())
        ]
        result = days_since_last_activity(activities)
        assert result == 7

    def test_has_recent_activity_function(self):
        """Test has_recent_activity convenience function"""
        activities = [
            MockActivity(registerdate=(datetime.now() - timedelta(days=7)).isoformat())
        ]
        result = has_recent_activity(activities, days=30)
        assert result is True
