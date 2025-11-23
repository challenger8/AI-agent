"""
services/moe/expert_ensemble.py
-------------------------------
Expert ensemble for combining outputs from multiple experts
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List
from datetime import datetime

from config.moe_settings import MoESettings
from .base_expert import ExpertResult
from utils.logging_config import get_logger


@dataclass
class EnsembleResult:
    """Result from ensemble combination"""
    query: str
    expert_results: List[ExpertResult]
    combined_data: Dict[str, Any]
    combined_confidence: float
    strategy_used: str
    primary_expert: str
    reasoning: str
    execution_time_ms: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'query': self.query,
            'expert_results': [r.to_dict() for r in self.expert_results],
            'combined_data': self.combined_data,
            'combined_confidence': self.combined_confidence,
            'strategy_used': self.strategy_used,
            'primary_expert': self.primary_expert,
            'reasoning': self.reasoning,
            'execution_time_ms': self.execution_time_ms,
            'timestamp': self.timestamp.isoformat(),
            'metadata': self.metadata
        }

    @property
    def is_successful(self) -> bool:
        """Check if ensemble result is successful"""
        return any(r.success for r in self.expert_results)

    @property
    def num_experts(self) -> int:
        """Number of experts that contributed"""
        return len([r for r in self.expert_results if r.success])


class ExpertEnsemble:
    """Combines outputs from multiple experts"""

    def __init__(self):
        """Initialize expert ensemble"""
        self.logger = get_logger(self.__class__.__name__)
        self._metrics = {
            'total_ensembles': 0,
            'by_strategy': {
                'weighted_average': 0,
                'winner_take_all': 0,
                'hierarchical': 0
            },
            'average_experts_per_ensemble': 0.0
        }

    def combine(
        self,
        query: str,
        expert_results: List[ExpertResult],
        weights: Dict[str, float] = None
    ) -> EnsembleResult:
        """
        Combine results from multiple experts

        Args:
            query: Original query
            expert_results: List of expert results
            weights: Optional custom weights for experts

        Returns:
            EnsembleResult with combined output
        """
        import time
        start_time = time.time()

        self._metrics['total_ensembles'] += 1

        # Filter successful results
        successful_results = [r for r in expert_results if r.success]

        if not successful_results:
            # No successful results
            return EnsembleResult(
                query=query,
                expert_results=expert_results,
                combined_data={'error': 'All experts failed'},
                combined_confidence=0.0,
                strategy_used='none',
                primary_expert='none',
                reasoning='All experts failed to provide results',
                execution_time_ms=(time.time() - start_time) * 1000
            )

        # Use configured strategy
        strategy = MoESettings.ENSEMBLE_STRATEGY

        if strategy == 'weighted_average':
            result = self._weighted_average_combine(query, successful_results, weights)
        elif strategy == 'winner_take_all':
            result = self._winner_take_all_combine(query, successful_results)
        else:  # hierarchical
            result = self._hierarchical_combine(query, successful_results, weights)

        # Update metrics
        self._metrics['by_strategy'][strategy] += 1
        total = self._metrics['total_ensembles']
        avg = self._metrics['average_experts_per_ensemble']
        self._metrics['average_experts_per_ensemble'] = (
            avg * (total - 1) + len(successful_results)
        ) / total

        result.execution_time_ms = (time.time() - start_time) * 1000
        result.expert_results = expert_results  # Include all results

        return result

    def _weighted_average_combine(
        self,
        query: str,
        results: List[ExpertResult],
        weights: Dict[str, float] = None
    ) -> EnsembleResult:
        """Combine using weighted average of expert outputs"""
        weights = weights or MoESettings.DEFAULT_EXPERT_WEIGHTS

        combined_data = {}
        total_weight = 0.0
        weighted_confidence = 0.0

        # Track primary expert (highest weighted contribution)
        primary_expert = None
        max_contribution = 0.0

        for result in results:
            expert_type = result.expert_type
            weight = weights.get(expert_type, 0.2)

            # Skip low confidence results
            if result.confidence < MoESettings.MIN_EXPERT_CONFIDENCE:
                continue

            # Calculate contribution
            contribution = weight * result.confidence
            if contribution > max_contribution:
                max_contribution = contribution
                primary_expert = expert_type

            total_weight += weight
            weighted_confidence += contribution

            # Merge data
            for key, value in result.data.items():
                if key not in combined_data:
                    combined_data[key] = value
                elif isinstance(value, list) and isinstance(combined_data[key], list):
                    combined_data[key].extend(value)
                elif isinstance(value, dict) and isinstance(combined_data[key], dict):
                    combined_data[key].update(value)
                else:
                    # Create list for conflicting scalar values
                    if not isinstance(combined_data[key], list):
                        combined_data[key] = [combined_data[key]]
                    combined_data[key].append(value)

        # Calculate combined confidence
        combined_confidence = weighted_confidence / total_weight if total_weight > 0 else 0.0

        reasoning = (
            f"Combined {len(results)} expert results using weighted average. "
            f"Primary expert: {primary_expert}"
        )

        return EnsembleResult(
            query=query,
            expert_results=results,
            combined_data=combined_data,
            combined_confidence=combined_confidence,
            strategy_used='weighted_average',
            primary_expert=primary_expert or results[0].expert_type,
            reasoning=reasoning
        )

    def _winner_take_all_combine(
        self,
        query: str,
        results: List[ExpertResult]
    ) -> EnsembleResult:
        """Use only the highest confidence expert's output"""
        # Find highest confidence result
        best_result = max(results, key=lambda r: r.confidence)

        reasoning = (
            f"Selected {best_result.expert_type} as winner with "
            f"confidence {best_result.confidence:.2f}"
        )

        return EnsembleResult(
            query=query,
            expert_results=results,
            combined_data=best_result.data,
            combined_confidence=best_result.confidence,
            strategy_used='winner_take_all',
            primary_expert=best_result.expert_type,
            reasoning=reasoning
        )

    def _hierarchical_combine(
        self,
        query: str,
        results: List[ExpertResult],
        weights: Dict[str, float] = None
    ) -> EnsembleResult:
        """Hierarchical combination with primary expert and secondary verification"""
        weights = weights or MoESettings.DEFAULT_EXPERT_WEIGHTS

        # Sort by weighted contribution
        sorted_results = sorted(
            results,
            key=lambda r: weights.get(r.expert_type, 0.2) * r.confidence,
            reverse=True
        )

        primary_result = sorted_results[0]
        combined_data = primary_result.data.copy()

        # Add supplementary data from other experts
        supplementary_experts = []
        for result in sorted_results[1:]:
            if result.confidence >= MoESettings.MIN_EXPERT_CONFIDENCE:
                supplementary_experts.append(result.expert_type)

                # Add non-conflicting data
                for key, value in result.data.items():
                    if key not in combined_data:
                        combined_data[key] = value
                    elif key == 'recommendations' and isinstance(value, list):
                        if isinstance(combined_data[key], list):
                            combined_data[key].extend(value)
                    elif key == 'risk_indicators' and isinstance(value, list):
                        if isinstance(combined_data[key], list):
                            combined_data[key].extend(value)

        # Calculate combined confidence
        combined_confidence = primary_result.confidence
        if supplementary_experts:
            # Slight boost for verification
            combined_confidence = min(combined_confidence + 0.05, 1.0)

        reasoning = (
            f"Primary expert: {primary_result.expert_type} "
            f"(confidence: {primary_result.confidence:.2f}). "
        )
        if supplementary_experts:
            reasoning += f"Supplemented by: {', '.join(supplementary_experts)}"
        else:
            reasoning += "No supplementary experts met confidence threshold."

        return EnsembleResult(
            query=query,
            expert_results=results,
            combined_data=combined_data,
            combined_confidence=combined_confidence,
            strategy_used='hierarchical',
            primary_expert=primary_result.expert_type,
            reasoning=reasoning
        )

    def get_metrics(self) -> Dict[str, Any]:
        """Get ensemble metrics"""
        return self._metrics.copy()

    def reset_metrics(self):
        """Reset ensemble metrics"""
        self._metrics = {
            'total_ensembles': 0,
            'by_strategy': {
                'weighted_average': 0,
                'winner_take_all': 0,
                'hierarchical': 0
            },
            'average_experts_per_ensemble': 0.0
        }
