"""
services/moe/expert_router_refactored.py
-----------------------------------------
REFACTORED: Simplified expert router with KISS principle

Changes:
- Extracted magic numbers to named constants
- Broke down complex _route_hybrid() into smaller methods
- Improved readability and maintainability
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple
from datetime import datetime
import re
from services.cache_service import generate_cache_key

from config.moe_settings import MoESettings
from config.routing_constants import RoutingConstants
from utils.logging_config import get_logger


@dataclass
class RoutingDecision:
    """Routing decision result"""
    query: str
    selected_experts: List[str]
    confidence_scores: Dict[str, float]
    query_type: str
    reasoning: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'query': self.query,
            'selected_experts': self.selected_experts,
            'confidence_scores': self.confidence_scores,
            'query_type': self.query_type,
            'reasoning': self.reasoning,
            'timestamp': self.timestamp.isoformat(),
            'metadata': self.metadata
        }

    @property
    def primary_expert(self) -> str:
        """Get the primary (highest confidence) expert"""
        if not self.selected_experts:
            return MoESettings.DEFAULT_EXPERT
        return self.selected_experts[0]

    @property
    def is_multi_expert(self) -> bool:
        """Check if multiple experts were selected"""
        return len(self.selected_experts) > 1


class ExpertRouter:
    """
    Routes queries to appropriate experts using hybrid strategy.

    REFACTORED: Simplified with KISS principle
    - Extracted magic numbers to RoutingConstants
    - Broke down complex methods into focused helpers
    - Improved code clarity
    """

    def __init__(self, embedding_service=None):
        """
        Initialize expert router

        Args:
            embedding_service: Optional embedding service for semantic routing
        """
        self.logger = get_logger(self.__class__.__name__)
        self.embedding_service = embedding_service
        self._routing_cache = {}
        self._metrics = {
            'total_routes': 0,
            'single_expert_routes': 0,
            'multi_expert_routes': 0,
            'fallback_routes': 0,
            'by_expert': {expert: 0 for expert in MoESettings.EXPERT_TYPES}
        }

    def route(self, query: str, context: Dict[str, Any] = None) -> RoutingDecision:
        """
        Route query to appropriate expert(s)

        Args:
            query: Input query
            context: Additional context

        Returns:
            RoutingDecision with selected experts
        """
        context = context or {}

        # Check cache
        cache_key = self._get_cache_key(query, context)
        if cache_key in self._routing_cache:
            self.logger.debug(f"Routing cache hit for query: {query[:50]}...")
            return self._routing_cache[cache_key]

        self._metrics['total_routes'] += 1

        # Determine routing strategy
        strategy = MoESettings.ROUTING_STRATEGY

        if strategy == 'rule_based':
            decision = self._route_rule_based(query, context)
        elif strategy == 'embedding_based':
            decision = self._route_embedding_based(query, context)
        else:  # hybrid
            decision = self._route_hybrid(query, context)

        # Update metrics
        self._update_metrics(decision)

        # Cache decision
        if MoESettings.CACHE_EXPERT_RESULTS:
            self._routing_cache[cache_key] = decision

        return decision

    def _route_rule_based(self, query: str, context: Dict[str, Any]) -> RoutingDecision:
        """Rule-based routing using keywords"""
        query_lower = query.lower()

        # Calculate keyword scores
        confidence_scores = self._calculate_keyword_scores(query_lower)

        # Select experts above threshold
        selected_experts, query_type = self._select_experts(confidence_scores)

        reasoning = f"Rule-based routing selected {len(selected_experts)} expert(s) based on keyword matching"

        return RoutingDecision(
            query=query,
            selected_experts=selected_experts,
            confidence_scores=confidence_scores,
            query_type=query_type,
            reasoning=reasoning,
            metadata={'strategy': 'rule_based'}
        )

    def _route_embedding_based(self, query: str, context: Dict[str, Any]) -> RoutingDecision:
        """Embedding-based routing using semantic similarity"""
        if not self.embedding_service:
            # No embedding service, fall back to rule-based
            self.logger.warning("No embedding service available, falling back to rule-based routing")
            return self._route_rule_based(query, context)

        # Get semantic similarity scores from embedding service
        confidence_scores = self.embedding_service.get_expert_similarities(query)

        # Apply context boosting
        confidence_scores = self._apply_context_boosts(confidence_scores, context)

        # Select experts above threshold
        selected_experts, query_type = self._select_experts(confidence_scores)

        reasoning = (
            f"Embedding-based routing selected {len(selected_experts)} expert(s) "
            f"based on semantic similarity"
        )

        return RoutingDecision(
            query=query,
            selected_experts=selected_experts,
            confidence_scores=confidence_scores,
            query_type=query_type,
            reasoning=reasoning,
            metadata={'strategy': 'embedding_based'}
        )

    def _route_hybrid(self, query: str, context: Dict[str, Any]) -> RoutingDecision:
        """
        Hybrid routing combining multiple strategies.

        REFACTORED: Simplified by delegating to focused helper methods
        """
        query_lower = query.lower()

        # Step 1: Calculate keyword scores
        confidence_scores = self._calculate_keyword_scores(query_lower)

        # Step 2: Apply context boosts
        confidence_scores = self._apply_context_boosts(confidence_scores, context)

        # Step 3: Apply pattern matching boosts
        confidence_scores = self._apply_pattern_boosts(confidence_scores, query_lower)

        # Step 4: Blend with semantic scores (if available)
        confidence_scores = self._blend_semantic_scores(confidence_scores, query)

        # Select experts
        selected_experts, query_type = self._select_experts(confidence_scores)

        reasoning = (
            f"Hybrid routing selected {len(selected_experts)} expert(s) "
            f"based on keywords, patterns, and context"
        )

        return RoutingDecision(
            query=query,
            selected_experts=selected_experts,
            confidence_scores=confidence_scores,
            query_type=query_type,
            reasoning=reasoning,
            metadata={'strategy': 'hybrid'}
        )

    # ========================================================================
    # REFACTORED: Helper methods extracted from complex _route_hybrid()
    # ========================================================================

    def _calculate_keyword_scores(self, query_lower: str) -> Dict[str, float]:
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

    def _apply_context_boosts(
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

    def _apply_pattern_boosts(
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

    def _blend_semantic_scores(
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

    # ========================================================================
    # Expert selection and metrics
    # ========================================================================

    def _select_experts(self, confidence_scores: Dict[str, float]) -> Tuple[List[str], str]:
        """
        Select experts based on confidence scores.

        FIXED: When no expert meets threshold, select highest scoring
        expert instead of hardcoded default.

        Returns:
            Tuple of (selected_experts list, query_type)
        """
        # Sort by confidence (highest first)
        sorted_experts = sorted(
            confidence_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )

        threshold = MoESettings.ROUTING_CONFIDENCE_THRESHOLD

        # Determine query type based on top expert
        if sorted_experts and sorted_experts[0][1] >= threshold:
            query_type = sorted_experts[0][0]
        else:
            query_type = 'mixed'

        # Select experts above threshold
        selected = []
        for expert, score in sorted_experts:
            if score >= threshold and len(selected) < MoESettings.MAX_ACTIVE_EXPERTS:
                selected.append(expert)

        # FIXED: If no experts selected, use HIGHEST SCORING (not hardcoded default!)
        if not selected:
            if sorted_experts and sorted_experts[0][1] > 0:
                # Use the expert with highest score, even if below threshold
                best_expert = sorted_experts[0][0]
                best_score = sorted_experts[0][1]
                selected = [best_expert]
                query_type = best_expert
                self.logger.debug(
                    f"No experts met threshold ({threshold:.2f}), "
                    f"using highest scoring: {best_expert} ({best_score:.2f})"
                )
            else:
                # Only use default if ALL scores are zero
                selected = [MoESettings.DEFAULT_EXPERT]
                query_type = MoESettings.DEFAULT_EXPERT
                self.logger.debug(
                    f"All expert scores are zero, using default: {MoESettings.DEFAULT_EXPERT}"
                )

            self._metrics['fallback_routes'] += 1

        # If single expert and multi-expert disabled, keep only first
        if not MoESettings.ENABLE_MULTI_EXPERT and len(selected) > 1:
            selected = [selected[0]]

        return selected, query_type

    def _update_metrics(self, decision: RoutingDecision):
        """Update routing metrics"""
        if len(decision.selected_experts) == 1:
            self._metrics['single_expert_routes'] += 1
        else:
            self._metrics['multi_expert_routes'] += 1

        for expert in decision.selected_experts:
            if expert in self._metrics['by_expert']:
                self._metrics['by_expert'][expert] += 1

    def _get_cache_key(self, query: str, context: Dict[str, Any]) -> str:
        """Generate cache key"""
        return generate_cache_key("routing", query, context=context)

    def get_metrics(self) -> Dict[str, Any]:
        """Get routing metrics"""
        metrics = self._metrics.copy()
        if metrics['total_routes'] > 0:
            metrics['multi_expert_rate'] = metrics['multi_expert_routes'] / metrics['total_routes']
            metrics['fallback_rate'] = metrics['fallback_routes'] / metrics['total_routes']
        else:
            metrics['multi_expert_rate'] = 0.0
            metrics['fallback_rate'] = 0.0
        return metrics

    def reset_metrics(self):
        """Reset routing metrics"""
        self._metrics = {
            'total_routes': 0,
            'single_expert_routes': 0,
            'multi_expert_routes': 0,
            'fallback_routes': 0,
            'by_expert': {expert: 0 for expert in MoESettings.EXPERT_TYPES}
        }

    def clear_cache(self):
        """Clear routing cache"""
        self._routing_cache.clear()
