"""
services/__init__.py
--------------------
Services package initialization
"""

from .base_service import BaseService
from .deal_service import DealService
from .sentiment_service import SentimentService
from .analytics_service import AnalyticsService
from .stt_service import STTService
from .cache_service import CacheService, get_cache_service

# Lazy imports for RAG services to avoid Keras/TensorFlow conflicts
def __getattr__(name):
    if name == 'EmbeddingService':
        from .embedding_service import EmbeddingService
        return EmbeddingService
    elif name == 'VectorStoreService':
        from .vector_store_service import VectorStoreService
        return VectorStoreService
    elif name == 'RAGSearchService':
        from .rag_search_service import RAGSearchService
        return RAGSearchService
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    'BaseService',
    'DealService',
    'SentimentService',
    'AnalyticsService',
    'STTService',
    'CacheService',
    'get_cache_service',
    'EmbeddingService',
    'VectorStoreService',
    'RAGSearchService',
]