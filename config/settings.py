"""
config/settings.py
------------------
Application configuration and settings
"""

import os
from pathlib import Path
from typing import Optional

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent

# Application settings
class AppSettings:
    APP_NAME = "Persian Deal Analyzer"
    VERSION = "1.0.0"
    DEBUG = os.getenv('DEBUG', 'false').lower() == 'true'
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

# MCP Server settings
class MCPSettings:
    SERVER_NAME = "deal-activity-sentiment-analyzer"
    SERVER_VERSION = "1.0.0"
    MAX_ACTIVITIES_TIMELINE = 10
    MAX_RECOMMENDATIONS = 5

# Sentiment Analysis settings
class SentimentSettings:

    # USE_DEEPSEEK_API = os.getenv('USE_DEEPSEEK_API', 'false').lower() == 'true'
    API_KEY = os.getenv('GEMINI_API_KEY')  # Load from env
    HF_TOKEN = os.getenv('HF_TOKEN')
    MODEL_NAME = "mistralai/Mixtral-8x7B-Instruct-v0.1"# if USE_DEEPSEEK_API else "HooshvareLab/bert-fa-base-uncased-sentiment-digikala"
    
    # For DeepSeek-V3 specifics
    DEEPSEEK_PROMPT_TEMPLATE = """
    Analyze the sentiment of this Persian text as one of: مثبت (positive), خنثی (neutral), or منفی (negative).
    Text: {text}
    Sentiment: 
    """
    
    MAX_TEXT_LENGTH = 512# if not USE_DEEPSEEK_API else 8192  # DeepSeek supports longer contexts
    CACHE_SIZE = 1000
    MIN_TEXT_LENGTH = 5
    
    # Label mappings
    LABEL_MAPPING = {
        'LABEL_0': 'منفی',
        'LABEL_1': 'خنثی', 
        'LABEL_2': 'مثبت',
        'NEGATIVE': 'منفی',
        'NEUTRAL': 'خنثی',
        'POSITIVE': 'مثبت'
    }

# Analysis settings
class AnalysisSettings:
    DEFAULT_ANALYSIS_DAYS = 30
    HEALTH_SCORE_BASE = 50
    HEALTH_SCORE_MAX = 100
    
    # Health score thresholds
    HEALTH_HIGH_THRESHOLD = 70
    HEALTH_MEDIUM_THRESHOLD = 40
    
    # Activity scoring
    RECENT_ACTIVITY_BONUS = 15
    ACTIVITY_VARIETY_BONUS = 8
    TOTAL_ACTIVITY_BONUS = 2
    
    # Risk thresholds
    STALE_ACTIVITY_DAYS = 14
    AGING_DEAL_DAYS = 60
    COLD_DEAL_DAYS = 30

# Path settings
class PathSettings:
    DATABASE_DIR = PROJECT_ROOT / "database"
    SERVICES_DIR = PROJECT_ROOT / "services"
    MCP_DIR = PROJECT_ROOT / "mcp"
    LOGS_DIR = PROJECT_ROOT / "logs"
    
    @classmethod
    def ensure_directories(cls):
        """Create necessary directories"""
        cls.LOGS_DIR.mkdir(exist_ok=True)

# Feature flags
class FeatureFlags:
    SENTIMENT_ANALYSIS_ENABLED = True
    ADVANCED_ANALYTICS_ENABLED = True
    CACHING_ENABLED = True
    DETAILED_LOGGING_ENABLED = False

def get_sentiment_available() -> bool:
    """Check if sentiment analysis is available"""
    try:
        import transformers
        return FeatureFlags.SENTIMENT_ANALYSIS_ENABLED
    except ImportError:
        return False
