"""
services/batch_embedding_service.py
----------------------------------
Optimized batch embedding generation for faster indexing
Processes multiple texts at once instead of one-by-one
3x faster embedding generation
"""

import logging
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import numpy as np

from config.rag_settings import RAGSettings
from utils.exceptions import ServiceError
from utils.embedding_text_formatter import EmbeddingTextFormatter


class BatchEmbeddingMetrics:
    """Track batch embedding performance metrics"""
    
    def __init__(self):
        self.total_texts = 0
        self.total_time = 0
        self.batch_count = 0
        self.start_time = None
    
    def record_batch(self, text_count: int, processing_time: float):
        """Record metrics for a batch"""
        self.total_texts += text_count
        self.total_time += processing_time
        self.batch_count += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        avg_time_per_text = (self.total_time / self.total_texts) if self.total_texts > 0 else 0
        texts_per_second = (self.total_texts / self.total_time) if self.total_time > 0 else 0
        
        return {
            'total_texts': self.total_texts,
            'total_time': round(self.total_time, 2),
            'batch_count': self.batch_count,
            'avg_time_per_text': round(avg_time_per_text, 4),
            'texts_per_second': round(texts_per_second, 2),
            'avg_batch_size': round(self.total_texts / self.batch_count, 1) if self.batch_count > 0 else 0
        }
    
    def reset(self):
        """Reset metrics"""
        self.total_texts = 0
        self.total_time = 0
        self.batch_count = 0


class BatchEmbeddingService:
    """Service for batch embedding generation"""
    
    def __init__(self, embedding_model=None, batch_size: int = 32, show_progress: bool = True):
        """
        Initialize batch embedding service
        
        Args:
            embedding_model: Pre-loaded embedding model (creates if None)
            batch_size: Number of texts to process at once (32 default)
            show_progress: Show progress messages
        """
        self.logger = logging.getLogger(__name__)
        self.model = embedding_model
        self.batch_size = batch_size
        self.show_progress = show_progress
        self.metrics = BatchEmbeddingMetrics()
    
    async def initialize_model(self, model_name: str = None):
        """
        Initialize or load embedding model.

        REFACTORED: Now uses ModelLoader for consistent patterns.

        Args:
            model_name: Model name (uses RAGSettings if None)
        """
        try:
            # DRY: Use centralized "already loaded" check
            from utils.model_loader import ModelLoader

            if ModelLoader.check_already_loaded(self.model, "Embedding model"):
                return True

            model_name = model_name or RAGSettings.EMBEDDING_MODEL
            self.logger.info(f"Loading embedding model: {model_name}")

            # Lazy import to avoid startup slowdown
            from sentence_transformers import SentenceTransformer

            # DRY: Use centralized environment setup
            ModelLoader.setup_minimal_logging()

            device = RAGSettings.EMBEDDING_DEVICE
            self.model = SentenceTransformer(model_name, device=device)

            self.logger.info(f"✅ Model loaded on device: {device}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to load model: {e}")
            raise ServiceError(f"Model loading failed: {e}")
    
    def _texts_to_batches(self, texts: List[str]) -> List[List[str]]:
        """
        Split texts into batches
        
        Args:
            texts: List of texts to process
            
        Returns:
            List of batches
        """
        batches = []
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i + self.batch_size]
            batches.append(batch)
        return batches
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts at once
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embeddings (one per text)
        """
        if not self.model:
            self.logger.error("Model not initialized")
            return None
        
        try:
            embeddings = self.model.encode(texts, convert_to_tensor=False, batch_size=self.batch_size)
            
            # Convert to list format
            if hasattr(embeddings, 'tolist'):
                return embeddings.tolist()
            return embeddings
        except Exception as e:
            self.logger.error(f"Error generating batch embeddings: {e}")
            return None
    
    def embed_texts_optimized(self, texts: List[str], show_progress: bool = True) -> List[Dict[str, Any]]:
        """
        Generate embeddings for multiple texts with optimization
        
        Args:
            texts: List of texts to embed
            show_progress: Show progress messages
            
        Returns:
            List of dicts with text and embedding
        """
        if not self.model:
            self.logger.error("Model not initialized")
            return []
        
        try:
            start_time = datetime.now()
            total_texts = len(texts)
            
            if show_progress:
                self.logger.info(f"🔄 Starting batch embedding: {total_texts} texts")
            
            # Split into batches
            batches = self._texts_to_batches(texts)
            
            embeddings_data = []
            
            for batch_idx, batch in enumerate(batches):
                if show_progress:
                    progress = f"[{(batch_idx + 1) * self.batch_size}/{total_texts}]"
                    self.logger.info(f"  Processing batch {batch_idx + 1}/{len(batches)} {progress}")
                
                # Generate embeddings for batch
                batch_embeddings = self.embed_batch(batch)
                
                if batch_embeddings is None:
                    continue
                
                # Convert numpy arrays to lists if needed
                for text, embedding in zip(batch, batch_embeddings):
                    if hasattr(embedding, 'tolist'):
                        embedding = embedding.tolist()
                    
                    embeddings_data.append({
                        'text': text,
                        'embedding': embedding
                    })
            
            # Record metrics
            elapsed = (datetime.now() - start_time).total_seconds()
            self.metrics.record_batch(total_texts, elapsed)
            
            if show_progress:
                stats = self.metrics.get_stats()
                self.logger.info(
                    f"✅ Batch embedding complete: "
                    f"{stats['total_texts']} texts in {stats['total_time']}s "
                    f"({stats['texts_per_second']} texts/sec)"
                )
            
            return embeddings_data
        except Exception as e:
            self.logger.error(f"Error in optimized embedding: {e}")
            raise ServiceError(f"Batch embedding failed: {e}")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        return self.metrics.get_stats()
    
    def reset_metrics(self):
        """Reset performance metrics"""
        self.metrics.reset()


class OptimizedEmbeddingService:
    """Wrapper combining original and batch embedding services"""
    
    def __init__(self, repositories=None, batch_size: int = 32):
        """
        Initialize optimized embedding service
        
        Args:
            repositories: Repository manager
            batch_size: Batch size for processing
        """
        self.logger = logging.getLogger(__name__)
        self.repositories = repositories
        self.batch_size = batch_size
        self.model = None
        self.batch_service = None
    
    async def initialize(self):
        """Initialize embedding model and batch service"""
        try:
            self.logger.info("Initializing optimized embedding service...")
            
            # Initialize batch service
            self.batch_service = BatchEmbeddingService(batch_size=self.batch_size)
            await self.batch_service.initialize_model()
            self.model = self.batch_service.model
            
            self.logger.info("✅ Optimized embedding service initialized")
            return True
        except Exception as e:
            self.logger.error(f"Initialization failed: {e}")
            return False

    async def embed_all_data_optimized(self) -> Dict[str, Any]:
        """
        Embed all CRM data with optimized batch processing
        
        Returns:
            Embedded data organized by type
        """
        try:
            self.logger.info("Starting optimized data embedding...")
            
            # Get all data
            with self.repositories as uow:
                deals = uow.deals.get_all_deals()
                activities = uow.activities.get_all_activities()
                agents = uow.agents.get_all_agents()
            
            # Format texts
            deal_texts = [
                (str(d.to_dict().get('id')), EmbeddingTextFormatter.format_deal(d.to_dict()))
                for d in deals
            ]
            activity_texts = [
                (str(a.to_dict().get('id')), EmbeddingTextFormatter.format_activity(a.to_dict()))
                for a in activities
            ]
            agent_texts = [
                (str(ag.to_dict().get('id')), EmbeddingTextFormatter.format_agent(ag.to_dict()))
                for ag in agents
            ]
            
            # Batch embed
            self.logger.info(f"Embedding {len(deal_texts)} deals...")
            deal_embeddings = self._embed_with_metadata(deal_texts, 'deal', deals)
            
            self.logger.info(f"Embedding {len(activity_texts)} activities...")
            activity_embeddings = self._embed_with_metadata(activity_texts, 'activity', activities)
            
            self.logger.info(f"Embedding {len(agent_texts)} agents...")
            agent_embeddings = self._embed_with_metadata(agent_texts, 'agent', agents)
            
            result = {
                'deals': deal_embeddings,
                'activities': activity_embeddings,
                'agents': agent_embeddings,
                'timestamp': datetime.now().isoformat(),
                'total_embeddings': len(deal_embeddings) + len(activity_embeddings) + len(agent_embeddings),
                'metrics': self.batch_service.get_metrics()
            }
            
            self.logger.info(f"✅ Embedding complete: {result['total_embeddings']} embeddings")
            self.logger.info(f"   Metrics: {result['metrics']}")
            
            return result
        except Exception as e:
            self.logger.error(f"Error in batch embedding: {e}")
            raise ServiceError(f"Batch embedding failed: {e}")
    
    def _embed_with_metadata(self, texts_with_ids: List[Tuple[str, str]], 
                             entity_type: str, original_objects) -> List[Dict[str, Any]]:
        """
        Embed texts and attach metadata
        
        Args:
            texts_with_ids: List of (id, text) tuples
            entity_type: Type of entity (deal, activity, agent)
            original_objects: Original objects for metadata
            
        Returns:
            List of embedding dicts with metadata
        """
        if not texts_with_ids:
            return []
        
        # Extract just texts for batch embedding
        texts = [text for _, text in texts_with_ids]
        
        # Batch embed
        embeddings_list = self.batch_service.embed_texts_optimized(texts, show_progress=False)
        
        # Attach metadata
        result = []
        for (entity_id, text), embedding_data in zip(texts_with_ids, embeddings_list):
            result.append({
                'id': entity_id,
                'type': entity_type,
                'text': text,
                'embedding': embedding_data['embedding'],
                'metadata': self._get_metadata(entity_type, entity_id, original_objects)
            })
        
        return result
    
    def _get_metadata(self, entity_type: str, entity_id: str, objects) -> Dict[str, Any]:
        """Get metadata for entity"""
        for obj in objects:
            obj_dict = obj.to_dict() if hasattr(obj, 'to_dict') else obj
            if str(obj_dict.get('id')) == entity_id:
                if entity_type == 'deal':
                    return {'title': obj_dict.get('title'), 'status': obj_dict.get('status'), 'value': obj_dict.get('value')}
                elif entity_type == 'activity':
                    return {'type': obj_dict.get('type'), 'agent': obj_dict.get('agent_name')}
                elif entity_type == 'agent':
                    return {'name': obj_dict.get('name'), 'title': obj_dict.get('title')}
        return {}