"""
utils/keyword_matcher.py
------------------------
Centralized keyword matching for expert routing.
DRY: Eliminates duplicate can_handle() logic across all expert classes.
OCP: New experts can be added via configuration without modifying code.
"""

import re
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class KeywordConfig:
    """Configuration for keyword matching"""
    keywords: List[str] = field(default_factory=list)
    patterns: List[str] = field(default_factory=list)
    context_keys: List[str] = field(default_factory=list)
    keyword_score: float = 0.15
    pattern_score: float = 0.2
    context_score: float = 0.3
    min_score: float = 0.0
    max_score: float = 1.0


class KeywordMatcher:
    """
    Centralized keyword matching for query routing.

    Used by all experts for consistent can_handle() implementation.

    SOLID Principles:
    - SRP: Only handles keyword matching
    - OCP: Configurable via KeywordConfig
    - DIP: Depends on configuration, not concrete implementations
    """

    # Pre-defined configurations for each expert type
    EXPERT_CONFIGS: Dict[str, KeywordConfig] = {
        'deal_analysis': KeywordConfig(
            keywords=[
                'deal', 'معامله', 'قرارداد', 'health', 'سلامت', 'score', 'امتیاز',
                'analyze', 'تحلیل', 'performance', 'عملکرد', 'status', 'وضعیت'
            ],
            patterns=[
                r'\bdeal[\s_-]?\d+\b',
                r'\bدیل[\s_-]?\d+\b'
            ],
            context_keys=['entity_type:deal']
        ),
        'sentiment': KeywordConfig(
            keywords=[
                'sentiment', 'احساس', 'feeling', 'emotion', 'حس', 'mood', 'خلق',
                'positive', 'مثبت', 'negative', 'منفی', 'neutral', 'خنثی',
                'opinion', 'نظر', 'tone', 'لحن'
            ],
            patterns=[],
            context_keys=['analyze_sentiment:true']
        ),
        'activity': KeywordConfig(
            keywords=[
                'activity', 'فعالیت', 'timeline', 'جدول زمانی', 'history', 'تاریخچه',
                'recent', 'اخیر', 'last', 'آخرین', 'trend', 'روند', 'summary', 'خلاصه',
                'what happened', 'چه اتفاقی', 'updates', 'بروزرسانی'
            ],
            patterns=[
                r'\blast\s+\d+\s+days?\b',
                r'\brecent\b',
                r'\bthis\s+week\b',
                r'\bthis\s+month\b'
            ],
            context_keys=['entity_type:activity']
        ),
        'risk_assessment': KeywordConfig(
            keywords=[
                'risk', 'ریسک', 'danger', 'خطر', 'warning', 'هشدار', 'problem', 'مشکل',
                'issue', 'concern', 'نگرانی', 'threat', 'تهدید', 'vulnerability', 'آسیب‌پذیری',
                'at risk', 'failing', 'delayed', 'تاخیر', 'lost', 'از دست رفته'
            ],
            patterns=[
                r'\bwhat.*risk\b',
                r'\bcheck.*risk\b',
                r'\brisk.*assessment\b',
                r'\bidentify.*problem\b'
            ],
            context_keys=['check_risks:true']
        ),
        'search': KeywordConfig(
            keywords=[
                'find', 'پیدا', 'search', 'جستجو', 'look', 'گشتن', 'query', 'پرس‌وجو',
                'where', 'کجا', 'which', 'کدام', 'related', 'مرتبط', 'similar', 'مشابه',
                'show me', 'نشان بده', 'list', 'لیست', 'get', 'بگیر'
            ],
            patterns=[
                r'^(what|where|which|who|how)\s',
                r'^(چه|کجا|کدام|چگونه)\s',
                r'\?$'
            ],
            context_keys=['search_mode:true'],
            min_score=0.3  # Search has higher minimum (fallback expert)
        )
    }

    def __init__(self, config: Optional[KeywordConfig] = None):
        """
        Initialize matcher with optional config.

        Args:
            config: KeywordConfig or None (use default)
        """
        self.config = config or KeywordConfig()
        self._compiled_patterns: List[re.Pattern] = []
        self._compile_patterns()

    def _compile_patterns(self):
        """Pre-compile regex patterns for performance"""
        self._compiled_patterns = []
        for pattern in self.config.patterns:
            try:
                self._compiled_patterns.append(re.compile(pattern, re.IGNORECASE))
            except re.error as e:
                logger.warning(f"Invalid regex pattern '{pattern}': {e}")

    @classmethod
    def for_expert(cls, expert_type: str) -> 'KeywordMatcher':
        """
        Create a matcher configured for a specific expert type.

        Args:
            expert_type: Type of expert

        Returns:
            Configured KeywordMatcher instance
        """
        config = cls.EXPERT_CONFIGS.get(expert_type, KeywordConfig())
        return cls(config)

    def calculate_score(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> float:
        """
        Calculate relevance score for a query.

        Args:
            query: User query string
            context: Optional context dictionary

        Returns:
            Score between 0.0 and 1.0
        """
        context = context or {}
        query_lower = query.lower()
        score = 0.0

        # Score from keywords
        score += self._score_keywords(query_lower)

        # Score from patterns
        score += self._score_patterns(query_lower)

        # Score from context
        score += self._score_context(context)

        # Check Persian text ratio (bonus for sentiment)
        if self._has_high_persian_ratio(query):
            score += 0.1

        # Apply min/max bounds
        score = max(self.config.min_score, min(score, self.config.max_score))

        return score

    def _score_keywords(self, query_lower: str) -> float:
        """Score based on keyword matches"""
        score = 0.0
        for keyword in self.config.keywords:
            if keyword.lower() in query_lower:
                score += self.config.keyword_score
        return score

    def _score_patterns(self, query_lower: str) -> float:
        """Score based on pattern matches"""
        score = 0.0
        for pattern in self._compiled_patterns:
            if pattern.search(query_lower):
                score += self.config.pattern_score
        return score

    def _score_context(self, context: Dict[str, Any]) -> float:
        """Score based on context keys"""
        score = 0.0
        for context_key in self.config.context_keys:
            if ':' in context_key:
                key, expected_value = context_key.split(':', 1)
                actual_value = str(context.get(key, '')).lower()
                if actual_value == expected_value.lower():
                    score += self.config.context_score
            elif context.get(context_key):
                score += self.config.context_score
        return score

    @staticmethod
    def _has_high_persian_ratio(query: str, threshold: float = 0.3) -> bool:
        """Check if query has high ratio of Persian characters"""
        if not query:
            return False
        persian_chars = sum(1 for c in query if '\u0600' <= c <= '\u06FF')
        return persian_chars > len(query) * threshold

    def matches_any_keyword(self, query: str) -> bool:
        """Check if query matches any keyword"""
        query_lower = query.lower()
        return any(kw.lower() in query_lower for kw in self.config.keywords)

    def get_matched_keywords(self, query: str) -> Set[str]:
        """Get set of matched keywords"""
        query_lower = query.lower()
        return {kw for kw in self.config.keywords if kw.lower() in query_lower}


class DealIdExtractor:
    """
    Utility for extracting deal IDs from queries.

    Centralizes _extract_deal_id() logic used by multiple experts.
    """

    # Patterns ordered by specificity
    PATTERNS = [
        r'\bdeal[\s_-]?(\d+)\b',      # English: deal123, deal-123
        r'\bدیل[\s_-]?(\d+)\b',        # Persian: دیل123
        r'\bقرارداد[\s_-]?(\d+)\b',    # Persian: قرارداد123
        r'\bمعامله[\s_-]?(\d+)\b',     # Persian: معامله123
    ]

    # Indicators that suggest the query is about deals
    DEAL_INDICATORS = ['deal', 'دیل', 'قرارداد', 'معامله', 'analyze', 'تحلیل']

    @classmethod
    def extract(
        cls,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Extract deal ID from query or context.

        Args:
            query: User query string
            context: Optional context dict

        Returns:
            Deal ID string or None
        """
        context = context or {}

        # Priority 1: Context
        if context.get('deal_id'):
            return str(context['deal_id'])

        # Priority 2: Specific patterns
        query_lower = query.lower()
        for pattern in cls.PATTERNS:
            match = re.search(pattern, query_lower, re.IGNORECASE)
            if match:
                return match.group(1)

        # Priority 3: Fallback - standalone number if deal-related
        if any(indicator in query_lower for indicator in cls.DEAL_INDICATORS):
            fallback_match = re.search(r'\b(\d+)\b', query)
            if fallback_match:
                return fallback_match.group(1)

        return None

    @classmethod
    def has_deal_id(
        cls,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Check if query/context contains a deal ID"""
        return cls.extract(query, context) is not None


# Convenience functions
def calculate_relevance_score(
    expert_type: str,
    query: str,
    context: Optional[Dict[str, Any]] = None
) -> float:
    """Calculate relevance score for an expert type"""
    matcher = KeywordMatcher.for_expert(expert_type)
    return matcher.calculate_score(query, context)


def extract_deal_id(
    query: str,
    context: Optional[Dict[str, Any]] = None
) -> Optional[str]:
    """Extract deal ID from query/context"""
    return DealIdExtractor.extract(query, context)
