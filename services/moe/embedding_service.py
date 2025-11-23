"""
services/moe/embedding_service.py
---------------------------------
Embedding service for semantic similarity-based routing
Uses TF-IDF as fallback when sentence-transformers unavailable
"""

import hashlib
from typing import Any, Dict, List, Optional
from collections import Counter
import math

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    np = None

from config.moe_settings import MoESettings
from utils.logging_config import get_logger


class EmbeddingService:
    """Service for generating and comparing text embeddings"""

    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)
        self._embedding_cache: Dict[str, Any] = {}
        self._expert_prototypes: Dict[str, Any] = {}
        self._vocabulary: Dict[str, int] = {}
        self._idf: Dict[str, float] = {}
        self._initialized = False

        if not NUMPY_AVAILABLE:
            self.logger.warning("NumPy not available, using simple keyword matching")
            self._use_transformers = False
            self._model = None
            self._initialize_simple_prototypes()
            return

        # Try to load sentence transformers
        self._use_transformers = False
        self._model = None
        try:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
            self._use_transformers = True
            self.logger.info("Using sentence-transformers for embeddings")
        except ImportError:
            self.logger.info("sentence-transformers not available, using TF-IDF fallback")

        self._initialize_expert_prototypes()

    def _initialize_simple_prototypes(self):
        """Initialize simple keyword-based prototypes when numpy not available"""
        from config.moe_settings import MoESettings
        self._expert_prototypes = MoESettings.ROUTING_KEYWORDS.copy()
        self._initialized = True
        self.logger.info("Initialized simple keyword-based prototypes")

    def _initialize_expert_prototypes(self):
        """Initialize prototype embeddings for each expert type"""
        # Create prototype texts for each expert
        expert_prototypes = {
            'deal_analysis': [
                "analyze deal health score performance metrics",
                "معامله قرارداد سلامت امتیاز تحلیل عملکرد",
                "deal status value pipeline stage conversion",
                "وضعیت معامله ارزش پایپلاین مرحله تبدیل"
            ],
            'sentiment': [
                "sentiment feeling emotion positive negative neutral",
                "احساس حس خلق مثبت منفی خنثی نظر",
                "mood opinion attitude perception feeling",
                "خلق و خو نظر نگرش درک احساس"
            ],
            'activity': [
                "activity timeline history recent last trend summary",
                "فعالیت جدول زمانی تاریخچه اخیر آخرین روند خلاصه",
                "actions events log record track",
                "اقدامات رویدادها گزارش ثبت پیگیری"
            ],
            'risk_assessment': [
                "risk danger warning problem issue threat vulnerability",
                "ریسک خطر هشدار مشکل نگرانی تهدید آسیب‌پذیری",
                "concern alert hazard exposure potential",
                "نگرانی هشدار خطر در معرض پتانسیل"
            ],
            'search': [
                "find search look query where which related similar",
                "پیدا جستجو گشتن پرس‌وجو کجا کدام مرتبط مشابه",
                "retrieve locate discover match",
                "بازیابی یافتن کشف تطبیق"
            ]
        }

        # Build vocabulary from all prototypes
        all_texts = []
        for texts in expert_prototypes.values():
            all_texts.extend(texts)
        self._build_vocabulary(all_texts)

        # Generate embeddings for each expert
        for expert_type, texts in expert_prototypes.items():
            embeddings = [self.embed(text) for text in texts]
            # Average the embeddings
            self._expert_prototypes[expert_type] = np.mean(embeddings, axis=0)

        self._initialized = True
        self.logger.info(f"Initialized {len(self._expert_prototypes)} expert prototypes")

    def _build_vocabulary(self, texts: List[str]):
        """Build vocabulary and IDF from texts"""
        doc_freq = Counter()
        all_words = set()

        for text in texts:
            words = self._tokenize(text)
            unique_words = set(words)
            all_words.update(unique_words)
            for word in unique_words:
                doc_freq[word] += 1

        # Create vocabulary mapping
        self._vocabulary = {word: idx for idx, word in enumerate(sorted(all_words))}

        # Calculate IDF
        num_docs = len(texts)
        for word, freq in doc_freq.items():
            self._idf[word] = math.log(num_docs / (1 + freq))

    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text into words"""
        # Simple tokenization - split on whitespace and punctuation
        import re
        words = re.findall(r'\w+', text.lower())
        return words

    def embed(self, text: str) -> Any:
        """
        Generate embedding for text

        Args:
            text: Input text

        Returns:
            Embedding vector as numpy array or list
        """
        if not NUMPY_AVAILABLE:
            # Return tokenized text as simple embedding
            return self._tokenize(text)

        # Check cache
        cache_key = hashlib.md5(text.encode()).hexdigest()
        if cache_key in self._embedding_cache:
            return self._embedding_cache[cache_key]

        if self._use_transformers and self._model:
            # Use sentence transformers
            embedding = self._model.encode(text, convert_to_numpy=True)
        else:
            # Use TF-IDF fallback
            embedding = self._tfidf_embed(text)

        # Cache the embedding
        if len(self._embedding_cache) < MoESettings.MAX_CACHE_SIZE:
            self._embedding_cache[cache_key] = embedding

        return embedding

    def _tfidf_embed(self, text: str) -> Any:
        """Generate TF-IDF embedding for text"""
        words = self._tokenize(text)

        # Calculate term frequencies
        tf = Counter(words)
        total_words = len(words)

        # Create embedding vector
        embedding = np.zeros(len(self._vocabulary) if self._vocabulary else 100)

        for word, count in tf.items():
            if word in self._vocabulary:
                idx = self._vocabulary[word]
                tf_value = count / total_words if total_words > 0 else 0
                idf_value = self._idf.get(word, 1.0)
                embedding[idx] = tf_value * idf_value

        # Normalize
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm

        return embedding

    def similarity(self, embedding1: Any, embedding2: Any) -> float:
        """
        Calculate cosine similarity between two embeddings

        Args:
            embedding1: First embedding
            embedding2: Second embedding

        Returns:
            Similarity score (0-1)
        """
        # Handle different embedding sizes
        if len(embedding1) != len(embedding2):
            # Pad shorter embedding
            max_len = max(len(embedding1), len(embedding2))
            embedding1 = np.pad(embedding1, (0, max_len - len(embedding1)))
            embedding2 = np.pad(embedding2, (0, max_len - len(embedding2)))

        # Calculate cosine similarity
        dot_product = np.dot(embedding1, embedding2)
        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        similarity = dot_product / (norm1 * norm2)

        # Normalize to 0-1 range
        return float((similarity + 1) / 2)

    def get_expert_similarities(self, query: str) -> Dict[str, float]:
        """
        Get similarity scores between query and all expert prototypes

        Args:
            query: Input query

        Returns:
            Dictionary of expert_type -> similarity_score
        """
        if not NUMPY_AVAILABLE:
            # Simple keyword matching
            return self._simple_keyword_similarity(query)

        if not self._initialized:
            self._initialize_expert_prototypes()

        query_embedding = self.embed(query)

        similarities = {}
        for expert_type, prototype in self._expert_prototypes.items():
            similarities[expert_type] = self.similarity(query_embedding, prototype)

        return similarities

    def _simple_keyword_similarity(self, query: str) -> Dict[str, float]:
        """Simple keyword-based similarity when numpy not available"""
        query_lower = query.lower()
        query_words = set(self._tokenize(query))

        similarities = {}
        for expert_type, keywords in self._expert_prototypes.items():
            matches = 0
            for keyword in keywords:
                if keyword.lower() in query_lower or keyword.lower() in query_words:
                    matches += 1
            # Normalize to 0-1
            similarities[expert_type] = min(matches / max(len(keywords), 1) * 3, 1.0)

        return similarities

    def batch_embed(self, texts: List[str]) -> List[Any]:
        """
        Generate embeddings for multiple texts

        Args:
            texts: List of input texts

        Returns:
            List of embedding vectors
        """
        if not NUMPY_AVAILABLE:
            return [self.embed(text) for text in texts]

        if self._use_transformers and self._model:
            # Batch encode with transformers
            embeddings = self._model.encode(texts, convert_to_numpy=True)
            return list(embeddings)
        else:
            # Sequential TF-IDF
            return [self.embed(text) for text in texts]

    def update_expert_prototype(self, expert_type: str, texts: List[str]):
        """
        Update expert prototype with new example texts

        Args:
            expert_type: Type of expert
            texts: New example texts for the expert
        """
        if expert_type not in MoESettings.EXPERT_TYPES:
            self.logger.warning(f"Unknown expert type: {expert_type}")
            return

        # Generate embeddings for new texts
        embeddings = self.batch_embed(texts)

        # Update prototype (weighted average with existing)
        if expert_type in self._expert_prototypes:
            old_prototype = self._expert_prototypes[expert_type]
            new_prototype = np.mean(embeddings, axis=0)
            # 70% old, 30% new
            self._expert_prototypes[expert_type] = 0.7 * old_prototype + 0.3 * new_prototype
        else:
            self._expert_prototypes[expert_type] = np.mean(embeddings, axis=0)

        self.logger.info(f"Updated prototype for expert: {expert_type}")

    def clear_cache(self):
        """Clear embedding cache"""
        self._embedding_cache.clear()
        self.logger.info("Cleared embedding cache")

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            'cache_size': len(self._embedding_cache),
            'max_cache_size': MoESettings.MAX_CACHE_SIZE,
            'vocabulary_size': len(self._vocabulary),
            'using_transformers': self._use_transformers
        }
