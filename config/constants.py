# config/constants.py (CREATE THIS FILE)
"""
Centralized constants for Persian Deal Analyzer
No more magic numbers scattered everywhere!
"""

class ConfidenceConfig:
    """Confidence calculation constants"""
    BASE_SCORE = 0.7
    SUCCESS_BOOST = 0.1
    DATA_PRESENCE_BOOST = 0.1
    SECONDARY_BOOST = 0.05
    MAX_CONFIDENCE = 1.0


class ExpertBoostKeys:
    """Keys that boost confidence for each expert type"""
    DEAL_ANALYSIS = ['health_score', 'recommendations', 'insights']
    RISK_ASSESSMENT = ['risk_indicators', 'recommendations', 'mitigation_actions']
    ACTIVITY = ['total_activities', 'timeline', 'frequency']
    SENTIMENT = ['sentiment', 'confidence', 'distribution']
    SEARCH = ['results', 'matches', 'relevance_scores']


class CacheConfig:
    """Cache service configuration constants"""
    # Connection timeouts
    SOCKET_CONNECT_TIMEOUT = 5  # seconds
    SOCKET_TIMEOUT = 5  # seconds
    MAX_CONNECTIONS = 10

    # Two-level cache sizes
    DEFAULT_L1_CACHE_SIZE = 100
    LARGE_L1_CACHE_SIZE = 200
    SMALL_L1_CACHE_SIZE = 50


class RiskAnalysisConfig:
    """Risk analysis configuration constants"""
    # Portfolio analysis limits (for performance)
    MAX_DEALS_TO_ANALYZE = 50
    MAX_HIGH_RISK_DEALS_TO_SHOW = 3

    # Risk percentage thresholds
    CRITICAL_RISK_PERCENTAGE = 30.0  # % of deals at high risk
    WARNING_RISK_PERCENTAGE = 15.0


class RepositoryConfig:
    """Repository configuration constants"""
    # Default field names
    DEFAULT_ID_FIELD = 'id'
    DEAL_ID_FIELD = 'Id'  # Deal model uses uppercase

    # Common excluded fields for updates
    EXCLUDE_TIMESTAMP_FIELDS = ['created_at', 'updated_at', 'last_update_time']