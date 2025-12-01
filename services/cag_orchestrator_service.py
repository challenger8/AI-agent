"""
services/cag_orchestrator_service.py
------------------------------------
CAG (Corrective Augmented Generation) Orchestrator
Combines RelevanceScorer + QueryRewriter + RAGSearch
Orchestrates the full CAG pipeline
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

from services.base_service import BaseService
from services.rag_search_service import RAGSearchService
from services.relevance_scorer_service import RelevanceScorer
from services.query_rewriter_service import QueryRewriter, QueryRewriterWithFallback
from config.cag_settings import CAGSettings
from utils.exceptions import ServiceError


class CAGOrchestrator(BaseService):
    """Orchestrates Corrective Augmented Generation"""
    
    def __init__(self, repositories=None):
        """
        Initialize CAG orchestrator
        
        Args:
            repositories: Repository manager
        """
        super().__init__(repositories)
        self.rag_service = None
        self.scorer = None
        self.rewriter = None
        self.logger = logging.getLogger(__name__)
        self._initialized = False
        
        # Metrics
        self.stats = {
            'total_searches': 0,
            'rewrites_triggered': 0,
            'rewrites_successful': 0,
            'correction_applied_count': 0,
            'average_iterations': 0,
        }
    
    async def initialize(self):
        """Initialize all components"""
        success = await self._safe_initialize(
            self._setup_cag_components,
            service_name="CAG Orchestrator",
            raise_on_error=True
        )
        # _initialized is set in _setup_cag_components, but if init fails, ensure it's False
        if not success:
            self._initialized = False
    
    async def _setup_cag_components(self):
        """Actual CAG components setup logic"""
        # Initialize RAG service
        self.rag_service = RAGSearchService(self.repositories)
        await self.rag_service.initialize()
        self.logger.info("✅ RAG service initialized")
        
        # Initialize scorer
        self.scorer = RelevanceScorer(
            confidence_threshold=CAGSettings.CONFIDENCE_THRESHOLD
        )
        self.logger.info("✅ Relevance scorer initialized")
        
        # Initialize rewriter with fallback
        self.rewriter = QueryRewriterWithFallback()
        self.logger.info("✅ Query rewriter initialized")
        
        self._initialized = True
    
    def _check_initialized(self):
        """Check if orchestrator is initialized"""
        if not self._initialized:
            raise ServiceError("CAG Orchestrator not initialized. Call initialize() first.")
    
    def search_with_cag(self, 
                       query: str,
                       document_type: str = 'deal',
                       n_results: int = 5) -> Dict[str, Any]:
        """
        Corrective Augmented Generation search
        
        Args:
            query: Search query
            document_type: 'deal', 'activity', or 'agent'
            n_results: Number of results per collection
            
        Returns:
            Search results with CAG metadata
        """
        try:
            self._check_initialized()
            
            start_time = datetime.now()
            self.stats['total_searches'] += 1
            
            # STEP 1: Initial search
            self.logger.debug(f"CAG Search: '{query}' (type={document_type})")
            initial_results = self._search_all(query, n_results)
            
            # STEP 2: Score results
            scored_results = self._score_results(initial_results, query, document_type)
            high_quality, low_quality = self.scorer.filter_by_threshold(scored_results)
            
            # Get statistics
            stats = self.scorer.get_average_confidence(scored_results)
            
            # STEP 3: Decide if correction needed
            should_correct = self._should_correct(stats, high_quality, document_type)
            
            final_results = initial_results
            correction_applied = False
            rewrites_used = []
            
            # STEP 4: Correct if needed
            if should_correct and len(rewrites_used) < CAGSettings.MAX_REWRITES:
                self.logger.debug(f"Triggering query correction for: {query}")
                self.stats['rewrites_triggered'] += 1
                
                corrected_query, corrected_results, rewrite_info = self._correct_query(
                    query, initial_results, n_results, document_type
                )
                
                if corrected_results:
                    final_results = corrected_results
                    correction_applied = True
                    rewrites_used = rewrite_info
                    self.stats['rewrites_successful'] += 1
            
            if correction_applied:
                self.stats['correction_applied_count'] += 1
            
            # Prepare response
            execution_time = (datetime.now() - start_time).total_seconds()
            
            response = {
                'status': 'success',
                'original_query': query,
                'document_type': document_type,
                'results': final_results,
                'correction': {
                    'applied': correction_applied,
                    'rewrites_used': rewrites_used,
                    'trigger_reason': 'low_confidence' if correction_applied else None
                },
                'confidence_metrics': stats,
                'execution_time': round(execution_time, 3),
                'timestamp': datetime.now().isoformat()
            }
            
            return response
            
        except Exception as e:
            self.logger.error(f"CAG search failed: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'original_query': query,
                'results': {},
                'correction': {'applied': False},
                'timestamp': datetime.now().isoformat()
            }
    
    def _search_all(self, query: str, n_results: int) -> Dict[str, List]:
        """
        Search across all collections
        
        Args:
            query: Search query
            n_results: Number of results
            
        Returns:
            Results by collection type
        """
        try:
            results = self.rag_service.search(query, n_results=n_results)
            return results.get('results', {})
        except Exception as e:
            self.logger.error(f"Search failed: {e}")
            return {'deals': [], 'activities': [], 'agents': []}
    
    def _score_results(self,
                      results: Dict[str, List],
                      query: str,
                      document_type: str) -> List:
        """
        Score all results
        
        Args:
            results: Results by type
            query: Original query
            document_type: Document type
            
        Returns:
            List of scored results
        """
        try:
            all_scored = []
            
            # Score deals
            for doc in results.get('deals', []):
                score = self.scorer.score_document(doc, query, 'deal')
                all_scored.append(score)
            
            # Score activities
            for doc in results.get('activities', []):
                score = self.scorer.score_document(doc, query, 'activity')
                all_scored.append(score)
            
            # Score agents
            for doc in results.get('agents', []):
                score = self.scorer.score_document(doc, query, 'agent')
                all_scored.append(score)
            
            return all_scored
            
        except Exception as e:
            self.logger.warning(f"Scoring failed: {e}")
            return []
    
    def _should_correct(self,
                       stats: Dict[str, Any],
                       high_quality: List,
                       document_type: str) -> bool:
        """
        Decide if correction is needed
        
        Args:
            stats: Confidence statistics
            high_quality: High-quality results
            document_type: Document type
            
        Returns:
            Whether to correct
        """
        strategy = CAGSettings.DECISION_STRATEGY
        avg_score = stats.get('average_score', 0)
        pass_rate = stats.get('pass_rate', 0)
        
        if strategy == 'threshold':
            threshold = CAGSettings.get_threshold_for_type(document_type)
            return avg_score < threshold
        
        elif strategy == 'hybrid':
            return (avg_score < CAGSettings.BATCH_QUALITY_THRESHOLD or
                    len(high_quality) < CAGSettings.MIN_HIGH_QUALITY_RESULTS)
        
        elif strategy == 'aggressive':
            return (avg_score < CAGSettings.BATCH_QUALITY_THRESHOLD or
                    len(high_quality) < 1)
        
        return False
    
    def _correct_query(self,
                      query: str,
                      initial_results: Dict[str, List],
                      n_results: int,
                      document_type: str) -> Tuple[str, Dict[str, List], List[str]]:
        """
        Generate and apply query correction
        
        Args:
            query: Original query
            initial_results: Initial search results
            n_results: Number of results
            document_type: Document type
            
        Returns:
            Tuple of (new_query, corrected_results, rewrites_used)
        """
        try:
            # Generate alternatives
            alternatives = self.rewriter.rewrite_with_fallback(query)
            
            if not alternatives:
                return query, initial_results, []
            
            # Try each alternative
            best_results = initial_results
            best_score = 0
            used_rewrites = []
            
            for alt_query in alternatives[:CAGSettings.MAX_REWRITES]:
                if alt_query == query:
                    continue  # Skip original
                
                self.logger.debug(f"Trying rewrite: {alt_query}")
                
                # Search with alternative
                alt_results = self._search_all(alt_query, n_results)
                
                # Score alternative
                alt_scored = self._score_results(alt_results, alt_query, document_type)
                
                if alt_scored:
                    alt_stats = self.scorer.get_average_confidence(alt_scored)
                    alt_score = alt_stats.get('average_score', 0)
                    
                    # Use if better
                    if alt_score > best_score:
                        best_results = alt_results
                        best_score = alt_score
                        used_rewrites = [alt_query]
                        self.logger.debug(f"Better score: {alt_score:.3f}")
            
            return query, best_results, used_rewrites
            
        except Exception as e:
            self.logger.error(f"Query correction failed: {e}")
            return query, initial_results, []
    
    def get_stats(self) -> Dict[str, Any]:
        """Get orchestrator statistics"""
        stats = self.stats.copy()
        
        # Calculate averages
        if stats['total_searches'] > 0:
            stats['rewrite_rate'] = round(
                stats['rewrites_triggered'] / stats['total_searches'], 3
            )
            stats['success_rate'] = round(
                stats['rewrites_successful'] / stats['rewrites_triggered'], 3
            ) if stats['rewrites_triggered'] > 0 else 0
        
        return stats
    
    def reset_stats(self):
        """Reset statistics"""
        self.stats = {
            'total_searches': 0,
            'rewrites_triggered': 0,
            'rewrites_successful': 0,
            'correction_applied_count': 0,
            'average_iterations': 0,
        }
        self.logger.info("Stats reset")


class CAGSearchManager:
    """High-level interface for CAG search"""
    
    def __init__(self, orchestrator: CAGOrchestrator):
        """
        Initialize manager
        
        Args:
            orchestrator: CAG orchestrator instance
        """
        self.orchestrator = orchestrator
        self.logger = logging.getLogger(__name__)
    
    async def initialize(self):
        """Initialize orchestrator"""
        await self.orchestrator.initialize()
    
    def search(self, 
              query: str,
              document_type: str = 'deal',
              n_results: int = 5,
              include_metadata: bool = True) -> Dict[str, Any]:
        """
        Perform CAG search
        
        Args:
            query: Search query
            document_type: 'deal', 'activity', or 'agent'
            n_results: Number of results
            include_metadata: Include CAG metadata
            
        Returns:
            Search results
        """
        result = self.orchestrator.search_with_cag(query, document_type, n_results)
        
        if include_metadata:
            return result
        else:
            # Return only results without CAG metadata
            return {
                'status': result['status'],
                'results': result.get('results', {}),
                'execution_time': result.get('execution_time')
            }
    
    def search_deals(self, query: str, n_results: int = 5) -> Dict[str, Any]:
        """Search deals with CAG"""
        return self.search(query, document_type='deal', n_results=n_results)
    
    def search_activities(self, query: str, n_results: int = 5) -> Dict[str, Any]:
        """Search activities with CAG"""
        return self.search(query, document_type='activity', n_results=n_results)
    
    def search_agents(self, query: str, n_results: int = 5) -> Dict[str, Any]:
        """Search agents with CAG"""
        return self.search(query, document_type='agent', n_results=n_results)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get CAG statistics"""
        return self.orchestrator.get_stats()