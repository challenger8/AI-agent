"""
tests/unit/test_embedding_service.py
------------------------------------
Unit tests for embedding service
"""

import pytest

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    np = None

from services.moe.embedding_service import EmbeddingService

pytestmark = pytest.mark.skipif(
    not NUMPY_AVAILABLE,
    reason="NumPy not installed"
)


class TestEmbeddingService:
    """Tests for EmbeddingService"""

    @pytest.fixture
    def embedding_service(self):
        """Create embedding service instance"""
        return EmbeddingService()

    def test_initialization(self, embedding_service):
        """Test service initialization"""
        assert embedding_service is not None
        assert embedding_service._initialized is True
        assert len(embedding_service._expert_prototypes) == 5

    def test_embed_returns_array(self, embedding_service):
        """Test embed returns numpy array"""
        text = "test query"
        embedding = embedding_service.embed(text)
        assert isinstance(embedding, np.ndarray)
        assert len(embedding) > 0

    def test_embed_caches_results(self, embedding_service):
        """Test embedding caching"""
        text = "cached query"
        embedding1 = embedding_service.embed(text)
        embedding2 = embedding_service.embed(text)
        assert np.array_equal(embedding1, embedding2)
        assert len(embedding_service._embedding_cache) > 0

    def test_similarity_same_text(self, embedding_service):
        """Test similarity of identical texts"""
        text = "identical text"
        embedding = embedding_service.embed(text)
        similarity = embedding_service.similarity(embedding, embedding)
        assert similarity == pytest.approx(1.0, abs=0.01)

    def test_similarity_range(self, embedding_service):
        """Test similarity is in valid range"""
        text1 = "deal analysis query"
        text2 = "sentiment feeling emotion"
        emb1 = embedding_service.embed(text1)
        emb2 = embedding_service.embed(text2)
        similarity = embedding_service.similarity(emb1, emb2)
        assert 0.0 <= similarity <= 1.0

    def test_get_expert_similarities(self, embedding_service):
        """Test getting expert similarity scores"""
        query = "analyze deal health"
        similarities = embedding_service.get_expert_similarities(query)
        assert isinstance(similarities, dict)
        assert len(similarities) == 5
        assert all(0.0 <= score <= 1.0 for score in similarities.values())

    def test_expert_similarities_deal_query(self, embedding_service):
        """Test deal query gets high deal_analysis score"""
        query = "deal health score performance"
        similarities = embedding_service.get_expert_similarities(query)
        assert 'deal_analysis' in similarities
        # Deal-related query should have reasonable score for deal_analysis
        assert similarities['deal_analysis'] > 0.3

    def test_expert_similarities_sentiment_query(self, embedding_service):
        """Test sentiment query gets high sentiment score"""
        query = "sentiment feeling emotion positive"
        similarities = embedding_service.get_expert_similarities(query)
        assert 'sentiment' in similarities
        # Sentiment query should have reasonable score for sentiment
        assert similarities['sentiment'] > 0.3

    def test_batch_embed(self, embedding_service):
        """Test batch embedding"""
        texts = ["query one", "query two", "query three"]
        embeddings = embedding_service.batch_embed(texts)
        assert len(embeddings) == 3
        assert all(isinstance(e, np.ndarray) for e in embeddings)

    def test_update_expert_prototype(self, embedding_service):
        """Test updating expert prototype"""
        original = embedding_service._expert_prototypes['deal_analysis'].copy()
        embedding_service.update_expert_prototype(
            'deal_analysis',
            ['new deal example', 'another deal text']
        )
        updated = embedding_service._expert_prototypes['deal_analysis']
        # Prototype should be updated (not identical)
        assert not np.array_equal(original, updated)

    def test_clear_cache(self, embedding_service):
        """Test clearing cache"""
        embedding_service.embed("cache test")
        assert len(embedding_service._embedding_cache) > 0
        embedding_service.clear_cache()
        assert len(embedding_service._embedding_cache) == 0

    def test_get_cache_stats(self, embedding_service):
        """Test getting cache statistics"""
        embedding_service.embed("stats test")
        stats = embedding_service.get_cache_stats()
        assert 'cache_size' in stats
        assert 'max_cache_size' in stats
        assert 'vocabulary_size' in stats
        assert 'using_transformers' in stats

    def test_tokenize(self, embedding_service):
        """Test tokenization"""
        text = "Hello World Test"
        tokens = embedding_service._tokenize(text)
        assert 'hello' in tokens
        assert 'world' in tokens
        assert len(tokens) == 3

    def test_persian_text_embedding(self, embedding_service):
        """Test Persian text embedding"""
        persian_text = "معامله قرارداد تحلیل"
        embedding = embedding_service.embed(persian_text)
        assert isinstance(embedding, np.ndarray)
        assert len(embedding) > 0

    def test_similarity_different_sizes(self, embedding_service):
        """Test similarity handles different embedding sizes"""
        emb1 = np.array([1, 2, 3])
        emb2 = np.array([1, 2, 3, 4, 5])
        similarity = embedding_service.similarity(emb1, emb2)
        assert 0.0 <= similarity <= 1.0

    def test_empty_text_embedding(self, embedding_service):
        """Test embedding empty text"""
        embedding = embedding_service.embed("")
        assert isinstance(embedding, np.ndarray)

    def test_tfidf_embed(self, embedding_service):
        """Test TF-IDF embedding directly"""
        text = "test query for tfidf"
        embedding = embedding_service._tfidf_embed(text)
        assert isinstance(embedding, np.ndarray)
        # Check normalization
        norm = np.linalg.norm(embedding)
        if norm > 0:
            assert norm == pytest.approx(1.0, abs=0.01)
