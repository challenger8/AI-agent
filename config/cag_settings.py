"""
config/cag_settings.py
---------------------
CAG (Corrective Augmented Generation) configuration
Settings for relevance scoring, query rewriting, and correction thresholds
"""

import os
from pathlib import Path


class CAGSettings:
    """Configuration for CAG system"""
    
    # ============================================================
    # RELEVANCE SCORING CONFIGURATION
    # ============================================================
    
    # Confidence threshold (0-1): results below this trigger query regeneration
    CONFIDENCE_THRESHOLD = float(os.getenv('CAG_CONFIDENCE_THRESHOLD', '0.6'))
    
    # Weights for relevance score calculation
    SIMILARITY_WEIGHT = float(os.getenv('CAG_SIMILARITY_WEIGHT', '0.5'))
    METADATA_WEIGHT = float(os.getenv('CAG_METADATA_WEIGHT', '0.3'))
    RECENCY_WEIGHT = float(os.getenv('CAG_RECENCY_WEIGHT', '0.2'))
    
    # Minimum number of high-quality results before rewriting
    # If we get fewer than this many high-score results, rewrite query
    MIN_HIGH_QUALITY_RESULTS = int(os.getenv('CAG_MIN_HIGH_QUALITY_RESULTS', '2'))
    
    # Overall quality threshold for entire result set (0-1)
    # If average score of all results is below this, trigger rewrite
    BATCH_QUALITY_THRESHOLD = float(os.getenv('CAG_BATCH_QUALITY_THRESHOLD', '0.55'))
    
    # ============================================================
    # QUERY REWRITING CONFIGURATION
    # ============================================================
    
    # Enable automatic query rewriting
    ENABLE_QUERY_REWRITING = os.getenv('CAG_ENABLE_QUERY_REWRITING', 'true').lower() == 'true'
    
    # Strategy for query rewriting: 'expand', 'rephrase', 'both'
    REWRITE_STRATEGY = os.getenv('CAG_REWRITE_STRATEGY', 'both')
    
    # Maximum rewrites allowed (prevents infinite loops)
    MAX_REWRITES = int(os.getenv('CAG_MAX_REWRITES', '2'))
    
    # Number of alternative queries to generate
    NUM_ALTERNATIVE_QUERIES = int(os.getenv('CAG_NUM_ALTERNATIVE_QUERIES', '3'))
    
    # Persian text normalization
    NORMALIZE_PERSIAN_TEXT = os.getenv('CAG_NORMALIZE_PERSIAN_TEXT', 'true').lower() == 'true'
    
    # Synonyms expansion for Persian language
    ENABLE_SYNONYM_EXPANSION = os.getenv('CAG_ENABLE_SYNONYM_EXPANSION', 'true').lower() == 'true'
    
    # ============================================================
    # CAG DECISION LOGIC
    # ============================================================
    
    # Decision strategy: 'threshold', 'hybrid', 'aggressive'
    # 'threshold': Use simple threshold
    # 'hybrid': Combine threshold + batch quality
    # 'aggressive': Rewrite if any result is low confidence
    DECISION_STRATEGY = os.getenv('CAG_DECISION_STRATEGY', 'hybrid')
    
    # Whether to always show correction metadata in results
    INCLUDE_CORRECTION_METADATA = os.getenv('CAG_INCLUDE_CORRECTION_METADATA', 'true').lower() == 'true'
    
    # Log detailed CAG operations
    VERBOSE_LOGGING = os.getenv('CAG_VERBOSE_LOGGING', 'false').lower() == 'true'
    
    # ============================================================
    # PERFORMANCE SETTINGS
    # ============================================================
    
    # Cache rewriting results (same query = same rewrite)
    CACHE_REWRITES = os.getenv('CAG_CACHE_REWRITES', 'true').lower() == 'true'
    
    # Maximum cache size for rewrites
    REWRITE_CACHE_SIZE = int(os.getenv('CAG_REWRITE_CACHE_SIZE', '100'))
    
    # Timeout for query rewriting (seconds)
    REWRITE_TIMEOUT = int(os.getenv('CAG_REWRITE_TIMEOUT', '10'))
    
    # ============================================================
    # ENTITY-SPECIFIC SETTINGS
    # ============================================================
    
    # Different thresholds for different entity types
    THRESHOLDS_BY_TYPE = {
        'deal': float(os.getenv('CAG_THRESHOLD_DEAL', '0.65')),
        'activity': float(os.getenv('CAG_THRESHOLD_ACTIVITY', '0.60')),
        'agent': float(os.getenv('CAG_THRESHOLD_AGENT', '0.55'))
    }
    
    # ============================================================
    # QUALITY METRICS
    # ============================================================
    
    # Track CAG success metrics
    ENABLE_METRICS = os.getenv('CAG_ENABLE_METRICS', 'true').lower() == 'true'
    
    # Metrics storage path
    METRICS_DIR = Path(os.getenv('CAG_METRICS_DIR', './data/cag_metrics'))
    METRICS_DIR.mkdir(parents=True, exist_ok=True)
    
    # ============================================================
    # VALIDATION
    # ============================================================
    
    @classmethod
    def validate(cls):
        """Validate CAG settings"""
        errors = []
        
        # Validate thresholds (0-1)
        if not (0.0 <= cls.CONFIDENCE_THRESHOLD <= 1.0):
            errors.append(f"CONFIDENCE_THRESHOLD must be 0-1, got {cls.CONFIDENCE_THRESHOLD}")
        
        if not (0.0 <= cls.BATCH_QUALITY_THRESHOLD <= 1.0):
            errors.append(f"BATCH_QUALITY_THRESHOLD must be 0-1, got {cls.BATCH_QUALITY_THRESHOLD}")
        
        # Validate weights sum to 1.0
        total_weight = cls.SIMILARITY_WEIGHT + cls.METADATA_WEIGHT + cls.RECENCY_WEIGHT
        if not (0.99 <= total_weight <= 1.01):  # Allow small floating point error
            errors.append(
                f"Weights must sum to 1.0, got {total_weight} "
                f"(SIM={cls.SIMILARITY_WEIGHT}, META={cls.METADATA_WEIGHT}, REC={cls.RECENCY_WEIGHT})"
            )
        
        # Validate strategies
        valid_strategies = ['expand', 'rephrase', 'both']
        if cls.REWRITE_STRATEGY not in valid_strategies:
            errors.append(f"REWRITE_STRATEGY must be one of {valid_strategies}")
        
        valid_decisions = ['threshold', 'hybrid', 'aggressive']
        if cls.DECISION_STRATEGY not in valid_decisions:
            errors.append(f"DECISION_STRATEGY must be one of {valid_decisions}")
        
        # Validate positive integers
        if cls.MAX_REWRITES <= 0:
            errors.append(f"MAX_REWRITES must be > 0, got {cls.MAX_REWRITES}")
        
        if cls.MIN_HIGH_QUALITY_RESULTS < 1:
            errors.append(f"MIN_HIGH_QUALITY_RESULTS must be >= 1, got {cls.MIN_HIGH_QUALITY_RESULTS}")
        
        if errors:
            raise ValueError("CAG Settings validation failed:\n" + "\n".join(f"  - {e}" for e in errors))
        
        return True
    
    @classmethod
    def get_threshold_for_type(cls, entity_type: str) -> float:
        """
        Get confidence threshold for specific entity type
        
        Args:
            entity_type: 'deal', 'activity', or 'agent'
            
        Returns:
            Threshold value (0-1)
        """
        return cls.THRESHOLDS_BY_TYPE.get(entity_type, cls.CONFIDENCE_THRESHOLD)
    
    @classmethod
    def to_dict(cls) -> dict:
        """Export all settings as dictionary"""
        return {
            'confidence_threshold': cls.CONFIDENCE_THRESHOLD,
            'similarity_weight': cls.SIMILARITY_WEIGHT,
            'metadata_weight': cls.METADATA_WEIGHT,
            'recency_weight': cls.RECENCY_WEIGHT,
            'min_high_quality_results': cls.MIN_HIGH_QUALITY_RESULTS,
            'batch_quality_threshold': cls.BATCH_QUALITY_THRESHOLD,
            'enable_query_rewriting': cls.ENABLE_QUERY_REWRITING,
            'rewrite_strategy': cls.REWRITE_STRATEGY,
            'max_rewrites': cls.MAX_REWRITES,
            'decision_strategy': cls.DECISION_STRATEGY,
            'enable_metrics': cls.ENABLE_METRICS
        }


# Validate on module load
try:
    CAGSettings.validate()
except ValueError as e:
    import logging
    logger = logging.getLogger(__name__)
    logger.error(f"CAG Settings validation error: {e}")
    # Don't raise - allow app to start with warnings