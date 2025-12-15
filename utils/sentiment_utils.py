"""
utils/sentiment_utils.py
------------------------
Unified sentiment normalization utilities.

DRY: Consolidates 40+ lines of duplicate bilingual sentiment handling
found across 3-4 service files:
- services/moe/experts/sentiment_expert.py
- services/analytics/health_calculator.py
- services/analytics/insight_generator.py
"""

from typing import Optional


class SentimentNormalizer:
    """
    Centralized sentiment normalization for Persian/English bilingual support.

    Provides consistent mapping between Persian and English sentiment labels,
    ensuring all sentiment analysis uses the same normalization logic.

    DRY: Eliminates duplicate sentiment mapping dictionaries and checks
    scattered across multiple analytics and expert files.
    """

    # Bilingual sentiment mapping (Persian → English)
    SENTIMENT_MAP = {
        # Persian labels
        'مثبت': 'positive',
        'منفی': 'negative',
        'خنثی': 'neutral',
        # English labels (identity mapping)
        'positive': 'positive',
        'negative': 'negative',
        'neutral': 'neutral',
        # Alternative spellings/variations
        'pos': 'positive',
        'neg': 'negative',
        'neut': 'neutral'
    }

    # Reverse mapping (English → Persian)
    PERSIAN_MAP = {
        'positive': 'مثبت',
        'negative': 'منفی',
        'neutral': 'خنثی'
    }

    @classmethod
    def normalize(cls, sentiment: str, default: str = 'neutral') -> str:
        """
        Normalize Persian/English sentiment to English constant.

        DRY: Replaces duplicate normalization logic in:
        - services/moe/experts/sentiment_expert.py:75-84
        - services/analytics/health_calculator.py:159
        - services/analytics/insight_generator.py:154-157

        Args:
            sentiment: Sentiment label (Persian or English)
            default: Default value if sentiment not recognized

        Returns:
            Normalized English sentiment: 'positive', 'negative', or 'neutral'

        Examples:
            >>> SentimentNormalizer.normalize('مثبت')
            'positive'
            >>> SentimentNormalizer.normalize('negative')
            'negative'
            >>> SentimentNormalizer.normalize('unknown')
            'neutral'
        """
        if not sentiment:
            return default

        # Normalize to lowercase and strip whitespace
        normalized_input = str(sentiment).strip().lower()

        return cls.SENTIMENT_MAP.get(normalized_input, default)

    @classmethod
    def to_persian(cls, sentiment: str) -> str:
        """
        Convert English sentiment to Persian.

        Args:
            sentiment: English sentiment ('positive', 'negative', 'neutral')

        Returns:
            Persian sentiment label

        Examples:
            >>> SentimentNormalizer.to_persian('positive')
            'مثبت'
        """
        normalized = cls.normalize(sentiment)
        return cls.PERSIAN_MAP.get(normalized, 'خنثی')

    @classmethod
    def is_positive(cls, sentiment: str) -> bool:
        """
        Check if sentiment is positive.

        DRY: Replaces checks like `if dominant in ['مثبت', 'positive']`

        Args:
            sentiment: Sentiment label (Persian or English)

        Returns:
            True if positive, False otherwise

        Examples:
            >>> SentimentNormalizer.is_positive('مثبت')
            True
            >>> SentimentNormalizer.is_positive('positive')
            True
            >>> SentimentNormalizer.is_positive('negative')
            False
        """
        return cls.normalize(sentiment) == 'positive'

    @classmethod
    def is_negative(cls, sentiment: str) -> bool:
        """
        Check if sentiment is negative.

        DRY: Replaces checks like `if dominant in ['منفی', 'negative']`

        Args:
            sentiment: Sentiment label (Persian or English)

        Returns:
            True if negative, False otherwise

        Examples:
            >>> SentimentNormalizer.is_negative('منفی')
            True
            >>> SentimentNormalizer.is_negative('negative')
            True
            >>> SentimentNormalizer.is_negative('positive')
            False
        """
        return cls.normalize(sentiment) == 'negative'

    @classmethod
    def is_neutral(cls, sentiment: str) -> bool:
        """
        Check if sentiment is neutral.

        Args:
            sentiment: Sentiment label (Persian or English)

        Returns:
            True if neutral, False otherwise

        Examples:
            >>> SentimentNormalizer.is_neutral('خنثی')
            True
            >>> SentimentNormalizer.is_neutral('neutral')
            True
            >>> SentimentNormalizer.is_neutral('positive')
            False
        """
        return cls.normalize(sentiment) == 'neutral'

    @classmethod
    def get_score_modifier(cls, sentiment: str, positive_bonus: int = 10, negative_penalty: int = 15) -> int:
        """
        Get score modifier based on sentiment.

        Convenience method for health score calculations that commonly
        add points for positive sentiment and subtract for negative.

        Args:
            sentiment: Sentiment label (Persian or English)
            positive_bonus: Points to add for positive sentiment
            negative_penalty: Points to subtract for negative sentiment

        Returns:
            Score modifier (positive number for bonus, negative for penalty, 0 for neutral)

        Examples:
            >>> SentimentNormalizer.get_score_modifier('مثبت')
            10
            >>> SentimentNormalizer.get_score_modifier('منفی')
            -15
            >>> SentimentNormalizer.get_score_modifier('neutral')
            0
        """
        normalized = cls.normalize(sentiment)

        if normalized == 'positive':
            return positive_bonus
        elif normalized == 'negative':
            return -negative_penalty
        else:
            return 0

    @classmethod
    def get_emoji(cls, sentiment: str) -> str:
        """
        Get emoji representation for sentiment.

        Args:
            sentiment: Sentiment label (Persian or English)

        Returns:
            Emoji string

        Examples:
            >>> SentimentNormalizer.get_emoji('positive')
            '😊'
            >>> SentimentNormalizer.get_emoji('منفی')
            '😟'
        """
        normalized = cls.normalize(sentiment)

        emoji_map = {
            'positive': '😊',
            'negative': '😟',
            'neutral': '😐'
        }

        return emoji_map.get(normalized, '😐')
