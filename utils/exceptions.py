"""
utils/exceptions.py
-------------------
Custom exceptions for the Persian Deal Analyzer
"""

class PersianDealAnalyzerError(Exception):
    """Base exception for the application"""
    pass

class DatabaseError(PersianDealAnalyzerError):
    """Database-related errors"""
    pass

class ServiceError(PersianDealAnalyzerError):
    """Service layer errors"""
    pass

class SentimentAnalysisError(ServiceError):
    """Sentiment analysis specific errors"""
    pass

class ValidationError(PersianDealAnalyzerError):
    """Input validation errors"""
    pass

class ConfigurationError(PersianDealAnalyzerError):
    """Configuration-related errors"""
    pass

class MCPServerError(PersianDealAnalyzerError):
    """MCP server specific errors"""
    pass
