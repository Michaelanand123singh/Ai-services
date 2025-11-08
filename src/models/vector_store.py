"""
Vector store implementations for similarity search
"""
from typing import List, Dict, Any, Optional, Tuple
import asyncio
import numpy as np
import faiss
import json
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass

from src.core.config import settings
from src.core.logger import ai_logger
from src.core.exceptions import VectorDatabaseError
from src.models.embedding_model import EmbeddingModel, get_embedding_model


@dataclass
class Document:
    """Document with metadata for vector storage"""
    id: str
    content: str
    embedding: Optional[List[float]] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class SearchResult:
    """Search result with similarity score"""
    document: Document
    score: float


class VectorStore(ABC):
    """Abstract base class for vector stores"""
    
    @abstractmethod
    async def add_documents(self, documents: List[Document]) -> None:
        """Add documents to the vector store"""
        pass
    
    @abstractmethod
    async def search(self, query_embedding: List[float], k: int = 5) -> List[SearchResult]:
        """Search for similar documents"""
        pass
    
    @abstractmethod
    async def delete_document(self, doc_id: str) -> bool:
        """Delete a document by ID"""
        pass
    
    @abstractmethod
    async def get_document_count(self) -> int:
        """Get the total number of documents"""
        pass


class FAISSVectorStore(VectorStore):
    """FAISS-based vector store implementation"""
    
    def __init__(self, dimension: int = 384, index_path: Optional[str] = None):
        self.dimension = dimension
        self.index_path = index_path or "faiss_index"
        self.index = None
        self.documents: Dict[int, Document] = {}
        self.id_mapping: Dict[str, int] = {}  # doc_id -> index_id
        self.next_id = 0
        
    async def initialize(self):
        """Initialize the FAISS index"""
        try:
            # Create FAISS index
            self.index = faiss.IndexFlatIP(self.dimension)  # Inner product (cosine similarity)
            
            # Try to load existing index
            if os.path.exists(f"{self.index_path}.index"):
                await self._load_index()
            
            ai_logger.logger.info(f"Initialized FAISS vector store with dimension {self.dimension}")
        except Exception as e:
            ai_logger.log_error(e, {"dimension": self.dimension})
            raise VectorDatabaseError(f"Failed to initialize FAISS index: {str(e)}")
    
    async def add_documents(self, documents: List[Document]) -> None:
        """Add documents to the FAISS index"""
        if not self.index:
            await self.initialize()
        
        try:
            embeddings = []
            for doc in documents:
                if doc.embedding is None:
                    raise VectorDatabaseError(f"Document {doc.id} has no embedding")
                
                # Normalize embedding for cosine similarity
                embedding = np.array(doc.embedding, dtype=np.float32)
                embedding = embedding / np.linalg.norm(embedding)
                embeddings.append(embedding)
                
                # Store document with internal ID
                internal_id = self.next_id
                self.documents[internal_id] = doc
                self.id_mapping[doc.id] = internal_id
                self.next_id += 1
            
            # Add to FAISS index
            embeddings_array = np.vstack(embeddings)
            await asyncio.to_thread(self.index.add, embeddings_array)
            
            ai_logger.logger.info(f"Added {len(documents)} documents to vector store")
            
            # Save index if path is specified
            if self.index_path:
                await self._save_index()
                
        except Exception as e:
            ai_logger.log_error(e, {"document_count": len(documents)})
            raise VectorDatabaseError(f"Failed to add documents: {str(e)}")
    
    async def search(self, query_embedding: List[float], k: int = 5) -> List[SearchResult]:
        """Search for similar documents"""
        if not self.index:
            await self.initialize()
        
        try:
            # Normalize query embedding
            query_vec = np.array(query_embedding, dtype=np.float32).reshape(1, -1)
            query_vec = query_vec / np.linalg.norm(query_vec)
            
            # Search in FAISS
            scores, indices = await asyncio.to_thread(
                self.index.search, query_vec, min(k, self.index.ntotal)
            )
            
            # Convert results
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx != -1 and idx in self.documents:  # -1 means no result found
                    results.append(SearchResult(
                        document=self.documents[idx],
                        score=float(score)
                    ))
            
            return results
            
        except Exception as e:
            ai_logger.log_error(e, {"k": k})
            raise VectorDatabaseError(f"Failed to search: {str(e)}")
    
    async def delete_document(self, doc_id: str) -> bool:
        """Delete a document by ID (not supported in basic FAISS)"""
        # Note: FAISS doesn't support deletion easily
        # This would require rebuilding the index
        ai_logger.logger.warning("Document deletion not implemented for FAISS store")
        return False
    
    async def get_document_count(self) -> int:
        """Get the total number of documents"""
        if not self.index:
            return 0
        return self.index.ntotal
    
    async def _save_index(self):
        """Save the FAISS index and metadata to disk"""
        try:
            # Save FAISS index
            await asyncio.to_thread(faiss.write_index, self.index, f"{self.index_path}.index")
            
            # Save metadata
            metadata = {
                "documents": {str(k): {
                    "id": doc.id,
                    "content": doc.content,
                    "embedding": doc.embedding,
                    "metadata": doc.metadata
                } for k, doc in self.documents.items()},
                "id_mapping": self.id_mapping,
                "next_id": self.next_id,
                "dimension": self.dimension
            }
            
            with open(f"{self.index_path}.metadata.json", "w") as f:
                json.dump(metadata, f, indent=2)
                
        except Exception as e:
            ai_logger.log_error(e, {"index_path": self.index_path})
            raise VectorDatabaseError(f"Failed to save index: {str(e)}")
    
    async def _load_index(self):
        """Load the FAISS index and metadata from disk"""
        try:
            # Load FAISS index
            self.index = await asyncio.to_thread(faiss.read_index, f"{self.index_path}.index")
            
            # Load metadata
            if os.path.exists(f"{self.index_path}.metadata.json"):
                with open(f"{self.index_path}.metadata.json", "r") as f:
                    metadata = json.load(f)
                
                # Restore documents
                self.documents = {}
                for k, doc_data in metadata["documents"].items():
                    doc = Document(
                        id=doc_data["id"],
                        content=doc_data["content"],
                        embedding=doc_data["embedding"],
                        metadata=doc_data.get("metadata")
                    )
                    self.documents[int(k)] = doc
                
                self.id_mapping = metadata["id_mapping"]
                self.next_id = metadata["next_id"]
                self.dimension = metadata["dimension"]
            
            ai_logger.logger.info(f"Loaded FAISS index with {self.index.ntotal} documents")
            
        except Exception as e:
            ai_logger.log_error(e, {"index_path": self.index_path})
            raise VectorDatabaseError(f"Failed to load index: {str(e)}")


class InMemoryVectorStore(VectorStore):
    """Simple in-memory vector store for testing"""
    
    def __init__(self):
        self.documents: List[Document] = []
    
    async def add_documents(self, documents: List[Document]) -> None:
        """Add documents to memory"""
        self.documents.extend(documents)
    
    async def search(self, query_embedding: List[float], k: int = 5) -> List[SearchResult]:
        """Search using brute force cosine similarity"""
        try:
            query_vec = np.array(query_embedding)
            query_norm = np.linalg.norm(query_vec)
            
            results = []
            for doc in self.documents:
                if doc.embedding:
                    doc_vec = np.array(doc.embedding)
                    doc_norm = np.linalg.norm(doc_vec)
                    
                    if query_norm > 0 and doc_norm > 0:
                        similarity = np.dot(query_vec, doc_vec) / (query_norm * doc_norm)
                        results.append(SearchResult(document=doc, score=float(similarity)))
            
            # Sort by similarity and return top k
            results.sort(key=lambda x: x.score, reverse=True)
            return results[:k]
            
        except Exception as e:
            ai_logger.log_error(e, {"k": k})
            raise VectorDatabaseError(f"Failed to search: {str(e)}")
    
    async def delete_document(self, doc_id: str) -> bool:
        """Delete a document by ID"""
        initial_count = len(self.documents)
        self.documents = [doc for doc in self.documents if doc.id != doc_id]
        return len(self.documents) < initial_count
    
    async def get_document_count(self) -> int:
        """Get the total number of documents"""
        return len(self.documents)


# Global vector store instance
_vector_store = None

async def get_vector_store(store_type: str = "faiss", **kwargs) -> VectorStore:
    """Get or create the global vector store instance"""
    global _vector_store
    
    if _vector_store is None:
        if store_type == "faiss":
            embedding_model = await get_embedding_model()
            dimension = embedding_model.get_dimension()
            _vector_store = FAISSVectorStore(dimension=dimension, **kwargs)
            await _vector_store.initialize()
        elif store_type == "memory":
            _vector_store = InMemoryVectorStore()
        else:
            raise VectorDatabaseError(f"Unsupported vector store type: {store_type}")
    
    return _vector_store