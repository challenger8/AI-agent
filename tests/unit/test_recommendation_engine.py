"""
tests/unit/test_recommendation_engine.py
-----------------------------------------
Unit tests for RecommendationEngine
Tests actionable recommendation generation based on health and risks
"""

import pytest
from services.analytics.recommendation_engine import RecommendationEngine


class TestRecommendationEngineInitialization:
    """Test RecommendationEngine initialization"""

    def test_init(self):
        """Test initialization"""
        engine = RecommendationEngine()

        assert engine is not None


class TestHealthBasedRecommendations:
    """Test health-based recommendations"""

    @pytest.fixture
    def engine(self):
        """Create engine instance"""
        return RecommendationEngine()

    def test_get_health_recommendations_low_health(self, engine):
        """Test recommendations for low health score"""
        recommendations = engine._get_health_recommendations(25)

        assert len(recommendations) == 3
        assert any('بررسی دلایل ضعف' in r for r in recommendations)
        assert any('ارزیابی احتمال موفقیت' in r for r in recommendations)
        assert any('تصمیم‌گیری' in r for r in recommendations)

    def test_get_health_recommendations_medium_health(self, engine):
        """Test recommendations for medium health score"""
        recommendations = engine._get_health_recommendations(55)

        assert len(recommendations) == 3
        assert any('افزایش تعامل' in r for r in recommendations)
        assert any('شناسایی موانع' in r for r in recommendations)
        assert any('برنامه‌ریزی' in r for r in recommendations)

    def test_get_health_recommendations_high_health(self, engine):
        """Test recommendations for high health score"""
        recommendations = engine._get_health_recommendations(85)

        assert len(recommendations) == 2
        assert any('momentum' in r for r in recommendations)
        assert any('آماده‌سازی' in r for r in recommendations)

    def test_get_health_recommendations_threshold_boundaries(self, engine):
        """Test recommendations at exact threshold boundaries"""
        # Test at 40 (boundary between low and medium)
        recs_at_40 = engine._get_health_recommendations(40)
        assert len(recs_at_40) == 3
        assert any('افزایش تعامل' in r for r in recs_at_40)

        # Test at 70 (boundary between medium and high)
        recs_at_70 = engine._get_health_recommendations(70)
        assert len(recs_at_70) == 2
        assert any('momentum' in r for r in recs_at_70)


class TestRiskBasedRecommendations:
    """Test risk-based recommendations"""

    @pytest.fixture
    def engine(self):
        """Create engine instance"""
        return RecommendationEngine()

    def test_generate_with_risk_recommendations(self, engine):
        """Test recommendations include risk-based suggestions"""
        deal = {'Id': '123', 'Status': 'Open'}
        health_score = 60
        risk_indicators = [
            {'type': 'inactivity', 'recommendation': 'پیگیری فوری مشتری'},
            {'type': 'low_health', 'recommendation': 'بررسی دلایل ضعف'}
        ]

        recommendations = engine.generate(deal, health_score, risk_indicators)

        # Should include risk recommendations
        assert 'پیگیری فوری مشتری' in recommendations
        assert 'بررسی دلایل ضعف' in recommendations

    def test_generate_prioritizes_top_risks(self, engine):
        """Test only top 3 risks are included"""
        deal = {'Id': '123', 'Status': 'Open'}
        health_score = 60
        risk_indicators = [
            {'type': 'risk1', 'recommendation': 'توصیه ۱'},
            {'type': 'risk2', 'recommendation': 'توصیه ۲'},
            {'type': 'risk3', 'recommendation': 'توصیه ۳'},
            {'type': 'risk4', 'recommendation': 'توصیه ۴'},
            {'type': 'risk5', 'recommendation': 'توصیه ۵'},
        ]

        recommendations = engine.generate(deal, health_score, risk_indicators)

        # Should only include first 3 risks
        assert 'توصیه ۱' in recommendations
        assert 'توصیه ۲' in recommendations
        assert 'توصیه ۳' in recommendations

    def test_generate_no_duplicate_recommendations(self, engine):
        """Test duplicate recommendations are filtered out"""
        deal = {'Id': '123', 'Status': 'Open'}
        health_score = 60
        risk_indicators = [
            {'type': 'risk1', 'recommendation': 'افزایش تعامل با مشتری'},
            {'type': 'risk2', 'recommendation': 'شناسایی موانع پیشرفت'},
        ]

        recommendations = engine.generate(deal, health_score, risk_indicators)

        # Check no duplicates
        assert len(recommendations) == len(set(recommendations))


class TestRecommendationGeneration:
    """Test full recommendation generation"""

    @pytest.fixture
    def engine(self):
        """Create engine instance"""
        return RecommendationEngine()

    def test_generate_with_no_risks(self, engine):
        """Test generate with no risk indicators"""
        deal = {'Id': '123', 'Status': 'Open'}
        health_score = 75
        risk_indicators = []

        recommendations = engine.generate(deal, health_score, risk_indicators)

        # Should have health-based recommendations
        assert len(recommendations) > 0
        assert any('momentum' in r for r in recommendations)

    def test_generate_with_risks_and_health(self, engine):
        """Test generate combines risks and health recommendations"""
        deal = {'Id': '123', 'Status': 'Open'}
        health_score = 55
        risk_indicators = [
            {'type': 'inactivity', 'recommendation': 'پیگیری فوری'}
        ]

        recommendations = engine.generate(deal, health_score, risk_indicators)

        # Should include both risk and health recommendations
        assert 'پیگیری فوری' in recommendations
        assert len(recommendations) >= 2

    def test_generate_max_5_recommendations(self, engine):
        """Test recommendations are capped at 5"""
        deal = {'Id': '123', 'Status': 'Open'}
        health_score = 35  # Low health = 3 recommendations
        risk_indicators = [
            {'type': 'risk1', 'recommendation': 'توصیه ۱'},
            {'type': 'risk2', 'recommendation': 'توصیه ۲'},
            {'type': 'risk3', 'recommendation': 'توصیه ۳'},
        ]

        recommendations = engine.generate(deal, health_score, risk_indicators)

        # Should be capped at 5
        assert len(recommendations) <= 5

    def test_generate_fallback_recommendation(self, engine):
        """Test fallback recommendation when no specific recommendations"""
        deal = {'Id': '123', 'Status': 'Open'}
        health_score = 75  # High health, but we'll mock empty recommendations
        risk_indicators = []

        # Mock to return empty health recommendations
        with pytest.mock.patch.object(engine, '_get_health_recommendations', return_value=[]):
            recommendations = engine.generate(deal, health_score, risk_indicators)

            # Should have fallback
            assert len(recommendations) == 1
            assert 'ادامه پیگیری منظم معامله' in recommendations

    def test_generate_skips_empty_risk_recommendations(self, engine):
        """Test risks without recommendations are skipped"""
        deal = {'Id': '123', 'Status': 'Open'}
        health_score = 60
        risk_indicators = [
            {'type': 'risk1'},  # No recommendation
            {'type': 'risk2', 'recommendation': ''},  # Empty recommendation
            {'type': 'risk3', 'recommendation': 'توصیه معتبر'},
        ]

        recommendations = engine.generate(deal, health_score, risk_indicators)

        # Should only include the valid recommendation
        assert 'توصیه معتبر' in recommendations


class TestEdgeCases:
    """Test edge cases"""

    @pytest.fixture
    def engine(self):
        """Create engine instance"""
        return RecommendationEngine()

    def test_generate_with_empty_deal(self, engine):
        """Test generate handles empty deal dict"""
        deal = {}
        health_score = 50
        risk_indicators = []

        recommendations = engine.generate(deal, health_score, risk_indicators)

        # Should still generate recommendations
        assert len(recommendations) > 0

    def test_generate_with_zero_health(self, engine):
        """Test generate handles zero health score"""
        deal = {'Id': '123'}
        health_score = 0
        risk_indicators = []

        recommendations = engine.generate(deal, health_score, risk_indicators)

        # Should generate low-health recommendations
        assert len(recommendations) > 0
        assert any('بررسی' in r for r in recommendations)

    def test_generate_with_max_health(self, engine):
        """Test generate handles maximum health score"""
        deal = {'Id': '123'}
        health_score = 100
        risk_indicators = []

        recommendations = engine.generate(deal, health_score, risk_indicators)

        # Should generate high-health recommendations
        assert len(recommendations) > 0
        assert any('momentum' in r or 'آماده‌سازی' in r for r in recommendations)

    def test_generate_preserves_order(self, engine):
        """Test recommendations preserve priority order (risks first)"""
        deal = {'Id': '123'}
        health_score = 60
        risk_indicators = [
            {'type': 'risk1', 'recommendation': 'ریسک ۱'},
            {'type': 'risk2', 'recommendation': 'ریسک ۲'},
        ]

        recommendations = engine.generate(deal, health_score, risk_indicators)

        # Risk recommendations should come first
        assert recommendations[0] == 'ریسک ۱'
        assert recommendations[1] == 'ریسک ۲'
