"""
services/relevance_scorer_service.py
------------------------------------
Relevance Scorer Service for CAG (Corrective Augmented Generation)
Evaluates confidence/relevance of retrieved documents
Determines if results are high-quality or need query regeneration
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import numpy as np

from config.cag_settings import CAGSettings
from utils.exceptions import ServiceError


@dataclass
class RelevanceScore:
    """Data class for relevance scoring results"""
    document_id: str
    text: str
    similarity_score: float  # 0-1 (from vector search)
    metadata_relevance: float  # 0-1 (metadata matching)
    overall_score: float  # 0-1 (weighted average)
    confidence_label: str  # 'high', 'medium', 'low'
    meets_threshold: bool  # True if passes confidence threshold
    reasoning: str  # Why this score was given


class RelevanceScorer:
    """Scores relevance/confidence of retrieved search results"""
    
    def __init__(self, confidence_threshold: float = 0.6):
        """
        Initialize relevance scorer
        
        Args:
            confidence_threshold: Minimum score to consider result relevant (0-1)
        """
        self.logger = logging.getLogger(__name__)
        self.confidence_threshold = confidence_threshold
        
        # Weights for scoring components
        self.similarity_weight = CAGSettings.SIMILARITY_WEIGHT
        self.metadata_weight = CAGSettings.METADATA_WEIGHT
        self.recency_weight = CAGSettings.RECENCY_WEIGHT
    
    def score_document(self, 
                      document: Dict[str, Any], 
                      query: str,
                      document_type: str = 'deal') -> RelevanceScore:
        """
        Score a single retrieved document
        
        Args:
            document: Retrieved document with id, text, metadata, similarity
            query: Original search query
            document_type: Type of document ('deal', 'activity', 'agent')
            
        Returns:
            RelevanceScore with all metrics
        """
        try:
            # Extract components
            doc_id = document.get('id', '')
            text = document.get('text', '')
            similarity_score = document.get('similarity', 0.0)
            metadata = document.get('metadata', {})
            
            # Calculate scores
            metadata_relevance = self._calculate_metadata_relevance(
                metadata, query, document_type
            )
            recency_score = self._calculate_recency_score(metadata)
            
            # Weighted overall score
            overall_score = (
                self.similarity_weight * similarity_score +
                self.metadata_weight * metadata_relevance +
                self.recency_weight * recency_score
            )
            
            # Clamp to 0-1
            overall_score = max(0.0, min(1.0, overall_score))
            
            # Determine confidence level
            confidence_label = self._get_confidence_label(overall_score)
            meets_threshold = overall_score >= self.confidence_threshold
            
            # Generate reasoning
            reasoning = self._generate_reasoning(
                similarity_score, metadata_relevance, recency_score, overall_score
            )
            
            return RelevanceScore(
                document_id=doc_id,
                text=text,
                similarity_score=similarity_score,
                metadata_relevance=metadata_relevance,
                overall_score=overall_score,
                confidence_label=confidence_label,
                meets_threshold=meets_threshold,
                reasoning=reasoning
            )
            
        except Exception as e:
            self.logger.error(f"Error scoring document: {e}")
            raise ServiceError(f"Failed to score document: {e}")
    
    def score_batch(self, 
                   documents: List[Dict[str, Any]], 
                   query: str,
                   document_type: str = 'deal') -> List[RelevanceScore]:
        """
        Score multiple documents at once
        
        Args:
            documents: List of retrieved documents
            query: Original search query
            document_type: Type of documents
            
        Returns:
            List of RelevanceScore objects
        """
        try:
            scores = []
            for doc in documents:
                score = self.score_document(doc, query, document_type)
                scores.append(score)
            
            self.logger.debug(f"Scored {len(scores)} documents")
            return scores
            
        except Exception as e:
            self.logger.error(f"Error batch scoring documents: {e}")
            raise ServiceError(f"Failed to batch score documents: {e}")
    
    def _calculate_metadata_relevance(self, 
                                     metadata: Dict[str, Any],
                                     query: str,
                                     document_type: str) -> float:
        """
        Calculate relevance based on metadata matching
        
        Args:
            metadata: Document metadata
            query: Search query
            document_type: Type of document
            
        Returns:
            Relevance score 0-1
        """
        try:
            relevance = 0.0
            match_count = 0
            max_matches = 5
            
            query_words = query.lower().split()
            
            # Check common metadata fields
            fields_to_check = ['title', 'status', 'customer_name', 'description', 'type']
            
            for field in fields_to_check:
                if field in metadata:
                    field_value = str(metadata[field]).lower()
                    
                    # Count word matches in this field
                    matches = sum(1 for word in query_words if word in field_value)
                    if matches > 0:
                        relevance += matches * 0.2
                        match_count += 1
            
            # Boost for exact type matches
            if document_type and 'type' in metadata:
                if str(metadata['type']).lower() == document_type.lower():
                    relevance += 0.15
            
            # Clamp to 0-1
            return min(1.0, relevance)
            
        except Exception as e:
            self.logger.warning(f"Error calculating metadata relevance: {e}")
            return 0.0
    
    def _calculate_recency_score(self, metadata: Dict[str, Any]) -> float:
        """
        Calculate relevance boost based on document recency
        
        Args:
            metadata: Document metadata
            
        Returns:
            Recency score 0-1
        """
        try:
            from datetime import datetime, timedelta
            
            # Look for date fields
            date_fields = ['created_at', 'updated_at', 'register_date', 'last_update_time']
            
            for field in date_fields:
                if field in metadata:
                    try:
                        # Parse date
                        if isinstance(metadata[field], str):
                            doc_date = datetime.fromisoformat(metadata[field])
                        else:
                            doc_date = metadata[field]
                        
                        # Calculate days old
                        days_old = (datetime.now() - doc_date).days
                        
                        # Decay: recent = high score, old = low score
                        if days_old <= 7:
                            return 1.0  # Very recent
                        elif days_old <= 30:
                            return 0.8  # Recent
                        elif days_old <= 90:
                            return 0.6  # Moderate
                        elif days_old <= 365:
                            return 0.4  # Old
                        else:
                            return 0.2  # Very old
                    except (ValueError, TypeError):
                        continue
            
            # No date found - neutral score
            return 0.5
            
        except Exception as e:
            self.logger.warning(f"Error calculating recency score: {e}")
            return 0.5
    
    def _get_confidence_label(self, score: float) -> str:
        """
        Convert numeric score to confidence label
        
        Args:
            score: Numeric score 0-1
            
        Returns:
            Confidence label: 'high', 'medium', or 'low'
        """
        if score >= 0.75:
            return 'high'
        elif score >= 0.5:
            return 'medium'
        else:
            return 'low'
    
    def _generate_reasoning(self,
                          similarity: float,
                          metadata: float,
                          recency: float,
                          overall: float) -> str:
        """
        Generate human-readable explanation of score
        
        Args:
            similarity: Similarity component score
            metadata: Metadata component score
            recency: Recency component score
            overall: Overall combined score
            
        Returns:
            Reasoning string
        """
        reasons = []
        
        # Analyze each component
        if similarity >= 0.8:
            reasons.append("High semantic similarity to query")
        elif similarity >= 0.5:
            reasons.append("Moderate semantic similarity")
        else:
            reasons.append("Low semantic similarity")
        
        if metadata >= 0.7:
            reasons.append("Strong metadata matches")
        elif metadata >= 0.3:
            reasons.append("Some metadata matches")
        else:
            reasons.append("Weak metadata matches")
        
        if recency >= 0.7:
            reasons.append("Recently updated")
        elif recency >= 0.4:
            reasons.append("Moderately recent")
        else:
            reasons.append("Older document")
        
        return " | ".join(reasons)
    
    def filter_by_threshold(self, 
                           scores: List[RelevanceScore]) -> Tuple[List[RelevanceScore], List[RelevanceScore]]:
        """
        Split scored documents into high-quality and low-quality
        
        Args:
            scores: List of RelevanceScore objects
            
        Returns:
            Tuple of (high_quality_scores, low_quality_scores)
        """
        high_quality = [s for s in scores if s.meets_threshold]
        low_quality = [s for s in scores if not s.meets_threshold]
        
        self.logger.debug(f"Filtered: {len(high_quality)} high-quality, {len(low_quality)} low-quality")
        
        return high_quality, low_quality
    
    def get_average_confidence(self, scores: List[RelevanceScore]) -> Dict[str, Any]:
        """
        Calculate average confidence metrics for a batch
        
        Args:
            scores: List of RelevanceScore objects
            
        Returns:
            Summary statistics
        """
        if not scores:
            return {
                'average_score': 0.0,
                'max_score': 0.0,
                'min_score': 0.0,
                'high_confidence_count': 0,
                'medium_confidence_count': 0,
                'low_confidence_count': 0,
                'pass_rate': 0.0
            }
        
        score_values = [s.overall_score for s in scores]
        
        confidence_counts = {
            'high': len([s for s in scores if s.confidence_label == 'high']),
            'medium': len([s for s in scores if s.confidence_label == 'medium']),
            'low': len([s for s in scores if s.confidence_label == 'low'])
        }
        
        pass_rate = len([s for s in scores if s.meets_threshold]) / len(scores) if scores else 0.0
        
        return {
            'average_score': round(np.mean(score_values), 4),
            'max_score': round(max(score_values), 4),
            'min_score': round(min(score_values), 4),
            'high_confidence_count': confidence_counts['high'],
            'medium_confidence_count': confidence_counts['medium'],
            'low_confidence_count': confidence_counts['low'],
            'pass_rate': round(pass_rate, 4)
        }
    
    def set_threshold(self, threshold: float):
        """
        Update confidence threshold
        
        Args:
            threshold: New threshold value (0-1)
        """
        if not (0.0 <= threshold <= 1.0):
            raise ValueError(f"Threshold must be between 0 and 1, got {threshold}")
        
        self.confidence_threshold = threshold
        self.logger.info(f"Confidence threshold updated to {threshold}")