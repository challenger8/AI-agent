"""
services/embedding_service.py
-----------------------------
Embedding generation service for RAG system
Converts deals, activities, and agents to text chunks and generates embeddings
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

from services.base_service import BaseService
from utils.exceptions import ServiceError
from utils.embedding_text_formatter import EmbeddingTextFormatter

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
    
    def _format_deal_text(self, deal: Dict[str, Any]) -> str:
        """Convert deal to searchable text. Delegates to EmbeddingTextFormatter."""
        return EmbeddingTextFormatter.format_deal(deal)

    def _format_activity_text(self, activity: Dict[str, Any]) -> str:
        """Convert activity to searchable text. Delegates to EmbeddingTextFormatter."""
        return EmbeddingTextFormatter.format_activity(activity)

    def _format_agent_text(self, agent: Dict[str, Any]) -> str:
        """Convert agent to searchable text. Delegates to EmbeddingTextFormatter."""
        return EmbeddingTextFormatter.format_agent(agent)
    
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
        """
        Generate embeddings for all deals
        
        Returns:
            List of deals with embeddings
        """
        try:
            with self.repositories as uow:
                deals = uow.deals.get_all_deals()
            
            embeddings_data = []
            for deal in deals:
                deal_dict = deal.to_dict() if hasattr(deal, 'to_dict') else deal
                text = self._format_deal_text(deal_dict)
                embedding = self.embed_text(text)
                
                if embedding:
                    embeddings_data.append({
                        'id': str(deal_dict.get('id')),
                        'type': 'deal',
                        'text': text,
                        'embedding': embedding,
                        'metadata': {
                            'title': deal_dict.get('title'),
                            'status': deal_dict.get('status'),
                            'value': deal_dict.get('value'),
                            'customer_name': deal_dict.get('customer_name'),
                        }
                    })
            
            self.logger.info(f"Generated embeddings for {len(embeddings_data)} deals")
            return embeddings_data
        except Exception as e:
            self.logger.error(f"Error embedding deals: {e}")
            raise ServiceError(f"Failed to embed deals: {e}")
    
    def embed_activities(self) -> List[Dict[str, Any]]:
        """
        Generate embeddings for all activities
        
        Returns:
            List of activities with embeddings
        """
        try:
            with self.repositories as uow:
                activities = uow.activities.get_all_activities()
            
            embeddings_data = []
            for activity in activities:
                activity_dict = activity.to_dict() if hasattr(activity, 'to_dict') else activity
                text = self._format_activity_text(activity_dict)
                embedding = self.embed_text(text)
                
                if embedding:
                    embeddings_data.append({
                        'id': str(activity_dict.get('id')),
                        'type': 'activity',
                        'text': text,
                        'embedding': embedding,
                        'metadata': {
                            'deal_id': str(activity_dict.get('deal_id')),
                            'agent_name': activity_dict.get('agent_name'),
                            'activity_date': activity_dict.get('activity_date'),
                            'type': activity_dict.get('type'),
                        }
                    })
            
            self.logger.info(f"Generated embeddings for {len(embeddings_data)} activities")
            return embeddings_data
        except Exception as e:
            self.logger.error(f"Error embedding activities: {e}")
            raise ServiceError(f"Failed to embed activities: {e}")
    
    def embed_agents(self) -> List[Dict[str, Any]]:
        """
        Generate embeddings for all agents
        
        Returns:
            List of agents with embeddings
        """
        try:
            with self.repositories as uow:
                agents = uow.agents.get_all_agents()
            
            embeddings_data = []
            for agent in agents:
                agent_dict = agent.to_dict() if hasattr(agent, 'to_dict') else agent
                text = self._format_agent_text(agent_dict)
                embedding = self.embed_text(text)
                
                if embedding:
                    embeddings_data.append({
                        'id': str(agent_dict.get('id')),
                        'type': 'agent',
                        'text': text,
                        'embedding': embedding,
                        'metadata': {
                            'name': agent_dict.get('name'),
                            'email': agent_dict.get('email'),
                            'phone': agent_dict.get('phone'),
                            'title': agent_dict.get('title'),
                        }
                    })
            
            self.logger.info(f"Generated embeddings for {len(embeddings_data)} agents")
            return embeddings_data
        except Exception as e:
            self.logger.error(f"Error embedding agents: {e}")
            raise ServiceError(f"Failed to embed agents: {e}")
    
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