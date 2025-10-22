"""
services/query_rewriter_service.py
----------------------------------
Query Rewriter Service for CAG (Corrective Augmented Generation)
Regenerates/rephrases queries when search confidence is low
Supports Persian text normalization and synonym expansion
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import re

from config.cag_settings import CAGSettings
from utils.exceptions import ServiceError


class QueryRewriter:
    """Rewrites queries to improve search results"""
    
    def __init__(self, 
                 strategy: str = 'both',
                 max_rewrites: int = 2,
                 cache_rewrites: bool = True):
        """
        Initialize query rewriter
        
        Args:
            strategy: 'expand', 'rephrase', or 'both'
            max_rewrites: Maximum rewrite attempts
            cache_rewrites: Cache rewrite results
        """
        self.logger = logging.getLogger(__name__)
        self.strategy = strategy
        self.max_rewrites = max_rewrites
        self.cache_rewrites = cache_rewrites
        self.rewrite_cache = {}
        
        # Persian synonyms dictionary
        self.persian_synonyms = {
            'قیمت': ['هزینه', 'تعرفه', 'نرخ'],
            'معامله': ['سفقه', 'قرارداد', 'تجارت'],
            'پیاده سازی': ['نصب', 'اجرا', 'بکارگیری'],
            'مشتری': ['خریدار', 'کلاینت', 'کاربر'],
            'فروش': ['بیع', 'تحویل', 'عرضه'],
            'تماس': ['تلفن', 'کال', 'ارتباط'],
            'جلسه': ['میتینگ', 'نشست', 'ملاقات'],
            'گزارش': ['رپورت', 'گزارشی', 'تفصیل'],
            'اطلاعات': ['داده', 'تفاصیل', 'مستندات'],
            'بسته': ['پکیج', 'مجموعه', 'سری'],
        }
        
        # English synonyms dictionary
        self.english_synonyms = {
            'pricing': ['cost', 'rate', 'fee', 'price'],
            'deal': ['sale', 'transaction', 'contract', 'agreement'],
            'implementation': ['deployment', 'execution', 'rollout'],
            'customer': ['client', 'buyer', 'user'],
            'contact': ['call', 'communication', 'conversation'],
            'meeting': ['call', 'discussion', 'session'],
            'support': ['help', 'service', 'assistance'],
            'package': ['bundle', 'plan', 'service'],
            'timeline': ['schedule', 'timeframe', 'dates'],
            'consulting': ['advisory', 'advice', 'guidance'],
        }
    
    def rewrite(self, query: str, document_type: str = 'deal', attempt: int = 1) -> List[str]:
        """
        Generate rewritten queries
        
        Args:
            query: Original query
            document_type: 'deal', 'activity', 'agent'
            attempt: Rewrite attempt number
            
        Returns:
            List of alternative queries
        """
        try:
            # Check cache
            cache_key = f"{query}_{document_type}_{attempt}"
            if self.cache_rewrites and cache_key in self.rewrite_cache:
                self.logger.debug(f"Cache hit for: {query}")
                return self.rewrite_cache[cache_key]
            
            rewrites = []
            
            if self.strategy in ['expand', 'both']:
                # Expand query with synonyms
                expanded = self._expand_query(query)
                rewrites.extend(expanded)
            
            if self.strategy in ['rephrase', 'both']:
                # Rephrase query
                rephrased = self._rephrase_query(query)
                rewrites.extend(rephrased)
            
            # Normalize Persian text
            normalized = self._normalize_query(query)
            if normalized != query:
                rewrites.append(normalized)
            
            # Deduplicate and limit
            rewrites = list(dict.fromkeys(rewrites))[:CAGSettings.NUM_ALTERNATIVE_QUERIES]
            
            # Cache result
            if self.cache_rewrites:
                self.rewrite_cache[cache_key] = rewrites
            
            self.logger.debug(f"Generated {len(rewrites)} rewrites for: {query}")
            return rewrites
            
        except Exception as e:
            self.logger.error(f"Query rewrite failed: {e}")
            raise ServiceError(f"Failed to rewrite query: {e}")
    
    def _expand_query(self, query: str) -> List[str]:
        """
        Expand query with synonyms
        
        Args:
            query: Original query
            
        Returns:
            List of expanded queries
        """
        try:
            expanded = []
            query_words = query.lower().split()
            
            for word in query_words:
                # Check Persian synonyms
                if word in self.persian_synonyms:
                    for syn in self.persian_synonyms[word]:
                        new_query = query.replace(word, syn)
                        expanded.append(new_query)
                
                # Check English synonyms
                if word in self.english_synonyms:
                    for syn in self.english_synonyms[word]:
                        new_query = query.replace(word, syn)
                        expanded.append(new_query)
            
            return expanded
            
        except Exception as e:
            self.logger.warning(f"Query expansion failed: {e}")
            return []
    
    def _rephrase_query(self, query: str) -> List[str]:
        """
        Rephrase query by reordering and restructuring
        
        Args:
            query: Original query
            
        Returns:
            List of rephrased queries
        """
        try:
            rephrased = []
            words = query.split()
            
            if len(words) < 2:
                return rephrased
            
            # Try: Last word + rest
            reordered = [words[-1]] + words[:-1]
            rephrased.append(' '.join(reordered))
            
            # Try: Adding common words
            prefixes = ['about', 'for', 'regarding']
            for prefix in prefixes:
                rephrased.append(f"{prefix} {query}")
            
            # Try: removing common words
            stopwords = {'about', 'for', 'the', 'a', 'and', 'or'}
            cleaned = ' '.join([w for w in words if w.lower() not in stopwords])
            if cleaned and cleaned != query:
                rephrased.append(cleaned)
            
            return rephrased
            
        except Exception as e:
            self.logger.warning(f"Query rephrasing failed: {e}")
            return []
    
    def _normalize_query(self, query: str) -> str:
        """
        Normalize Persian text (remove diacritics, standardize)
        
        Args:
            query: Original query
            
        Returns:
            Normalized query
        """
        try:
            if not CAGSettings.NORMALIZE_PERSIAN_TEXT:
                return query
            
            # Persian-specific normalization
            normalized = query
            
            # Remove Persian diacritics
            normalized = re.sub(r'[\u064B-\u0652]', '', normalized)  # Remove Arabic diacritics
            
            # Normalize Persian/Arabic characters
            replacements = {
                'ۀ': 'ه',  # Persian heh goal
                'ؤ': 'و',  # Waw with hamza
                'ئ': 'ی',  # Yeh with hamza
                'ة': 'ت',  # Teh marbuta
                'ٰ': '',    # Superscript alef
            }
            
            for old, new in replacements.items():
                normalized = normalized.replace(old, new)
            
            # Normalize spaces
            normalized = re.sub(r'\s+', ' ', normalized).strip()
            
            return normalized
            
        except Exception as e:
            self.logger.warning(f"Query normalization failed: {e}")
            return query
    
    def should_rewrite(self, 
                      confidence_score: float,
                      high_quality_count: int,
                      decision_strategy: str = 'hybrid') -> bool:
        """
        Decide if query should be rewritten
        
        Args:
            confidence_score: Average confidence score
            high_quality_count: Number of high-quality results
            decision_strategy: 'threshold', 'hybrid', or 'aggressive'
            
        Returns:
            Whether to rewrite the query
        """
        if decision_strategy == 'threshold':
            return confidence_score < CAGSettings.CONFIDENCE_THRESHOLD
        
        elif decision_strategy == 'hybrid':
            return (confidence_score < CAGSettings.BATCH_QUALITY_THRESHOLD or 
                    high_quality_count < CAGSettings.MIN_HIGH_QUALITY_RESULTS)
        
        elif decision_strategy == 'aggressive':
            # Rewrite if any concern
            return (confidence_score < CAGSettings.BATCH_QUALITY_THRESHOLD or 
                    high_quality_count < 1)
        
        return False
    
    def get_best_rewrite(self, 
                        rewrites: List[str],
                        original_query: str) -> str:
        """
        Select best rewrite (prefers synonyms over pure rephrase)
        
        Args:
            rewrites: List of alternative queries
            original_query: Original query
            
        Returns:
            Best rewrite to use
        """
        if not rewrites:
            return original_query
        
        if len(rewrites) == 1:
            return rewrites[0]
        
        # Prefer first rewrite (usually synonym-based)
        return rewrites[0]
    
    def clear_cache(self):
        """Clear rewrite cache"""
        self.rewrite_cache.clear()
        self.logger.info("Rewrite cache cleared")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            'cache_size': len(self.rewrite_cache),
            'max_size': CAGSettings.REWRITE_CACHE_SIZE,
            'cached_queries': list(self.rewrite_cache.keys())[:10]  # First 10
        }


class QueryRewriterWithFallback:
    """QueryRewriter with fallback strategies"""
    
    def __init__(self):
        """Initialize with primary and fallback rewriters"""
        self.primary = QueryRewriter(strategy='both')
        self.fallback = QueryRewriter(strategy='expand')
        self.logger = logging.getLogger(__name__)
    
    def rewrite_with_fallback(self, query: str, attempt: int = 1) -> List[str]:
        """
        Rewrite with fallback if primary fails
        
        Args:
            query: Original query
            attempt: Attempt number
            
        Returns:
            List of rewritten queries
        """
        try:
            # Try primary strategy
            rewrites = self.primary.rewrite(query, attempt=attempt)
            
            if rewrites:
                return rewrites
            
            # Fallback to expansion only
            self.logger.info(f"Primary rewrite empty, using fallback for: {query}")
            return self.fallback.rewrite(query, attempt=attempt)
            
        except Exception as e:
            self.logger.error(f"Rewrite with fallback failed: {e}")
            # Last resort: return query as-is in a list
            return [query]