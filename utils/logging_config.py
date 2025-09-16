"""
utils/logging_config.py
-----------------------
Centralized logging configuration
"""

import logging
import sys
from pathlib import Path
from typing import Optional

from config.settings import AppSettings, PathSettings

def setup_logging(
    level: Optional[str] = None,
    log_file: Optional[str] = None,
    detailed: bool = False
) -> logging.Logger:
    """
    Setup application logging configuration
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR)
        log_file: Optional log file path
        detailed: Whether to use detailed formatting
    
    Returns:
        Configured logger instance
    """
    # Ensure logs directory exists
    PathSettings.ensure_directories()
    
    # Set log level
    log_level = getattr(logging, (level or AppSettings.LOG_LEVEL).upper(), logging.INFO)
    
    # Create formatters
    if detailed:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    # Create handlers
    handlers = []
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)
    handlers.append(console_handler)
    
    # File handler (optional)
    if log_file:
        log_path = PathSettings.LOGS_DIR / log_file
        file_handler = logging.FileHandler(log_path, encoding='utf-8')
        file_handler.setFormatter(formatter)
        file_handler.setLevel(log_level)
        handlers.append(file_handler)
    
    # Configure root logger
    logging.basicConfig(
        level=log_level,
        handlers=handlers,
        force=True
    )
    
    # Create application logger
    logger = logging.getLogger(AppSettings.APP_NAME)
    logger.setLevel(log_level)
    
    return logger

def get_logger(name: str) -> logging.Logger:
    """Get a logger for a specific module"""
    return logging.getLogger(f"{AppSettings.APP_NAME}.{name}")
