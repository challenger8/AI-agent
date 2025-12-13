"""
tests/unit/test_deal_status_detector.py
---------------------------------------
Unit tests for DealStatusDetector utility class.
"""

import pytest
from datetime import datetime, timedelta
from utils.deal_status_detector import (
    DealStatusDetector,
    DealStatus,
    detect_deal_status,
    is_deal_won,
    is_deal_lost,
    is_deal_open
)


class TestDealStatusDetector:
    """Tests for DealStatusDetector class"""

    def test_detect_won_by_timestamp(self):
        """Test detecting won deal by timestamp field"""
        deal = {
            'id': '1',
            'title': 'Test Deal',
            'change_to_won_time': (datetime.now() - timedelta(days=10)).isoformat()
        }
        result = DealStatusDetector.detect(deal)
        assert result == DealStatus.WON

    def test_detect_won_by_camelcase_field(self):
        """Test detecting won deal by CamelCase field"""
        deal = {
            'id': '1',
            'ChangeToWonTime': (datetime.now() - timedelta(days=10)).isoformat()
        }
        result = DealStatusDetector.detect(deal)
        assert result == DealStatus.WON

    def test_detect_lost_by_timestamp(self):
        """Test detecting lost deal by timestamp field"""
        deal = {
            'id': '1',
            'change_to_loss_time': (datetime.now() - timedelta(days=5)).isoformat()
        }
        result = DealStatusDetector.detect(deal)
        assert result == DealStatus.LOST

    def test_detect_won_by_status_text(self):
        """Test detecting won deal by status text"""
        deal = {
            'id': '1',
            'status': 'Won'
        }
        result = DealStatusDetector.detect(deal)
        assert result == DealStatus.WON

    def test_detect_won_by_persian_status(self):
        """Test detecting won deal by Persian status"""
        deal = {
            'id': '1',
            'Status': 'بسته شده'
        }
        result = DealStatusDetector.detect(deal)
        assert result == DealStatus.WON

    def test_detect_lost_by_status_text(self):
        """Test detecting lost deal by status text"""
        deal = {
            'id': '1',
            'status': 'Lost'
        }
        result = DealStatusDetector.detect(deal)
        assert result == DealStatus.LOST

    def test_detect_lost_by_persian_status(self):
        """Test detecting lost deal by Persian status"""
        deal = {
            'id': '1',
            'status': 'لغو شده'
        }
        result = DealStatusDetector.detect(deal)
        assert result == DealStatus.LOST

    def test_detect_open_by_status_text(self):
        """Test detecting open deal by status text"""
        deal = {
            'id': '1',
            'status': 'in_progress'
        }
        result = DealStatusDetector.detect(deal)
        assert result == DealStatus.OPEN

    def test_detect_open_by_persian_status(self):
        """Test detecting open deal by Persian status"""
        deal = {
            'id': '1',
            'status': 'در حال پیگیری'
        }
        result = DealStatusDetector.detect(deal)
        assert result == DealStatus.OPEN

    def test_detect_unknown_empty_deal(self):
        """Test detecting unknown for empty deal"""
        result = DealStatusDetector.detect({})
        assert result == DealStatus.UNKNOWN

    def test_detect_unknown_none_deal(self):
        """Test detecting unknown for None deal"""
        result = DealStatusDetector.detect(None)
        assert result == DealStatus.UNKNOWN

    def test_detect_string_returns_string(self):
        """Test detect_string returns string value"""
        deal = {'status': 'Won'}
        result = DealStatusDetector.detect_string(deal)
        assert result == 'won'

    def test_timestamp_priority_over_status(self):
        """Test that timestamp takes priority over status text"""
        deal = {
            'status': 'open',
            'change_to_won_time': (datetime.now() - timedelta(days=5)).isoformat()
        }
        result = DealStatusDetector.detect(deal)
        assert result == DealStatus.WON

    def test_get_status_change_date_won(self):
        """Test get_status_change_date for won deal"""
        won_time = datetime.now() - timedelta(days=10)
        deal = {
            'change_to_won_time': won_time.isoformat()
        }
        result = DealStatusDetector.get_status_change_date(deal)
        assert result is not None
        assert result.date() == won_time.date()

    def test_get_status_change_date_lost(self):
        """Test get_status_change_date for lost deal"""
        lost_time = datetime.now() - timedelta(days=5)
        deal = {
            'change_to_loss_time': lost_time.isoformat()
        }
        result = DealStatusDetector.get_status_change_date(deal)
        assert result is not None
        assert result.date() == lost_time.date()

    def test_get_status_change_date_open(self):
        """Test get_status_change_date returns None for open deal"""
        deal = {'status': 'open'}
        result = DealStatusDetector.get_status_change_date(deal)
        assert result is None

    def test_get_days_since_status_change(self):
        """Test get_days_since_status_change"""
        deal = {
            'change_to_won_time': (datetime.now() - timedelta(days=15)).isoformat()
        }
        result = DealStatusDetector.get_days_since_status_change(deal)
        assert result == 15

    def test_get_days_since_status_change_open(self):
        """Test get_days_since_status_change for open deal"""
        deal = {'status': 'open'}
        result = DealStatusDetector.get_days_since_status_change(deal)
        assert result is None

    def test_get_deal_age_days_closed(self):
        """Test get_deal_age_days for closed deal"""
        register_time = datetime.now() - timedelta(days=30)
        won_time = datetime.now() - timedelta(days=10)
        deal = {
            'RegisterTime': register_time.isoformat(),
            'change_to_won_time': won_time.isoformat()
        }
        result = DealStatusDetector.get_deal_age_days(deal)
        # Should be 20 days (from register to won)
        assert result == 20

    def test_get_deal_age_days_open(self):
        """Test get_deal_age_days for open deal"""
        register_time = datetime.now() - timedelta(days=30)
        deal = {
            'register_time': register_time.isoformat(),
            'status': 'open'
        }
        result = DealStatusDetector.get_deal_age_days(deal)
        # Should be ~30 days (from register to now)
        assert 29 <= result <= 31

    def test_is_won(self):
        """Test is_won helper method"""
        deal = {'change_to_won_time': datetime.now().isoformat()}
        assert DealStatusDetector.is_won(deal) is True

        deal2 = {'status': 'Lost'}
        assert DealStatusDetector.is_won(deal2) is False

    def test_is_lost(self):
        """Test is_lost helper method"""
        deal = {'change_to_loss_time': datetime.now().isoformat()}
        assert DealStatusDetector.is_lost(deal) is True

        deal2 = {'status': 'Won'}
        assert DealStatusDetector.is_lost(deal2) is False

    def test_is_open(self):
        """Test is_open helper method"""
        deal = {'status': 'in_progress'}
        assert DealStatusDetector.is_open(deal) is True

        deal2 = {'status': 'Won'}
        assert DealStatusDetector.is_open(deal2) is False

    def test_is_closed(self):
        """Test is_closed helper method"""
        won_deal = {'status': 'Won'}
        assert DealStatusDetector.is_closed(won_deal) is True

        lost_deal = {'status': 'Lost'}
        assert DealStatusDetector.is_closed(lost_deal) is True

        open_deal = {'status': 'open'}
        assert DealStatusDetector.is_closed(open_deal) is False

    def test_get_status_with_details(self):
        """Test get_status_with_details returns comprehensive info"""
        register_time = datetime.now() - timedelta(days=30)
        won_time = datetime.now() - timedelta(days=10)
        deal = {
            'register_time': register_time.isoformat(),
            'change_to_won_time': won_time.isoformat()
        }
        result = DealStatusDetector.get_status_with_details(deal)

        assert result['status'] == 'won'
        assert result['is_closed'] is True
        assert result['days_since_status_change'] == 10
        assert result['status_change_date'] is not None


class TestConvenienceFunctions:
    """Tests for module-level convenience functions"""

    def test_detect_deal_status_function(self):
        """Test detect_deal_status convenience function"""
        deal = {'status': 'Won'}
        result = detect_deal_status(deal)
        assert result == 'won'

    def test_is_deal_won_function(self):
        """Test is_deal_won convenience function"""
        deal = {'status': 'Won'}
        assert is_deal_won(deal) is True

    def test_is_deal_lost_function(self):
        """Test is_deal_lost convenience function"""
        deal = {'status': 'Lost'}
        assert is_deal_lost(deal) is True

    def test_is_deal_open_function(self):
        """Test is_deal_open convenience function"""
        deal = {'status': 'in_progress'}
        assert is_deal_open(deal) is True
