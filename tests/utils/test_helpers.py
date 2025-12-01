"""
tests/utils/test_helpers.py
---------------------------
Shared test utilities (DRY principle)
"""

import json
from typing import Any, Dict, Union


def parse_result(result: Any) -> Dict[str, Any]:
    """
    Parse result from tool handler - handles dict, str, or object with .text
    
    Used across integration tests for MCP tool responses.
    
    Args:
        result: Result from tool handler (dict, str, list, or object with .text)
        
    Returns:
        Parsed dictionary
        
    Examples:
        >>> parse_result({"key": "value"})
        {"key": "value"}
        
        >>> parse_result('{"key": "value"}')
        {"key": "value"}
        
        >>> class Result:
        ...     text = '{"key": "value"}'
        >>> parse_result(Result())
        {"key": "value"}
    """
    if isinstance(result, dict):
        return result
    elif isinstance(result, str):
        return json.loads(result) if result.startswith('{') else {"text": result}
    elif isinstance(result, list) and len(result) > 0:
        item = result[0]
        if hasattr(item, 'text'):
            return json.loads(item.text)
        elif isinstance(item, str):
            return json.loads(item) if item.startswith('{') else {"text": item}
        return item
    elif hasattr(result, 'text'):
        return json.loads(result.text)
    return result


def assert_valid_health_score(score: int, message: str = "") -> None:
    """
    Assert that health score is in valid range 0-100
    
    Args:
        score: Health score to validate
        message: Optional custom error message
    """
    assert isinstance(score, int), f"Health score must be int, got {type(score).__name__}. {message}"
    assert 0 <= score <= 100, f"Health score must be 0-100, got {score}. {message}"


def assert_valid_sentiment_label(label: str) -> None:
    """
    Assert that sentiment label is valid Persian sentiment
    
    Args:
        label: Sentiment label to validate
    """
    valid_labels = ['مثبت', 'خنثی', 'منفی', 'positive', 'negative', 'neutral']
    assert label in valid_labels, f"Invalid sentiment label: {label}. Must be one of {valid_labels}"