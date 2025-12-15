"""
services/analytics/context.py
------------------------------
Context dataclasses for analytics operations

KISS PRINCIPLE: Replace multiple parameters with context objects
Makes function signatures cleaner and more maintainable
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class DealAnalysisContext:
    """
    Context for deal analysis operations.

    KISS: Single parameter instead of passing 5+ separate parameters
    Makes code more maintainable and reduces coupling
    """
    deal: Dict[str, Any]
    activities: List[Any]
    sentiment_summary: Dict[str, Any]
    health_score: int
    risk_indicators: List[Dict[str, Any]]

    @classmethod
    def create(
        cls,
        deal: Dict[str, Any],
        activities: List[Any],
        sentiment_summary: Optional[Dict[str, Any]] = None,
        health_score: int = 0,
        risk_indicators: Optional[List[Dict[str, Any]]] = None
    ) -> 'DealAnalysisContext':
        """
        Factory method for creating context.

        Args:
            deal: Deal dictionary
            activities: List of activities
            sentiment_summary: Optional sentiment analysis summary
            health_score: Health score (default: 0)
            risk_indicators: Optional risk indicators list

        Returns:
            DealAnalysisContext instance
        """
        return cls(
            deal=deal,
            activities=activities,
            sentiment_summary=sentiment_summary or {},
            health_score=health_score,
            risk_indicators=risk_indicators or []
        )


@dataclass
class HealthCalculationContext:
    """
    Context for health score calculation.

    Simpler than DealAnalysisContext - only what's needed for scoring
    """
    deal: Dict[str, Any]
    activities: List[Any]
    sentiment_summary: Dict[str, Any]


@dataclass
class RiskAnalysisContext:
    """
    Context for risk analysis.

    Focused on risk-specific data
    """
    deal: Dict[str, Any]
    activities: List[Any]
    health_score: int
