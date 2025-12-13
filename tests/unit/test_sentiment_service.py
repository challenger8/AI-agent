"""
tests/unit/test_sentiment_service.py
------------------------------------
Unit tests for SentimentService
"""

import pytest

@pytest.mark.unit
class TestSentimentService:
    """Test SentimentService functionality"""
    @pytest.mark.unit
    def test_service_initialization(self, sentiment_service):
        """Test sentiment service creates successfully"""
        assert sentiment_service is not None
        assert hasattr(sentiment_service, 'available')
    @pytest.mark.unit
    def test_analyze_text_mock(self, mock_sentiment_service):
        """Test sentiment analysis with mock service"""
        result = mock_sentiment_service.analyze_text("متن تست")
        
        assert result is not None
        assert 'sentiment' in result
        assert 'confidence' in result
    @pytest.mark.unit
    def test_analyze_text_empty(self, sentiment_service):
        """Test analyzing empty text"""
        result = sentiment_service.analyze_text("")
        
        # Should handle gracefully
        assert result is not None
        assert 'error' in result or result['sentiment'] == 'خنثی'
    @pytest.mark.unit
    def test_analyze_text_too_short(self, sentiment_service):
        """Test analyzing text that's too short"""
        result = sentiment_service.analyze_text("کوتاه")
        
        # Should handle gracefully (min length is 5)
        assert result is not None
    @pytest.mark.unit
    def test_analyze_text_very_long(self, sentiment_service):
        """Test analyzing very long text (truncation)"""
        # Create text longer than MAX_TEXT_LENGTH
        long_text = "این یک متن بسیار طولانی است " * 100
        
        result = sentiment_service.analyze_text(long_text)
        
        # Should handle truncation
        assert result is not None
    @pytest.mark.unit
    def test_analyze_batch(self, mock_sentiment_service):
        """Test batch sentiment analysis"""
        texts = [
            "متن مثبت خوب",
            "متن منفی بد",
            "متن خنثی عادی"
        ]
        
        results = mock_sentiment_service.analyze_batch(texts)
        
        assert len(results) == 3
        assert all('sentiment' in r for r in results)
    @pytest.mark.unit
    def test_analyze_batch_empty_list(self, sentiment_service):
        """Test batch analysis with empty list"""
        results = sentiment_service.analyze_batch([])
        
        assert isinstance(results, list)
        assert len(results) == 0
    @pytest.mark.unit
    def test_get_cache_stats(self, sentiment_service):
        """Test getting cache statistics"""
        stats = sentiment_service.get_cache_stats()
        
        assert isinstance(stats, dict)
        assert 'model_loaded' in stats
        assert 'available' in stats
    @pytest.mark.unit
    def test_clear_cache(self, sentiment_service):
        """Test clearing sentiment cache"""
        # Should not raise exception
        sentiment_service.clear_cache()
        
        # Cache should be empty
        stats = sentiment_service.get_cache_stats()
        assert stats['cache_size'] == 0

@pytest.mark.unit
class TestSentimentServiceActivities:
    """Test sentiment analysis on activities"""
    @pytest.mark.unit
    def test_analyze_activities_sentiment_empty(self, sentiment_service):
        """Test analyzing empty activities list"""
        result = sentiment_service.analyze_activities_sentiment([])
        
        assert result is not None
        assert result['total_activities'] == 0
        assert result['analyzed_activities'] == 0
    @pytest.mark.unit
    def test_analyze_activities_sentiment_mock(self, mock_sentiment_service, sample_activities_list):
        """Test analyzing activities with mock service"""
        result = mock_sentiment_service.analyze_activities_sentiment(
            sample_activities_list[:3]
        )
        
        # Mock should return basic structure
        assert result is not None
        assert isinstance(result, dict)
    @pytest.mark.unit
    def test_get_sentiment_trends_empty(self, sentiment_service):
        """Test getting trends with no activities"""
        result = sentiment_service.get_sentiment_trends([], days=7)
        
        assert result is not None
        assert 'trends' in result or result.get('trends') == []
    @pytest.mark.unit
    def test_get_sentiment_trends_mock(self, mock_sentiment_service, sample_activities_list):
        """Test sentiment trends with mock service"""
        result = mock_sentiment_service.get_sentiment_trends(
            sample_activities_list[:5],
            days=7
        )
        
        # Should return structure even if mocked
        assert result is not None
        assert isinstance(result, dict)

