"""
services/moe/moe_orchestrator.py
--------------------------------
Main MoE orchestrator service that coordinates all experts
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List, Optional
from datetime import datetime

from config.moe_settings import MoESettings
from .base_expert import BaseExpert, ExpertResult
from .expert_router import ExpertRouter, RoutingDecision
from .expert_ensemble import ExpertEnsemble, EnsembleResult
from .experts import (
    DealAnalysisExpert,
    SentimentExpert,
    ActivityExpert,
    RiskAssessmentExpert,
    SearchExpert
)
from utils.logging_config import get_logger


class MoEOrchestrator:
    """Main orchestrator for Mixture of Experts system"""

    def __init__(self, repositories=None, services: Dict[str, Any] = None):
        """
        Initialize MoE orchestrator

        Args:
            repositories: Database repositories
            services: Dictionary of available services
        """
        self.logger = get_logger(self.__class__.__name__)
        self.repositories = repositories
        self.services = services or {}

        # Initialize components
        self.router = ExpertRouter()
        self.ensemble = ExpertEnsemble()

        # Initialize experts
        self.experts: Dict[str, BaseExpert] = {}
        self._initialize_experts()

        # Metrics
        self._metrics = {
            'total_queries': 0,
            'successful_queries': 0,
            'failed_queries': 0,
            'total_execution_time_ms': 0.0,
            'by_expert': {expert_type: 0 for expert_type in MoESettings.EXPERT_TYPES}
        }

        self.logger.info(f"MoE Orchestrator initialized with {len(self.experts)} experts")

    def _initialize_experts(self):
        """Initialize all expert instances"""
        expert_classes = {
            'deal_analysis': DealAnalysisExpert,
            'sentiment': SentimentExpert,
            'activity': ActivityExpert,
            'risk_assessment': RiskAssessmentExpert,
            'search': SearchExpert
        }

        for expert_type, expert_class in expert_classes.items():
            try:
                expert = expert_class(
                    repositories=self.repositories,
                    services=self.services
                )
                self.experts[expert_type] = expert
                self.logger.debug(f"Initialized expert: {expert_type}")
            except Exception as e:
                self.logger.error(f"Failed to initialize expert {expert_type}: {e}")

    async def process(
        self,
        query: str,
        context: Dict[str, Any] = None
    ) -> EnsembleResult:
        """
        Process a query through the MoE system

        Args:
            query: Input query
            context: Additional context

        Returns:
            EnsembleResult with combined expert outputs
        """
        import time
        start_time = time.time()

        context = context or {}
        self._metrics['total_queries'] += 1

        try:
            # Step 1: Route query to experts
            routing_decision = self.router.route(query, context)
            self.logger.debug(
                f"Routed query to experts: {routing_decision.selected_experts}"
            )

            # Step 2: Execute selected experts
            expert_results = await self._execute_experts(
                query,
                routing_decision.selected_experts,
                context
            )

            # Step 3: Combine results
            ensemble_result = self.ensemble.combine(
                query=query,
                expert_results=expert_results
            )

            # Add routing info if configured
            if MoESettings.INCLUDE_ROUTING_INFO:
                ensemble_result.metadata['routing'] = routing_decision.to_dict()

            # Update metrics
            execution_time = (time.time() - start_time) * 1000
            ensemble_result.execution_time_ms = execution_time

            if ensemble_result.is_successful:
                self._metrics['successful_queries'] += 1
            else:
                self._metrics['failed_queries'] += 1

            self._metrics['total_execution_time_ms'] += execution_time

            # Update expert usage metrics
            for expert_type in routing_decision.selected_experts:
                if expert_type in self._metrics['by_expert']:
                    self._metrics['by_expert'][expert_type] += 1

            self.logger.info(
                f"MoE processed query in {execution_time:.2f}ms "
                f"using {len(routing_decision.selected_experts)} expert(s)"
            )

            return ensemble_result

        except Exception as e:
            self.logger.error(f"MoE processing error: {e}")
            self._metrics['failed_queries'] += 1

            execution_time = (time.time() - start_time) * 1000

            return EnsembleResult(
                query=query,
                expert_results=[],
                combined_data={'error': str(e)},
                combined_confidence=0.0,
                strategy_used='none',
                primary_expert='none',
                reasoning=f"MoE processing failed: {str(e)}",
                execution_time_ms=execution_time
            )

    async def _execute_experts(
        self,
        query: str,
        selected_experts: List[str],
        context: Dict[str, Any]
    ) -> List[ExpertResult]:
        """
        Execute selected experts

        Args:
            query: Input query
            selected_experts: List of expert types to execute
            context: Additional context

        Returns:
            List of expert results
        """
        if MoESettings.PARALLEL_EXECUTION and len(selected_experts) > 1:
            # Execute in parallel
            return await self._execute_parallel(query, selected_experts, context)
        else:
            # Execute sequentially
            return await self._execute_sequential(query, selected_experts, context)

    async def _execute_parallel(
        self,
        query: str,
        selected_experts: List[str],
        context: Dict[str, Any]
    ) -> List[ExpertResult]:
        """Execute experts in parallel"""
        tasks = []

        for expert_type in selected_experts:
            expert = self.experts.get(expert_type)
            if expert:
                timeout = MoESettings.get_timeout_for_expert(expert_type)
                task = asyncio.create_task(
                    self._execute_with_timeout(expert, query, context, timeout)
                )
                tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Convert exceptions to error results
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                expert_type = selected_experts[i] if i < len(selected_experts) else 'unknown'
                final_results.append(
                    ExpertResult.error_result(expert_type, str(result))
                )
            elif isinstance(result, ExpertResult):
                final_results.append(result)

        return final_results

    async def _execute_sequential(
        self,
        query: str,
        selected_experts: List[str],
        context: Dict[str, Any]
    ) -> List[ExpertResult]:
        """Execute experts sequentially"""
        results = []

        for expert_type in selected_experts:
            expert = self.experts.get(expert_type)
            if expert:
                timeout = MoESettings.get_timeout_for_expert(expert_type)
                result = await self._execute_with_timeout(expert, query, context, timeout)
                results.append(result)

        return results

    async def _execute_with_timeout(
        self,
        expert: BaseExpert,
        query: str,
        context: Dict[str, Any],
        timeout: int
    ) -> ExpertResult:
        """Execute an expert with timeout"""
        try:
            result = await asyncio.wait_for(
                expert.execute(query, context),
                timeout=timeout
            )
            return result
        except asyncio.TimeoutError:
            self.logger.warning(f"Expert {expert.expert_type} timed out after {timeout}s")
            return ExpertResult.error_result(
                expert.expert_type,
                f"Timeout after {timeout} seconds"
            )
        except Exception as e:
            self.logger.error(f"Expert {expert.expert_type} error: {e}")
            return ExpertResult.error_result(expert.expert_type, str(e))

    def process_sync(
        self,
        query: str,
        context: Dict[str, Any] = None
    ) -> EnsembleResult:
        """
        Synchronous version of process

        Args:
            query: Input query
            context: Additional context

        Returns:
            EnsembleResult with combined expert outputs
        """
        return asyncio.run(self.process(query, context))

    def get_expert(self, expert_type: str) -> Optional[BaseExpert]:
        """Get a specific expert by type"""
        return self.experts.get(expert_type)

    def get_available_experts(self) -> List[str]:
        """Get list of available expert types"""
        return list(self.experts.keys())

    def get_expert_descriptions(self) -> Dict[str, str]:
        """Get descriptions of all experts"""
        return {
            expert_type: expert.description
            for expert_type, expert in self.experts.items()
        }

    def analyze_query(self, query: str, context: Dict[str, Any] = None) -> RoutingDecision:
        """
        Analyze a query without executing experts

        Args:
            query: Input query
            context: Additional context

        Returns:
            RoutingDecision with selected experts
        """
        return self.router.route(query, context)

    def get_metrics(self) -> Dict[str, Any]:
        """Get MoE orchestrator metrics"""
        metrics = self._metrics.copy()

        if metrics['total_queries'] > 0:
            metrics['success_rate'] = metrics['successful_queries'] / metrics['total_queries']
            metrics['average_execution_time_ms'] = (
                metrics['total_execution_time_ms'] / metrics['total_queries']
            )
        else:
            metrics['success_rate'] = 0.0
            metrics['average_execution_time_ms'] = 0.0

        # Add component metrics
        metrics['router'] = self.router.get_metrics()
        metrics['ensemble'] = self.ensemble.get_metrics()
        metrics['experts'] = {
            expert_type: expert.get_metrics()
            for expert_type, expert in self.experts.items()
        }

        return metrics

    def reset_metrics(self):
        """Reset all metrics"""
        self._metrics = {
            'total_queries': 0,
            'successful_queries': 0,
            'failed_queries': 0,
            'total_execution_time_ms': 0.0,
            'by_expert': {expert_type: 0 for expert_type in MoESettings.EXPERT_TYPES}
        }

        self.router.reset_metrics()
        self.ensemble.reset_metrics()

        for expert in self.experts.values():
            expert.reset_metrics()

    def get_settings(self) -> Dict[str, Any]:
        """Get current MoE settings"""
        return MoESettings.to_dict()
