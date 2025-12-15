"""
services/moe/base_expert.py
---------------------------
Abstract base class for all experts in the Mixture of Experts system.
REFACTORED: Uses centralized KeywordMatcher and DealIdExtractor.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime

from utils.logging_config import get_logger
from utils.exceptions import ServiceError
from utils.mixins import CacheableMixin
from utils.keyword_matcher import KeywordMatcher, DealIdExtractor
from config.constants import ConfidenceConfig

@dataclass
class ExpertResult:
    """Result from an expert analysis"""
    expert_type: str
    success: bool
    data: Dict[str, Any]
    confidence: float  # 0-1 confidence score
    reasoning: str = ""
    execution_time_ms: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'expert_type': self.expert_type,
            'success': self.success,
            'data': self.data,
            'confidence': self.confidence,
            'reasoning': self.reasoning,
            'execution_time_ms': self.execution_time_ms,
            'timestamp': self.timestamp.isoformat(),
            'metadata': self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ExpertResult':
        """Create from dictionary"""
        timestamp = data.get('timestamp')
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        elif timestamp is None:
            timestamp = datetime.now()

        return cls(
            expert_type=data['expert_type'],
            success=data['success'],
            data=data.get('data', {}),
            confidence=data.get('confidence', 0.0),
            reasoning=data.get('reasoning', ''),
            execution_time_ms=data.get('execution_time_ms', 0.0),
            timestamp=timestamp,
            metadata=data.get('metadata', {})
        )

    def is_high_confidence(self, threshold: float = 0.7) -> bool:
        """Check if result is high confidence"""
        return self.confidence >= threshold

    @staticmethod
    def error_result(expert_type: str, error_message: str) -> 'ExpertResult':
        """Create an error result"""
        return ExpertResult(
            expert_type=expert_type,
            success=False,
            data={'error': error_message},
            confidence=0.0,
            reasoning=f"Expert failed: {error_message}"
        )


class BaseExpert(CacheableMixin, ABC):
    """
    Abstract base class for all experts.

    REFACTORED: Now uses CacheableMixin for DRY cache operations.
    """

    def __init__(self, repositories=None, services: Dict[str, Any] = None):
        """
        Initialize base expert

        Args:
            repositories: Database repositories instance
            services: Dictionary of available services
        """
        super().__init__()
        self.repositories = repositories
        self.services = services or {}
        self.logger = get_logger(self.__class__.__name__)
        self._metrics = {
            'total_calls': 0,
            'successful_calls': 0,
            'failed_calls': 0,
            'total_execution_time_ms': 0.0,
            'average_confidence': 0.0
        }

    @property
    @abstractmethod
    def expert_type(self) -> str:
        """Return the expert type identifier"""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Return a description of this expert's capabilities"""
        pass

    @property
    def supported_query_types(self) -> List[str]:
        """Return list of query types this expert can handle"""
        return [self.expert_type]
    @property
    def confidence_boost_keys(self) -> List[str]:
        """
        Override in subclass to specify which result keys boost confidence.
        
        Returns:
            List of keys that indicate high-quality results
        """
        return []
    
    def calculate_confidence(self, query: str, result: Dict[str, Any]) -> float:
        """
        Calculate confidence score for the result.
        
        Uses base score + boosts for data presence.
        Override confidence_boost_keys in subclass to customize.
        
        Args:
            query: Original query
            result: Result dictionary
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        if not result or 'error' in result:
            return 0.0
        
        confidence = ConfidenceConfig.BASE_SCORE
        
        # Apply boosts for each key present
        boost_keys = self.confidence_boost_keys
        primary_keys = boost_keys[:2] if len(boost_keys) >= 2 else boost_keys
        secondary_keys = boost_keys[2:] if len(boost_keys) > 2 else []
        
        for key in primary_keys:
            if self._has_meaningful_value(result, key):
                confidence += ConfidenceConfig.DATA_PRESENCE_BOOST
        
        for key in secondary_keys:
            if self._has_meaningful_value(result, key):
                confidence += ConfidenceConfig.SECONDARY_BOOST
        
        return min(confidence, ConfidenceConfig.MAX_CONFIDENCE)
    
    def _has_meaningful_value(self, result: Dict, key: str) -> bool:
        """Check if key has a meaningful (non-empty) value"""
        value = result.get(key)
        if value is None:
            return False
        if isinstance(value, (list, dict, str)) and len(value) == 0:
            return False
        if isinstance(value, (int, float)) and value == 0:
            return False
        return True
    @abstractmethod
    async def analyze(self, query: str, context: Dict[str, Any] = None) -> ExpertResult:
        """
        Perform analysis based on query

        Args:
            query: The input query or text to analyze
            context: Additional context for the analysis

        Returns:
            ExpertResult with analysis results
        """
        pass

    

    def can_handle(self, query: str, context: Dict[str, Any] = None) -> float:
        """
        Determine if this expert can handle the query

        Args:
            query: The input query
            context: Additional context

        Returns:
            Confidence score (0-1) that this expert can handle the query
        """
        # Default implementation - override in subclasses
        return 0.5

    def preprocess_query(self, query: str) -> str:
        """
        Preprocess the query before analysis

        Args:
            query: Raw input query

        Returns:
            Preprocessed query
        """
        # Default: trim whitespace
        return query.strip()

    def postprocess_result(self, result: ExpertResult) -> ExpertResult:
        """
        Postprocess the result after analysis

        Args:
            result: Raw expert result

        Returns:
            Postprocessed result
        """
        # Default: no postprocessing
        return result

    async def execute(self, query: str, context: Dict[str, Any] = None) -> ExpertResult:
        """
        Execute the expert analysis with timing and error handling

        Args:
            query: Input query
            context: Additional context

        Returns:
            ExpertResult with analysis
        """
        import time
        start_time = time.time()

        self._metrics['total_calls'] += 1

        try:
            # Preprocess query
            processed_query = self.preprocess_query(query)

            # Perform analysis
            result = await self.analyze(processed_query, context)

            # Calculate execution time
            execution_time_ms = (time.time() - start_time) * 1000
            result.execution_time_ms = execution_time_ms

            # Postprocess result
            result = self.postprocess_result(result)

            # Update metrics
            if result.success:
                self._metrics['successful_calls'] += 1
            else:
                self._metrics['failed_calls'] += 1

            self._metrics['total_execution_time_ms'] += execution_time_ms

            # Update average confidence
            total = self._metrics['total_calls']
            avg = self._metrics['average_confidence']
            self._metrics['average_confidence'] = (avg * (total - 1) + result.confidence) / total

            self.logger.debug(
                f"Expert {self.expert_type} completed in {execution_time_ms:.2f}ms "
                f"with confidence {result.confidence:.2f}"
            )

            return result

        except Exception as e:
            self.logger.error(f"Expert {self.expert_type} failed: {str(e)}")
            self._metrics['failed_calls'] += 1

            execution_time_ms = (time.time() - start_time) * 1000

            return ExpertResult(
                expert_type=self.expert_type,
                success=False,
                data={'error': str(e)},
                confidence=0.0,
                reasoning=f"Expert execution failed: {str(e)}",
                execution_time_ms=execution_time_ms
            )

    def get_metrics(self) -> Dict[str, Any]:
        """Get expert performance metrics"""
        metrics = self._metrics.copy()
        if metrics['total_calls'] > 0:
            metrics['success_rate'] = metrics['successful_calls'] / metrics['total_calls']
            metrics['average_execution_time_ms'] = (
                metrics['total_execution_time_ms'] / metrics['total_calls']
            )
        else:
            metrics['success_rate'] = 0.0
            metrics['average_execution_time_ms'] = 0.0
        return metrics

    def reset_metrics(self):
        """Reset expert metrics"""
        self._metrics = {
            'total_calls': 0,
            'successful_calls': 0,
            'failed_calls': 0,
            'total_execution_time_ms': 0.0,
            'average_confidence': 0.0
        }

    # Cache methods inherited from CacheableMixin:
    # - _get_from_cache(key)
    # - _set_cache(key, value)
    # - _clear_cache()
    # - _has_cache(key)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(type={self.expert_type})"
    def _extract_deal_id(self, query: str, context: Dict[str, Any] = None) -> Optional[str]:
        """
        Extract deal ID from query or context.

        Uses centralized DealIdExtractor utility.

        Args:
            query: User query string
            context: Optional context dict

        Returns:
            Deal ID string or None if not found
        """
        return DealIdExtractor.extract(query, context)

    def _get_keyword_matcher(self) -> KeywordMatcher:
        """
        Get keyword matcher for this expert type.

        Uses centralized KeywordMatcher utility.

        Returns:
            KeywordMatcher configured for this expert
        """
        return KeywordMatcher.for_expert(self.expert_type)