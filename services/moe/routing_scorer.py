"""
services/moe/routing_scorer.py
-------------------------------
Scoring logic for expert routing.

Extracted from ExpertRouter to improve separation of concerns (SRP).
"""

import re
from typing import Any, Dict
from config.moe_settings import MoESettings
from config.routing_constants import RoutingConstants
from utils.logging_config import get_logger


class RoutingScorer:
    """
    Calculates confidence scores for expert routing.

    Responsibilities:
    - Calculate keyword-based scores
    - Apply context boosts
    - Apply pattern matching boosts
    - Blend semantic similarity scores
    """

    def __init__(self, embedding_service=None):
        """
        Initialize routing scorer.

        Args:
            embedding_service: Optional embedding service for semantic scoring
        """
        self.logger = get_logger(self.__class__.__name__)
        self.embedding_service = embedding_service

    def calculate_keyword_scores(self, query_lower: str) -> Dict[str, float]:
        """
        Calculate expert scores based on keyword matching.

        Args:
            query_lower: Lowercased query string

        Returns:
            Dictionary of expert -> confidence score
        """
        confidence_scores = {}

        for expert_type, keywords in MoESettings.ROUTING_KEYWORDS.items():
            score = 0.0

            for keyword in keywords:
                if keyword.lower() in query_lower:
                    score += 1.0

            # Normalize using named constant
            if keywords:
                score = min(
                    score / len(keywords) * RoutingConstants.KEYWORD_SCORE_MULTIPLIER,
                    RoutingConstants.MAX_KEYWORD_SCORE
                )

            confidence_scores[expert_type] = score

        return confidence_scores

    def apply_context_boosts(
        self,
        scores: Dict[str, float],
        context: Dict[str, Any]
    ) -> Dict[str, float]:
        """
        Apply context-based boosts to confidence scores.

        Args:
            scores: Current confidence scores
            context: Context dictionary

        Returns:
            Updated confidence scores
        """
        if not context:
            return scores

        # Boost based on explicit hints
        if 'expert_hint' in context:
            hint = context['expert_hint']
            if hint in scores:
                scores[hint] = min(
                    scores[hint] + RoutingConstants.EXPERT_HINT_BOOST,
                    RoutingConstants.MAX_KEYWORD_SCORE
                )

        # Boost based on entity type
        if 'entity_type' in context:
            entity = context['entity_type']
            if entity == 'deal' and 'deal_analysis' in scores:
                scores['deal_analysis'] = min(
                    scores.get('deal_analysis', 0) + RoutingConstants.ENTITY_TYPE_BOOST,
                    RoutingConstants.MAX_KEYWORD_SCORE
                )
            elif entity == 'activity' and 'activity' in scores:
                scores['activity'] = min(
                    scores.get('activity', 0) + RoutingConstants.ENTITY_TYPE_BOOST,
                    RoutingConstants.MAX_KEYWORD_SCORE
                )

        # Boost based on previous expert success
        if 'last_successful_expert' in context:
            last_expert = context['last_successful_expert']
            if last_expert in scores:
                scores[last_expert] = min(
                    scores[last_expert] + RoutingConstants.LAST_SUCCESSFUL_BOOST,
                    RoutingConstants.MAX_KEYWORD_SCORE
                )

        return scores

    def apply_pattern_boosts(
        self,
        scores: Dict[str, float],
        query_lower: str
    ) -> Dict[str, float]:
        """
        Apply pattern matching boosts to confidence scores.

        Args:
            scores: Current confidence scores
            query_lower: Lowercased query string

        Returns:
            Updated confidence scores
        """
        patterns = getattr(MoESettings, 'ROUTING_PATTERNS', {})

        for expert_type, expert_patterns in patterns.items():
            for pattern in expert_patterns:
                if re.search(pattern, query_lower):
                    scores[expert_type] = min(
                        scores.get(expert_type, 0) + RoutingConstants.PATTERN_MATCH_BOOST,
                        RoutingConstants.MAX_KEYWORD_SCORE
                    )

        return scores

    def blend_semantic_scores(
        self,
        scores: Dict[str, float],
        query: str
    ) -> Dict[str, float]:
        """
        Blend rule-based scores with semantic similarity scores.

        Args:
            scores: Current confidence scores
            query: Query string

        Returns:
            Blended confidence scores
        """
        if not self.embedding_service:
            return scores

        try:
            semantic_scores = self.embedding_service.get_expert_similarities(query)
            for expert_type, semantic_score in semantic_scores.items():
                if expert_type in scores:
                    # Blend using named constants
                    blended = (
                        RoutingConstants.RULE_BASED_WEIGHT * scores[expert_type] +
                        RoutingConstants.SEMANTIC_WEIGHT * semantic_score
                    )
                    scores[expert_type] = min(blended, RoutingConstants.MAX_KEYWORD_SCORE)
        except Exception as e:
            self.logger.warning(f"Embedding scoring failed: {e}")

        return scores

    def calculate_hybrid_scores(
        self,
        query: str,
        context: Dict[str, Any]
    ) -> Dict[str, float]:
        """
        Calculate hybrid scores combining all strategies.

        Convenience method that applies all scoring strategies in sequence.

        Args:
            query: Query string
            context: Context dictionary

        Returns:
            Final confidence scores
        """
        query_lower = query.lower()

        # Step 1: Calculate keyword scores
        scores = self.calculate_keyword_scores(query_lower)

        # Step 2: Apply context boosts
        scores = self.apply_context_boosts(scores, context)

        # Step 3: Apply pattern matching boosts
        scores = self.apply_pattern_boosts(scores, query_lower)

        # Step 4: Blend with semantic scores (if available)
        scores = self.blend_semantic_scores(scores, query)

        return scores
