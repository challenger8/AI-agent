"""
tests/unit/test_keyword_matcher.py
----------------------------------
Unit tests for KeywordMatcher utility class.
"""

import pytest
from utils.keyword_matcher import (
    KeywordMatcher,
    KeywordConfig,
    DealIdExtractor,
    calculate_relevance_score,
    extract_deal_id
)


class TestKeywordConfig:
    """Tests for KeywordConfig dataclass"""

    def test_default_config(self):
        """Test default configuration values"""
        config = KeywordConfig()
        assert config.keywords == []
        assert config.patterns == []
        assert config.keyword_score == 0.15
        assert config.min_score == 0.0
        assert config.max_score == 1.0

    def test_custom_config(self):
        """Test custom configuration"""
        config = KeywordConfig(
            keywords=['test', 'example'],
            keyword_score=0.2,
            min_score=0.1
        )
        assert config.keywords == ['test', 'example']
        assert config.keyword_score == 0.2
        assert config.min_score == 0.1


class TestKeywordMatcher:
    """Tests for KeywordMatcher class"""

    def test_for_expert_deal_analysis(self):
        """Test creating matcher for deal_analysis expert"""
        matcher = KeywordMatcher.for_expert('deal_analysis')
        assert matcher is not None
        assert 'deal' in matcher.config.keywords
        assert 'health' in matcher.config.keywords

    def test_for_expert_sentiment(self):
        """Test creating matcher for sentiment expert"""
        matcher = KeywordMatcher.for_expert('sentiment')
        assert matcher is not None
        assert 'sentiment' in matcher.config.keywords
        assert 'مثبت' in matcher.config.keywords

    def test_for_expert_activity(self):
        """Test creating matcher for activity expert"""
        matcher = KeywordMatcher.for_expert('activity')
        assert matcher is not None
        assert 'activity' in matcher.config.keywords
        assert 'timeline' in matcher.config.keywords

    def test_for_expert_risk_assessment(self):
        """Test creating matcher for risk_assessment expert"""
        matcher = KeywordMatcher.for_expert('risk_assessment')
        assert matcher is not None
        assert 'risk' in matcher.config.keywords
        assert 'warning' in matcher.config.keywords

    def test_for_expert_search(self):
        """Test creating matcher for search expert"""
        matcher = KeywordMatcher.for_expert('search')
        assert matcher is not None
        assert 'find' in matcher.config.keywords
        assert 'search' in matcher.config.keywords
        assert matcher.config.min_score == 0.3  # Search has higher min

    def test_for_unknown_expert(self):
        """Test creating matcher for unknown expert type"""
        matcher = KeywordMatcher.for_expert('unknown')
        assert matcher is not None
        # Should return empty config
        assert matcher.config.keywords == []

    def test_calculate_score_single_keyword(self):
        """Test score calculation with single keyword match"""
        config = KeywordConfig(keywords=['test'], keyword_score=0.15)
        matcher = KeywordMatcher(config)
        score = matcher.calculate_score("this is a test query")
        assert score == 0.15

    def test_calculate_score_multiple_keywords(self):
        """Test score calculation with multiple keyword matches"""
        config = KeywordConfig(keywords=['test', 'query', 'example'], keyword_score=0.15)
        matcher = KeywordMatcher(config)
        score = matcher.calculate_score("this is a test query")
        assert score == 0.30  # 2 matches * 0.15

    def test_calculate_score_no_match(self):
        """Test score calculation with no matches"""
        config = KeywordConfig(keywords=['xyz', 'abc'])
        matcher = KeywordMatcher(config)
        score = matcher.calculate_score("this is a test query")
        assert score == 0.0

    def test_calculate_score_with_patterns(self):
        """Test score calculation with regex patterns"""
        config = KeywordConfig(
            patterns=[r'\bdeal[\s_-]?\d+\b'],
            pattern_score=0.2
        )
        matcher = KeywordMatcher(config)
        score = matcher.calculate_score("analyze deal-123")
        assert score == 0.2

    def test_calculate_score_with_context(self):
        """Test score calculation with context boost"""
        config = KeywordConfig(
            context_keys=['entity_type:deal'],
            context_score=0.3
        )
        matcher = KeywordMatcher(config)
        score = matcher.calculate_score("analyze", {'entity_type': 'deal'})
        assert score == 0.3

    def test_calculate_score_max_bound(self):
        """Test score is bounded by max_score"""
        config = KeywordConfig(
            keywords=['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'],
            keyword_score=0.2,
            max_score=1.0
        )
        matcher = KeywordMatcher(config)
        score = matcher.calculate_score("a b c d e f g h")
        assert score == 1.0

    def test_calculate_score_min_bound(self):
        """Test score respects min_score"""
        config = KeywordConfig(
            keywords=['xyz'],
            min_score=0.3
        )
        matcher = KeywordMatcher(config)
        score = matcher.calculate_score("no match here")
        assert score == 0.3

    def test_matches_any_keyword_true(self):
        """Test matches_any_keyword returns True"""
        config = KeywordConfig(keywords=['test', 'example'])
        matcher = KeywordMatcher(config)
        assert matcher.matches_any_keyword("this is a test") is True

    def test_matches_any_keyword_false(self):
        """Test matches_any_keyword returns False"""
        config = KeywordConfig(keywords=['xyz', 'abc'])
        matcher = KeywordMatcher(config)
        assert matcher.matches_any_keyword("this is a test") is False

    def test_get_matched_keywords(self):
        """Test get_matched_keywords returns set of matches"""
        config = KeywordConfig(keywords=['test', 'example', 'query'])
        matcher = KeywordMatcher(config)
        matches = matcher.get_matched_keywords("this test is a query")
        assert matches == {'test', 'query'}

    def test_has_high_persian_ratio_true(self):
        """Test Persian detection with high ratio"""
        assert KeywordMatcher._has_high_persian_ratio("این یک متن فارسی است") is True

    def test_has_high_persian_ratio_false(self):
        """Test Persian detection with low ratio"""
        assert KeywordMatcher._has_high_persian_ratio("this is english text") is False

    def test_calculate_score_persian_bonus(self):
        """Test Persian text gets bonus"""
        config = KeywordConfig()
        matcher = KeywordMatcher(config)
        score = matcher.calculate_score("این یک متن فارسی است")
        assert score == 0.1  # Persian bonus


class TestDealIdExtractor:
    """Tests for DealIdExtractor class"""

    def test_extract_from_context(self):
        """Test extracting deal ID from context"""
        result = DealIdExtractor.extract("analyze deal", {'deal_id': '123'})
        assert result == '123'

    def test_extract_english_pattern(self):
        """Test extracting deal ID from English pattern"""
        result = DealIdExtractor.extract("analyze deal-456")
        assert result == '456'

    def test_extract_english_pattern_with_space(self):
        """Test extracting deal ID with space"""
        result = DealIdExtractor.extract("analyze deal 789")
        assert result == '789'

    def test_extract_persian_pattern(self):
        """Test extracting deal ID from Persian pattern"""
        result = DealIdExtractor.extract("تحلیل دیل 123")
        assert result == '123'

    def test_extract_fallback_number(self):
        """Test fallback number extraction"""
        result = DealIdExtractor.extract("analyze deal with id 999")
        assert result == '999'

    def test_extract_no_match(self):
        """Test no match returns None"""
        result = DealIdExtractor.extract("hello world")
        assert result is None

    def test_extract_number_without_deal_indicator(self):
        """Test number without deal indicator returns None"""
        result = DealIdExtractor.extract("the price is 500")
        assert result is None

    def test_has_deal_id_true(self):
        """Test has_deal_id returns True"""
        assert DealIdExtractor.has_deal_id("analyze deal 123") is True

    def test_has_deal_id_false(self):
        """Test has_deal_id returns False"""
        assert DealIdExtractor.has_deal_id("hello world") is False

    def test_has_deal_id_with_context(self):
        """Test has_deal_id with context"""
        assert DealIdExtractor.has_deal_id("analyze", {'deal_id': '123'}) is True


class TestConvenienceFunctions:
    """Tests for module-level convenience functions"""

    def test_calculate_relevance_score(self):
        """Test calculate_relevance_score function"""
        score = calculate_relevance_score('deal_analysis', 'analyze deal health')
        assert score > 0

    def test_extract_deal_id_function(self):
        """Test extract_deal_id convenience function"""
        result = extract_deal_id("analyze deal 123")
        assert result == '123'
