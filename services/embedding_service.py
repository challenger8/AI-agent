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

class EmbeddingService(BaseService):
    """Service for generating embeddings from CRM data"""
    
    def __init__(self, repositories=None, model_name: str = "sentence-transformers/paraphrase-MiniLM-L6-v2"):
        """
        Initialize embedding service
        
        Args:
            repositories: Repository manager
            model_name: Sentence transformer model name (lightweight PyTorch-only model)
        """
        super().__init__(repositories)
        self.model_name = model_name
        self.model = None
        self.logger = logging.getLogger(__name__)
    
    async def initialize(self):
        """Load embedding model"""
        try:
            self.logger.info(f"Loading embedding model: {self.model_name}")
            
            # Lazy import to avoid dependencies at module load time
            from sentence_transformers import SentenceTransformer
            import os
            
            # Disable TensorFlow/Keras completely
            os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
            os.environ['TOKENIZERS_PARALLELISM'] = 'false'
            os.environ['CUDA_VISIBLE_DEVICES'] = '-1'  # CPU only
            
            # Load model with PyTorch backend
            self.model = SentenceTransformer(self.model_name, device='cpu')
            self.logger.info("Embedding model loaded successfully")
        except Exception as e:
            self.logger.error(f"Failed to load embedding model: {e}")
            # Return gracefully - model will be None
            self.logger.warning("Continuing without embedding model")
    
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
        """
        Convert deal to searchable text
        
        Args:
            deal: Deal dictionary
            
        Returns:
            Formatted text for embedding
        """
        text_parts = [
            f"Deal: {deal.get('title', 'N/A')}",
            f"Status: {deal.get('status', 'N/A')}",
            f"Value: {deal.get('value', 0)}",
            f"Customer: {deal.get('customer_name', 'N/A')}",
            f"Description: {deal.get('description', '')}",
        ]
        return " | ".join(filter(None, text_parts))
    
    def _format_activity_text(self, activity: Dict[str, Any]) -> str:
        """
        Convert activity to searchable text
        
        Args:
            activity: Activity dictionary
            
        Returns:
            Formatted text for embedding
        """
        text_parts = [
            f"Activity: {activity.get('type', 'N/A')}",
            f"Agent: {activity.get('agent_name', 'N/A')}",
            f"Date: {activity.get('activity_date', 'N/A')}",
            f"Notes: {activity.get('notes', '')}",
            f"Outcome: {activity.get('outcome', '')}",
        ]
        return " | ".join(filter(None, text_parts))
    
    def _format_agent_text(self, agent: Dict[str, Any]) -> str:
        """
        Convert agent to searchable text
        
        Args:
            agent: Agent dictionary
            
        Returns:
            Formatted text for embedding
        """
        text_parts = [
            f"Agent: {agent.get('name', 'N/A')}",
            f"Email: {agent.get('email', 'N/A')}",
            f"Phone: {agent.get('phone', 'N/A')}",
            f"Title: {agent.get('title', 'N/A')}",
        ]
        return " | ".join(filter(None, text_parts))
    
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