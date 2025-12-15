"""
tests/unit/test_insight_generator.py
-------------------------------------
Unit tests for InsightGenerator
Tests insight generation for both deal-level and portfolio-level analytics
"""

import pytest
from unittest.mock import MagicMock, patch

from services.analytics.insight_generator import InsightGenerator
from services.analytics.context import DealAnalysisContext


class TestInsightGeneratorInitialization:
    """Test InsightGenerator initialization"""

    def test_init(self):
        """Test initialization"""
        generator = InsightGenerator()

        assert generator is not None


class TestDealInsightsWithContext:
    """Test deal insights generation with context object"""

    @pytest.fixture
    def generator(self):
        """Create generator instance"""
        return InsightGenerator()

    def test_generate_deal_insights_with_context(self, generator):
        """Test generating insights using DealAnalysisContext"""
        context = DealAnalysisContext(
            deal={'Id': '123', 'Status': 'Open'},
            activities=[MagicMock()] * 5,
            sentiment_summary={'sentiment_available': True, 'dominant_sentiment': 'مثبت'},
            health_score=75,
            risk_indicators=[]
        )

        insights = generator.generate_deal_insights(context)

        assert isinstance(insights, list)
        assert len(insights) > 0

    def test_generate_deal_insights_with_high_health(self, generator):
        """Test insights for deal with high health score"""
        context = DealAnalysisContext(
            deal={'Id': '123'},
            activities=[],
            sentiment_summary={},
            health_score=85,
            risk_indicators=[]
        )

        with patch('services.analytics.insight_generator.AnalysisSettings') as mock_settings:
            mock_settings.HEALTH_HIGH_THRESHOLD = 70

            insights = generator.generate_deal_insights(context)

            health_insights = [i for i in insights if 'سالم' in i]
            assert len(health_insights) > 0


class TestDealInsightsLegacyAPI:
    """Test deal insights generation with legacy parameters"""

    @pytest.fixture
    def generator(self):
        """Create generator instance"""
        return InsightGenerator()

    def test_generate_deal_insights_legacy_params(self, generator):
        """Test generating insights using legacy parameters"""
        deal = {'Id': '123', 'Status': 'Open'}
        activities = [MagicMock()] * 5
        sentiment_summary = {'sentiment_available': False}
        health_score = 60
        risk_indicators = []

        insights = generator.generate_deal_insights(
            deal=deal,
            activities=activities,
            sentiment_summary=sentiment_summary,
            health_score=health_score,
            risk_indicators=risk_indicators
        )

        assert isinstance(insights, list)
        assert len(insights) > 0


class TestHealthInsights:
    """Test health-related insights"""

    @pytest.fixture
    def generator(self):
        """Create generator instance"""
        return InsightGenerator()

    def test_health_insights_high_score(self, generator):
        """Test insights for high health score"""
        with patch('services.analytics.insight_generator.AnalysisSettings') as mock_settings:
            mock_settings.HEALTH_HIGH_THRESHOLD = 70

            insights = generator._health_insights(85)

            assert len(insights) == 2
            assert any('سالم' in i for i in insights)
            assert any('فرصت' in i for i in insights)

    def test_health_insights_medium_score(self, generator):
        """Test insights for medium health score"""
        with patch('services.analytics.insight_generator.AnalysisSettings') as mock_settings:
            mock_settings.HEALTH_HIGH_THRESHOLD = 70
            mock_settings.HEALTH_MEDIUM_THRESHOLD = 40

            insights = generator._health_insights(55)

            assert len(insights) == 2
            assert any('متوسط' in i for i in insights)
            assert any('تعامل' in i for i in insights)

    def test_health_insights_low_score(self, generator):
        """Test insights for low health score"""
        with patch('services.analytics.insight_generator.AnalysisSettings') as mock_settings:
            mock_settings.HEALTH_MEDIUM_THRESHOLD = 40

            insights = generator._health_insights(25)

            assert len(insights) == 2
            assert any('خطر' in i for i in insights)
            assert any('بازبینی' in i for i in insights)


class TestActivityInsights:
    """Test activity-related insights"""

    @pytest.fixture
    def generator(self):
        """Create generator instance"""
        return InsightGenerator()

    def test_activity_insights_no_activities(self, generator):
        """Test insights when no activities"""
        insights = generator._activity_insights([])

        assert len(insights) == 1
        assert 'هیچ فعالیتی' in insights[0]

    def test_activity_insights_high_engagement(self, generator):
        """Test insights for high activity engagement"""
        activities = [MagicMock()] * 12

        insights = generator._activity_insights(activities)

        assert len(insights) == 1
        assert 'تعامل خوب' in insights[0]
        assert '12' in insights[0]

    def test_activity_insights_low_engagement(self, generator):
        """Test insights for low activity engagement"""
        activities = [MagicMock(), MagicMock()]

        insights = generator._activity_insights(activities)

        assert len(insights) == 1
        assert 'تعامل کم' in insights[0]

    def test_activity_insights_moderate_no_insight(self, generator):
        """Test no insights generated for moderate activity"""
        activities = [MagicMock()] * 5

        insights = generator._activity_insights(activities)

        assert len(insights) == 0


class TestSentimentInsights:
    """Test sentiment-related insights"""

    @pytest.fixture
    def generator(self):
        """Create generator instance"""
        return InsightGenerator()

    def test_sentiment_insights_positive(self, generator):
        """Test insights for positive sentiment"""
        sentiment_summary = {
            'sentiment_available': True,
            'dominant_sentiment': 'مثبت'
        }

        with patch('services.analytics.insight_generator.SentimentNormalizer.is_positive', return_value=True):
            with patch('services.analytics.insight_generator.SentimentNormalizer.get_emoji', return_value='😊'):
                insights = generator._sentiment_insights(sentiment_summary)

                assert len(insights) == 1
                assert 'احساسات مثبت' in insights[0]

    def test_sentiment_insights_negative(self, generator):
        """Test insights for negative sentiment"""
        sentiment_summary = {
            'sentiment_available': True,
            'dominant_sentiment': 'منفی'
        }

        with patch('services.analytics.insight_generator.SentimentNormalizer.is_positive', return_value=False):
            with patch('services.analytics.insight_generator.SentimentNormalizer.is_negative', return_value=True):
                with patch('services.analytics.insight_generator.SentimentNormalizer.get_emoji', return_value='😞'):
                    insights = generator._sentiment_insights(sentiment_summary)

                    assert len(insights) == 1
                    assert 'احساسات منفی' in insights[0]

    def test_sentiment_insights_not_available(self, generator):
        """Test no insights when sentiment not available"""
        sentiment_summary = {'sentiment_available': False}

        insights = generator._sentiment_insights(sentiment_summary)

        assert len(insights) == 0

    def test_sentiment_insights_neutral(self, generator):
        """Test no insights for neutral sentiment"""
        sentiment_summary = {
            'sentiment_available': True,
            'dominant_sentiment': 'خنثی'
        }

        with patch('services.analytics.insight_generator.SentimentNormalizer.is_positive', return_value=False):
            with patch('services.analytics.insight_generator.SentimentNormalizer.is_negative', return_value=False):
                insights = generator._sentiment_insights(sentiment_summary)

                assert len(insights) == 0


class TestRiskInsights:
    """Test risk-related insights"""

    @pytest.fixture
    def generator(self):
        """Create generator instance"""
        return InsightGenerator()

    def test_deal_insights_with_high_risks(self, generator):
        """Test insights include high risk warning"""
        context = DealAnalysisContext(
            deal={'Id': '123'},
            activities=[],
            sentiment_summary={},
            health_score=50,
            risk_indicators=[
                {'severity': 'high', 'type': 'inactivity'},
                {'severity': 'high', 'type': 'low_health'},
                {'severity': 'medium', 'type': 'aging'}
            ]
        )

        insights = generator.generate_deal_insights(context)

        risk_insights = [i for i in insights if 'خطر' in i and 'اولویت بالا' in i]
        assert len(risk_insights) == 1
        assert '2' in risk_insights[0]  # 2 high risks

    def test_deal_insights_no_high_risks(self, generator):
        """Test no risk warning when no high risks"""
        context = DealAnalysisContext(
            deal={'Id': '123'},
            activities=[],
            sentiment_summary={},
            health_score=50,
            risk_indicators=[
                {'severity': 'medium', 'type': 'aging'}
            ]
        )

        insights = generator.generate_deal_insights(context)

        risk_insights = [i for i in insights if 'اولویت بالا' in i]
        assert len(risk_insights) == 0


class TestPortfolioInsights:
    """Test portfolio-level insights"""

    @pytest.fixture
    def generator(self):
        """Create generator instance"""
        return InsightGenerator()

    def test_generate_portfolio_insights_high_activity_rate(self, generator):
        """Test portfolio insights with high activity rate"""
        summary = {'activity_rate': 75}
        activity_breakdown = {}
        sentiment_overview = {}
        health_overview = {'average_health_score': 50, 'at_risk_count': 0}

        insights = generator.generate_portfolio_insights(
            summary, activity_breakdown, sentiment_overview, health_overview
        )

        activity_insights = [i for i in insights if 'نرخ فعالیت بالا' in i]
        assert len(activity_insights) == 1

    def test_generate_portfolio_insights_low_activity_rate(self, generator):
        """Test portfolio insights with low activity rate"""
        summary = {'activity_rate': 30}
        activity_breakdown = {}
        sentiment_overview = {}
        health_overview = {'average_health_score': 50, 'at_risk_count': 0}

        insights = generator.generate_portfolio_insights(
            summary, activity_breakdown, sentiment_overview, health_overview
        )

        activity_insights = [i for i in insights if 'نرخ فعالیت پایین' in i]
        assert len(activity_insights) == 1

    def test_generate_portfolio_insights_good_health(self, generator):
        """Test portfolio insights with good average health"""
        summary = {'activity_rate': 50}
        activity_breakdown = {}
        sentiment_overview = {}
        health_overview = {'average_health_score': 75, 'at_risk_count': 0}

        insights = generator.generate_portfolio_insights(
            summary, activity_breakdown, sentiment_overview, health_overview
        )

        health_insights = [i for i in insights if 'سلامت پورتفولیو خوب' in i]
        assert len(health_insights) == 1

    def test_generate_portfolio_insights_poor_health(self, generator):
        """Test portfolio insights with poor average health"""
        summary = {'activity_rate': 50}
        activity_breakdown = {}
        sentiment_overview = {}
        health_overview = {'average_health_score': 40, 'at_risk_count': 0}

        insights = generator.generate_portfolio_insights(
            summary, activity_breakdown, sentiment_overview, health_overview
        )

        health_insights = [i for i in insights if 'نیاز به توجه' in i]
        assert len(health_insights) == 1

    def test_generate_portfolio_insights_at_risk_deals(self, generator):
        """Test portfolio insights with at-risk deals"""
        summary = {'activity_rate': 50}
        activity_breakdown = {}
        sentiment_overview = {}
        health_overview = {'average_health_score': 60, 'at_risk_count': 5}

        insights = generator.generate_portfolio_insights(
            summary, activity_breakdown, sentiment_overview, health_overview
        )

        risk_insights = [i for i in insights if 'معامله در خطر' in i]
        assert len(risk_insights) == 1
        assert '5' in risk_insights[0]

    def test_generate_portfolio_insights_comprehensive(self, generator):
        """Test comprehensive portfolio insights"""
        summary = {'activity_rate': 75}
        activity_breakdown = {}
        sentiment_overview = {}
        health_overview = {'average_health_score': 70, 'at_risk_count': 3}

        insights = generator.generate_portfolio_insights(
            summary, activity_breakdown, sentiment_overview, health_overview
        )

        # Should have insights for: high activity, good health, at-risk deals
        assert len(insights) >= 3
