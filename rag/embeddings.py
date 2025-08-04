"""Embedding providers for FixChain RAG system."""

import logging
from typing import List, Optional
from openai import OpenAI
from .interfaces import EmbeddingProvider

logger = logging.getLogger(__name__)


class OpenAIEmbeddingProvider(EmbeddingProvider):
    """OpenAI embedding provider implementation."""
    
    def __init__(self, api_key: str, model: str = "text-embedding-ada-002", max_retries: int = 3):
        """Initialize OpenAI embedding provider.
        
        Args:
            api_key: OpenAI API key
            model: Embedding model name
            max_retries: Maximum retry attempts
        """
        self.client = OpenAI(api_key=api_key, max_retries=max_retries)
        self.model = model
        self._dimensions = self._get_model_dimensions()
        
    def _get_model_dimensions(self) -> int:
        """Get embedding dimensions for the model."""
        model_dimensions = {
            "text-embedding-ada-002": 1536,
            "text-embedding-3-small": 1536,
            "text-embedding-3-large": 3072,
        }
        return model_dimensions.get(self.model, 1536)
    
    def embed_text(self, text: str) -> List[float]:
        """Generate embedding vector for given text.
        
        Args:
            text: Input text to embed
            
        Returns:
            List of float values representing the embedding vector
        """
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Failed to generate embedding for text: {e}")
            raise
    
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embedding vectors for multiple texts.
        
        Args:
            texts: List of input texts to embed
            
        Returns:
            List of embedding vectors
        """
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=texts
            )
            return [data.embedding for data in response.data]
        except Exception as e:
            logger.error(f"Failed to generate embeddings for texts: {e}")
            raise
    
    @property
    def dimensions(self) -> int:
        """Get the dimensionality of the embedding vectors."""
        return self._dimensions


class HuggingFaceEmbeddingProvider(EmbeddingProvider):
    """HuggingFace embedding provider implementation using sentence-transformers."""
    
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """Initialize HuggingFace embedding provider.
        
        Args:
            model_name: HuggingFace model name
        """
        try:
            from sentence_transformers import SentenceTransformer
            self.model_name = model_name
            self.model = SentenceTransformer(model_name)
            logger.info(f"Loaded HuggingFace model: {model_name}")
        except ImportError:
            raise ImportError("sentence-transformers library is required. Install with: pip install sentence-transformers")
        except Exception as e:
            logger.error(f"Failed to load HuggingFace model {model_name}: {e}")
            raise
    
    def embed_text(self, text: str) -> List[float]:
        """Generate embedding vector for given text."""
        try:
            embedding = self.model.encode([text])[0]
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Failed to generate embedding for text: {e}")
            raise
    
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embedding vectors for multiple texts."""
        try:
            embeddings = self.model.encode(texts)
            return embeddings.tolist()
        except Exception as e:
            logger.error(f"Failed to generate embeddings for texts: {e}")
            raise
    
    @property
    def dimensions(self) -> int:
        """Get the dimensionality of the embedding vectors."""
        # Get actual dimensions from the model
        try:
            return self.model.get_sentence_embedding_dimension()
        except:
            # Fallback to common dimensions
            model_dimensions = {
                "sentence-transformers/all-MiniLM-L6-v2": 384,
                "sentence-transformers/all-mpnet-base-v2": 768,
                "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2": 384,
            }
            return model_dimensions.get(self.model_name, 384)