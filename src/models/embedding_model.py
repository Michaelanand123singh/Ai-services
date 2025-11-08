"""
Embedding model for vector representations
"""
from typing import List, Optional, Union
import asyncio
import numpy as np
from sentence_transformers import SentenceTransformer
import openai

from src.core.config import settings
from src.core.logger import ai_logger
from src.core.exceptions import EmbeddingError


class EmbeddingModel:
    """Embedding model for generating vector representations"""
    
    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or "all-MiniLM-L6-v2"
        self.model = None
        self.embedding_dimension = 384  # Default for all-MiniLM-L6-v2
        
    async def initialize(self):
        """Initialize the embedding model"""
        try:
            if self.model_name.startswith("text-embedding"):
                # OpenAI embedding model
                if not settings.openai_api_key:
                    raise EmbeddingError("OpenAI API key required for OpenAI embeddings")
                self.embedding_dimension = 1536  # OpenAI text-embedding-ada-002 dimension
            else:
                # Sentence transformer model
                self.model = await asyncio.to_thread(
                    SentenceTransformer, self.model_name
                )
                self.embedding_dimension = self.model.get_sentence_embedding_dimension()
                
            ai_logger.logger.info(f"Initialized embedding model: {self.model_name}")
        except Exception as e:
            ai_logger.log_error(e, {"model_name": self.model_name})
            raise EmbeddingError(f"Failed to initialize embedding model: {str(e)}")
    
    async def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text"""
        try:
            if self.model_name.startswith("text-embedding"):
                return await self._embed_with_openai(text)
            else:
                return await self._embed_with_sentence_transformer(text)
        except Exception as e:
            ai_logger.log_error(e, {"text_length": len(text)})
            raise EmbeddingError(f"Failed to generate embedding: {str(e)}")
    
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        try:
            if self.model_name.startswith("text-embedding"):
                return await self._embed_batch_with_openai(texts)
            else:
                return await self._embed_batch_with_sentence_transformer(texts)
        except Exception as e:
            ai_logger.log_error(e, {"batch_size": len(texts)})
            raise EmbeddingError(f"Failed to generate batch embeddings: {str(e)}")
    
    async def _embed_with_openai(self, text: str) -> List[float]:
        """Generate embedding using OpenAI API"""
        client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
        response = await client.embeddings.create(
            model=self.model_name,
            input=text
        )
        return response.data[0].embedding
    
    async def _embed_batch_with_openai(self, texts: List[str]) -> List[List[float]]:
        """Generate batch embeddings using OpenAI API"""
        client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
        response = await client.embeddings.create(
            model=self.model_name,
            input=texts
        )
        return [data.embedding for data in response.data]
    
    async def _embed_with_sentence_transformer(self, text: str) -> List[float]:
        """Generate embedding using sentence transformers"""
        if not self.model:
            await self.initialize()
        
        embedding = await asyncio.to_thread(
            self.model.encode, text, convert_to_tensor=False
        )
        return embedding.tolist()
    
    async def _embed_batch_with_sentence_transformer(self, texts: List[str]) -> List[List[float]]:
        """Generate batch embeddings using sentence transformers"""
        if not self.model:
            await self.initialize()
        
        embeddings = await asyncio.to_thread(
            self.model.encode, texts, convert_to_tensor=False
        )
        return embeddings.tolist()
    
    def get_dimension(self) -> int:
        """Get the embedding dimension"""
        return self.embedding_dimension
    
    async def similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Calculate cosine similarity between two embeddings"""
        try:
            # Convert to numpy arrays
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            
            # Calculate cosine similarity
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            return float(dot_product / (norm1 * norm2))
        except Exception as e:
            ai_logger.log_error(e, {"embedding_dims": [len(embedding1), len(embedding2)]})
            raise EmbeddingError(f"Failed to calculate similarity: {str(e)}")


# Global embedding model instance
_embedding_model = None

async def get_embedding_model(model_name: Optional[str] = None) -> EmbeddingModel:
    """Get or create the global embedding model instance"""
    global _embedding_model
    
    if _embedding_model is None or (model_name and _embedding_model.model_name != model_name):
        _embedding_model = EmbeddingModel(model_name)
        await _embedding_model.initialize()
    
    return _embedding_model