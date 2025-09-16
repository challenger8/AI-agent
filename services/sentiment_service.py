"""
services/sentiment_service.py
-----------------------------
Sentiment analysis service for Persian text
"""

import asyncio
from typing import Dict, List, Any, Optional
from collections import defaultdict

from services.base_service import BaseService
from config.settings import SentimentSettings, FeatureFlags, get_sentiment_available
from utils.exceptions import SentimentAnalysisError

class SentimentService(BaseService):
    """Persian sentiment analysis service with caching"""
    
    def __init__(self, repositories=None):
        super().__init__(repositories)
        self.pipeline = None
        self.model_loaded = False
        self.sentiment_cache = {}
        self.available = get_sentiment_available()
    
    async def initialize(self) -> bool:
        """
        Initialize sentiment analysis model
        
        Returns:
            True if initialization successful, False otherwise
        """
        if not self.available:
            self.logger.warning("Sentiment analysis not available - transformers not installed")
            return False
        
        if self.model_loaded:
            return True
        
        try:
            self.logger.info("Loading Persian sentiment model...")
            
            from transformers import pipeline
            
            self.pipeline = pipeline(
                "sentiment-analysis",
                model=SentimentSettings.MODEL_NAME,
                tokenizer=SentimentSettings.MODEL_NAME,
                return_all_scores=True
            )
            
            self.model_loaded = True
            self.logger.info("Persian sentiment model loaded successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load sentiment model: {e}")
            raise SentimentAnalysisError(f"Model initialization failed: {e}")
    
    def analyze_text(self, text: str) -> Dict[str, Any]:
        """
        Analyze sentiment of Persian text
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with sentiment analysis results
        """
        if not self.available or not self.model_loaded or not self.pipeline:
            return {
                "sentiment": "خنثی",
                "confidence": 0.0,
                "error": "Model not available"
            }
        
        # Validate input
        if not text or len(text.strip()) < SentimentSettings.MIN_TEXT_LENGTH:
            return {
                "sentiment": "خنثی",
                "confidence": 0.0,
                "error": "Text too short"
            }
        
        # Check cache first
        cache_key = hash(text.strip())
        cached_result = self._get_from_cache(f"sentiment_{cache_key}")
        if cached_result:
            self.logger.debug("Retrieved sentiment from cache")
            return cached_result
        
        try:
            # Analyze sentiment
            truncated_text = text[:SentimentSettings.MAX_TEXT_LENGTH]
            results = self.pipeline(truncated_text)
            
            # Process results
            if results and len(results) > 0:
                if isinstance(results[0], list):
                    best_result = max(results[0], key=lambda x: x['score'])
                else:
                    best_result = results[0]
                
                # Map to Persian labels
                sentiment = SentimentSettings.LABEL_MAPPING.get(
                    best_result['label'], 
                    best_result['label']
                )
                confidence = best_result['score']
                
                result = {
                    "sentiment": sentiment,
                    "confidence": round(confidence, 3),
                    "text_preview": text[:50] + "..." if len(text) > 50 else text
                }
                
                # Cache result
                self._set_cache(f"sentiment_{cache_key}", result)
                return result
            
        except Exception as e:
            self.logger.error(f"Error analyzing sentiment: {e}")
        
        return {
            "sentiment": "خنثی",
            "confidence": 0.0,
            "error": "Analysis failed"
        }
    
    def analyze_batch(self, texts: List[str]) -> List[Dict[str, Any]]:
        """
        Analyze sentiment for multiple texts
        
        Args:
            texts: List of texts to analyze
            
        Returns:
            List of sentiment analysis results
        """
        results = []
        for text in texts:
            result = self.analyze_text(text)
            results.append(result)
        return results
    
    def analyze_activities_sentiment(self, activities: List[Any]) -> Dict[str, Any]:
        """
        Analyze sentiment for multiple activities
        
        Args:
            activities: List of activity objects
            
        Returns:
            Comprehensive sentiment analysis summary
        """
        if not activities:
            return self._empty_sentiment_summary()
        
        sentiments = []
        analyzed_count = 0
        
        for activity in activities:
            # Check if activity has description
            description = getattr(activity, 'activity_description', None)
            if not description or len(description.strip()) < SentimentSettings.MIN_TEXT_LENGTH:
                continue
            
            sentiment_result = self.analyze_text(description)
            if "error" not in sentiment_result:
                sentiments.append({
                    "activity_id": getattr(activity, 'activity_id', None),
                    "sentiment": sentiment_result["sentiment"],
                    "confidence": sentiment_result["confidence"],
                    "date": getattr(activity, 'created_date', None),
                    "description_preview": description[:50] + "..." if len(description) > 50 else description
                })
                analyzed_count += 1
        
        # Calculate summary statistics
        summary = self._calculate_sentiment_summary(sentiments)
        
        return {
            "total_activities": len(activities),
            "analyzed_activities": analyzed_count,
            "sentiments": sentiments,
            "summary": summary
        }
    
    def get_sentiment_trends(self, activities: List[Any], days: int = 7) -> Dict[str, Any]:
        """
        Get sentiment trends over time
        
        Args:
            activities: List of activity objects
            days: Number of days to analyze
            
        Returns:
            Sentiment trends analysis
        """
        from datetime import datetime, timedelta
        
        sentiment_analysis = self.analyze_activities_sentiment(activities)
        sentiments = sentiment_analysis["sentiments"]
        
        if not sentiments:
            return {"trends": [], "summary": "No data available"}
        
        # Group by date
        daily_sentiments = defaultdict(list)
        cutoff_date = datetime.now() - timedelta(days=days)
        
        for sentiment in sentiments:
            if sentiment["date"] and sentiment["date"] >= cutoff_date:
                date_key = sentiment["date"].date() if hasattr(sentiment["date"], 'date') else sentiment["date"]
                daily_sentiments[date_key].append(sentiment["sentiment"])
        
        # Calculate daily trends
        trends = []
        for date, day_sentiments in sorted(daily_sentiments.items()):
            sentiment_counts = defaultdict(int)
            for s in day_sentiments:
                sentiment_counts[s] += 1
            
            dominant = max(sentiment_counts.items(), key=lambda x: x[1])[0] if sentiment_counts else "خنثی"
            
            trends.append({
                "date": str(date),
                "dominant_sentiment": dominant,
                "sentiment_breakdown": dict(sentiment_counts),
                "total_activities": len(day_sentiments)
            })
        
        return {
            "trends": trends,
            "period_days": days,
            "summary": f"Analyzed {len(trends)} days with sentiment data"
        }
    
    def _calculate_sentiment_summary(self, sentiments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate sentiment summary statistics"""
        if not sentiments:
            return {"sentiment_breakdown": {}, "avg_confidence": 0, "dominant_sentiment": "خنثی"}
        
        sentiment_counts = defaultdict(int)
        total_confidence = 0
        
        for sentiment in sentiments:
            sentiment_counts[sentiment["sentiment"]] += 1
            total_confidence += sentiment["confidence"]
        
        dominant_sentiment = max(sentiment_counts.items(), key=lambda x: x[1])[0] if sentiment_counts else "خنثی"
        avg_confidence = round(total_confidence / len(sentiments), 3)
        
        return {
            "sentiment_breakdown": dict(sentiment_counts),
            "avg_confidence": avg_confidence,
            "dominant_sentiment": dominant_sentiment
        }
    
    def _empty_sentiment_summary(self) -> Dict[str, Any]:
        """Return empty sentiment summary"""
        return {
            "total_activities": 0,
            "analyzed_activities": 0,
            "sentiments": [],
            "summary": {
                "sentiment_breakdown": {},
                "avg_confidence": 0,
                "dominant_sentiment": "خنثی"
            }
        }
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            "cache_size": len(self.sentiment_cache),
            "model_loaded": self.model_loaded,
            "available": self.available
        }
    
    def clear_cache(self) -> None:
        """Clear sentiment cache"""
        self._clear_cache()
        self.sentiment_cache.clear()
        self.logger.info("Sentiment cache cleared")
