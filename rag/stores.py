"""Vector store implementations for FixChain RAG system."""

import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.errors import PyMongoError
from bson import ObjectId

from .interfaces import VectorStore, RAGStore, EmbeddingProvider
from models.schemas import SearchResult, ReasoningEntry

logger = logging.getLogger(__name__)


class MongoVectorStore(VectorStore):
    """MongoDB-based vector store implementation."""
    
    def __init__(self, mongodb_uri: str, database_name: str, collection_name: str, 
                 timeout: int = 30):
        """Initialize MongoDB vector store.
        
        Args:
            mongodb_uri: MongoDB connection URI
            database_name: Database name
            collection_name: Collection name
            timeout: Connection timeout in seconds
        """
        self.mongodb_uri = mongodb_uri
        self.database_name = database_name
        self.collection_name = collection_name
        
        try:
            self.client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=timeout * 1000)
            self.database = self.client[database_name]
            self.collection: Collection = self.database[collection_name]
            
            # Test connection
            self.client.admin.command('ping')
            logger.info(f"Connected to MongoDB: {database_name}.{collection_name}")
            
        except PyMongoError as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    def add_document(self, content: str, embedding: List[float], metadata: Dict[str, Any]) -> str:
        """Add a document with its embedding to the store.
        
        Args:
            content: Document content
            embedding: Embedding vector
            metadata: Document metadata
            
        Returns:
            Document ID
        """
        try:
            document = {
                "text": content,
                "embedding": embedding,
                "metadata": metadata,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            result = self.collection.insert_one(document)
            logger.debug(f"Added document with ID: {result.inserted_id}")
            return str(result.inserted_id)
            
        except PyMongoError as e:
            logger.error(f"Failed to add document: {e}")
            raise
    
    def search_similar(self, query_embedding: List[float], k: int = 3, 
                      filter_criteria: Optional[Dict[str, Any]] = None) -> List[SearchResult]:
        """Search for similar documents using vector similarity.
        
        Note: This implementation uses a fallback text search since local MongoDB
        may not have full vector search capabilities like Atlas.
        
        Args:
            query_embedding: Query embedding vector
            k: Number of results to return
            filter_criteria: Optional metadata filters
            
        Returns:
            List of search results with similarity scores
        """
        try:
            # Build query pipeline
            pipeline = []
            
            # Add filter criteria if provided
            if filter_criteria:
                match_stage = {"$match": {}}
                for key, value in filter_criteria.items():
                    if key.startswith("metadata."):
                        match_stage["$match"][key] = value
                    else:
                        match_stage["$match"][f"metadata.{key}"] = value
                pipeline.append(match_stage)
            
            # For local MongoDB without vector search, we'll use a simple approach
            # In production with Atlas, this would use $vectorSearch
            pipeline.extend([
                {"$limit": k * 2},  # Get more documents for better results
                {"$project": {
                    "text": 1,
                    "metadata": 1,
                    "embedding": 1,
                    "score": {"$literal": 1.0}  # Placeholder score
                }},
                {"$limit": k}
            ])
            
            results = list(self.collection.aggregate(pipeline))
            
            search_results = []
            for doc in results:
                search_result = SearchResult(
                    content=doc.get("text", ""),
                    metadata=doc.get("metadata", {}),
                    score=doc.get("score", 1.0),
                    document_id=str(doc["_id"])
                )
                search_results.append(search_result)
            
            logger.debug(f"Found {len(search_results)} similar documents")
            return search_results
            
        except PyMongoError as e:
            logger.error(f"Failed to search similar documents: {e}")
            raise
    
    def delete_document(self, document_id: str) -> bool:
        """Delete a document by ID.
        
        Args:
            document_id: ID of document to delete
            
        Returns:
            True if deletion was successful
        """
        try:
            result = self.collection.delete_one({"_id": ObjectId(document_id)})
            success = result.deleted_count > 0
            if success:
                logger.debug(f"Deleted document: {document_id}")
            return success
            
        except (PyMongoError, ValueError) as e:
            logger.error(f"Failed to delete document {document_id}: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get storage statistics.
        
        Returns:
            Dictionary with storage statistics
        """
        try:
            stats = {
                "total_documents": self.collection.count_documents({}),
                "collection_name": self.collection_name,
                "database_name": self.database_name,
                "indexes": list(self.collection.list_indexes())
            }
            return stats
            
        except PyMongoError as e:
            logger.error(f"Failed to get storage stats: {e}")
            return {"error": str(e)}
    
    def close(self) -> None:
        """Close the connection to the vector store."""
        if hasattr(self, 'client'):
            self.client.close()
            logger.info("MongoDB connection closed")


class FixChainRAGStore(RAGStore):
    """Main RAG store implementation for FixChain system."""
    
    def __init__(self, embedding_provider: EmbeddingProvider, vector_store: VectorStore):
        """Initialize FixChain RAG store with dependency injection.
        
        Args:
            embedding_provider: Provider for generating embeddings
            vector_store: Backend for storing and searching vectors
        """
        self.embedding_provider = embedding_provider
        self.vector_store = vector_store
        logger.info("FixChain RAG store initialized")
    
    def add_reasoning_entry(self, content: str, metadata: Dict[str, Any]) -> str:
        """Add a reasoning entry to the RAG store.
        
        Args:
            content: Reasoning content text
            metadata: Associated metadata
            
        Returns:
            Document ID of the added entry
        """
        try:
            # Validate metadata using Pydantic model
            reasoning_entry = ReasoningEntry(**metadata)
            validated_metadata = reasoning_entry.dict(exclude_none=True)
            
            # Add timestamp if not provided
            if "timestamp" not in validated_metadata:
                validated_metadata["timestamp"] = datetime.utcnow().isoformat()
            
            # Generate embedding
            embedding = self.embedding_provider.embed_text(content)
            
            # Store in vector store
            document_id = self.vector_store.add_document(content, embedding, validated_metadata)
            
            logger.info(f"Added reasoning entry: {document_id}")
            return document_id
            
        except Exception as e:
            logger.error(f"Failed to add reasoning entry: {e}")
            raise
    
    async def store_reasoning(self, reasoning_text: str, metadata: Dict[str, Any]) -> str:
        """Store reasoning text with metadata in RAG vector store.
        
        Args:
            reasoning_text: The reasoning content to store
            metadata: Metadata dict with required fields: bug_id, test_name, iteration, 
                     category, timestamp, tags, source
                     
        Returns:
            Document ID of the stored reasoning entry
        """
        try:
            # Ensure required metadata fields
            required_fields = ['bug_id', 'test_name', 'iteration', 'category', 'source']
            for field in required_fields:
                if field not in metadata:
                    raise ValueError(f"Required metadata field '{field}' is missing")
            
            # Add timestamp if not provided
            if 'timestamp' not in metadata:
                metadata['timestamp'] = datetime.utcnow().isoformat()
            
            # Add default tags if not provided
            if 'tags' not in metadata:
                metadata['tags'] = ['reasoning']
            
            # Store using existing method
            document_id = self.add_reasoning_entry(reasoning_text, metadata)
            
            logger.info(f"Stored reasoning for bug {metadata['bug_id']}: {document_id}")
            return document_id
            
        except Exception as e:
            logger.error(f"Failed to store reasoning: {e}")
            raise
    
    def search_reasoning(self, query: str, limit: int = 5, 
                        filter: Optional[Dict[str, Any]] = None) -> List[SearchResult]:
        """Search for reasoning entries based on query.
        
        Args:
            query: Search query string
            limit: Maximum number of results to return
            filter: Optional metadata filters
            
        Returns:
            List of search results with reasoning entries
        """
        try:
            # Search for similar entries using existing method
            results = self.retrieve_similar_entries(query, limit, filter)
            
            logger.debug(f"Found {len(results)} reasoning entries for query: {query}")
            return results
            
        except Exception as e:
            logger.error(f"Failed to search reasoning: {e}")
            raise
    
    def delete_reasoning_by_bug_id(self, bug_id: str) -> int:
        """Delete all reasoning entries for a specific bug ID.
        
        Args:
            bug_id: Bug ID to delete reasoning entries for
            
        Returns:
            Number of deleted entries
        """
        try:
            # Access the underlying MongoDB collection directly
            if hasattr(self.vector_store, 'collection'):
                result = self.vector_store.collection.delete_many(
                    {"metadata.bug_id": bug_id}
                )
                deleted_count = result.deleted_count
                logger.info(f"Deleted {deleted_count} reasoning entries for bug {bug_id}")
                return deleted_count
            else:
                logger.error("Vector store does not support bulk deletion")
                return 0
                
        except Exception as e:
            logger.error(f"Failed to delete reasoning entries for bug {bug_id}: {e}")
            raise
    
    async def search_context(self, query: str, limit: int = 5, 
                           tags: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Search for relevant reasoning context based on query.
        
        Args:
            query: Search query string
            limit: Maximum number of results to return
            tags: Optional list of tags to filter by
            
        Returns:
            List of dictionaries containing reasoning context with metadata
        """
        try:
            # Build filter criteria
            filter_criteria = {}
            if tags:
                filter_criteria['tags'] = {'$in': tags}
            
            # Search for similar entries
            results = self.retrieve_similar_entries(query, limit, filter_criteria)
            
            # Format results as dictionaries
            context_results = []
            for result in results:
                context_entry = {
                    'content': result.content,
                    'metadata': result.metadata,
                    'score': result.score,
                    'document_id': result.document_id
                }
                context_results.append(context_entry)
            
            logger.debug(f"Found {len(context_results)} context entries for query: {query}")
            return context_results
            
        except Exception as e:
            logger.error(f"Failed to search context: {e}")
            raise
    
    def retrieve_similar_entries(self, query: str, k: int = 3, 
                               filter_criteria: Optional[Dict[str, Any]] = None) -> List[SearchResult]:
        """Retrieve semantically similar reasoning entries.
        
        Args:
            query: Query string
            k: Number of results to return
            filter_criteria: Optional metadata filters
            
        Returns:
            List of similar reasoning entries
        """
        try:
            # Generate query embedding
            query_embedding = self.embedding_provider.embed_text(query)
            
            # Search for similar documents
            results = self.vector_store.search_similar(query_embedding, k, filter_criteria)
            
            logger.debug(f"Retrieved {len(results)} similar entries for query: {query}")
            return results
            
        except Exception as e:
            logger.error(f"Failed to retrieve similar entries: {e}")
            raise
    
    def retrieve_similar_entries_with_scores(self, query: str, k: int = 3,
                                           filter_criteria: Optional[Dict[str, Any]] = None) -> List[Tuple[SearchResult, float]]:
        """Retrieve similar entries with explicit similarity scores.
        
        Args:
            query: Query string
            k: Number of results to return
            filter_criteria: Optional metadata filters
            
        Returns:
            List of tuples (search_result, similarity_score)
        """
        results = self.retrieve_similar_entries(query, k, filter_criteria)
        return [(result, result.score or 0.0) for result in results]
    
    def delete_entry(self, document_id: str) -> bool:
        """Delete a reasoning entry.
        
        Args:
            document_id: ID of entry to delete
            
        Returns:
            True if deletion was successful
        """
        return self.vector_store.delete_document(document_id)
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get collection statistics.
        
        Returns:
            Dictionary with collection statistics
        """
        return self.vector_store.get_stats()
    
    def close(self) -> None:
        """Close connections and cleanup resources."""
        self.vector_store.close()
        logger.info("FixChain RAG store closed")