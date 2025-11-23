"""
services/moe/__init__.py
------------------------
Mixture of Experts module for Persian Deal Analyzer
"""

from .base_expert import BaseExpert, ExpertResult
from .expert_router import ExpertRouter, RoutingDecision
from .expert_ensemble import ExpertEnsemble, EnsembleResult
from .moe_orchestrator import MoEOrchestrator
from .cache_service import CacheService, ExpertResultCache, RoutingCache
from .monitoring import PerformanceMonitor, get_monitor
from .feedback_loop import FeedbackLoop, get_feedback_loop

# Optional imports that require numpy
try:
    from .embedding_service import EmbeddingService
except ImportError:
    EmbeddingService = None

__all__ = [
    'BaseExpert',
    'ExpertResult',
    'ExpertRouter',
    'RoutingDecision',
    'ExpertEnsemble',
    'EnsembleResult',
    'MoEOrchestrator',
    'EmbeddingService',
    'CacheService',
    'ExpertResultCache',
    'RoutingCache',
    'PerformanceMonitor',
    'get_monitor',
    'FeedbackLoop',
    'get_feedback_loop'
]
