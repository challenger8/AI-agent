"""
config/moe/settings.py
----------------------
Backward-compatible facade for MoESettings

REFACTORED: This is now a thin facade over the modular config system.
Maintains backward compatibility while delegating to focused modules.
"""

import logging
from typing import Dict, List
from .config import MoEConfig, load_moe_config
from .validator import MoEConfigValidator
from .accessor import MoEConfigAccessor

logger = logging.getLogger(__name__)


# Initialize configuration singleton
_config = load_moe_config()
_accessor = MoEConfigAccessor(_config)
_validator = MoEConfigValidator()

# Validate on initialization
try:
    _validator.validate_and_raise(_config)
except ValueError as e:
    logger.error(f"MoE Settings validation error: {e}")


class MoESettings:
    """
    Backward-compatible facade for MoE configuration.

    REFACTORED: Now delegates to modular components:
    - MoEConfig: Data storage
    - MoEConfigValidator: Validation logic
    - MoEConfigAccessor: Access methods

    This class exists for backward compatibility.
    New code should use the modular components directly.
    """

    # Expose config attributes as class variables for backward compatibility
    EXPERT_TYPES = _config.expert_types
    ROUTING_STRATEGY = _config.routing_strategy
    ROUTING_CONFIDENCE_THRESHOLD = _config.routing_confidence_threshold
    ENABLE_MULTI_EXPERT = _config.enable_multi_expert
    MAX_ACTIVE_EXPERTS = _config.max_active_experts
    ROUTING_KEYWORDS = _config.routing_keywords
    ROUTING_PATTERNS = _config.routing_patterns
    ENSEMBLE_STRATEGY = _config.ensemble_strategy
    DEFAULT_EXPERT_WEIGHTS = _config.default_expert_weights
    MIN_EXPERT_CONFIDENCE = _config.min_expert_confidence
    NORMALIZE_OUTPUTS = _config.normalize_outputs
    CONFIDENCE_THRESHOLDS = _config.confidence_thresholds
    EXPERT_TIMEOUTS = _config.expert_timeouts
    PARALLEL_EXECUTION = _config.parallel_execution
    MAX_CONCURRENT_EXPERTS = _config.max_concurrent_experts
    CACHE_EXPERT_RESULTS = _config.cache_expert_results
    CACHE_TTL = _config.cache_ttl
    MAX_CACHE_SIZE = _config.max_cache_size
    ENABLE_METRICS = _config.enable_metrics
    INCLUDE_ROUTING_INFO = _config.include_routing_info
    DEFAULT_EXPERT = _config.default_expert
    ENABLE_FALLBACK = _config.enable_fallback

    # Delegate methods to accessor

    @classmethod
    def validate(cls):
        """Validate MoE settings (backward compatible)"""
        _validator.validate_and_raise(_config)
        return True

    @classmethod
    def get_threshold_for_expert(cls, expert_type: str) -> float:
        """Get confidence threshold for specific expert type"""
        return _accessor.get_threshold_for_expert(expert_type)

    @classmethod
    def get_timeout_for_expert(cls, expert_type: str) -> int:
        """Get timeout for specific expert type"""
        return _accessor.get_timeout_for_expert(expert_type)

    @classmethod
    def get_weight_for_expert(cls, expert_type: str) -> float:
        """Get default weight for specific expert type"""
        return _accessor.get_weight_for_expert(expert_type)

    @classmethod
    def get_experts_for_query_type(cls, query_type: str) -> List[str]:
        """Get list of experts for a query type"""
        return _accessor.get_experts_for_query_type(query_type)

    @classmethod
    def to_dict(cls) -> Dict:
        """Export all settings as dictionary"""
        return _accessor.to_dict()
