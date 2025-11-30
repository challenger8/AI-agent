"""
services/moe/expert_router.py
-----------------------------
Expert router for Mixture of Experts system
Classifies queries and routes to appropriate expert(s)
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple
from datetime import datetime
import re
from services.cache_service import generate_cache_key

from config.moe_settings import MoESettings
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
    """Routes queries to appropriate experts using hybrid strategy"""

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
        confidence_scores = {}

        # Calculate score for each expert based on keyword matches
        for expert_type, keywords in MoESettings.ROUTING_KEYWORDS.items():
            score = 0.0
            matched_keywords = []

            for keyword in keywords:
                if keyword.lower() in query_lower:
                    score += 1.0
                    matched_keywords.append(keyword)

            # Normalize score
            if keywords:
                score = min(score / len(keywords) * 3, 1.0)  # Scale up but cap at 1.0

            confidence_scores[expert_type] = score

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
        if context:
            if 'expert_hint' in context:
                hint = context['expert_hint']
                if hint in confidence_scores:
                    confidence_scores[hint] = min(confidence_scores[hint] + 0.2, 1.0)

            if 'entity_type' in context:
                entity = context['entity_type']
                if entity == 'deal' and 'deal_analysis' in confidence_scores:
                    confidence_scores['deal_analysis'] = min(
                        confidence_scores['deal_analysis'] + 0.15, 1.0
                    )
                elif entity == 'activity' and 'activity' in confidence_scores:
                    confidence_scores['activity'] = min(
                        confidence_scores['activity'] + 0.15, 1.0
                    )

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
        """Hybrid routing combining rules and context"""
        query_lower = query.lower()
        confidence_scores = {}

        # Step 1: Rule-based keyword matching
        for expert_type, keywords in MoESettings.ROUTING_KEYWORDS.items():
            score = 0.0

            for keyword in keywords:
                if keyword.lower() in query_lower:
                    score += 1.0

            # Normalize
            if keywords:
                score = min(score / len(keywords) * 3, 1.0)

            confidence_scores[expert_type] = score

        # Step 2: Context-based boosting
        if context:
            # Boost based on explicit hints
            if 'expert_hint' in context:
                hint = context['expert_hint']
                if hint in confidence_scores:
                    confidence_scores[hint] = min(confidence_scores[hint] + 0.3, 1.0)

            # Boost based on entity type
            if 'entity_type' in context:
                entity = context['entity_type']
                if entity == 'deal':
                    confidence_scores['deal_analysis'] = min(
                        confidence_scores.get('deal_analysis', 0) + 0.2, 1.0
                    )
                elif entity == 'activity':
                    confidence_scores['activity'] = min(
                        confidence_scores.get('activity', 0) + 0.2, 1.0
                    )

            # Boost based on previous expert success
            if 'last_successful_expert' in context:
                last_expert = context['last_successful_expert']
                if last_expert in confidence_scores:
                    confidence_scores[last_expert] = min(
                        confidence_scores[last_expert] + 0.1, 1.0
                    )

        # Step 3: Pattern-based detection using extended patterns from settings
        patterns = getattr(MoESettings, 'ROUTING_PATTERNS', {})
        if not patterns:
            # Fallback patterns if not defined in settings
            patterns = {
                'deal_analysis': [r'\bdeal\s+\d+\b', r'\banalyze\s+deal\b'],
                'sentiment': [r'\bsentiment\b', r'\bfeeling\b'],
                'risk_assessment': [r'\brisk\b', r'\bwarning\b'],
                'search': [r'\bfind\b', r'\bsearch\b']
            }

        for expert_type, expert_patterns in patterns.items():
            for pattern in expert_patterns:
                if re.search(pattern, query_lower):
                    confidence_scores[expert_type] = min(
                        confidence_scores.get(expert_type, 0) + 0.25, 1.0
                    )

        # Step 4: Embedding-based boost (if available)
        if self.embedding_service:
            try:
                semantic_scores = self.embedding_service.get_expert_similarities(query)
                for expert_type, semantic_score in semantic_scores.items():
                    # Blend rule-based and semantic scores (60% rules, 40% semantic)
                    if expert_type in confidence_scores:
                        blended = (0.6 * confidence_scores[expert_type] +
                                   0.4 * semantic_score)
                        confidence_scores[expert_type] = min(blended, 1.0)
            except Exception as e:
                self.logger.warning(f"Embedding scoring failed: {e}")

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

    def _select_experts(self, confidence_scores: Dict[str, float]) -> Tuple[List[str], str]:
        """
        Select experts based on confidence scores

        Returns:
            Tuple of (selected_experts list, query_type)
        """
        # Sort by confidence
        sorted_experts = sorted(
            confidence_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )

        # Determine query type based on top expert
        if sorted_experts and sorted_experts[0][1] >= MoESettings.ROUTING_CONFIDENCE_THRESHOLD:
            query_type = sorted_experts[0][0]
        else:
            query_type = 'mixed'

        # Select experts above threshold
        selected = []
        threshold = MoESettings.ROUTING_CONFIDENCE_THRESHOLD

        for expert, score in sorted_experts:
            if score >= threshold and len(selected) < MoESettings.MAX_ACTIVE_EXPERTS:
                selected.append(expert)

        # If no experts selected, use default
        if not selected:
            selected = [MoESettings.DEFAULT_EXPERT]
            query_type = MoESettings.DEFAULT_EXPERT
            self._metrics['fallback_routes'] += 1
            self.logger.debug(f"No experts met threshold, using default: {MoESettings.DEFAULT_EXPERT}")

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
