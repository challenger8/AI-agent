"""
config/moe/config.py
--------------------
MoE configuration data structures (DATA ONLY - No logic)

SOLID: Single Responsibility - Configuration data storage only
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List


@dataclass
class MoEConfig:
    """
    Mixture of Experts configuration data.

    Single Responsibility: Store configuration values only.
    No validation, no accessor logic, no business logic.
    """

    # Expert types
    expert_types: List[str] = field(default_factory=lambda: [
        'deal_analysis',
        'sentiment',
        'activity',
        'risk_assessment',
        'search'
    ])

    # Routing configuration
    routing_strategy: str = 'hybrid'  # 'rule_based', 'embedding_based', 'hybrid'
    routing_confidence_threshold: float = 0.7
    enable_multi_expert: bool = True
    max_active_experts: int = 3

    # Routing keywords (Persian and English)
    routing_keywords: Dict[str, List[str]] = field(default_factory=lambda: {
        'deal_analysis': [
            'deal', 'معامله', 'قرارداد', 'health', 'سلامت', 'score', 'امتیاز',
            'analyze', 'تحلیل', 'performance', 'عملکرد', 'status', 'وضعیت',
            'pipeline', 'پایپلاین', 'conversion', 'تبدیل', 'stage', 'مرحله',
            'value', 'ارزش', 'revenue', 'درآمد', 'forecast', 'پیش‌بینی',
            'opportunity', 'فرصت', 'prospect', 'مشتری بالقوه', 'lead', 'سرنخ',
            'win', 'برد', 'loss', 'باخت', 'close', 'بستن', 'negotiate', 'مذاکره',
            'contract', 'قرارداد', 'proposal', 'پیشنهاد', 'quote', 'قیمت‌گذاری',
            'دیل', 'معاملات', 'قراردادها', 'فروش', 'خرید'
        ],
        'sentiment': [
            'sentiment', 'احساس', 'feeling', 'emotion', 'حس', 'mood', 'خلق',
            'positive', 'مثبت', 'negative', 'منفی', 'neutral', 'خنثی', 'opinion', 'نظر',
            'satisfaction', 'رضایت', 'happy', 'خوشحال', 'angry', 'عصبانی',
            'frustrated', 'ناامید', 'pleased', 'راضی', 'disappointed', 'ناراضی',
            'tone', 'لحن', 'attitude', 'نگرش', 'perception', 'درک', 'view', 'دیدگاه',
            'feedback', 'بازخورد', 'review', 'بررسی', 'comment', 'نظر',
            'احساسات', 'عواطف', 'خلق‌وخو', 'روحیه', 'برداشت'
        ],
        'activity': [
            'activity', 'فعالیت', 'timeline', 'جدول زمانی', 'history', 'تاریخچه',
            'recent', 'اخیر', 'last', 'آخرین', 'trend', 'روند', 'summary', 'خلاصه',
            'action', 'اقدام', 'event', 'رویداد', 'log', 'گزارش', 'record', 'ثبت',
            'track', 'پیگیری', 'update', 'به‌روزرسانی', 'change', 'تغییر',
            'meeting', 'جلسه', 'call', 'تماس', 'email', 'ایمیل', 'task', 'وظیفه',
            'note', 'یادداشت', 'interaction', 'تعامل', 'communication', 'ارتباط',
            'فعالیت‌ها', 'رویدادها', 'تماس‌ها', 'جلسات', 'اقدامات'
        ],
        'risk_assessment': [
            'risk', 'ریسک', 'danger', 'خطر', 'warning', 'هشدار', 'problem', 'مشکل',
            'issue', 'concern', 'نگرانی', 'threat', 'تهدید', 'vulnerability', 'آسیب‌پذیری',
            'alert', 'اخطار', 'critical', 'بحرانی', 'urgent', 'فوری', 'severe', 'شدید',
            'exposure', 'در معرض', 'potential', 'بالقوه', 'likelihood', 'احتمال',
            'impact', 'تأثیر', 'mitigation', 'کاهش', 'assessment', 'ارزیابی',
            'blocker', 'مانع', 'obstacle', 'موانع', 'challenge', 'چالش',
            'ریسک‌ها', 'خطرات', 'مشکلات', 'موانع', 'چالش‌ها'
        ],
        'search': [
            'find', 'پیدا', 'search', 'جستجو', 'look', 'گشتن', 'query', 'پرس‌وجو',
            'where', 'کجا', 'which', 'کدام', 'related', 'مرتبط', 'similar', 'مشابه',
            'retrieve', 'بازیابی', 'locate', 'یافتن', 'discover', 'کشف', 'match', 'تطبیق',
            'filter', 'فیلتر', 'list', 'لیست', 'show', 'نمایش', 'display', 'نشان',
            'get', 'گرفتن', 'fetch', 'واکشی', 'lookup', 'جستجو کردن',
            'جست‌وجو', 'پیداکردن', 'یافتن', 'نشان‌دادن', 'لیست‌کردن'
        ]
    })

    # Extended regex patterns
    routing_patterns: Dict[str, List[str]] = field(default_factory=lambda: {
        'deal_analysis': [
            r'\bdeal\s+\d+\b',
            r'\banalyze\s+deal\b',
            r'\bdeal\s+health\b',
            r'\bدیل\s+\d+\b',
            r'\bتحلیل\s+معامله\b',
            r'\bسلامت\s+معامله\b',
        ],
        'sentiment': [
            r'\bsentiment\b',
            r'\bfeeling\b',
            r'\bاحساس\b',
            r'\bتحلیل\s+احساسات\b',
        ],
        'risk_assessment': [
            r'\brisk\b',
            r'\bwarning\b',
            r'\bریسک\b',
            r'\bارزیابی\s+ریسک\b',
        ],
        'activity': [
            r'\bactivity\b',
            r'\btimeline\b',
            r'\bفعالیت\b',
            r'\bتاریخچه\b',
        ],
        'search': [
            r'\bfind\b',
            r'\bsearch\b',
            r'\bجستجو\b',
            r'\bپیدا\b',
        ]
    })

    # Ensemble configuration
    ensemble_strategy: str = 'weighted_average'  # 'weighted_average', 'winner_take_all', 'hierarchical'
    default_expert_weights: Dict[str, float] = field(default_factory=lambda: {
        'deal_analysis': 0.25,
        'sentiment': 0.20,
        'activity': 0.20,
        'risk_assessment': 0.20,
        'search': 0.15
    })
    min_expert_confidence: float = 0.5
    normalize_outputs: bool = True

    # Expert-specific thresholds
    confidence_thresholds: Dict[str, float] = field(default_factory=lambda: {
        'deal_analysis': 0.65,
        'sentiment': 0.60,
        'activity': 0.55,
        'risk_assessment': 0.70,
        'search': 0.60
    })

    # Expert timeouts (seconds)
    expert_timeouts: Dict[str, int] = field(default_factory=lambda: {
        'deal_analysis': 10,
        'sentiment': 15,
        'activity': 8,
        'risk_assessment': 10,
        'search': 20
    })

    # Performance settings
    parallel_execution: bool = True
    max_concurrent_experts: int = 5

    # Caching (SIMPLIFIED - removed YAGNI features)
    cache_expert_results: bool = True
    cache_ttl: int = 300  # 5 minutes
    max_cache_size: int = 500

    # Logging and metrics (SIMPLIFIED)
    enable_metrics: bool = True
    include_routing_info: bool = True
    metrics_dir: Path = field(default_factory=lambda: Path('./data/moe_metrics'))

    # Fallback configuration
    default_expert: str = 'search'
    enable_fallback: bool = True

    def __post_init__(self):
        """Ensure directories exist"""
        if self.metrics_dir:
            self.metrics_dir.mkdir(parents=True, exist_ok=True)


def load_moe_config() -> MoEConfig:
    """
    Load MoE configuration from environment variables.

    Returns:
        MoEConfig instance with values from environment or defaults
    """
    return MoEConfig(
        routing_strategy=os.getenv('MOE_ROUTING_STRATEGY', 'hybrid'),
        routing_confidence_threshold=float(os.getenv('MOE_ROUTING_CONFIDENCE', '0.7')),
        enable_multi_expert=os.getenv('MOE_ENABLE_MULTI_EXPERT', 'true').lower() == 'true',
        max_active_experts=int(os.getenv('MOE_MAX_ACTIVE_EXPERTS', '3')),
        ensemble_strategy=os.getenv('MOE_ENSEMBLE_STRATEGY', 'weighted_average'),
        min_expert_confidence=float(os.getenv('MOE_MIN_EXPERT_CONFIDENCE', '0.5')),
        parallel_execution=os.getenv('MOE_PARALLEL_EXECUTION', 'true').lower() == 'true',
        max_concurrent_experts=int(os.getenv('MOE_MAX_CONCURRENT', '5')),
        cache_expert_results=os.getenv('MOE_CACHE_RESULTS', 'true').lower() == 'true',
        cache_ttl=int(os.getenv('MOE_CACHE_TTL', '300')),
        max_cache_size=int(os.getenv('MOE_MAX_CACHE_SIZE', '500')),
        enable_metrics=os.getenv('MOE_ENABLE_METRICS', 'true').lower() == 'true',
        include_routing_info=os.getenv('MOE_INCLUDE_ROUTING_INFO', 'true').lower() == 'true',
        default_expert=os.getenv('MOE_DEFAULT_EXPERT', 'search'),
        enable_fallback=os.getenv('MOE_ENABLE_FALLBACK', 'true').lower() == 'true',
    )
