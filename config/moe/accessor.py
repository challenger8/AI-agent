"""
config/moe/accessor.py
----------------------
MoE configuration accessor methods

SOLID: Single Responsibility - Configuration access logic only
"""

from typing import Dict, List
from .config import MoEConfig


class MoEConfigAccessor:
    """
    Provides convenient access methods for MoE configuration.

    Single Responsibility: Configuration accessor logic only.
    """

    def __init__(self, config: MoEConfig):
        """
        Initialize accessor with configuration.

        Args:
            config: MoEConfig instance
        """
        self.config = config

    def get_threshold_for_expert(self, expert_type: str) -> float:
        """
        Get confidence threshold for specific expert type.

        Args:
            expert_type: Expert type name

        Returns:
            Confidence threshold (0-1), falls back to routing threshold if not found
        """
        return self.config.confidence_thresholds.get(
            expert_type,
            self.config.routing_confidence_threshold
        )

    def get_timeout_for_expert(self, expert_type: str) -> int:
        """
        Get timeout for specific expert type.

        Args:
            expert_type: Expert type name

        Returns:
            Timeout in seconds, falls back to 10 seconds if not found
        """
        return self.config.expert_timeouts.get(expert_type, 10)

    def get_weight_for_expert(self, expert_type: str) -> float:
        """
        Get default weight for specific expert type.

        Args:
            expert_type: Expert type name

        Returns:
            Weight value (0-1), falls back to 0.2 if not found
        """
        return self.config.default_expert_weights.get(expert_type, 0.2)

    def get_experts_for_query_type(self, query_type: str) -> List[str]:
        """
        Get list of experts for a query type.

        Args:
            query_type: Query type classification

        Returns:
            List of expert type names
        """
        # Query type to expert mapping
        query_type_mapping = {
            'deal_analysis': ['deal_analysis', 'risk_assessment'],
            'sentiment': ['sentiment'],
            'activity': ['activity', 'deal_analysis'],
            'risk': ['risk_assessment', 'deal_analysis'],
            'search': ['search'],
            'mixed': self.config.expert_types
        }

        return query_type_mapping.get(query_type, [self.config.default_expert])

    def to_dict(self) -> Dict:
        """
        Export configuration as dictionary.

        Returns:
            Dictionary representation of configuration
        """
        return {
            'expert_types': self.config.expert_types,
            'routing_strategy': self.config.routing_strategy,
            'routing_confidence_threshold': self.config.routing_confidence_threshold,
            'enable_multi_expert': self.config.enable_multi_expert,
            'max_active_experts': self.config.max_active_experts,
            'ensemble_strategy': self.config.ensemble_strategy,
            'default_expert_weights': self.config.default_expert_weights,
            'min_expert_confidence': self.config.min_expert_confidence,
            'parallel_execution': self.config.parallel_execution,
            'cache_expert_results': self.config.cache_expert_results,
            'enable_metrics': self.config.enable_metrics,
            'default_expert': self.config.default_expert
        }
