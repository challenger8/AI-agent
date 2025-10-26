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
    # Model configuration
    API_KEY = os.getenv('GEMINI_API_KEY')
    HF_TOKEN = os.getenv('HF_TOKEN')
    MODEL_NAME = "Qwen/Qwen2-0.5B-Instruct"
    
    # Use prompt-based sentiment analysis instead of classification pipeline
    USE_PROMPT_BASED = True
    
    # Prompt template
    DEEPSEEK_PROMPT_TEMPLATE = """Analyze the sentiment of this Persian text as one of: مثبت (positive), خنثی (neutral), or منفی (negative).
Text: {text}
Sentiment:"""
    
    # Text generation settings
    MAX_NEW_TOKENS = 10  # Short response expected
    TEMPERATURE = 0.1   # Low randomness for consistent results
    TOP_P = 0.9
    
    # Text length settings
    MAX_TEXT_LENGTH = 512
    CACHE_SIZE = 1000
    MIN_TEXT_LENGTH = 5
    
    # Label mappings - map text output to normalized sentiment
    LABEL_MAPPING = {
        'LABEL_0': 'منفی',
        'LABEL_1': 'خنثی', 
        'LABEL_2': 'مثبت',
        'NEGATIVE': 'منفی',
        'negative': 'منفی',
        'NEUTRAL': 'خنثی',
        'POSITIVE': 'مثبت',
        'positive': 'مثبت'
    }
    # Label mappings
    

# Analysis settings
class AnalysisSettings:
    DEFAULT_ANALYSIS_DAYS = 30
    HEALTH_SCORE_BASE = 50
    HEALTH_SCORE_MAX = 100
    
    # Health score thresholds
    HEALTH_HIGH_THRESHOLD = 70
    HEALTH_MEDIUM_THRESHOLD = 40
    
    # Deal Status Definitions
    DEAL_STATUS_WON = ['Won', 'بسته شده', 'closed_won', 'completed']
    DEAL_STATUS_LOST = ['Lost', 'لغو شده', 'cancelled', 'failed']
    DEAL_STATUS_OPEN = ['در حال پیگیری', 'در حال', 'in_progress', 'open', 'active','Pending']
    
    # Inactivity thresholds (UNIFIED - used consistently across scoring and risk detection)
    INACTIVITY_RECENT_DAYS = 7      # Recent activity (bonus applies)
    INACTIVITY_WARNING_DAYS = 14    # Starting to worry (reduced bonus)
    INACTIVITY_CONCERN_DAYS = 30    # Should take action (penalty applies)
    INACTIVITY_CRITICAL_DAYS = 60   # Critical inactivity (high penalty)
    
    # Activity scoring
    RECENT_ACTIVITY_BONUS = 15
    ACTIVITY_VARIETY_BONUS = 8
    TOTAL_ACTIVITY_BONUS = 2
    
    # Open Deal Scoring - Thresholds
    OPEN_DEAL_BASE_SCORE = 50
    OPEN_DEAL_NO_ACTIVITIES_PENALTY = 30
    OPEN_DEAL_WARNING_INACTIVITY_PENALTY = 15    # 14-30 days
    OPEN_DEAL_CONCERN_INACTIVITY_PENALTY = 30    # 30-60 days
    OPEN_DEAL_CRITICAL_INACTIVITY_PENALTY = 40   # 60+ days
    
    # Closed Deal Scoring
    WON_DEAL_BASE_SCORE = 85        # Won deals start high
    LOST_DEAL_BASE_SCORE = 20       # Lost deals stay low
    
    # Activity scoring
    ACTIVITY_FREQUENCY_LOW = 3      # Less than 3 = low
    ACTIVITY_FREQUENCY_MEDIUM = 5   # 3-5 = medium
    ACTIVITY_FREQUENCY_HIGH = 10    # 5-10 = high
    
    ACTIVITY_VARIETY_THRESHOLD = 3  # At least 3 different types
    
    # Sentiment scoring (for open deals)
    POSITIVE_SENTIMENT_BONUS = 15
    NEGATIVE_SENTIMENT_PENALTY = 20  # Changed from -25 (was asymmetric)
    SENTIMENT_CONFIDENCE_THRESHOLD = 0.60  # Only apply if confident
    
    # Risk thresholds (renamed for clarity - only for OPEN deals)
    OPEN_DEAL_STALE_ACTIVITY_DAYS = 14
    AGING_DEAL_DAYS = 60
    OPEN_DEAL_CRITICAL_ACTIVITY_DAYS = 30


# Path settings
class PathSettings:
    DATABASE_DIR = PROJECT_ROOT / "database"
    SERVICES_DIR = PROJECT_ROOT / "services"
    MCP_DIR = PROJECT_ROOT / "mcp_spec"
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
    STT_ENABLED = True 
class STTSettings:
    """Speech-to-Text configuration"""
    
    # Model configuration - matching sentiment pattern
    HF_TOKEN = os.getenv('HF_TOKEN')  # Use same token as sentiment
    MODEL_NAME = "vhdm/whisper-large-fa-v1"  # Persian-optimized Whisper Large
    USE_TRANSFORMERS = True  # Use HuggingFace transformers
    
    # Cache configuration - use project's models directory
    CACHE_DIR = PROJECT_ROOT / "models"
    
    # Audio processing
    AUDIO_DIR = Path(os.getenv('AUDIO_DIR', PROJECT_ROOT / "audio_files"))
    SUPPORTED_FORMATS = ['.mp3', '.wav', '.m4a', '.flac', '.ogg', '.webm']
    MAX_AUDIO_SIZE_MB = 100
    SAMPLE_RATE = 16000  # Whisper expects 16kHz
    
    # Transcription settings
    LANGUAGE = "fa"  # Persian/Farsi
    TASK = "transcribe"  # Options: transcribe, translate
    
    # Transformers-specific settings
    CHUNK_LENGTH_S = 30  # Process audio in 30-second chunks
    BATCH_SIZE = 16
    RETURN_TIMESTAMPS = True
    
    # Performance
    USE_GPU = False  # Set to False if no GPU available
    TORCH_DTYPE = "float16"  # float16 for GPU, float32 for CPU
    
    # Cache settings
    CACHE_TRANSCRIPTIONS = True
    CACHE_TTL_SECONDS = 3600 * 24 * 7  # 1 week
    MODEL_SIZE = "large"          # For logging: model name
    FP16 = True                   # Use float16 for GPU
    BEAM_SIZE = 5                 # Beam search width
    BEST_OF = 5                   # Number of candidates to evaluate
    TEMPERATURE = 0.0   
    @classmethod
    def ensure_directories(cls):
        """Create necessary directories"""
        cls.AUDIO_DIR.mkdir(exist_ok=True)
        cls.CACHE_DIR.mkdir(exist_ok=True)


def get_stt_available() -> bool:
    """Check if STT is available"""
    try:
        import transformers  # ✅ Check for transformers (Hugging Face)
        import torch  # ✅ Also check for torch
        return FeatureFlags.STT_ENABLED
    except ImportError:
        return False
def get_sentiment_available() -> bool:
    """Check if sentiment analysis is available"""
    try:
        import transformers
        return FeatureFlags.SENTIMENT_ANALYSIS_ENABLED
    except ImportError:
        return False
