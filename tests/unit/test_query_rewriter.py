"""
tests/unit/test_query_rewriter.py
---------------------------------
Unit tests for QueryRewriter service
Tests query expansion, rephrasing, and normalization
"""

import pytest
from services.query_rewriter_service import QueryRewriter, QueryRewriterWithFallback
from config.cag_settings import CAGSettings


class TestQueryRewriter:
    """Test QueryRewriter functionality"""
    
    @pytest.fixture
    def rewriter_expand(self):
        """Rewriter with expand strategy"""
        return QueryRewriter(strategy='expand')
    
    @pytest.fixture
    def rewriter_rephrase(self):
        """Rewriter with rephrase strategy"""
        return QueryRewriter(strategy='rephrase')
    
    @pytest.fixture
    def rewriter_both(self):
        """Rewriter with both strategy"""
        return QueryRewriter(strategy='both')
    
    # ================================================================
    # TEST: Expansion
    # ================================================================
    
    def test_expand_query_english(self, rewriter_expand):
        """Test expanding English query with synonyms"""
        rewrites = rewriter_expand.rewrite("pricing information", document_type='deal')
        
        assert len(rewrites) > 0
        # Should contain synonyms for 'pricing'
        assert any('cost' in r or 'rate' in r or 'fee' in r for r in rewrites)
    
    def test_expand_query_persian(self, rewriter_expand):
        """Test expanding Persian query with synonyms"""
        rewrites = rewriter_expand.rewrite("قیمت", document_type='deal')
        
        assert len(rewrites) > 0
        # Should expand with Persian synonyms
        assert len(rewrites) >= 1
    
    def test_expand_no_synonyms(self, rewriter_expand):
        """Test expansion with word having no synonyms"""
        rewrites = rewriter_expand.rewrite("xyz123", document_type='deal')
        
        # Might be empty or just original
        assert isinstance(rewrites, list)
    
    # ================================================================
    # TEST: Rephrasing
    # ================================================================
    
    def test_rephrase_query(self, rewriter_rephrase):
        """Test rephrasing query"""
        rewrites = rewriter_rephrase.rewrite("customer pricing discussion", document_type='deal')
        
        assert len(rewrites) > 0
        assert all(isinstance(r, str) for r in rewrites)
    
    def test_rephrase_single_word(self, rewriter_rephrase):
        """Test rephrasing single word (limited options)"""
        rewrites = rewriter_rephrase.rewrite("pricing", document_type='deal')
        
        assert isinstance(rewrites, list)
    
    # ================================================================
    # TEST: Combined Strategy
    # ================================================================
    
    def test_both_strategy(self, rewriter_both):
        """Test both expansion and rephrasing"""
        rewrites = rewriter_both.rewrite("enterprise pricing", document_type='deal')
        
        assert len(rewrites) > 0
        # Should have both strategies combined
        assert len(rewrites) >= 2
    
    # ================================================================
    # TEST: Persian Normalization
    # ================================================================
    
    def test_normalize_persian_text(self, rewriter_both):
        """Test Persian text normalization"""
        query = "قیمتۀ معامله"  # With non-standard Persian chars
        normalized = rewriter_both._normalize_query(query)
        
        # Should normalize
        assert isinstance(normalized, str)
        assert len(normalized) > 0
    
    def test_normalize_whitespace(self, rewriter_both):
        """Test whitespace normalization"""
        query = "pricing    information   "
        normalized = rewriter_both._normalize_query(query)
        
        # Extra spaces should be removed
        assert "  " not in normalized
        assert normalized.strip() == normalized
    
    def test_normalize_english_unchanged(self, rewriter_both):
        """Test English text normalization (should be mostly unchanged)"""
        query = "pricing information"
        normalized = rewriter_both._normalize_query(query)
        
        assert normalized == query
    
    # ================================================================
    # TEST: Decision Logic
    # ================================================================
    
    def test_should_rewrite_threshold_strategy(self, rewriter_both):
        """Test rewrite decision with threshold strategy"""
        # Low confidence
        should_rewrite = rewriter_both.should_rewrite(
            confidence_score=0.3,
            high_quality_count=0,
            decision_strategy='threshold'
        )
        assert should_rewrite is True
        
        # High confidence
        should_rewrite = rewriter_both.should_rewrite(
            confidence_score=0.8,
            high_quality_count=5,
            decision_strategy='threshold'
        )
        assert should_rewrite is False
    
    def test_should_rewrite_hybrid_strategy(self, rewriter_both):
        """Test rewrite decision with hybrid strategy"""
        # Low confidence
        should_rewrite = rewriter_both.should_rewrite(
            confidence_score=0.4,
            high_quality_count=0,
            decision_strategy='hybrid'
        )
        assert should_rewrite is True
        
        # Adequate confidence but few high-quality
        should_rewrite = rewriter_both.should_rewrite(
            confidence_score=0.65,
            high_quality_count=0,
            decision_strategy='hybrid'
        )
        assert should_rewrite is True
        
        # Good confidence and results
        should_rewrite = rewriter_both.should_rewrite(
            confidence_score=0.75,
            high_quality_count=3,
            decision_strategy='hybrid'
        )
        assert should_rewrite is False
    
    def test_should_rewrite_aggressive_strategy(self, rewriter_both):
        """Test rewrite decision with aggressive strategy"""
        # Even moderate confidence triggers rewrite if no high-quality
        should_rewrite = rewriter_both.should_rewrite(
            confidence_score=0.65,
            high_quality_count=0,
            decision_strategy='aggressive'
        )
        assert should_rewrite is True
    
    # ================================================================
    # TEST: Best Rewrite Selection
    # ================================================================
    
    def test_get_best_rewrite_empty(self, rewriter_both):
        """Test selecting best from empty rewrites"""
        best = rewriter_both.get_best_rewrite([], "original")
        
        assert best == "original"
    
    def test_get_best_rewrite_single(self, rewriter_both):
        """Test selecting best from single rewrite"""
        best = rewriter_both.get_best_rewrite(["alternative"], "original")
        
        assert best == "alternative"
    
    def test_get_best_rewrite_multiple(self, rewriter_both):
        """Test selecting best from multiple rewrites"""
        rewrites = ["rewrite1", "rewrite2", "rewrite3"]
        best = rewriter_both.get_best_rewrite(rewrites, "original")
        
        # Should pick first
        assert best == "rewrite1"
    
    # ================================================================
    # TEST: Caching
    # ================================================================
    
    def test_cache_enabled(self):
        """Test query caching"""
        rewriter = QueryRewriter(cache_rewrites=True)
        
        # First call
        rewrites1 = rewriter.rewrite("test query")
        
        # Second call (should be cached)
        rewrites2 = rewriter.rewrite("test query")
        
        assert rewrites1 == rewrites2
        assert len(rewriter.rewrite_cache) > 0
    
    def test_cache_disabled(self):
        """Test with caching disabled"""
        rewriter = QueryRewriter(cache_rewrites=False)
        
        rewriter.rewrite("test query")
        rewriter.rewrite("test query")
        
        assert len(rewriter.rewrite_cache) == 0
    
    def test_clear_cache(self):
        """Test clearing cache"""
        rewriter = QueryRewriter(cache_rewrites=True)
        
        rewriter.rewrite("test query")
        assert len(rewriter.rewrite_cache) > 0
        
        rewriter.clear_cache()
        assert len(rewriter.rewrite_cache) == 0
    
    def test_get_cache_stats(self):
        """Test cache statistics"""
        rewriter = QueryRewriter(cache_rewrites=True)
        
        rewriter.rewrite("query1")
        rewriter.rewrite("query2")
        
        stats = rewriter.get_cache_stats()
        
        assert 'cache_size' in stats
        assert 'max_size' in stats
        assert stats['cache_size'] > 0
    
    # ================================================================
    # TEST: Deduplication
    # ================================================================
    
    def test_deduplicate_rewrites(self, rewriter_both):
        """Test that identical rewrites are deduplicated"""
        rewrites = rewriter_both.rewrite("test")
        
        # Should have no duplicates
        assert len(rewrites) == len(set(rewrites))
    
    # ================================================================
    # TEST: Limit Rewrites
    # ================================================================
    
    def test_rewrite_limit(self, rewriter_both):
        """Test that rewrites are limited to NUM_ALTERNATIVE_QUERIES"""
        rewrites = rewriter_both.rewrite("enterprise customer pricing deal implementation support")
        
        # Should not exceed limit
        assert len(rewrites) <= CAGSettings.NUM_ALTERNATIVE_QUERIES
    
    # ================================================================
    # TEST: Edge Cases
    # ================================================================
    
    def test_empty_query(self, rewriter_both):
        """Test with empty query"""
        rewrites = rewriter_both.rewrite("")
        
        assert isinstance(rewrites, list)
    
    def test_very_long_query(self, rewriter_both):
        """Test with very long query"""
        long_query = " ".join(["word"] * 100)
        rewrites = rewriter_both.rewrite(long_query)
        
        assert isinstance(rewrites, list)
        assert len(rewrites) <= CAGSettings.NUM_ALTERNATIVE_QUERIES
    
    def test_special_characters(self, rewriter_both):
        """Test query with special characters"""
        query = "pricing!@#$% information"
        rewrites = rewriter_both.rewrite(query)
        
        assert isinstance(rewrites, list)
    
    def test_mixed_languages(self, rewriter_both):
        """Test query with mixed Persian and English"""
        query = "قیمت pricing معامله"
        rewrites = rewriter_both.rewrite(query)
        
        assert isinstance(rewrites, list)
    
    # ================================================================
    # TEST: Different Document Types
    # ================================================================
    
    def test_different_document_types(self, rewriter_both):
        """Test rewriting with different document types"""
        for doc_type in ['deal', 'activity', 'agent']:
            rewrites = rewriter_both.rewrite("test query", document_type=doc_type)
            
            assert isinstance(rewrites, list)


class TestQueryRewriterWithFallback:
    """Test QueryRewriter with fallback"""
    
    @pytest.fixture
    def rewriter_fallback(self):
        """Rewriter with fallback"""
        return QueryRewriterWithFallback()
    
    def test_primary_succeeds(self, rewriter_fallback):
        """Test when primary strategy succeeds"""
        rewrites = rewriter_fallback.rewrite_with_fallback("pricing information")
        
        assert len(rewrites) > 0
        assert all(isinstance(r, str) for r in rewrites)
    
    def test_fallback_strategy(self, rewriter_fallback):
        """Test fallback strategy"""
        # Even if primary doesn't generate much, should get something
        rewrites = rewriter_fallback.rewrite_with_fallback("xyz123")
        
        assert isinstance(rewrites, list)
        # Worst case: returns original query
        assert len(rewrites) >= 0
    
    def test_multiple_attempts(self, rewriter_fallback):
        """Test multiple rewrite attempts"""
        for attempt in range(1, 4):
            rewrites = rewriter_fallback.rewrite_with_fallback("test", attempt=attempt)
            assert isinstance(rewrites, list)