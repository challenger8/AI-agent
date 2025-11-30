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