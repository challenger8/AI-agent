"""
services/moe/feedback_loop.py
-----------------------------
Feedback loop for learning and improving routing decisions
"""

import json
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from threading import Lock

from config.moe_settings import MoESettings
from utils.logging_config import get_logger


@dataclass
class FeedbackEntry:
    """Feedback entry for a query"""
    feedback_id: str
    query_id: str
    query: str
    timestamp: float
    selected_experts: List[str]
    correct_expert: Optional[str]
    rating: int  # 1-5
    comments: str = ""
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExpertFeedbackStats:
    """Aggregated feedback stats for an expert"""
    expert_type: str
    total_feedback: int = 0
    positive_feedback: int = 0  # rating >= 4
    negative_feedback: int = 0  # rating <= 2
    neutral_feedback: int = 0   # rating == 3
    avg_rating: float = 0.0
    correct_selections: int = 0
    incorrect_selections: int = 0


class FeedbackLoop:
    """Feedback loop for improving MoE routing"""

    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)
        self._lock = Lock()

        # Feedback storage
        self._feedback_entries: List[FeedbackEntry] = []
        self._max_entries = 5000

        # Expert stats
        self._expert_stats: Dict[str, ExpertFeedbackStats] = {}
        for expert_type in MoESettings.EXPERT_TYPES:
            self._expert_stats[expert_type] = ExpertFeedbackStats(expert_type=expert_type)

        # Query pattern learning
        self._query_patterns: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))

        # Weight adjustments
        self._weight_adjustments: Dict[str, float] = {
            expert: 0.0 for expert in MoESettings.EXPERT_TYPES
        }

        # Load existing feedback if available
        self._load_feedback()

    def record_feedback(
        self,
        query_id: str,
        query: str,
        selected_experts: List[str],
        rating: int,
        correct_expert: str = None,
        comments: str = "",
        context: Dict[str, Any] = None
    ) -> str:
        """
        Record feedback for a query

        Args:
            query_id: ID of the query
            query: Original query text
            selected_experts: Experts that were selected
            rating: Rating 1-5
            correct_expert: Which expert should have been used
            comments: User comments
            context: Additional context

        Returns:
            Feedback ID
        """
        import uuid
        feedback_id = str(uuid.uuid4())[:8]

        entry = FeedbackEntry(
            feedback_id=feedback_id,
            query_id=query_id,
            query=query,
            timestamp=time.time(),
            selected_experts=selected_experts,
            correct_expert=correct_expert,
            rating=rating,
            comments=comments,
            context=context or {}
        )

        with self._lock:
            # Store entry
            self._feedback_entries.append(entry)

            # Trim if needed
            if len(self._feedback_entries) > self._max_entries:
                self._feedback_entries = self._feedback_entries[-self._max_entries:]

            # Update expert stats
            self._update_expert_stats(entry)

            # Learn query patterns
            self._learn_from_feedback(entry)

            # Adjust weights
            self._adjust_weights(entry)

        self.logger.info(f"Recorded feedback {feedback_id} for query: {query[:30]}...")

        return feedback_id

    def _update_expert_stats(self, entry: FeedbackEntry):
        """Update expert statistics from feedback"""
        for expert in entry.selected_experts:
            if expert in self._expert_stats:
                stats = self._expert_stats[expert]
                stats.total_feedback += 1

                if entry.rating >= 4:
                    stats.positive_feedback += 1
                elif entry.rating <= 2:
                    stats.negative_feedback += 1
                else:
                    stats.neutral_feedback += 1

                # Update average rating
                total = stats.positive_feedback + stats.negative_feedback + stats.neutral_feedback
                stats.avg_rating = (
                    (stats.positive_feedback * 4.5 +
                     stats.neutral_feedback * 3.0 +
                     stats.negative_feedback * 1.5) / total
                )

                # Track correct/incorrect selections
                if entry.correct_expert:
                    if expert == entry.correct_expert:
                        stats.correct_selections += 1
                    else:
                        stats.incorrect_selections += 1

    def _learn_from_feedback(self, entry: FeedbackEntry):
        """Learn query patterns from feedback"""
        # Extract keywords from query
        keywords = self._extract_keywords(entry.query)

        # Determine the best expert for this query
        best_expert = entry.correct_expert or (
            entry.selected_experts[0] if entry.rating >= 4 else None
        )

        if best_expert and keywords:
            for keyword in keywords:
                self._query_patterns[keyword][best_expert] += 1

    def _extract_keywords(self, query: str) -> List[str]:
        """Extract keywords from query"""
        import re
        # Simple keyword extraction - split and filter
        words = re.findall(r'\w+', query.lower())
        # Filter out common stop words
        stop_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'in', 'on', 'at', 'to', 'for'}
        return [w for w in words if w not in stop_words and len(w) > 2]

    def _adjust_weights(self, entry: FeedbackEntry):
        """Adjust expert weights based on feedback"""
        adjustment_factor = 0.01  # Small adjustments

        for expert in entry.selected_experts:
            if expert in self._weight_adjustments:
                if entry.rating >= 4:
                    # Positive feedback - increase weight
                    self._weight_adjustments[expert] += adjustment_factor
                elif entry.rating <= 2:
                    # Negative feedback - decrease weight
                    self._weight_adjustments[expert] -= adjustment_factor

                # Clamp adjustments
                self._weight_adjustments[expert] = max(
                    -0.1,
                    min(0.1, self._weight_adjustments[expert])
                )

    def get_weight_adjustments(self) -> Dict[str, float]:
        """
        Get current weight adjustments

        Returns:
            Dictionary of expert -> adjustment
        """
        with self._lock:
            return self._weight_adjustments.copy()

    def get_adjusted_weights(self) -> Dict[str, float]:
        """
        Get weights with adjustments applied

        Returns:
            Adjusted weights
        """
        base_weights = MoESettings.DEFAULT_EXPERT_WEIGHTS.copy()

        with self._lock:
            for expert, adjustment in self._weight_adjustments.items():
                if expert in base_weights:
                    base_weights[expert] = max(0.05, min(0.5, base_weights[expert] + adjustment))

        # Normalize to sum to 1
        total = sum(base_weights.values())
        return {k: v / total for k, v in base_weights.items()}

    def suggest_expert_for_query(self, query: str) -> Optional[str]:
        """
        Suggest best expert based on learned patterns

        Args:
            query: Input query

        Returns:
            Suggested expert type or None
        """
        keywords = self._extract_keywords(query)

        if not keywords:
            return None

        # Count votes for each expert
        expert_votes: Dict[str, int] = defaultdict(int)

        with self._lock:
            for keyword in keywords:
                if keyword in self._query_patterns:
                    for expert, count in self._query_patterns[keyword].items():
                        expert_votes[expert] += count

        if not expert_votes:
            return None

        # Return expert with most votes
        return max(expert_votes.items(), key=lambda x: x[1])[0]

    def get_expert_stats(self) -> Dict[str, Dict[str, Any]]:
        """
        Get feedback statistics for all experts

        Returns:
            Expert statistics
        """
        with self._lock:
            return {
                expert_type: {
                    'total_feedback': stats.total_feedback,
                    'positive_feedback': stats.positive_feedback,
                    'negative_feedback': stats.negative_feedback,
                    'neutral_feedback': stats.neutral_feedback,
                    'avg_rating': stats.avg_rating,
                    'correct_selections': stats.correct_selections,
                    'incorrect_selections': stats.incorrect_selections,
                    'accuracy': (
                        stats.correct_selections /
                        (stats.correct_selections + stats.incorrect_selections)
                        if (stats.correct_selections + stats.incorrect_selections) > 0
                        else 0.0
                    )
                }
                for expert_type, stats in self._expert_stats.items()
            }

    def get_recent_feedback(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent feedback entries

        Args:
            limit: Maximum entries to return

        Returns:
            List of feedback entries
        """
        with self._lock:
            entries = self._feedback_entries[-limit:]
            return [
                {
                    'feedback_id': e.feedback_id,
                    'query': e.query[:50] + '...' if len(e.query) > 50 else e.query,
                    'selected_experts': e.selected_experts,
                    'correct_expert': e.correct_expert,
                    'rating': e.rating,
                    'timestamp': datetime.fromtimestamp(e.timestamp).isoformat()
                }
                for e in entries
            ]

    def export_feedback(self, filepath: str = None) -> str:
        """
        Export feedback data to JSON

        Args:
            filepath: Output file path

        Returns:
            Path to exported file
        """
        if filepath is None:
            filepath = MoESettings.METRICS_DIR / f"feedback_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        data = {
            'export_timestamp': datetime.now().isoformat(),
            'total_entries': len(self._feedback_entries),
            'expert_stats': self.get_expert_stats(),
            'weight_adjustments': self._weight_adjustments,
            'query_patterns': dict(self._query_patterns)
        }

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

        self.logger.info(f"Exported feedback to {filepath}")
        return str(filepath)

    def _load_feedback(self):
        """Load existing feedback from file"""
        feedback_file = MoESettings.METRICS_DIR / "feedback_latest.json"
        if feedback_file.exists():
            try:
                with open(feedback_file) as f:
                    data = json.load(f)
                    self._weight_adjustments = data.get('weight_adjustments', self._weight_adjustments)
                    self.logger.info(f"Loaded feedback from {feedback_file}")
            except Exception as e:
                self.logger.warning(f"Failed to load feedback: {e}")

    def save_feedback(self):
        """Save current feedback state"""
        filepath = MoESettings.METRICS_DIR / "feedback_latest.json"
        self.export_feedback(str(filepath))

    def reset(self):
        """Reset all feedback data"""
        with self._lock:
            self._feedback_entries.clear()
            for stats in self._expert_stats.values():
                stats.total_feedback = 0
                stats.positive_feedback = 0
                stats.negative_feedback = 0
                stats.neutral_feedback = 0
                stats.avg_rating = 0.0
                stats.correct_selections = 0
                stats.incorrect_selections = 0
            self._query_patterns.clear()
            self._weight_adjustments = {
                expert: 0.0 for expert in MoESettings.EXPERT_TYPES
            }

        self.logger.info("Feedback data reset")


# Global feedback loop instance
_feedback_loop: Optional[FeedbackLoop] = None


def get_feedback_loop() -> FeedbackLoop:
    """Get global feedback loop instance"""
    global _feedback_loop
    if _feedback_loop is None:
        _feedback_loop = FeedbackLoop()
    return _feedback_loop
