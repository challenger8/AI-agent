"""
services/embedding_service.py
-----------------------------
Embedding generation service for RAG system
Converts deals, activities, and agents to text chunks and generates embeddings
"""

import logging
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime

from services.base_service import BaseService
from utils.exceptions import ServiceError
from utils.embedding_text_formatter import EmbeddingTextFormatter
from utils.model_utils import ensure_dict
from config.entity_types import EntityTypes

class EmbeddingService(BaseService):
    """Service for generating embeddings from CRM data"""
    def __init__(self, repositories=None, model_name: str = "sentence-transformers/paraphrase-MiniLM-L6-v2"):
        super().__init__(repositories)
        self.model_name = model_name
        self.model = None
    
    async def initialize(self):
        """Load embedding model"""
        await self._safe_initialize(
            self._load_model,
            service_name=f"Embedding Model ({self.model_name})"
        )
        
        # If model failed to load, log warning
        if not self.model:
            self.logger.warning("Continuing without embedding model")
    
    async def _load_model(self):
        """Actual model loading logic"""
        # Lazy import to avoid dependencies at module load time
        from sentence_transformers import SentenceTransformer
        import os
        
        # Disable TensorFlow/Keras completely
        os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
        os.environ['TOKENIZERS_PARALLELISM'] = 'false'
        os.environ['CUDA_VISIBLE_DEVICES'] = '-1'  # CPU only
        
        # Load model with PyTorch backend
        self.model = SentenceTransformer(self.model_name, device='cpu')
    def embed_texts_batch(self, texts: List[str], batch_size: int = 32) -> Optional[List[List[float]]]:
        """
        Generate embeddings for multiple texts at once (optimized)
        
        Args:
            texts: List of texts to embed
            batch_size: Number of texts per batch
            
        Returns:
            List of embeddings or None on error
        """
        if not self.model:
            self.logger.error("Model not initialized. Call initialize() first")
            return None
        
        if not texts:
            return []
        
        try:
            # Use batch encoding for better performance
            embeddings = self.model.encode(texts, batch_size=batch_size, convert_to_tensor=False)
            
            # Convert to list if numpy array
            if hasattr(embeddings, 'tolist'):
                return embeddings.tolist()
            return embeddings
        except Exception as e:
            self.logger.error(f"Error generating batch embeddings: {e}")
            return None
    
    # Configuration for entity embedding - maps entity type to (formatter, metadata_extractor)
    _ENTITY_CONFIG = {
        EntityTypes.DEALS: {
            'formatter': EmbeddingTextFormatter.format_deal,
            'metadata_keys': ['title', 'status', 'value', 'customer_name'],
        },
        EntityTypes.ACTIVITIES: {
            'formatter': EmbeddingTextFormatter.format_activity,
            'metadata_keys': ['deal_id', 'agent_name', 'activity_date', 'type'],
        },
        EntityTypes.AGENTS: {
            'formatter': EmbeddingTextFormatter.format_agent,
            'metadata_keys': ['name', 'email', 'phone', 'title'],
        },
    }

    def _extract_metadata(self, entity_dict: Dict[str, Any], keys: List[str]) -> Dict[str, Any]:
        """Extract metadata fields from entity dict."""
        return {key: entity_dict.get(key) for key in keys}

    def _get_entities_from_repo(self, entity_type: str) -> List[Any]:
        """Get all entities of given type from repository."""
        with self.repositories as uow:
            if entity_type == EntityTypes.DEALS:
                return uow.deals.get_all_deals()
            elif entity_type == EntityTypes.ACTIVITIES:
                return uow.activities.get_all_activities()
            elif entity_type == EntityTypes.AGENTS:
                return uow.agents.get_all_agents()
            else:
                raise ServiceError(f"Unknown entity type: {entity_type}")

    def _embed_entities(self, entity_type: str) -> List[Dict[str, Any]]:
        """
        Generic method to embed entities of any type.

        Args:
            entity_type: One of EntityTypes.DEALS, ACTIVITIES, AGENTS

        Returns:
            List of entities with embeddings
        """
        config = self._ENTITY_CONFIG.get(entity_type)
        if not config:
            raise ServiceError(f"No embedding config for entity type: {entity_type}")

        singular_type = EntityTypes.get_singular(entity_type)

        try:
            entities = self._get_entities_from_repo(entity_type)
            embeddings_data = []

            for entity in entities:
                entity_dict = ensure_dict(entity)
                text = config['formatter'](entity_dict)
                embedding = self.embed_text(text)

                if embedding:
                    embeddings_data.append({
                        'id': str(entity_dict.get('id')),
                        'type': singular_type,
                        'text': text,
                        'embedding': embedding,
                        'metadata': self._extract_metadata(entity_dict, config['metadata_keys'])
                    })

            self.logger.info(f"Generated embeddings for {len(embeddings_data)} {entity_type}")
            return embeddings_data

        except Exception as e:
            self.logger.error(f"Error embedding {entity_type}: {e}")
            raise ServiceError(f"Failed to embed {entity_type}: {e}")

    def embed_text(self, text: str) -> Optional[List[float]]:
        """
        Generate embedding for text
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector or None on error
        """
        if not self.model:
            self.logger.error("Model not initialized. Call initialize() first")
            return None
        
        try:
            embedding = self.model.encode(text, convert_to_tensor=False)
            # Convert numpy array to list
            if hasattr(embedding, 'tolist'):
                return embedding.tolist()
            return embedding
        except Exception as e:
            self.logger.error(f"Error generating embedding: {e}")
            return None
    
    def embed_deals(self) -> List[Dict[str, Any]]:
        """Generate embeddings for all deals. Delegates to generic _embed_entities."""
        return self._embed_entities(EntityTypes.DEALS)

    def embed_activities(self) -> List[Dict[str, Any]]:
        """Generate embeddings for all activities. Delegates to generic _embed_entities."""
        return self._embed_entities(EntityTypes.ACTIVITIES)

    def embed_agents(self) -> List[Dict[str, Any]]:
        """Generate embeddings for all agents. Delegates to generic _embed_entities."""
        return self._embed_entities(EntityTypes.AGENTS)
    
    def embed_all_data(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Generate embeddings for all CRM data
        
        Returns:
            Dictionary with embeddings for deals, activities, and agents
        """
        try:
            self.logger.info("Starting full data embedding process")
            
            deals_embeddings = self.embed_deals()
            activities_embeddings = self.embed_activities()
            agents_embeddings = self.embed_agents()
            
            result = {
                'deals': deals_embeddings,
                'activities': activities_embeddings,
                'agents': agents_embeddings,
                'timestamp': datetime.now().isoformat(),
                'total_embeddings': len(deals_embeddings) + len(activities_embeddings) + len(agents_embeddings)
            }
            
            self.logger.info(f"Embedding complete: {result['total_embeddings']} total embeddings")
            return result
        except Exception as e:
            self.logger.error(f"Error in full embedding process: {e}")
            raise ServiceError(f"Full data embedding failed: {e}")