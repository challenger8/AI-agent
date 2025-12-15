"""
services/moe/routing_metrics.py
--------------------------------
Routing metrics tracking for expert router.

Extracted from ExpertRouter to improve separation of concerns (SRP).
"""

from typing import Any, Dict
from config.moe_settings import MoESettings


class RoutingMetrics:
    """
    Tracks routing metrics for expert selection.

    Responsibilities:
    - Track routing counts (total, single, multi, fallback)
    - Track per-expert routing counts
    - Calculate routing rates
    - Reset metrics
    """

    def __init__(self):
        """Initialize routing metrics"""
        self._metrics = {
            'total_routes': 0,
            'single_expert_routes': 0,
            'multi_expert_routes': 0,
            'fallback_routes': 0,
            'by_expert': {expert: 0 for expert in MoESettings.EXPERT_TYPES}
        }

    def record_route(self, selected_experts: list, is_fallback: bool = False):
        """
        Record a routing decision.

        Args:
            selected_experts: List of selected expert names
            is_fallback: Whether this was a fallback route
        """
        self._metrics['total_routes'] += 1

        if len(selected_experts) == 1:
            self._metrics['single_expert_routes'] += 1
        else:
            self._metrics['multi_expert_routes'] += 1

        if is_fallback:
            self._metrics['fallback_routes'] += 1

        for expert in selected_experts:
            if expert in self._metrics['by_expert']:
                self._metrics['by_expert'][expert] += 1

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get current routing metrics with calculated rates.

        Returns:
            Dictionary containing metrics and calculated rates
        """
        metrics = self._metrics.copy()

        if metrics['total_routes'] > 0:
            metrics['multi_expert_rate'] = (
                metrics['multi_expert_routes'] / metrics['total_routes']
            )
            metrics['fallback_rate'] = (
                metrics['fallback_routes'] / metrics['total_routes']
            )
        else:
            metrics['multi_expert_rate'] = 0.0
            metrics['fallback_rate'] = 0.0

        return metrics

    def reset(self):
        """Reset all routing metrics"""
        self._metrics = {
            'total_routes': 0,
            'single_expert_routes': 0,
            'multi_expert_routes': 0,
            'fallback_routes': 0,
            'by_expert': {expert: 0 for expert in MoESettings.EXPERT_TYPES}
        }

    @property
    def total_routes(self) -> int:
        """Get total number of routes"""
        return self._metrics['total_routes']

    @property
    def fallback_routes(self) -> int:
        """Get number of fallback routes"""
        return self._metrics['fallback_routes']
