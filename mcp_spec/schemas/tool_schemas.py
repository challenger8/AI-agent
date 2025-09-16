"""
mcp/schemas/tool_schemas.py
---------------------------
Tool input schemas for MCP server
"""

from typing import Dict, Any

# Deal analysis schemas
ANALYZE_DEAL_SCHEMA = {
    "type": "object",
    "properties": {
        "deal_id": {
            "type": "integer",
            "description": "Deal ID to analyze"
        }
    },
    "required": ["deal_id"]
}

ANALYZE_DEALS_OVERVIEW_SCHEMA = {
    "type": "object",
    "properties": {
        "status": {
            "type": "string",
            "enum": ["در حال پیگیری", "مذاکره", "بسته شده", "لغو شده"],
            "description": "Filter by deal status (optional)"
        },
        "days": {
            "type": "integer",
            "minimum": 1,
            "maximum": 365,
            "default": 30,
            "description": "Analysis period in days"
        }
    }
}

GET_DEAL_ACTIVITIES_SCHEMA = {
    "type": "object",
    "properties": {
        "deal_id": {
            "type": "integer", 
            "description": "Deal ID"
        }
    },
    "required": ["deal_id"]
}

# Sentiment analysis schemas
ANALYZE_TEXT_SENTIMENT_SCHEMA = {
    "type": "object",
    "properties": {
        "text": {
            "type": "string",
            "minLength": 5,
            "description": "Persian text to analyze"
        }
    },
    "required": ["text"]
}

SENTIMENT_TRENDS_SCHEMA = {
    "type": "object",
    "properties": {
        "deal_id": {
            "type": "integer",
            "description": "Deal ID for sentiment trend analysis"
        },
        "days": {
            "type": "integer",
            "minimum": 1,
            "maximum": 90,
            "default": 7,
            "description": "Number of days for trend analysis"
        }
    },
    "required": ["deal_id"]
}

# Portfolio analysis schemas
PORTFOLIO_HEALTH_SCHEMA = {
    "type": "object",
    "properties": {
        "status_filter": {
            "type": "string",
            "enum": ["در حال پیگیری", "مذاکره", "بسته شده", "لغو شده"],
            "description": "Optional status filter"
        },
        "days": {
            "type": "integer",
            "minimum": 1,
            "maximum": 365,
            "default": 30,
            "description": "Analysis period in days"
        }
    }
}

def get_tool_schemas() -> Dict[str, Dict[str, Any]]:
    """Get all tool schemas"""
    return {
        "analyze_deal": ANALYZE_DEAL_SCHEMA,
        "analyze_deals_overview": ANALYZE_DEALS_OVERVIEW_SCHEMA,
        "get_deal_activities_with_sentiment": GET_DEAL_ACTIVITIES_SCHEMA,
        "analyze_text_sentiment": ANALYZE_TEXT_SENTIMENT_SCHEMA,
        "get_sentiment_trends": SENTIMENT_TRENDS_SCHEMA,
        "analyze_portfolio_health": PORTFOLIO_HEALTH_SCHEMA
    }
