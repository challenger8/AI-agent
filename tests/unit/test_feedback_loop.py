"""
tests/unit/test_feedback_loop.py
--------------------------------
Unit tests for feedback loop
"""

import pytest

from services.moe.feedback_loop import (
    FeedbackLoop,
    FeedbackEntry,
    get_feedback_loop
)


class TestFeedbackEntry:
    """Tests for FeedbackEntry"""

    def test_entry_creation(self):
        """Test creating feedback entry"""
        import time
        entry = FeedbackEntry(
            feedback_id="f1",
            query_id="q1",
            query="test query",
            timestamp=time.time(),
            selected_experts=['deal_analysis'],
            correct_expert='deal_analysis',
            rating=5
        )
        assert entry.feedback_id == "f1"
        assert entry.rating == 5


class TestFeedbackLoop:
    """Tests for FeedbackLoop"""

    @pytest.fixture
    def feedback(self):
        """Create fresh feedback loop instance"""
        fb = FeedbackLoop()
        fb.reset()
        return fb

    def test_initialization(self, feedback):
        """Test feedback loop initialization"""
        assert feedback is not None
        assert len(feedback._expert_stats) == 5

    def test_record_feedback(self, feedback):
        """Test recording feedback"""
        feedback_id = feedback.record_feedback(
            query_id="q1",
            query="test query",
            selected_experts=['deal_analysis'],
            rating=5
        )
        assert feedback_id is not None
        assert len(feedback._feedback_entries) == 1

    def test_positive_feedback_updates_stats(self, feedback):
        """Test positive feedback updates stats"""
        feedback.record_feedback(
            query_id="q1",
            query="deal analysis query",
            selected_experts=['deal_analysis'],
            rating=5
        )

        stats = feedback.get_expert_stats()
        assert stats['deal_analysis']['total_feedback'] == 1
        assert stats['deal_analysis']['positive_feedback'] == 1

    def test_negative_feedback_updates_stats(self, feedback):
        """Test negative feedback updates stats"""
        feedback.record_feedback(
            query_id="q1",
            query="bad query",
            selected_experts=['sentiment'],
            rating=1
        )

        stats = feedback.get_expert_stats()
        assert stats['sentiment']['total_feedback'] == 1
        assert stats['sentiment']['negative_feedback'] == 1

    def test_neutral_feedback(self, feedback):
        """Test neutral feedback"""
        feedback.record_feedback(
            query_id="q1",
            query="neutral query",
            selected_experts=['activity'],
            rating=3
        )

        stats = feedback.get_expert_stats()
        assert stats['activity']['neutral_feedback'] == 1

    def test_correct_expert_tracking(self, feedback):
        """Test tracking correct expert selections"""
        # Correct selection
        feedback.record_feedback(
            query_id="q1",
            query="deal query",
            selected_experts=['deal_analysis'],
            rating=5,
            correct_expert='deal_analysis'
        )

        stats = feedback.get_expert_stats()
        assert stats['deal_analysis']['correct_selections'] == 1

    def test_incorrect_expert_tracking(self, feedback):
        """Test tracking incorrect expert selections"""
        # Incorrect selection
        feedback.record_feedback(
            query_id="q1",
            query="deal query",
            selected_experts=['sentiment'],
            rating=2,
            correct_expert='deal_analysis'
        )

        stats = feedback.get_expert_stats()
        assert stats['sentiment']['incorrect_selections'] == 1

    def test_weight_adjustments(self, feedback):
        """Test weight adjustments from feedback"""
        # Positive feedback should increase weight
        feedback.record_feedback(
            query_id="q1",
            query="good query",
            selected_experts=['deal_analysis'],
            rating=5
        )

        adjustments = feedback.get_weight_adjustments()
        assert adjustments['deal_analysis'] > 0

    def test_negative_weight_adjustment(self, feedback):
        """Test negative weight adjustment"""
        # Negative feedback should decrease weight
        feedback.record_feedback(
            query_id="q1",
            query="bad query",
            selected_experts=['sentiment'],
            rating=1
        )

        adjustments = feedback.get_weight_adjustments()
        assert adjustments['sentiment'] < 0

    def test_get_adjusted_weights(self, feedback):
        """Test getting adjusted weights"""
        # Record some feedback
        for _ in range(5):
            feedback.record_feedback(
                query_id="q",
                query="query",
                selected_experts=['deal_analysis'],
                rating=5
            )

        weights = feedback.get_adjusted_weights()
        assert sum(weights.values()) == pytest.approx(1.0, abs=0.01)

    def test_suggest_expert_for_query(self, feedback):
        """Test expert suggestion based on patterns"""
        # Train with feedback
        for _ in range(10):
            feedback.record_feedback(
                query_id="q",
                query="analyze deal health",
                selected_experts=['deal_analysis'],
                rating=5,
                correct_expert='deal_analysis'
            )

        suggestion = feedback.suggest_expert_for_query("deal health analysis")
        # Should suggest deal_analysis based on learned patterns
        assert suggestion is not None

    def test_get_recent_feedback(self, feedback):
        """Test getting recent feedback"""
        for i in range(15):
            feedback.record_feedback(
                query_id=f"q{i}",
                query=f"query {i}",
                selected_experts=['search'],
                rating=4
            )

        recent = feedback.get_recent_feedback(limit=10)
        assert len(recent) == 10

    def test_reset(self, feedback):
        """Test resetting feedback data"""
        feedback.record_feedback(
            query_id="q1",
            query="test",
            selected_experts=['deal_analysis'],
            rating=5
        )

        feedback.reset()

        stats = feedback.get_expert_stats()
        assert stats['deal_analysis']['total_feedback'] == 0
        assert len(feedback._feedback_entries) == 0

    def test_extract_keywords(self, feedback):
        """Test keyword extraction"""
        keywords = feedback._extract_keywords("test query the keywords")
        assert 'test' in keywords
        assert 'query' in keywords
        assert 'keywords' in keywords
        # Stop words should be filtered
        assert 'the' not in keywords

    def test_average_rating(self, feedback):
        """Test average rating calculation"""
        feedback.record_feedback(
            query_id="q1",
            query="query 1",
            selected_experts=['deal_analysis'],
            rating=5
        )
        feedback.record_feedback(
            query_id="q2",
            query="query 2",
            selected_experts=['deal_analysis'],
            rating=1
        )

        stats = feedback.get_expert_stats()
        # Should be average of positive (4.5) and negative (1.5)
        assert 1.5 <= stats['deal_analysis']['avg_rating'] <= 4.5


class TestGetFeedbackLoop:
    """Tests for global feedback loop"""

    def test_get_feedback_loop_singleton(self):
        """Test global feedback loop is singleton"""
        f1 = get_feedback_loop()
        f2 = get_feedback_loop()
        assert f1 is f2
