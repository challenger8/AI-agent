"""
config/rag_settings.py
---------------------
RAG system configuration for production data persistence
Manages ChromaDB persistence, embedding storage, and data lifecycle
"""

import os
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent


class RAGSettings:
    """Configuration for RAG system with persistent storage"""
    
    # ============================================================
    # PERSISTENT STORAGE PATHS
    # ============================================================
    
    # Main data directory
    DATA_DIR = Path(os.getenv('RAG_DATA_DIR', PROJECT_ROOT / "data"))
    
    # ChromaDB persistent storage
    CHROMA_DB_DIR = DATA_DIR / "chroma_db"
    CHROMA_DB_DIR.mkdir(parents=True, exist_ok=True)
    
    # Embeddings cache (for quick reloads)
    EMBEDDINGS_CACHE_DIR = DATA_DIR / "embeddings_cache"
    EMBEDDINGS_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    
    # Index metadata (tracks what's indexed)
    INDEX_METADATA_FILE = DATA_DIR / "index_metadata.json"
    
    # Backup directory
    BACKUP_DIR = DATA_DIR / "backups"
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    
    # Logs directory for RAG operations
    RAG_LOGS_DIR = PROJECT_ROOT / "logs" / "rag"
    RAG_LOGS_DIR.mkdir(parents=True, exist_ok=True)
    
    # ============================================================
    # CHROMADB CONFIGURATION
    # ============================================================
    
    # Enable persistence
    PERSIST_ENABLED = os.getenv('RAG_PERSIST_ENABLED', 'true').lower() == 'true'
    
    # ChromaDB implementation
    CHROMA_IMPL = "duckdb+parquet"  # Persistent backend
    
    # Collection settings
    CHROMA_COLLECTIONS = ['deals', 'activities', 'agents']
    
    # Vector similarity metric
    SIMILARITY_METRIC = "cosine"
    
    # ============================================================
    # EMBEDDING CONFIGURATION
    # ============================================================
    
    # Model name
    EMBEDDING_MODEL = os.getenv(
        'RAG_EMBEDDING_MODEL',
        'sentence-transformers/paraphrase-MiniLM-L6-v2'
    )
    
    # Embedding dimension (depends on model)
    EMBEDDING_DIMENSION = 384
    
    # Device for embeddings (cpu/cuda)
    EMBEDDING_DEVICE = os.getenv('RAG_EMBEDDING_DEVICE', 'cpu')
    
    # Batch size for embedding generation
    EMBEDDING_BATCH_SIZE = int(os.getenv('RAG_EMBEDDING_BATCH_SIZE', '32'))
    
    # Cache embeddings for faster reindexing
    CACHE_EMBEDDINGS = os.getenv('RAG_CACHE_EMBEDDINGS', 'true').lower() == 'true'
    
    # ============================================================
    # INDEXING CONFIGURATION
    # ============================================================
    
    # Auto-reindex on database changes
    AUTO_REINDEX = os.getenv('RAG_AUTO_REINDEX', 'false').lower() == 'true'
    
    # Reindex interval (seconds) if auto-reindex enabled
    REINDEX_INTERVAL = int(os.getenv('RAG_REINDEX_INTERVAL', '3600'))  # 1 hour
    
    # Maximum documents per collection before reindexing
    REINDEX_THRESHOLD = int(os.getenv('RAG_REINDEX_THRESHOLD', '1000'))
    
    # ============================================================
    # BACKUP CONFIGURATION
    # ============================================================
    
    # Enable automatic backups
    AUTO_BACKUP = os.getenv('RAG_AUTO_BACKUP', 'true').lower() == 'true'
    
    # Backup interval (seconds)
    BACKUP_INTERVAL = int(os.getenv('RAG_BACKUP_INTERVAL', '86400'))  # 24 hours
    
    # Keep last N backups
    BACKUP_RETENTION = int(os.getenv('RAG_BACKUP_RETENTION', '7'))
    
    # ============================================================
    # PERFORMANCE CONFIGURATION
    # ============================================================
    
    # Search result caching
    CACHE_SEARCH_RESULTS = os.getenv('RAG_CACHE_SEARCH_RESULTS', 'true').lower() == 'true'
    
    # Search result cache TTL (seconds)
    SEARCH_CACHE_TTL = int(os.getenv('RAG_SEARCH_CACHE_TTL', '300'))  # 5 minutes
    
    # Maximum search results
    MAX_SEARCH_RESULTS = int(os.getenv('RAG_MAX_SEARCH_RESULTS', '100'))
    
    # ============================================================
    # MAINTENANCE CONFIGURATION
    # ============================================================
    
    # Enable maintenance tasks
    MAINTENANCE_ENABLED = os.getenv('RAG_MAINTENANCE_ENABLED', 'true').lower() == 'true'
    
    # Cleanup old embeddings cache
    CLEANUP_CACHE_DAYS = int(os.getenv('RAG_CLEANUP_CACHE_DAYS', '30'))
    
    # Log level for RAG operations
    LOG_LEVEL = os.getenv('RAG_LOG_LEVEL', 'INFO')
    
    # ============================================================
    # ENVIRONMENT-SPECIFIC SETTINGS
    # ============================================================
    
    @classmethod
    def get_environment(cls) -> str:
        """Get current environment"""
        return os.getenv('ENVIRONMENT', 'development')
    
    @classmethod
    def is_production(cls) -> bool:
        """Check if running in production"""
        return cls.get_environment() == 'production'
    
    @classmethod
    def is_development(cls) -> bool:
        """Check if running in development"""
        return cls.get_environment() == 'development'
    
    @classmethod
    def configure_for_environment(cls):
        """Configure settings based on environment"""
        env = cls.get_environment()
        
        if env == 'production':
            logger.info("🔴 Configuring RAG for PRODUCTION")
            cls.AUTO_BACKUP = True
            cls.AUTO_REINDEX = True
            cls.PERSIST_ENABLED = True
            cls.MAINTENANCE_ENABLED = True
        elif env == 'staging':
            logger.info("🟡 Configuring RAG for STAGING")
            cls.AUTO_BACKUP = True
            cls.AUTO_REINDEX = False
            cls.PERSIST_ENABLED = True
            cls.MAINTENANCE_ENABLED = True
        else:
            logger.info("🟢 Configuring RAG for DEVELOPMENT")
            cls.AUTO_BACKUP = False
            cls.AUTO_REINDEX = False
            cls.PERSIST_ENABLED = True
            cls.MAINTENANCE_ENABLED = False
    
    @classmethod
    def get_chroma_settings(cls) -> dict:
        """Get ChromaDB settings"""
        return {
            'persist_directory': str(cls.CHROMA_DB_DIR),
            'chroma_db_impl': cls.CHROMA_IMPL,
            'anonymized_telemetry': False,
            'allow_reset': True,
        }
    
    @classmethod
    def validate_paths(cls) -> bool:
        """Validate all required paths exist"""
        paths = [
            cls.DATA_DIR,
            cls.CHROMA_DB_DIR,
            cls.EMBEDDINGS_CACHE_DIR,
            cls.BACKUP_DIR,
            cls.RAG_LOGS_DIR,
        ]
        
        for path in paths:
            if not path.exists():
                logger.warning(f"Creating path: {path}")
                path.mkdir(parents=True, exist_ok=True)
        
        return True