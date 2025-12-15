"""
config/routing_constants.py
---------------------------
Constants for MoE expert routing

CLEAN CODE: Extracted magic numbers to named constants for clarity
"""


class RoutingConstants:
    """
    Constants for expert routing calculations.

    CLEAN CODE PRINCIPLE: Named constants instead of magic numbers
    Makes code self-documenting and easier to tune.
    """

    # Keyword scoring
    KEYWORD_SCORE_MULTIPLIER = 3.0  # Scale up keyword matches
    MAX_KEYWORD_SCORE = 1.0  # Cap at 1.0

    # Hybrid routing weights
    RULE_BASED_WEIGHT = 0.6  # 60% rule-based
    SEMANTIC_WEIGHT = 0.4  # 40% semantic

    # Context boost amounts
    EXPERT_HINT_BOOST = 0.3  # Strong boost for explicit hints
    ENTITY_TYPE_BOOST = 0.2  # Moderate boost for entity type
    LAST_SUCCESSFUL_BOOST = 0.1  # Small boost for previous success

    # Pattern matching
    PATTERN_MATCH_BOOST = 0.25  # Boost for regex pattern matches


class ScoringConstants:
    """
    Constants for health/risk scoring calculations.

    CLEAN CODE: Makes scoring algorithms transparent
    """

    # Health score ranges
    MIN_HEALTH_SCORE = 0
    MAX_HEALTH_SCORE = 100

    # Default confidence when uncertain
    DEFAULT_CONFIDENCE = 0.5
