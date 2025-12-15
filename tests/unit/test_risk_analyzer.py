"""
tests/unit/test_risk_analyzer.py
----------------------------------
Unit tests for RiskAnalyzer
Tests risk identification and assessment for deals
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta

from services.analytics.risk_analyzer import RiskAnalyzer
from config.constants import RiskType, RiskSeverity, RecommendationType


class TestRiskAnalyzerInitialization:
    """Test RiskAnalyzer initialization"""

    def test_init_with_deal_service(self):
        """Test initialization with deal service"""
        mock_service = MagicMock()
        analyzer = RiskAnalyzer(deal_service=mock_service)

        assert analyzer.deal_service == mock_service

    def test_init_without_deal_service(self):
        """Test initialization without deal service"""
        analyzer = RiskAnalyzer()

        assert analyzer.deal_service is None


class TestLowHealthScoreRisk:
    """Test low health score risk identification"""

    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance"""
        return RiskAnalyzer()

    def test_identify_risks_low_health_high_severity(self, analyzer):
        """Test low health score triggers high severity risk"""
        deal = {'Id': '123', 'Status': 'Open'}
        activities = [MagicMock()]
        health_score = 20

        with patch('services.analytics.risk_analyzer.AnalysisSettings') as mock_settings:
            mock_settings.HEALTH_MEDIUM_THRESHOLD = 40

            with patch.object(analyzer, '_days_since_last_activity', return_value=10):
                risks = analyzer.identify_risks(deal, activities, health_score)

                # Should have low health risk
                low_health_risks = [r for r in risks if r['type'] == RiskType.LOW_HEALTH_SCORE]
                assert len(low_health_risks) == 1
                assert low_health_risks[0]['severity'] == RiskSeverity.HIGH

    def test_identify_risks_low_health_medium_severity(self, analyzer):
        """Test medium-low health score triggers medium severity risk"""
        deal = {'Id': '123', 'Status': 'Open'}
        activities = [MagicMock()]
        health_score = 35

        with patch('services.analytics.risk_analyzer.AnalysisSettings') as mock_settings:
            mock_settings.HEALTH_MEDIUM_THRESHOLD = 40

            with patch.object(analyzer, '_days_since_last_activity', return_value=10):
                risks = analyzer.identify_risks(deal, activities, health_score)

                low_health_risks = [r for r in risks if r['type'] == RiskType.LOW_HEALTH_SCORE]
                assert len(low_health_risks) == 1
                assert low_health_risks[0]['severity'] == RiskSeverity.MEDIUM

    def test_identify_risks_healthy_score_no_risk(self, analyzer):
        """Test healthy score does not trigger low health risk"""
        deal = {'Id': '123', 'Status': 'Open'}
        activities = [MagicMock()]
        health_score = 75

        with patch('services.analytics.risk_analyzer.AnalysisSettings') as mock_settings:
            mock_settings.HEALTH_MEDIUM_THRESHOLD = 40

            with patch.object(analyzer, '_days_since_last_activity', return_value=10):
                risks = analyzer.identify_risks(deal, activities, health_score)

                # Should not have low health risk
                low_health_risks = [r for r in risks if r['type'] == RiskType.LOW_HEALTH_SCORE]
                assert len(low_health_risks) == 0


class TestInactivityRisk:
    """Test inactivity risk assessment"""

    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance"""
        return RiskAnalyzer()

    def test_assess_inactivity_critical(self, analyzer):
        """Test critical inactivity risk (>60 days)"""
        with patch('services.analytics.risk_analyzer.AnalysisSettings') as mock_settings:
            mock_settings.INACTIVITY_CRITICAL_DAYS = 60

            risk = analyzer._assess_inactivity_risk(75)

            assert risk is not None
            assert risk['type'] == RiskType.CRITICAL_INACTIVITY
            assert risk['severity'] == RiskSeverity.CRITICAL
            assert '75 روز' in risk['description']

    def test_assess_inactivity_high(self, analyzer):
        """Test high inactivity risk (>30 days)"""
        with patch('services.analytics.risk_analyzer.AnalysisSettings') as mock_settings:
            mock_settings.INACTIVITY_CRITICAL_DAYS = 60
            mock_settings.INACTIVITY_CONCERN_DAYS = 30

            risk = analyzer._assess_inactivity_risk(45)

            assert risk is not None
            assert risk['type'] == RiskType.HIGH_INACTIVITY
            assert risk['severity'] == RiskSeverity.HIGH

    def test_assess_inactivity_moderate(self, analyzer):
        """Test moderate inactivity risk (>14 days)"""
        with patch('services.analytics.risk_analyzer.AnalysisSettings') as mock_settings:
            mock_settings.INACTIVITY_CONCERN_DAYS = 30
            mock_settings.INACTIVITY_WARNING_DAYS = 14

            risk = analyzer._assess_inactivity_risk(20)

            assert risk is not None
            assert risk['type'] == RiskType.MODERATE_INACTIVITY
            assert risk['severity'] == RiskSeverity.MEDIUM

    def test_assess_inactivity_no_risk(self, analyzer):
        """Test no inactivity risk for recent activity"""
        with patch('services.analytics.risk_analyzer.AnalysisSettings') as mock_settings:
            mock_settings.INACTIVITY_WARNING_DAYS = 14

            risk = analyzer._assess_inactivity_risk(10)

            assert risk is None

    def test_identify_risks_includes_inactivity(self, analyzer):
        """Test identify_risks includes inactivity assessment"""
        deal = {'Id': '123', 'Status': 'Open'}
        activities = [MagicMock()]
        health_score = 60

        with patch('services.analytics.risk_analyzer.AnalysisSettings') as mock_settings:
            mock_settings.HEALTH_MEDIUM_THRESHOLD = 40
            mock_settings.INACTIVITY_CONCERN_DAYS = 30

            with patch.object(analyzer, '_days_since_last_activity', return_value=45):
                risks = analyzer.identify_risks(deal, activities, health_score)

                inactivity_risks = [r for r in risks if 'INACTIVITY' in r['type']]
                assert len(inactivity_risks) == 1


class TestNoActivityRisk:
    """Test no activity risk detection"""

    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance"""
        return RiskAnalyzer()

    def test_identify_risks_no_activities(self, analyzer):
        """Test no activities triggers critical risk"""
        deal = {'Id': '123', 'Status': 'Open'}
        activities = []
        health_score = 50

        with patch('services.analytics.risk_analyzer.AnalysisSettings') as mock_settings:
            mock_settings.HEALTH_MEDIUM_THRESHOLD = 40

            risks = analyzer.identify_risks(deal, activities, health_score)

            no_activity_risks = [r for r in risks if r['type'] == RiskType.NO_ACTIVITY]
            assert len(no_activity_risks) == 1
            assert no_activity_risks[0]['severity'] == RiskSeverity.CRITICAL

    def test_identify_risks_with_activities_no_risk(self, analyzer):
        """Test deals with activities don't get no-activity risk"""
        deal = {'Id': '123', 'Status': 'Open'}
        activities = [MagicMock()]
        health_score = 50

        with patch('services.analytics.risk_analyzer.AnalysisSettings') as mock_settings:
            mock_settings.HEALTH_MEDIUM_THRESHOLD = 40

            with patch.object(analyzer, '_days_since_last_activity', return_value=5):
                risks = analyzer.identify_risks(deal, activities, health_score)

                no_activity_risks = [r for r in risks if r['type'] == RiskType.NO_ACTIVITY]
                assert len(no_activity_risks) == 0


class TestDealAgingRisk:
    """Test deal aging risk assessment"""

    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance"""
        return RiskAnalyzer()

    def test_assess_aging_risk_high(self, analyzer):
        """Test high aging risk for old deals (>180 days)"""
        register_time = '2023-01-01T00:00:00'
        deal = {'Id': '123', 'register_time': register_time}

        with patch('services.analytics.risk_analyzer.DateUtils.parse_iso_date') as mock_parse:
            with patch('services.analytics.risk_analyzer.DateUtils.days_since', return_value=200):
                mock_parse.return_value = datetime(2023, 1, 1)

                risk = analyzer._assess_aging_risk(deal)

                assert risk is not None
                assert risk['type'] == RiskType.DEAL_AGING
                assert risk['severity'] == RiskSeverity.HIGH
                assert '200 روز' in risk['description']

    def test_assess_aging_risk_medium(self, analyzer):
        """Test medium aging risk for moderate age (>90 days)"""
        register_time = '2023-10-01T00:00:00'
        deal = {'Id': '123', 'register_time': register_time}

        with patch('services.analytics.risk_analyzer.DateUtils.parse_iso_date') as mock_parse:
            with patch('services.analytics.risk_analyzer.DateUtils.days_since', return_value=120):
                mock_parse.return_value = datetime(2023, 10, 1)

                risk = analyzer._assess_aging_risk(deal)

                assert risk is not None
                assert risk['type'] == RiskType.DEAL_AGING
                assert risk['severity'] == RiskSeverity.MEDIUM

    def test_assess_aging_risk_no_risk(self, analyzer):
        """Test no aging risk for young deals"""
        register_time = '2024-10-01T00:00:00'
        deal = {'Id': '123', 'register_time': register_time}

        with patch('services.analytics.risk_analyzer.DateUtils.parse_iso_date') as mock_parse:
            with patch('services.analytics.risk_analyzer.DateUtils.days_since', return_value=30):
                mock_parse.return_value = datetime(2024, 10, 1)

                risk = analyzer._assess_aging_risk(deal)

                assert risk is None

    def test_assess_aging_risk_missing_register_time(self, analyzer):
        """Test no aging risk when register time missing"""
        deal = {'Id': '123'}

        risk = analyzer._assess_aging_risk(deal)

        assert risk is None

    def test_assess_aging_risk_invalid_date(self, analyzer):
        """Test no aging risk for invalid date"""
        deal = {'Id': '123', 'register_time': 'invalid-date'}

        with patch('services.analytics.risk_analyzer.DateUtils.parse_iso_date', return_value=None):
            risk = analyzer._assess_aging_risk(deal)

            assert risk is None

    def test_assess_aging_risk_alternative_field_name(self, analyzer):
        """Test aging risk with alternative field name RegisterTime"""
        register_time = '2023-01-01T00:00:00'
        deal = {'Id': '123', 'RegisterTime': register_time}

        with patch('services.analytics.risk_analyzer.DateUtils.parse_iso_date') as mock_parse:
            with patch('services.analytics.risk_analyzer.DateUtils.days_since', return_value=200):
                mock_parse.return_value = datetime(2023, 1, 1)

                risk = analyzer._assess_aging_risk(deal)

                assert risk is not None

    def test_identify_risks_includes_aging(self, analyzer):
        """Test identify_risks includes aging assessment"""
        register_time = '2023-01-01T00:00:00'
        deal = {'Id': '123', 'Status': 'Open', 'register_time': register_time}
        activities = [MagicMock()]
        health_score = 60

        with patch('services.analytics.risk_analyzer.AnalysisSettings') as mock_settings:
            mock_settings.HEALTH_MEDIUM_THRESHOLD = 40

            with patch.object(analyzer, '_days_since_last_activity', return_value=5):
                with patch('services.analytics.risk_analyzer.DateUtils.parse_iso_date') as mock_parse:
                    with patch('services.analytics.risk_analyzer.DateUtils.days_since', return_value=200):
                        mock_parse.return_value = datetime(2023, 1, 1)

                        risks = analyzer.identify_risks(deal, activities, health_score)

                        aging_risks = [r for r in risks if r['type'] == RiskType.DEAL_AGING]
                        assert len(aging_risks) == 1


class TestMultipleRisks:
    """Test identification of multiple risks"""

    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance"""
        return RiskAnalyzer()

    def test_identify_risks_multiple_risks(self, analyzer):
        """Test identifying multiple risks simultaneously"""
        register_time = '2023-01-01T00:00:00'
        deal = {'Id': '123', 'Status': 'Open', 'register_time': register_time}
        activities = [MagicMock()]
        health_score = 20  # Low health

        with patch('services.analytics.risk_analyzer.AnalysisSettings') as mock_settings:
            mock_settings.HEALTH_MEDIUM_THRESHOLD = 40
            mock_settings.INACTIVITY_CONCERN_DAYS = 30

            with patch.object(analyzer, '_days_since_last_activity', return_value=45):  # High inactivity
                with patch('services.analytics.risk_analyzer.DateUtils.parse_iso_date') as mock_parse:
                    with patch('services.analytics.risk_analyzer.DateUtils.days_since', return_value=200):  # Aging
                        mock_parse.return_value = datetime(2023, 1, 1)

                        risks = analyzer.identify_risks(deal, activities, health_score)

                        # Should have 3 risks: low health, inactivity, aging
                        assert len(risks) >= 3

    def test_identify_risks_no_risks(self, analyzer):
        """Test healthy deal with no risks"""
        register_time = '2024-10-01T00:00:00'
        deal = {'Id': '123', 'Status': 'Open', 'register_time': register_time}
        activities = [MagicMock()] * 5
        health_score = 80  # High health

        with patch('services.analytics.risk_analyzer.AnalysisSettings') as mock_settings:
            mock_settings.HEALTH_MEDIUM_THRESHOLD = 40
            mock_settings.INACTIVITY_WARNING_DAYS = 14

            with patch.object(analyzer, '_days_since_last_activity', return_value=3):  # Recent
                with patch('services.analytics.risk_analyzer.DateUtils.parse_iso_date') as mock_parse:
                    with patch('services.analytics.risk_analyzer.DateUtils.days_since', return_value=30):  # Young
                        mock_parse.return_value = datetime(2024, 10, 1)

                        risks = analyzer.identify_risks(deal, activities, health_score)

                        # Should have no risks
                        assert len(risks) == 0


class TestHelperMethods:
    """Test helper methods"""

    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance"""
        return RiskAnalyzer()

    def test_days_since_last_activity_delegates_to_utility(self, analyzer):
        """Test days since last activity delegates to ActivityUtils"""
        activities = [MagicMock()]

        with patch('services.analytics.risk_analyzer.ActivityUtils.days_since_last_activity', return_value=15):
            days = analyzer._days_since_last_activity(activities)

            assert days == 15
