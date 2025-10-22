"""
tests/unit/test_relevance_scorer.py
-----------------------------------
Unit tests for RelevanceScorer service
Tests scoring logic, thresholds, and batch operations
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock

from services.relevance_scorer_service import RelevanceScorer, RelevanceScore
from config.cag_settings import CAGSettings


class TestRelevanceScorer:
    """Test RelevanceScorer functionality"""
    
    @pytest.fixture
    def scorer(self):
        """Initialize scorer with default settings"""
        return RelevanceScorer(confidence_threshold=0.6)
    
    @pytest.fixture
    def sample_document(self):
        """Sample document for testing"""
        return {
            'id': 'deal_1',
            'text': 'Enterprise software pricing discussion',
            'similarity': 0.85,
            'metadata': {
                'title': 'Enterprise Deal',
                'status': 'open',
                'customer_name': 'Tech Corp',
                'type': 'deal',
                'created_at': (datetime.now() - timedelta(days=1)).isoformat()
            }
        }
    
    @pytest.fixture
    def low_quality_document(self):
        """Low-quality document for testing"""
        return {
            'id': 'deal_2',
            'text': 'Random text about something',
            'similarity': 0.35,
            'metadata': {
                'title': 'Old Deal',
                'status': 'closed',
                'type': 'deal',
                'created_at': (datetime.now() - timedelta(days=365)).isoformat()
            }
        }
    
    # ================================================================
    # TEST: Document Scoring
    # ================================================================
    
    def test_score_high_quality_document(self, scorer, sample_document):
        """Test scoring a high-quality document"""
        score = scorer.score_document(sample_document, query="pricing enterprise", document_type='deal')
        
        assert isinstance(score, RelevanceScore)
        assert score.document_id == 'deal_1'
        assert score.similarity_score == 0.85
        assert score.overall_score >= 0.6
        assert score.meets_threshold is True
        assert score.confidence_label in ['high', 'medium']
    
    def test_score_low_quality_document(self, scorer, low_quality_document):
        """Test scoring a low-quality document"""
        score = scorer.score_document(low_quality_document, query="pricing", document_type='deal')
        
        assert isinstance(score, RelevanceScore)
        assert score.similarity_score == 0.35
        assert score.overall_score < 0.7
        assert score.reasoning is not None
        assert len(score.reasoning) > 0
    
    def test_similarity_component(self, scorer, sample_document):
        """Test similarity score calculation"""
        score = scorer.score_document(sample_document, query="pricing", document_type='deal')
        
        # High similarity should be major component
        assert score.similarity_score == 0.85
        # Overall should be influenced by high similarity
        assert score.overall_score > 0.5
    
    def test_metadata_relevance_component(self, scorer):
        """Test metadata relevance calculation"""
        doc = {
            'id': 'test_1',
            'text': 'Test text',
            'similarity': 0.5,
            'metadata': {
                'title': 'pricing consultation',
                'customer_name': 'enterprise client',
                'type': 'deal'
            }
        }
        
        score = scorer.score_document(doc, query="pricing enterprise consultation", document_type='deal')
        
        # Multiple metadata matches should boost score
        assert score.metadata_relevance > 0.0
        assert score.overall_score >= score.similarity_score  # Metadata should help
    
    def test_recency_score_very_recent(self, scorer):
        """Test recency scoring for very recent documents"""
        doc = {
            'id': 'recent_1',
            'text': 'Recent deal',
            'similarity': 0.6,
            'metadata': {
                'title': 'Recent Deal',
                'updated_at': (datetime.now() - timedelta(days=1)).isoformat(),
                'type': 'deal'
            }
        }
        
        score = scorer.score_document(doc, query="deal", document_type='deal')
        
        # Should get recency boost
        assert score.reasoning is not None
        assert 'recent' in score.reasoning.lower()
    
    def test_recency_score_old_document(self, scorer):
        """Test recency scoring for old documents"""
        doc = {
            'id': 'old_1',
            'text': 'Old deal',
            'similarity': 0.6,
            'metadata': {
                'title': 'Old Deal',
                'updated_at': (datetime.now() - timedelta(days=400)).isoformat(),
                'type': 'deal'
            }
        }
        
        score = scorer.score_document(doc, query="deal", document_type='deal')
        
        # Should mention old in reasoning
        assert score.reasoning is not None
    
    def test_metadata_type_matching(self, scorer):
        """Test type matching in metadata"""
        doc_deal = {
            'id': 'test_deal',
            'text': 'Test',
            'similarity': 0.5,
            'metadata': {'type': 'deal', 'title': 'Deal'}
        }
        
        doc_activity = {
            'id': 'test_activity',
            'text': 'Test',
            'similarity': 0.5,
            'metadata': {'type': 'activity', 'title': 'Activity'}
        }
        
        score_deal = scorer.score_document(doc_deal, query="test", document_type='deal')
        score_activity = scorer.score_document(doc_activity, query="test", document_type='deal')
        
        # Deal should score higher when document_type matches
        assert score_deal.overall_score > score_activity.overall_score
    
    # ================================================================
    # TEST: Confidence Labels
    # ================================================================
    
    def test_confidence_label_high(self, scorer):
        """Test high confidence label"""
        label = scorer._get_confidence_label(0.85)
        assert label == 'high'
    
    def test_confidence_label_medium(self, scorer):
        """Test medium confidence label"""
        label = scorer._get_confidence_label(0.60)
        assert label == 'medium'
    
    def test_confidence_label_low(self, scorer):
        """Test low confidence label"""
        label = scorer._get_confidence_label(0.40)
        assert label == 'low'
    
    # ================================================================
    # TEST: Batch Scoring
    # ================================================================
    
    def test_score_batch(self, scorer, sample_document, low_quality_document):
        """Test batch scoring multiple documents"""
        documents = [sample_document, low_quality_document]
        
        scores = scorer.score_batch(documents, query="pricing enterprise", document_type='deal')
        
        assert len(scores) == 2
        assert all(isinstance(s, RelevanceScore) for s in scores)
        # First should be higher quality
        assert scores[0].overall_score > scores[1].overall_score
    
    def test_batch_empty_list(self, scorer):
        """Test batch scoring with empty list"""
        scores = scorer.score_batch([], query="test")
        
        assert scores == []
    
    # ================================================================
    # TEST: Filtering by Threshold
    # ================================================================
    
    def test_filter_by_threshold(self, scorer):
        """Test filtering documents by confidence threshold"""
        # Create mock scores
        high_score = RelevanceScore(
            document_id='high',
            text='High quality',
            similarity_score=0.9,
            metadata_relevance=0.8,
            overall_score=0.85,
            confidence_label='high',
            meets_threshold=True,
            reasoning='Good match'
        )
        
        low_score = RelevanceScore(
            document_id='low',
            text='Low quality',
            similarity_score=0.3,
            metadata_relevance=0.2,
            overall_score=0.25,
            confidence_label='low',
            meets_threshold=False,
            reasoning='Poor match'
        )
        
        scores = [high_score, low_score]
        high_quality, low_quality = scorer.filter_by_threshold(scores)
        
        assert len(high_quality) == 1
        assert len(low_quality) == 1
        assert high_quality[0].document_id == 'high'
        assert low_quality[0].document_id == 'low'
    
    def test_filter_all_pass_threshold(self, scorer):
        """Test filtering when all pass threshold"""
        score1 = RelevanceScore(
            document_id='1', text='', similarity_score=0.8,
            metadata_relevance=0.7, overall_score=0.75,
            confidence_label='high', meets_threshold=True, reasoning=''
        )
        score2 = RelevanceScore(
            document_id='2', text='', similarity_score=0.7,
            metadata_relevance=0.6, overall_score=0.65,
            confidence_label='medium', meets_threshold=True, reasoning=''
        )
        
        high_quality, low_quality = scorer.filter_by_threshold([score1, score2])
        
        assert len(high_quality) == 2
        assert len(low_quality) == 0
    
    def test_filter_all_fail_threshold(self, scorer):
        """Test filtering when all fail threshold"""
        score1 = RelevanceScore(
            document_id='1', text='', similarity_score=0.3,
            metadata_relevance=0.2, overall_score=0.25,
            confidence_label='low', meets_threshold=False, reasoning=''
        )
        score2 = RelevanceScore(
            document_id='2', text='', similarity_score=0.4,
            metadata_relevance=0.3, overall_score=0.35,
            confidence_label='low', meets_threshold=False, reasoning=''
        )
        
        high_quality, low_quality = scorer.filter_by_threshold([score1, score2])
        
        assert len(high_quality) == 0
        assert len(low_quality) == 2
    
    # ================================================================
    # TEST: Batch Statistics
    # ================================================================
    
    def test_average_confidence_mixed(self, scorer):
        """Test average confidence with mixed quality scores"""
        scores = [
            RelevanceScore(
                document_id='high', text='', similarity_score=0.9,
                metadata_relevance=0.85, overall_score=0.87,
                confidence_label='high', meets_threshold=True, reasoning=''
            ),
            RelevanceScore(
                document_id='med', text='', similarity_score=0.6,
                metadata_relevance=0.6, overall_score=0.6,
                confidence_label='medium', meets_threshold=True, reasoning=''
            ),
            RelevanceScore(
                document_id='low', text='', similarity_score=0.3,
                metadata_relevance=0.2, overall_score=0.25,
                confidence_label='low', meets_threshold=False, reasoning=''
            )
        ]
        
        stats = scorer.get_average_confidence(scores)
        
        assert 'average_score' in stats
        assert 'max_score' in stats
        assert 'min_score' in stats
        assert stats['high_confidence_count'] == 1
        assert stats['medium_confidence_count'] == 1
        assert stats['low_confidence_count'] == 1
        assert stats['pass_rate'] == pytest.approx(2/3, rel=0.01)
    
    def test_average_confidence_empty(self, scorer):
        """Test average confidence with empty list"""
        stats = scorer.get_average_confidence([])
        
        assert stats['average_score'] == 0.0
        assert stats['pass_rate'] == 0.0
        assert stats['high_confidence_count'] == 0
    
    def test_average_confidence_all_high(self, scorer):
        """Test average confidence with all high scores"""
        scores = [
            RelevanceScore(
                document_id=f'doc_{i}', text='', similarity_score=0.9,
                metadata_relevance=0.85, overall_score=0.87,
                confidence_label='high', meets_threshold=True, reasoning=''
            )
            for i in range(3)
        ]
        
        stats = scorer.get_average_confidence(scores)
        
        assert stats['pass_rate'] == 1.0
        assert stats['high_confidence_count'] == 3
        assert stats['average_score'] == pytest.approx(0.87, rel=0.01)
    
    # ================================================================
    # TEST: Threshold Management
    # ================================================================
    
    def test_set_valid_threshold(self, scorer):
        """Test setting valid threshold"""
        scorer.set_threshold(0.75)
        
        assert scorer.confidence_threshold == 0.75
    
    def test_set_invalid_threshold_too_high(self, scorer):
        """Test setting threshold > 1.0"""
        with pytest.raises(ValueError):
            scorer.set_threshold(1.5)
    
    def test_set_invalid_threshold_negative(self, scorer):
        """Test setting negative threshold"""
        with pytest.raises(ValueError):
            scorer.set_threshold(-0.5)
    
    def test_threshold_affects_meets_threshold(self):
        """Test that threshold setting affects scoring"""
        doc = {
            'id': 'test',
            'text': 'test',
            'similarity': 0.75,
            'metadata': {'title': 'Test Deal', 'customer_name': 'Test Company'}
        }
        
        # Low threshold - should pass
        scorer_low = RelevanceScorer(confidence_threshold=0.5)
        score_low = scorer_low.score_document(doc, query="test deal", document_type='deal')
        
        # High threshold - should fail
        scorer_high = RelevanceScorer(confidence_threshold=0.85)
        score_high = scorer_high.score_document(doc, query="test deal", document_type='deal')
        
        # Both have same overall score but different pass status
        assert score_low.overall_score == score_high.overall_score
        assert score_low.meets_threshold is True  # Passes low threshold
        assert score_high.meets_threshold is False  # Fails high threshold
        assert score_low.meets_threshold != score_high.meets_threshold
    
    # ================================================================
    # TEST: Edge Cases
    # ================================================================
    
    def test_missing_metadata_fields(self, scorer):
        """Test scoring with missing metadata"""
        doc = {
            'id': 'sparse_doc',
            'text': 'Minimal metadata',
            'similarity': 0.7,
            'metadata': {}  # Empty metadata
        }
        
        # Should not crash
        score = scorer.score_document(doc, query="test", document_type='deal')
        
        assert score.overall_score >= 0.0
        assert score.overall_score <= 1.0
    
    def test_missing_date_fields(self, scorer):
        """Test recency calculation with missing dates"""
        doc = {
            'id': 'no_date',
            'text': 'No date info',
            'similarity': 0.7,
            'metadata': {'title': 'No Date Deal', 'type': 'deal'}
        }
        
        score = scorer.score_document(doc, query="deal", document_type='deal')
        
        # Should still work, recency defaults to 0.5
        assert score.overall_score > 0.0
    
    def test_invalid_date_format(self, scorer):
        """Test with invalid date format in metadata"""
        doc = {
            'id': 'bad_date',
            'text': 'Bad date',
            'similarity': 0.7,
            'metadata': {
                'title': 'Bad Date Deal',
                'updated_at': 'not-a-date',
                'type': 'deal'
            }
        }
        
        # Should not crash
        score = scorer.score_document(doc, query="deal", document_type='deal')
        
        assert score.overall_score >= 0.0
    
    def test_unicode_query_and_text(self, scorer):
        """Test with Persian/Unicode text"""
        doc = {
            'id': 'persian_doc',
            'text': 'معامله قیمت داری',  # Persian: "pricing deal"
            'similarity': 0.8,
            'metadata': {
                'title': 'معامله تجاری',  # Persian: "business deal"
                'type': 'deal'
            }
        }
        
        score = scorer.score_document(doc, query="قیمت", document_type='deal')
        
        assert score.overall_score >= 0.0
        assert score.document_id == 'persian_doc'