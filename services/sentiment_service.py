"""
services/sentiment_service.py
-----------------------------
Sentiment analysis service for Persian text using Qwen2 with prompts
"""

import asyncio
from typing import Dict, List, Any, Optional
from collections import defaultdict
from services.cache import get_cache_service, CacheService
from services.cache_strategies import CacheTTLStrategy
from services.cache.base_cache import CacheKeyBuilder

from services.base_service import BaseService
from config.settings import SentimentSettings, FeatureFlags, get_sentiment_available
from utils.exceptions import SentimentAnalysisError

class SentimentService(BaseService):
    """Persian sentiment analysis service using prompt-based generation"""
    
    def __init__(self, repositories=None):
        super().__init__(repositories)
        self.model = None
        self.tokenizer = None
        self.model_loaded = False
        self.sentiment_cache = {}
        self.available = get_sentiment_available()
        self.cache_service = get_cache_service()
    
    async def initialize(self) -> bool:
        """
        Initialize Qwen2 model for prompt-based sentiment analysis.

        REFACTORED: Now uses ModelLoader for consistent patterns.

        Returns:
            True if initialization successful, False otherwise
        """
        if not self.available:
            self.logger.warning("Sentiment analysis not available - transformers not installed")
            return False

        # DRY: Use centralized "already loaded" check pattern
        from utils.model_loader import ModelLoader

        if self.model_loaded and ModelLoader.check_already_loaded(self.model, "Sentiment model"):
            return True

        try:
            self.logger.info("Loading Qwen2 sentiment model...")

            from transformers import AutoModelForCausalLM, AutoTokenizer
            import torch

            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                SentimentSettings.MODEL_NAME,
                token=SentimentSettings.HF_TOKEN,
                trust_remote_code=True
            )

            # Load model
            device = "cuda" if torch.cuda.is_available() else "cpu"
            self.model = AutoModelForCausalLM.from_pretrained(
                SentimentSettings.MODEL_NAME,
                token=SentimentSettings.HF_TOKEN,
                trust_remote_code=True,
                device_map=device,
                torch_dtype=torch.float16 if device == "cuda" else torch.float32
            )

            self.model.eval()
            self.model_loaded = True
            self.logger.info(f"Qwen2 sentiment model loaded successfully on {device}")

            return True

        except Exception as e:
            self.logger.error(f"Failed to load Qwen2 model: {e}")
            raise SentimentAnalysisError(f"Model initialization failed: {e}")
    
    def analyze_text(self, text: str) -> Dict[str, Any]:
        """
        Analyze sentiment using prompt-based generation
        """
        if not self.available or not self.model_loaded or not self.model or not self.tokenizer:
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
        
        # Generate cache key
        text_hash = self.cache_service.hash_text(text.strip())
        cache_key = CacheKeyBuilder.build("sentiment", text_hash)
        
        # Try to get from Redis cache
        cached_result = self.cache_service.get(cache_key)
        if cached_result:
            self.logger.debug(f"Sentiment cache HIT for text hash: {text_hash[:8]}")
            return cached_result
        
        # Not in cache - analyze
        try:
            truncated_text = text[:SentimentSettings.MAX_TEXT_LENGTH]
            
            # Format prompt
            prompt = SentimentSettings.DEEPSEEK_PROMPT_TEMPLATE.format(text=truncated_text)
            
            # Generate sentiment using model
            sentiment_text = self._generate_sentiment(prompt)
            
            # Parse output to extract sentiment
            sentiment, confidence = self._parse_sentiment_output(sentiment_text)
            
            result = {
                "sentiment": sentiment,
                "confidence": confidence,
                "text_preview": text[:50] + "..." if len(text) > 50 else text
            }
            
            # Cache result for 1 hour (3600 seconds)
            ttl = CacheTTLStrategy.get_sentiment_ttl()
            self.cache_service.set(cache_key, result, ttl=ttl)
            self.logger.debug(f"Sentiment cached for text hash: {text_hash[:8]}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error analyzing sentiment: {e}")
        
        return {
            "sentiment": "خنثی",
            "confidence": 0.0,
            "error": "Analysis failed"
        }
    
    def _generate_sentiment(self, prompt: str) -> str:
        """
        Generate sentiment response using Qwen2
        
        Args:
            prompt: Formatted prompt
            
        Returns:
            Generated sentiment text
        """
        import torch
        
        try:
            # Encode prompt
            inputs = self.tokenizer.encode(prompt, return_tensors="pt")
            
            # Generate
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs,
                    max_new_tokens=SentimentSettings.MAX_NEW_TOKENS,
                    temperature=SentimentSettings.TEMPERATURE,
                    top_p=SentimentSettings.TOP_P,
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id
                )
            
            # Decode - get only the new tokens
            generated_text = self.tokenizer.decode(
                outputs[0][len(inputs[0]):],
                skip_special_tokens=True
            )
            
            return generated_text.strip()
            
        except Exception as e:
            self.logger.error(f"Error generating sentiment: {e}")
            return "خنثی"
    
    def _parse_sentiment_output(self, output: str) -> tuple:
        """
        Parse model output to extract sentiment label and confidence
        
        Args:
            output: Generated text from model
            
        Returns:
            Tuple of (sentiment, confidence)
        """
        output = output.strip().lower()
        
        # Extract sentiment words
        for label, normalized in SentimentSettings.LABEL_MAPPING.items():
            if label.lower() in output:
                # High confidence if exact label found
                confidence = 0.85
                return normalized, confidence
        
        # If no clear sentiment found, default to neutral
        self.logger.warning(f"Could not parse sentiment from: {output}")
        return "خنثی", 0.5
    
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
    
    def clear_cache(self):
        """Clear all sentiment caches"""
        # Clear in-memory cache
        self._clear_cache()
        self.sentiment_cache.clear()
        
        # Clear Redis cache
        deleted = self.cache_service.delete_pattern("sentiment:*")
        self.logger.info(f"Cleared sentiment cache: {deleted} keys deleted")
        
        return deleted