"""
utils/__init__.py
-----------------
Utility modules for Persian Deal Analyzer
"""

from utils.date_utils import DateUtils, parse_iso_date, days_since
from utils.activity_utils import ActivityUtils, days_since_last_activity, has_recent_activity
from utils.deal_status_detector import (
    DealStatusDetector,
    DealStatus,
    detect_deal_status,
    is_deal_won,
    is_deal_lost,
    is_deal_open
)
from utils.keyword_matcher import (
    KeywordMatcher,
    KeywordConfig,
    DealIdExtractor,
    calculate_relevance_score,
    extract_deal_id
)
from utils.exceptions import (
    PersianDealAnalyzerError,
    DatabaseError,
    ServiceError,
    SentimentAnalysisError,
    ValidationError,
    ConfigurationError,
    MCPServerError
)
from utils.model_utils import ensure_dict, get_id_from_entity

__all__ = [
    # Date utilities
    'DateUtils',
    'parse_iso_date',
    'days_since',

    # Activity utilities
    'ActivityUtils',
    'days_since_last_activity',
    'has_recent_activity',

    # Deal status detection
    'DealStatusDetector',
    'DealStatus',
    'detect_deal_status',
    'is_deal_won',
    'is_deal_lost',
    'is_deal_open',

    # Keyword matching
    'KeywordMatcher',
    'KeywordConfig',
    'DealIdExtractor',
    'calculate_relevance_score',
    'extract_deal_id',

    # Exceptions
    'PersianDealAnalyzerError',
    'DatabaseError',
    'ServiceError',
    'SentimentAnalysisError',
    'ValidationError',
    'ConfigurationError',
    'MCPServerError',

    # Model utilities
    'ensure_dict',
    'get_id_from_entity',
]
