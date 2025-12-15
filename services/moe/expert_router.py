"""
services/moe/expert_router_refactored.py
-----------------------------------------
REFACTORED: Simplified expert router with KISS and SRP principles

Changes (v1):
- Extracted magic numbers to named constants
- Broke down complex _route_hybrid() into smaller methods
- Improved readability and maintainability

Changes (v2):
- Extracted RoutingMetrics class for metrics tracking (SRP)
- Extracted RoutingScorer class for scoring logic (SRP)
- Reduced ExpertRouter from 467 to ~220 lines
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple
from datetime import datetime

from config.moe_settings import MoESettings
from utils.logging_config import get_logger
from services.moe.routing_metrics import RoutingMetrics
from services.moe.routing_scorer import RoutingScorer


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
        self._metrics = RoutingMetrics()
        self._scorer = RoutingScorer(embedding_service)

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

        # Determine routing strategy
        strategy = MoESettings.ROUTING_STRATEGY

        if strategy == 'rule_based':
            decision = self._route_rule_based(query, context)
        elif strategy == 'embedding_based':
            decision = self._route_embedding_based(query, context)
        else:  # hybrid
            decision = self._route_hybrid(query, context)

        # Cache decision
        if MoESettings.CACHE_EXPERT_RESULTS:
            self._routing_cache[cache_key] = decision

        return decision

    def _route_rule_based(self, query: str, context: Dict[str, Any]) -> RoutingDecision:
        """Rule-based routing using keywords"""
        query_lower = query.lower()

        # Calculate keyword scores using scorer
        confidence_scores = self._scorer.calculate_keyword_scores(query_lower)

        # Select experts above threshold
        selected_experts, query_type, is_fallback = self._select_experts(confidence_scores)

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

        # Apply context boosting using scorer
        confidence_scores = self._scorer.apply_context_boosts(confidence_scores, context)

        # Select experts above threshold
        selected_experts, query_type, is_fallback = self._select_experts(confidence_scores)

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

        REFACTORED: Simplified by delegating to RoutingScorer
        """
        # Use scorer's convenient method for hybrid scoring
        confidence_scores = self._scorer.calculate_hybrid_scores(query, context)

        # Select experts
        selected_experts, query_type, is_fallback = self._select_experts(confidence_scores)

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
    # Expert selection and metrics (scoring now delegated to RoutingScorer)
    # ========================================================================

    def _select_experts(self, confidence_scores: Dict[str, float]) -> Tuple[List[str], str, bool]:
        """
        Select experts based on confidence scores.

        FIXED: When no expert meets threshold, select highest scoring
        expert instead of hardcoded default.

        Returns:
            Tuple of (selected_experts list, query_type, is_fallback)
        """
        # Sort by confidence (highest first)
        sorted_experts = sorted(
            confidence_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )

        threshold = MoESettings.ROUTING_CONFIDENCE_THRESHOLD
        is_fallback = False

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
            is_fallback = True
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

        # If single expert and multi-expert disabled, keep only first
        if not MoESettings.ENABLE_MULTI_EXPERT and len(selected) > 1:
            selected = [selected[0]]

        # Record metrics
        self._metrics.record_route(selected, is_fallback)

        return selected, query_type, is_fallback

    def _get_cache_key(self, query: str, context: Dict[str, Any]) -> str:
        """
        Generate cache key for routing decisions.

        REFACTORED: Now uses CacheKeyBuilder.build() for consistency.
        """
        from services.cache.base_cache import CacheKeyBuilder
        return CacheKeyBuilder.build("routing", query, context=context)

    def get_metrics(self) -> Dict[str, Any]:
        """Get routing metrics (delegates to RoutingMetrics)"""
        return self._metrics.get_metrics()

    def reset_metrics(self):
        """Reset routing metrics (delegates to RoutingMetrics)"""
        self._metrics.reset()

    def clear_cache(self):
        """Clear routing cache"""
        self._routing_cache.clear()
