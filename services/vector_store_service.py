"""
services/vector_store_service.py
--------------------------------
Vector store service for semantic search using ChromaDB
Manages embeddings storage and similarity queries
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import chromadb

from services.base_service import BaseService
from services.embedding_service import EmbeddingService
from utils.exceptions import ServiceError

class VectorStoreService(BaseService):
    """Service for managing vector embeddings in ChromaDB"""
    
    def __init__(self, repositories=None, persist_dir: str = None):
        """
        Initialize vector store service
        
        Args:
            repositories: Repository manager
            persist_dir: Directory to persist ChromaDB data (uses RAGSettings if None)
        """
        super().__init__(repositories)
        
        # Use RAGSettings for persistent storage by default
        if persist_dir is None:
            from config.rag_settings import RAGSettings
            RAGSettings.validate_paths()
            persist_dir = str(RAGSettings.CHROMA_DB_DIR)
        
        self.persist_dir = persist_dir
        self.client = None
        self.collections = {}
        self.logger = logging.getLogger(__name__)
    async def initialize(self):
        """Initialize ChromaDB client and collections"""
        success = await self._safe_initialize(
            self._setup_chromadb,
            service_name=f"ChromaDB (persist_dir: {self.persist_dir})",
            raise_on_error=True  # This service requires ChromaDB to work
        )
        # If initialization failed but didn't raise, ensure state is consistent
        if not success and not self.client:
            raise ServiceError("ChromaDB initialization failed")
    
    async def _setup_chromadb(self):
        """Actual ChromaDB setup logic"""
        # Initialize ChromaDB with modern API (no deprecated Settings)
        self.client = chromadb.PersistentClient(path=self.persist_dir)
        
        # Create/get collections for each data type
        self._initialize_collections()
    def _initialize_collections(self):
        """Create or get ChromaDB collections for each entity type"""
        collection_names = ['deals', 'activities', 'agents']
        
        for collection_name in collection_names:
            try:
                collection = self.client.get_or_create_collection(
                    name=collection_name,
                    metadata={"hnsw:space": "cosine"}
                )
                self.collections[collection_name] = collection
                self.logger.info(f"Collection '{collection_name}' ready")
            except Exception as e:
                self.logger.error(f"Error creating collection {collection_name}: {e}")
                raise
    
    def add_embeddings(self, embeddings_data: List[Dict[str, Any]], collection_name: str) -> bool:
        """
        Add embeddings to ChromaDB collection
        
        Args:
            embeddings_data: List of embedding data dictionaries
            collection_name: Name of collection ('deals', 'activities', 'agents')
            
        Returns:
            True if successful
        """
        if collection_name not in self.collections:
            self.logger.error(f"Collection {collection_name} not found")
            return False
        
        try:
            collection = self.collections[collection_name]
            
            for item in embeddings_data:
                # Ensure metadata is not empty - ChromaDB requires at least one field
                metadata = item.get('metadata', {})
                if not metadata:
                    metadata = {'type': collection_name}
                
                collection.add(
                    ids=[item['id']],
                    embeddings=[item['embedding']],
                    documents=[item['text']],
                    metadatas=[metadata]
                )
            
            self.logger.info(f"Added {len(embeddings_data)} embeddings to {collection_name}")
            return True
        except Exception as e:
            self.logger.error(f"Error adding embeddings: {e}")
            raise ServiceError(f"Failed to add embeddings: {e}")
    
    def add_all_embeddings(self, embedding_service_or_dict) -> Dict[str, bool]:
        """
        Generate and add all embeddings to vector store
        
        Args:
            embedding_service_or_dict: Either EmbeddingService object or embeddings dict
            
        Returns:
            Status for each collection
        """
        try:
            self.logger.info("Adding all embeddings")
            
            # Handle both EmbeddingService and dict ✅ FLEXIBLE
            if isinstance(embedding_service_or_dict, dict):
                all_embeddings = embedding_service_or_dict
                self.logger.info("Using provided embeddings dict")
            else:
                self.logger.info("Generating embeddings from service")
                all_embeddings = embedding_service_or_dict.embed_all_data()
            
            results = {}
            
            # Add deals
            if all_embeddings.get('deals'):
                results['deals'] = self.add_embeddings(all_embeddings['deals'], 'deals')
            
            # Add activities
            if all_embeddings.get('activities'):
                results['activities'] = self.add_embeddings(all_embeddings['activities'], 'activities')
            
            # Add agents
            if all_embeddings.get('agents'):
                results['agents'] = self.add_embeddings(all_embeddings['agents'], 'agents')
            
            self.logger.info(f"All embeddings added: {results}")
            return results
        except Exception as e:
            self.logger.error(f"Error adding all embeddings: {e}")
            raise ServiceError(f"Failed to add all embeddings: {e}")
    
    def search(self, query_text: str, collection_name: str, n_results: int = 5, 
               where: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """
        Semantic search in collection
        
        Args:
            query_text: Query text to search
            collection_name: Name of collection to search
            n_results: Number of results to return
            where: Optional metadata filter
            
        Returns:
            List of search results with scores
        """
        if collection_name not in self.collections:
            self.logger.error(f"Collection {collection_name} not found")
            return []
        
        try:
            collection = self.collections[collection_name]
            
            results = collection.query(
                query_texts=[query_text],
                n_results=n_results,
                where=where
            )
            
            # Format results
            formatted_results = []
            if results['ids'] and results['ids'][0]:
                for i, doc_id in enumerate(results['ids'][0]):
                    formatted_results.append({
                        'id': doc_id,
                        'text': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i],
                        'distance': results['distances'][0][i] if results['distances'] else 0,
                        'similarity': 1 - results['distances'][0][i] if results['distances'] else 0
                    })
            
            self.logger.debug(f"Search in {collection_name}: found {len(formatted_results)} results")
            return formatted_results
        except Exception as e:
            self.logger.error(f"Error searching {collection_name}: {e}")
            return []
    
    def search_all_collections(self, query_text: str, n_results: int = 5) -> Dict[str, List[Dict[str, Any]]]:
        """
        Search across all collections
        
        Args:
            query_text: Query text to search
            n_results: Number of results per collection
            
        Returns:
            Dictionary with results from each collection
        """
        try:
            results = {
                'deals': self.search(query_text, 'deals', n_results),
                'activities': self.search(query_text, 'activities', n_results),
                'agents': self.search(query_text, 'agents', n_results)
            }
            
            self.logger.debug(f"Cross-collection search: {sum(len(r) for r in results.values())} total results")
            return results
        except Exception as e:
            self.logger.error(f"Error in cross-collection search: {e}")
            return {'deals': [], 'activities': [], 'agents': []}
    
    def delete_collection(self, collection_name: str) -> bool:
        """
        Delete and recreate a collection (useful for reindexing)
        
        Args:
            collection_name: Name of collection to delete
            
        Returns:
            True if successful
        """
        try:
            if collection_name in self.collections:
                self.client.delete_collection(name=collection_name)
                del self.collections[collection_name]
                
                # Recreate collection
                collection = self.client.get_or_create_collection(
                    name=collection_name,
                    metadata={"hnsw:space": "cosine"}
                )
                self.collections[collection_name] = collection
                
                self.logger.info(f"Collection {collection_name} reset")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error deleting collection {collection_name}: {e}")
            return False
    
    def get_collection_stats(self, collection_name: str) -> Dict[str, Any]:
        """
        Get statistics about a collection
        
        Args:
            collection_name: Name of collection
            
        Returns:
            Collection statistics
        """
        try:
            if collection_name not in self.collections:
                return {}
            
            collection = self.collections[collection_name]
            count = collection.count()
            
            return {
                'collection_name': collection_name,
                'document_count': count,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Error getting collection stats: {e}")
            return {}
    
    def get_all_stats(self) -> Dict[str, Any]:
        """
        Get statistics for all collections
        
        Returns:
            Statistics for all collections
        """
        try:
            stats = {}
            total_documents = 0
            
            for collection_name in self.collections.keys():
                collection_stats = self.get_collection_stats(collection_name)
                stats[collection_name] = collection_stats
                total_documents += collection_stats.get('document_count', 0)
            
            stats['total_documents'] = total_documents
            stats['timestamp'] = datetime.now().isoformat()
            
            return stats
        except Exception as e:
            self.logger.error(f"Error getting all stats: {e}")
            return {}