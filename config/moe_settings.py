"""
config/moe_settings.py
---------------------
Mixture of Experts (MoE) configuration
Settings for expert routing, ensemble strategies, and expert-specific thresholds
"""

import os
from pathlib import Path


class MoESettings:
    """Configuration for Mixture of Experts system"""

    # ============================================================
    # EXPERT TYPES
    # ============================================================

    # Available expert types
    EXPERT_TYPES = [
        'deal_analysis',    # Deal health scoring, insights
        'sentiment',        # Persian text sentiment analysis
        'activity',         # Activity summarization, trends
        'risk_assessment',  # Risk evaluation, predictions
        'search'           # RAG/CAG semantic search
    ]

    # Query type to expert mapping
    QUERY_TYPE_MAPPING = {
        'deal_analysis': ['deal_analysis', 'risk_assessment'],
        'sentiment': ['sentiment'],
        'activity': ['activity', 'deal_analysis'],
        'risk': ['risk_assessment', 'deal_analysis'],
        'search': ['search'],
        'mixed': ['deal_analysis', 'sentiment', 'activity', 'risk_assessment', 'search']
    }

    # ============================================================
    # ROUTER CONFIGURATION
    # ============================================================

    # Routing strategy: 'rule_based', 'embedding_based', 'hybrid'
    ROUTING_STRATEGY = os.getenv('MOE_ROUTING_STRATEGY', 'hybrid')

    # Confidence threshold for routing decisions (0-1)
    ROUTING_CONFIDENCE_THRESHOLD = float(os.getenv('MOE_ROUTING_CONFIDENCE', '0.7'))

    # Enable multi-expert routing (query can go to multiple experts)
    ENABLE_MULTI_EXPERT = os.getenv('MOE_ENABLE_MULTI_EXPERT', 'true').lower() == 'true'

    # Maximum number of experts to activate for a single query
    MAX_ACTIVE_EXPERTS = int(os.getenv('MOE_MAX_ACTIVE_EXPERTS', '3'))

    # Keywords for rule-based routing (Persian and English)
    ROUTING_KEYWORDS = {
        'deal_analysis': [
            'deal', 'معامله', 'قرارداد', 'health', 'سلامت', 'score', 'امتیاز',
            'analyze', 'تحلیل', 'performance', 'عملکرد', 'status', 'وضعیت'
        ],
        'sentiment': [
            'sentiment', 'احساس', 'feeling', 'emotion', 'حس', 'mood', 'خلق',
            'positive', 'مثبت', 'negative', 'منفی', 'neutral', 'خنثی', 'opinion', 'نظر'
        ],
        'activity': [
            'activity', 'فعالیت', 'timeline', 'جدول زمانی', 'history', 'تاریخچه',
            'recent', 'اخیر', 'last', 'آخرین', 'trend', 'روند', 'summary', 'خلاصه'
        ],
        'risk_assessment': [
            'risk', 'ریسک', 'danger', 'خطر', 'warning', 'هشدار', 'problem', 'مشکل',
            'issue', 'concern', 'نگرانی', 'threat', 'تهدید', 'vulnerability', 'آسیب‌پذیری'
        ],
        'search': [
            'find', 'پیدا', 'search', 'جستجو', 'look', 'گشتن', 'query', 'پرس‌وجو',
            'where', 'کجا', 'which', 'کدام', 'related', 'مرتبط', 'similar', 'مشابه'
        ]
    }

    # ============================================================
    # ENSEMBLE CONFIGURATION
    # ============================================================

    # Ensemble strategy: 'weighted_average', 'winner_take_all', 'hierarchical'
    ENSEMBLE_STRATEGY = os.getenv('MOE_ENSEMBLE_STRATEGY', 'weighted_average')

    # Default weights for each expert type (normalized to sum to 1.0)
    DEFAULT_EXPERT_WEIGHTS = {
        'deal_analysis': float(os.getenv('MOE_WEIGHT_DEAL', '0.25')),
        'sentiment': float(os.getenv('MOE_WEIGHT_SENTIMENT', '0.20')),
        'activity': float(os.getenv('MOE_WEIGHT_ACTIVITY', '0.20')),
        'risk_assessment': float(os.getenv('MOE_WEIGHT_RISK', '0.20')),
        'search': float(os.getenv('MOE_WEIGHT_SEARCH', '0.15'))
    }

    # Minimum confidence for expert output to be included in ensemble
    MIN_EXPERT_CONFIDENCE = float(os.getenv('MOE_MIN_EXPERT_CONFIDENCE', '0.5'))

    # Whether to normalize expert outputs before combining
    NORMALIZE_OUTPUTS = os.getenv('MOE_NORMALIZE_OUTPUTS', 'true').lower() == 'true'

    # ============================================================
    # EXPERT-SPECIFIC THRESHOLDS
    # ============================================================

    # Confidence thresholds by expert type
    CONFIDENCE_THRESHOLDS = {
        'deal_analysis': float(os.getenv('MOE_THRESHOLD_DEAL', '0.65')),
        'sentiment': float(os.getenv('MOE_THRESHOLD_SENTIMENT', '0.60')),
        'activity': float(os.getenv('MOE_THRESHOLD_ACTIVITY', '0.55')),
        'risk_assessment': float(os.getenv('MOE_THRESHOLD_RISK', '0.70')),
        'search': float(os.getenv('MOE_THRESHOLD_SEARCH', '0.60'))
    }

    # Timeout for each expert (seconds)
    EXPERT_TIMEOUTS = {
        'deal_analysis': int(os.getenv('MOE_TIMEOUT_DEAL', '10')),
        'sentiment': int(os.getenv('MOE_TIMEOUT_SENTIMENT', '15')),
        'activity': int(os.getenv('MOE_TIMEOUT_ACTIVITY', '8')),
        'risk_assessment': int(os.getenv('MOE_TIMEOUT_RISK', '10')),
        'search': int(os.getenv('MOE_TIMEOUT_SEARCH', '20'))
    }

    # ============================================================
    # PERFORMANCE SETTINGS
    # ============================================================

    # Enable parallel expert execution
    PARALLEL_EXECUTION = os.getenv('MOE_PARALLEL_EXECUTION', 'true').lower() == 'true'

    # Maximum concurrent expert calls
    MAX_CONCURRENT_EXPERTS = int(os.getenv('MOE_MAX_CONCURRENT', '5'))

    # Cache expert results
    CACHE_EXPERT_RESULTS = os.getenv('MOE_CACHE_RESULTS', 'true').lower() == 'true'

    # Cache TTL (seconds)
    CACHE_TTL = int(os.getenv('MOE_CACHE_TTL', '300'))

    # Maximum cache entries
    MAX_CACHE_SIZE = int(os.getenv('MOE_MAX_CACHE_SIZE', '500'))

    # ============================================================
    # LOGGING AND METRICS
    # ============================================================

    # Enable verbose MoE logging
    VERBOSE_LOGGING = os.getenv('MOE_VERBOSE_LOGGING', 'false').lower() == 'true'

    # Track MoE metrics
    ENABLE_METRICS = os.getenv('MOE_ENABLE_METRICS', 'true').lower() == 'true'

    # Metrics storage path
    METRICS_DIR = Path(os.getenv('MOE_METRICS_DIR', './data/moe_metrics'))
    METRICS_DIR.mkdir(parents=True, exist_ok=True)

    # Include routing decisions in output
    INCLUDE_ROUTING_INFO = os.getenv('MOE_INCLUDE_ROUTING_INFO', 'true').lower() == 'true'

    # ============================================================
    # FALLBACK CONFIGURATION
    # ============================================================

    # Default expert to use when routing fails
    DEFAULT_EXPERT = os.getenv('MOE_DEFAULT_EXPERT', 'search')

    # Enable fallback to default expert
    ENABLE_FALLBACK = os.getenv('MOE_ENABLE_FALLBACK', 'true').lower() == 'true'

    # Retry failed experts
    RETRY_FAILED_EXPERTS = os.getenv('MOE_RETRY_FAILED', 'true').lower() == 'true'

    # Maximum retries per expert
    MAX_RETRIES = int(os.getenv('MOE_MAX_RETRIES', '2'))

    # ============================================================
    # VALIDATION
    # ============================================================

    @classmethod
    def validate(cls):
        """Validate MoE settings"""
        errors = []

        # Validate routing strategy
        valid_routing = ['rule_based', 'embedding_based', 'hybrid']
        if cls.ROUTING_STRATEGY not in valid_routing:
            errors.append(f"ROUTING_STRATEGY must be one of {valid_routing}")

        # Validate ensemble strategy
        valid_ensemble = ['weighted_average', 'winner_take_all', 'hierarchical']
        if cls.ENSEMBLE_STRATEGY not in valid_ensemble:
            errors.append(f"ENSEMBLE_STRATEGY must be one of {valid_ensemble}")

        # Validate thresholds (0-1)
        if not (0.0 <= cls.ROUTING_CONFIDENCE_THRESHOLD <= 1.0):
            errors.append(f"ROUTING_CONFIDENCE_THRESHOLD must be 0-1")

        if not (0.0 <= cls.MIN_EXPERT_CONFIDENCE <= 1.0):
            errors.append(f"MIN_EXPERT_CONFIDENCE must be 0-1")

        # Validate weights sum to ~1.0
        total_weight = sum(cls.DEFAULT_EXPERT_WEIGHTS.values())
        if not (0.99 <= total_weight <= 1.01):
            errors.append(f"DEFAULT_EXPERT_WEIGHTS must sum to 1.0, got {total_weight}")

        # Validate positive integers
        if cls.MAX_ACTIVE_EXPERTS < 1:
            errors.append(f"MAX_ACTIVE_EXPERTS must be >= 1")

        if cls.MAX_CONCURRENT_EXPERTS < 1:
            errors.append(f"MAX_CONCURRENT_EXPERTS must be >= 1")

        # Validate default expert
        if cls.DEFAULT_EXPERT not in cls.EXPERT_TYPES:
            errors.append(f"DEFAULT_EXPERT must be one of {cls.EXPERT_TYPES}")

        if errors:
            raise ValueError("MoE Settings validation failed:\n" + "\n".join(f"  - {e}" for e in errors))

        return True

    @classmethod
    def get_threshold_for_expert(cls, expert_type: str) -> float:
        """Get confidence threshold for specific expert type"""
        return cls.CONFIDENCE_THRESHOLDS.get(expert_type, cls.ROUTING_CONFIDENCE_THRESHOLD)

    @classmethod
    def get_timeout_for_expert(cls, expert_type: str) -> int:
        """Get timeout for specific expert type"""
        return cls.EXPERT_TIMEOUTS.get(expert_type, 10)

    @classmethod
    def get_weight_for_expert(cls, expert_type: str) -> float:
        """Get default weight for specific expert type"""
        return cls.DEFAULT_EXPERT_WEIGHTS.get(expert_type, 0.2)

    @classmethod
    def get_experts_for_query_type(cls, query_type: str) -> list:
        """Get list of experts for a query type"""
        return cls.QUERY_TYPE_MAPPING.get(query_type, [cls.DEFAULT_EXPERT])

    @classmethod
    def to_dict(cls) -> dict:
        """Export all settings as dictionary"""
        return {
            'expert_types': cls.EXPERT_TYPES,
            'routing_strategy': cls.ROUTING_STRATEGY,
            'routing_confidence_threshold': cls.ROUTING_CONFIDENCE_THRESHOLD,
            'enable_multi_expert': cls.ENABLE_MULTI_EXPERT,
            'max_active_experts': cls.MAX_ACTIVE_EXPERTS,
            'ensemble_strategy': cls.ENSEMBLE_STRATEGY,
            'default_expert_weights': cls.DEFAULT_EXPERT_WEIGHTS,
            'min_expert_confidence': cls.MIN_EXPERT_CONFIDENCE,
            'parallel_execution': cls.PARALLEL_EXECUTION,
            'cache_expert_results': cls.CACHE_EXPERT_RESULTS,
            'enable_metrics': cls.ENABLE_METRICS,
            'default_expert': cls.DEFAULT_EXPERT
        }


# Validate on module load
try:
    MoESettings.validate()
except ValueError as e:
    import logging
    logger = logging.getLogger(__name__)
    logger.error(f"MoE Settings validation error: {e}")
