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


class HealthCategory:
    """Health category constants (English keys for code, Persian values for UI)"""
    HEALTHY = 'healthy'
    MEDIUM = 'medium'
    AT_RISK = 'at_risk'

    # Persian translations
    TRANSLATIONS = {
        'healthy': 'سالم',
        'medium': 'متوسط',
        'at_risk': 'در خطر'
    }

    @classmethod
    def translate(cls, key: str) -> str:
        """Get Persian translation for category key"""
        return cls.TRANSLATIONS.get(key, key)


class RiskSeverity:
    """Risk severity levels (English keys for code, Persian values for UI)"""
    CRITICAL = 'critical'
    HIGH = 'high'
    MEDIUM = 'medium'
    LOW = 'low'

    # Persian translations
    TRANSLATIONS = {
        'critical': 'بحرانی',
        'high': 'بالا',
        'medium': 'متوسط',
        'low': 'پایین'
    }

    @classmethod
    def translate(cls, key: str) -> str:
        """Get Persian translation for severity key"""
        return cls.TRANSLATIONS.get(key, key)


class RiskType:
    """Risk type constants (English keys for code, Persian descriptions for UI)"""
    LOW_HEALTH_SCORE = 'low_health_score'
    CRITICAL_INACTIVITY = 'critical_inactivity'
    HIGH_INACTIVITY = 'high_inactivity'
    MODERATE_INACTIVITY = 'moderate_inactivity'
    NO_ACTIVITY = 'no_activity'
    DEAL_AGING = 'deal_aging'

    # Persian descriptions
    DESCRIPTIONS = {
        'low_health_score': 'امتیاز سلامت پایین',
        'critical_inactivity': 'عدم فعالیت بحرانی',
        'high_inactivity': 'عدم فعالیت بالا',
        'moderate_inactivity': 'عدم فعالیت متوسط',
        'no_activity': 'هیچ فعالیتی ثبت نشده',
        'deal_aging': 'معامله قدیمی'
    }

    @classmethod
    def describe(cls, risk_type: str) -> str:
        """Get Persian description for risk type"""
        return cls.DESCRIPTIONS.get(risk_type, risk_type)


class RecommendationType:
    """Recommendation constants (English keys for code, Persian for UI)"""
    IMMEDIATE_REVIEW = 'immediate_review'
    URGENT_FOLLOWUP = 'urgent_followup'
    SCHEDULE_ACTIVITY = 'schedule_activity'
    REVIEW_COMMUNICATIONS = 'review_communications'
    UPDATE_TIMELINE = 'update_timeline'
    CONTINUE_MONITORING = 'continue_monitoring'
    START_ENGAGEMENT = 'start_engagement'
    REASSESS_SUCCESS = 'reassess_success'
    REVIEW_OBSTACLES = 'review_obstacles'

    # Persian translations
    TRANSLATIONS = {
        'immediate_review': 'بازبینی فوری استراتژی معامله',
        'urgent_followup': 'پیگیری اضطراری',
        'schedule_activity': 'برنامه‌ریزی جلسه',
        'review_communications': 'بررسی ارتباطات و رفع نگرانی‌ها',
        'update_timeline': 'بروزرسانی جدول زمانی و اطلاع‌رسانی',
        'continue_monitoring': 'ادامه نظارت - خطر بحرانی شناسایی نشد',
        'start_engagement': 'شروع فوری تعامل با مشتری',
        'reassess_success': 'ارزیابی مجدد احتمال موفقیت',
        'review_obstacles': 'بررسی موانع پیشرفت'
    }

    @classmethod
    def translate(cls, key: str) -> str:
        """Get Persian translation for recommendation"""
        return cls.TRANSLATIONS.get(key, key)