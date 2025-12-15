"""
tests/unit/test_health_calculator.py
-------------------------------------
Unit tests for HealthCalculator
Tests health score calculation for won, lost, and open deals
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta

from services.analytics.health_calculator import HealthCalculator
from config.constants import HealthCategory


class TestHealthCalculatorInitialization:
    """Test HealthCalculator initialization"""

    def test_init_with_deal_service(self):
        """Test initialization with deal service"""
        mock_service = MagicMock()
        calculator = HealthCalculator(deal_service=mock_service)

        assert calculator.deal_service == mock_service

    def test_init_without_deal_service(self):
        """Test initialization without deal service"""
        calculator = HealthCalculator()

        assert calculator.deal_service is None


class TestHealthScoreCalculation:
    """Test health score calculation routing"""

    @pytest.fixture
    def calculator(self):
        """Create calculator instance"""
        return HealthCalculator()

    def test_calculate_routes_to_won(self, calculator):
        """Test calculate routes to _calculate_won for won deals"""
        deal = {'Status': 'Won', 'Id': '123'}
        activities = []
        sentiment_summary = {}

        with patch.object(calculator, '_calculate_won', return_value=85) as mock_won:
            score = calculator.calculate(deal, activities, sentiment_summary)

            assert score == 85
            mock_won.assert_called_once_with(deal, activities)

    def test_calculate_routes_to_lost(self, calculator):
        """Test calculate routes to _calculate_lost for lost deals"""
        deal = {'Status': 'Lost', 'Id': '123'}
        activities = []
        sentiment_summary = {}

        with patch.object(calculator, '_calculate_lost', return_value=20) as mock_lost:
            score = calculator.calculate(deal, activities, sentiment_summary)

            assert score == 20
            mock_lost.assert_called_once_with(deal, activities)

    def test_calculate_routes_to_open(self, calculator):
        """Test calculate routes to _calculate_open for open deals"""
        deal = {'Status': 'Open', 'Id': '123'}
        activities = []
        sentiment_summary = {}

        with patch.object(calculator, '_calculate_open', return_value=60) as mock_open:
            score = calculator.calculate(deal, activities, sentiment_summary)

            assert score == 60
            mock_open.assert_called_once_with(deal, activities, sentiment_summary)

    def test_calculate_unknown_status_returns_low_score(self, calculator):
        """Test calculate returns 30 for unknown status"""
        deal = {'Status': 'Unknown', 'Id': '123'}
        activities = []
        sentiment_summary = {}

        score = calculator.calculate(deal, activities, sentiment_summary)

        assert score == 30


class TestHealthCategories:
    """Test health category assignment"""

    @pytest.fixture
    def calculator(self):
        """Create calculator instance"""
        return HealthCalculator()

    def test_get_category_healthy(self, calculator):
        """Test healthy category for high scores"""
        with patch('services.analytics.health_calculator.AnalysisSettings') as mock_settings:
            mock_settings.HEALTH_HIGH_THRESHOLD = 70

            category = calculator.get_category(85)

            assert category == HealthCategory.HEALTHY

    def test_get_category_medium(self, calculator):
        """Test medium category for mid-range scores"""
        with patch('services.analytics.health_calculator.AnalysisSettings') as mock_settings:
            mock_settings.HEALTH_HIGH_THRESHOLD = 70
            mock_settings.HEALTH_MEDIUM_THRESHOLD = 40

            category = calculator.get_category(55)

            assert category == HealthCategory.MEDIUM

    def test_get_category_at_risk(self, calculator):
        """Test at-risk category for low scores"""
        with patch('services.analytics.health_calculator.AnalysisSettings') as mock_settings:
            mock_settings.HEALTH_MEDIUM_THRESHOLD = 40

            category = calculator.get_category(25)

            assert category == HealthCategory.AT_RISK

    def test_get_category_persian(self, calculator):
        """Test Persian category translation"""
        with patch('services.analytics.health_calculator.AnalysisSettings') as mock_settings:
            mock_settings.HEALTH_HIGH_THRESHOLD = 70

            # Mock the translate method
            with patch.object(HealthCategory, 'translate', return_value='سالم') as mock_translate:
                persian = calculator.get_category_persian(85)

                assert persian == 'سالم'
                mock_translate.assert_called_once_with(HealthCategory.HEALTHY)


class TestWonDealScoring:
    """Test scoring for won deals"""

    @pytest.fixture
    def calculator(self):
        """Create calculator instance"""
        return HealthCalculator()

    def test_calculate_won_base_score(self, calculator):
        """Test base score for won deals"""
        deal = {'Id': '123', 'Status': 'Won'}
        activities = []

        score = calculator._calculate_won(deal, activities)

        assert score == 85

    def test_calculate_won_with_post_close_activities(self, calculator):
        """Test won deal with follow-up activities after close"""
        won_time = '2024-01-01T00:00:00'
        deal = {'Id': '123', 'Status': 'Won', 'change_to_won_time': won_time}
        activities = [MagicMock(), MagicMock(), MagicMock()]  # 3 activities

        with patch.object(calculator, '_count_activities_after', return_value=3):
            score = calculator._calculate_won(deal, activities)

            # Base 85 + (3 * 3) = 94
            assert score == 94

    def test_calculate_won_caps_at_100(self, calculator):
        """Test won deal score caps at 100"""
        won_time = '2024-01-01T00:00:00'
        deal = {'Id': '123', 'Status': 'Won', 'change_to_won_time': won_time}
        activities = [MagicMock()] * 20  # Many activities

        with patch.object(calculator, '_count_activities_after', return_value=20):
            score = calculator._calculate_won(deal, activities)

            assert score == 100

    def test_calculate_won_alternative_field_name(self, calculator):
        """Test won deal with alternative field name ChangeToWonTime"""
        won_time = '2024-01-01T00:00:00'
        deal = {'Id': '123', 'Status': 'Won', 'ChangeToWonTime': won_time}
        activities = [MagicMock()]

        with patch.object(calculator, '_count_activities_after', return_value=1):
            score = calculator._calculate_won(deal, activities)

            assert score == 88  # 85 + 3


class TestLostDealScoring:
    """Test scoring for lost deals"""

    @pytest.fixture
    def calculator(self):
        """Create calculator instance"""
        return HealthCalculator()

    def test_calculate_lost_base_score(self, calculator):
        """Test base score for lost deals"""
        deal = {'Id': '123', 'Status': 'Lost'}
        activities = []

        score = calculator._calculate_lost(deal, activities)

        assert score == 20

    def test_calculate_lost_with_loss_reason(self, calculator):
        """Test lost deal with documented loss reason"""
        deal = {'Id': '123', 'Status': 'Lost', 'lost_reason_note': 'Price too high'}
        activities = []

        score = calculator._calculate_lost(deal, activities)

        assert score == 30  # 20 + 10

    def test_calculate_lost_with_learning_activities(self, calculator):
        """Test lost deal with learning activities"""
        deal = {'Id': '123', 'Status': 'Lost'}
        activities = [MagicMock()] * 5

        score = calculator._calculate_lost(deal, activities)

        assert score == 25  # 20 + min(5, 10) = 25

    def test_calculate_lost_caps_at_40(self, calculator):
        """Test lost deal score caps at 40"""
        deal = {'Id': '123', 'Status': 'Lost', 'lost_reason_note': 'Documented'}
        activities = [MagicMock()] * 20

        score = calculator._calculate_lost(deal, activities)

        assert score == 40  # Capped

    def test_calculate_lost_alternative_field_name(self, calculator):
        """Test lost deal with alternative field name LostReasonNote"""
        deal = {'Id': '123', 'Status': 'Lost', 'LostReasonNote': 'Budget constraints'}
        activities = []

        score = calculator._calculate_lost(deal, activities)

        assert score == 30


class TestOpenDealScoring:
    """Test scoring for open deals"""

    @pytest.fixture
    def calculator(self):
        """Create calculator instance"""
        return HealthCalculator()

    def test_calculate_open_recent_activity_high_bonus(self, calculator):
        """Test open deal with very recent activity"""
        deal = {'Id': '123', 'Status': 'Open'}
        activities = [MagicMock()]
        sentiment_summary = {'sentiment_available': False}

        with patch.object(calculator, '_days_since_last_activity', return_value=5):
            score = calculator._calculate_open(deal, activities, sentiment_summary)

            # Base 50 + 20 (recent) + 0 (volume) = 70
            assert score == 70

    def test_calculate_open_moderate_activity_recency(self, calculator):
        """Test open deal with moderately recent activity"""
        deal = {'Id': '123', 'Status': 'Open'}
        activities = [MagicMock()]
        sentiment_summary = {'sentiment_available': False}

        with patch.object(calculator, '_days_since_last_activity', return_value=10):
            score = calculator._calculate_open(deal, activities, sentiment_summary)

            # Base 50 + 10 (moderate) = 60
            assert score == 60

    def test_calculate_open_stale_activity_penalty(self, calculator):
        """Test open deal with stale activity"""
        deal = {'Id': '123', 'Status': 'Open'}
        activities = [MagicMock()]
        sentiment_summary = {'sentiment_available': False}

        with patch.object(calculator, '_days_since_last_activity', return_value=45):
            score = calculator._calculate_open(deal, activities, sentiment_summary)

            # Base 50 - 20 (stale) = 30
            assert score == 30

    def test_calculate_open_very_stale_penalty(self, calculator):
        """Test open deal with very stale activity"""
        deal = {'Id': '123', 'Status': 'Open'}
        activities = [MagicMock()]
        sentiment_summary = {'sentiment_available': False}

        with patch.object(calculator, '_days_since_last_activity', return_value=90):
            score = calculator._calculate_open(deal, activities, sentiment_summary)

            # Base 50 - 35 (very stale) = 15
            assert score == 15

    def test_calculate_open_no_activities_penalty(self, calculator):
        """Test open deal with no activities"""
        deal = {'Id': '123', 'Status': 'Open'}
        activities = []
        sentiment_summary = {'sentiment_available': False}

        score = calculator._calculate_open(deal, activities, sentiment_summary)

        # Base 50 - 25 (no activities) - 10 (low volume) = 15
        assert score == 15

    def test_calculate_open_high_activity_volume_bonus(self, calculator):
        """Test open deal with high activity volume"""
        deal = {'Id': '123', 'Status': 'Open'}
        activities = [MagicMock()] * 12
        sentiment_summary = {'sentiment_available': False}

        with patch.object(calculator, '_days_since_last_activity', return_value=5):
            score = calculator._calculate_open(deal, activities, sentiment_summary)

            # Base 50 + 20 (recent) + 15 (high volume) = 85
            assert score == 85

    def test_calculate_open_medium_activity_volume_bonus(self, calculator):
        """Test open deal with medium activity volume"""
        deal = {'Id': '123', 'Status': 'Open'}
        activities = [MagicMock()] * 7
        sentiment_summary = {'sentiment_available': False}

        with patch.object(calculator, '_days_since_last_activity', return_value=5):
            score = calculator._calculate_open(deal, activities, sentiment_summary)

            # Base 50 + 20 (recent) + 10 (medium volume) = 80
            assert score == 80

    def test_calculate_open_positive_sentiment_bonus(self, calculator):
        """Test open deal with positive sentiment"""
        deal = {'Id': '123', 'Status': 'Open'}
        activities = [MagicMock()] * 3
        sentiment_summary = {
            'sentiment_available': True,
            'dominant_sentiment': 'مثبت'
        }

        with patch.object(calculator, '_days_since_last_activity', return_value=5):
            with patch('services.analytics.health_calculator.SentimentNormalizer.get_score_modifier', return_value=10):
                score = calculator._calculate_open(deal, activities, sentiment_summary)

                # Base 50 + 20 (recent) + 10 (sentiment) = 80
                assert score == 80

    def test_calculate_open_negative_sentiment_penalty(self, calculator):
        """Test open deal with negative sentiment"""
        deal = {'Id': '123', 'Status': 'Open'}
        activities = [MagicMock()] * 3
        sentiment_summary = {
            'sentiment_available': True,
            'dominant_sentiment': 'منفی'
        }

        with patch.object(calculator, '_days_since_last_activity', return_value=5):
            with patch('services.analytics.health_calculator.SentimentNormalizer.get_score_modifier', return_value=-15):
                score = calculator._calculate_open(deal, activities, sentiment_summary)

                # Base 50 + 20 (recent) - 15 (sentiment) = 55
                assert score == 55

    def test_calculate_open_score_capped_at_100(self, calculator):
        """Test open deal score caps at 100"""
        deal = {'Id': '123', 'Status': 'Open'}
        activities = [MagicMock()] * 20
        sentiment_summary = {
            'sentiment_available': True,
            'dominant_sentiment': 'مثبت'
        }

        with patch.object(calculator, '_days_since_last_activity', return_value=3):
            with patch('services.analytics.health_calculator.SentimentNormalizer.get_score_modifier', return_value=20):
                score = calculator._calculate_open(deal, activities, sentiment_summary)

                assert score == 100

    def test_calculate_open_score_floored_at_0(self, calculator):
        """Test open deal score floors at 0"""
        deal = {'Id': '123', 'Status': 'Open'}
        activities = []
        sentiment_summary = {
            'sentiment_available': True,
            'dominant_sentiment': 'منفی'
        }

        with patch('services.analytics.health_calculator.SentimentNormalizer.get_score_modifier', return_value=-50):
            score = calculator._calculate_open(deal, activities, sentiment_summary)

            assert score == 0


class TestHelperMethods:
    """Test helper methods"""

    @pytest.fixture
    def calculator(self):
        """Create calculator instance"""
        return HealthCalculator()

    def test_detect_deal_status_delegates_to_utility(self, calculator):
        """Test deal status detection delegates to DealStatusDetector"""
        deal = {'Status': 'Open'}

        with patch('services.analytics.health_calculator.DealStatusDetector.detect_string', return_value='open'):
            status = calculator._detect_deal_status(deal)

            assert status == 'open'

    def test_count_activities_after_delegates_to_utility(self, calculator):
        """Test count activities after delegates to utilities"""
        activities = [MagicMock(), MagicMock()]
        after_date = '2024-01-01T00:00:00'

        with patch('services.analytics.health_calculator.DateUtils.parse_iso_date') as mock_parse:
            with patch('services.analytics.health_calculator.ActivityUtils.count_activities_after', return_value=2):
                count = calculator._count_activities_after(activities, after_date)

                assert count == 2

    def test_count_activities_after_invalid_date(self, calculator):
        """Test count activities after with invalid date"""
        activities = [MagicMock()]
        after_date = 'invalid'

        with patch('services.analytics.health_calculator.DateUtils.parse_iso_date', return_value=None):
            count = calculator._count_activities_after(activities, after_date)

            assert count == 0

    def test_days_since_last_activity_delegates_to_utility(self, calculator):
        """Test days since last activity delegates to ActivityUtils"""
        activities = [MagicMock()]

        with patch('services.analytics.health_calculator.ActivityUtils.days_since_last_activity', return_value=10):
            days = calculator._days_since_last_activity(activities)

            assert days == 10
