"""
config/moe/validator.py
-----------------------
MoE configuration validation logic

SOLID: Single Responsibility - Validation only
"""

from typing import List
from .config import MoEConfig


class MoEConfigValidator:
    """
    Validates MoE configuration.

    Single Responsibility: Configuration validation only.
    """

    # Valid strategies
    VALID_ROUTING_STRATEGIES = ['rule_based', 'embedding_based', 'hybrid']
    VALID_ENSEMBLE_STRATEGIES = ['weighted_average', 'winner_take_all', 'hierarchical']

    @staticmethod
    def validate(config: MoEConfig) -> List[str]:
        """
        Validate MoE configuration.

        Args:
            config: MoEConfig instance to validate

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        # Validate routing strategy
        if config.routing_strategy not in MoEConfigValidator.VALID_ROUTING_STRATEGIES:
            errors.append(
                f"routing_strategy must be one of {MoEConfigValidator.VALID_ROUTING_STRATEGIES}, "
                f"got '{config.routing_strategy}'"
            )

        # Validate ensemble strategy
        if config.ensemble_strategy not in MoEConfigValidator.VALID_ENSEMBLE_STRATEGIES:
            errors.append(
                f"ensemble_strategy must be one of {MoEConfigValidator.VALID_ENSEMBLE_STRATEGIES}, "
                f"got '{config.ensemble_strategy}'"
            )

        # Validate thresholds (0-1 range)
        if not (0.0 <= config.routing_confidence_threshold <= 1.0):
            errors.append(
                f"routing_confidence_threshold must be 0-1, got {config.routing_confidence_threshold}"
            )

        if not (0.0 <= config.min_expert_confidence <= 1.0):
            errors.append(
                f"min_expert_confidence must be 0-1, got {config.min_expert_confidence}"
            )

        # Validate expert weights sum to ~1.0
        total_weight = sum(config.default_expert_weights.values())
        if not (0.99 <= total_weight <= 1.01):
            errors.append(
                f"default_expert_weights must sum to 1.0, got {total_weight:.3f}"
            )

        # Validate positive integers
        if config.max_active_experts < 1:
            errors.append(
                f"max_active_experts must be >= 1, got {config.max_active_experts}"
            )

        if config.max_concurrent_experts < 1:
            errors.append(
                f"max_concurrent_experts must be >= 1, got {config.max_concurrent_experts}"
            )

        # Validate default expert exists in expert types
        if config.default_expert not in config.expert_types:
            errors.append(
                f"default_expert '{config.default_expert}' must be one of {config.expert_types}"
            )

        return errors

    @staticmethod
    def validate_and_raise(config: MoEConfig):
        """
        Validate configuration and raise ValueError if invalid.

        Args:
            config: MoEConfig instance to validate

        Raises:
            ValueError: If configuration is invalid
        """
        errors = MoEConfigValidator.validate(config)
        if errors:
            error_msg = "MoE Configuration validation failed:\n" + "\n".join(
                f"  - {error}" for error in errors
            )
            raise ValueError(error_msg)
