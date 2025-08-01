"""Unit tests for FixChain RAG store functionality."""

import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from typing import List, Dict, Any

from rag.interfaces import EmbeddingProvider, VectorStore
from rag.stores import FixChainRAGStore
from models.schemas import SearchResult


class MockEmbeddingProvider(EmbeddingProvider):
    """Mock embedding provider for testing."""
    
    def embed_text(self, text: str) -> List[float]:
        # Return a simple mock embedding based on text length
        return [float(len(text)) / 100.0] * 1536
    
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        return [self.embed_text(text) for text in texts]
    
    @property
    def dimensions(self) -> int:
        return 1536


class MockVectorStore(VectorStore):
    """Mock vector store for testing."""
    
    def __init__(self):
        self.documents = {}
        self.next_id = 1
    
    def add_document(self, content: str, embedding: List[float], metadata: Dict[str, Any]) -> str:
        doc_id = str(self.next_id)
        self.documents[doc_id] = {
            "content": content,
            "embedding": embedding,
            "metadata": metadata
        }
        self.next_id += 1
        return doc_id
    
    def search_similar(self, query_embedding: List[float], k: int = 3, 
                      filter_criteria: Dict[str, Any] = None) -> List[SearchResult]:
        # Simple mock search - return all documents with mock scores
        results = []
        for doc_id, doc in list(self.documents.items())[:k]:
            result = SearchResult(
                content=doc["content"],
                metadata=doc["metadata"],
                score=0.9,  # Mock similarity score
                document_id=doc_id
            )
            results.append(result)
        return results
    
    def delete_document(self, document_id: str) -> bool:
        if document_id in self.documents:
            del self.documents[document_id]
            return True
        return False
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_documents": len(self.documents),
            "collection_name": "test_collection",
            "database_name": "test_db"
        }
    
    def close(self) -> None:
        pass


class TestFixChainRAGStore(unittest.TestCase):
    """Test cases for FixChainRAGStore."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_embedding_provider = MockEmbeddingProvider()
        self.mock_vector_store = MockVectorStore()
        self.rag_store = FixChainRAGStore(
            embedding_provider=self.mock_embedding_provider,
            vector_store=self.mock_vector_store
        )
    
    def test_add_reasoning_entry(self):
        """Test adding a reasoning entry."""
        content = "Fixing bug_X in method `sendEmail` caused bug_Y before. Best approach is refactoring with null check."
        metadata = {
            "bug_id": "BUG-001",
            "method_name": "sendEmail",
            "fix_type": "null_check_refactor",
            "severity": "medium"
        }
        
        # Add reasoning entry
        doc_id = self.rag_store.add_reasoning_entry(content, metadata)
        
        # Verify the entry was added
        self.assertIsNotNone(doc_id)
        self.assertEqual(doc_id, "1")
        
        # Verify the document exists in the mock store
        self.assertIn(doc_id, self.mock_vector_store.documents)
        stored_doc = self.mock_vector_store.documents[doc_id]
        self.assertEqual(stored_doc["content"], content)
        self.assertEqual(stored_doc["metadata"]["bug_id"], "BUG-001")
        self.assertIn("timestamp", stored_doc["metadata"])
    
    def test_retrieve_similar_entries(self):
        """Test retrieving similar reasoning entries."""
        # Add some test entries
        entries = [
            {
                "content": "Email validation bug fix with regex pattern",
                "metadata": {"bug_id": "BUG-001", "method_name": "validateEmail"}
            },
            {
                "content": "Null pointer exception in sendEmail method",
                "metadata": {"bug_id": "BUG-002", "method_name": "sendEmail"}
            },
            {
                "content": "Database connection timeout handling",
                "metadata": {"bug_id": "BUG-003", "method_name": "connectDB"}
            }
        ]
        
        for entry in entries:
            self.rag_store.add_reasoning_entry(entry["content"], entry["metadata"])
        
        # Search for similar entries
        query = "email method null pointer exception fix"
        results = self.rag_store.retrieve_similar_entries(query, k=2)
        
        # Verify results
        self.assertIsInstance(results, list)
        self.assertLessEqual(len(results), 2)
        
        for result in results:
            self.assertIsInstance(result, SearchResult)
            self.assertIsNotNone(result.content)
            self.assertIsNotNone(result.metadata)
            self.assertIsNotNone(result.score)
            self.assertIsNotNone(result.document_id)
    
    def test_retrieve_similar_entries_with_scores(self):
        """Test retrieving similar entries with explicit scores."""
        # Add a test entry
        content = "Test reasoning content"
        metadata = {"bug_id": "TEST-001"}
        self.rag_store.add_reasoning_entry(content, metadata)
        
        # Retrieve with scores
        query = "test content"
        results_with_scores = self.rag_store.retrieve_similar_entries_with_scores(query, k=1)
        
        # Verify results
        self.assertIsInstance(results_with_scores, list)
        self.assertEqual(len(results_with_scores), 1)
        
        result, score = results_with_scores[0]
        self.assertIsInstance(result, SearchResult)
        self.assertIsInstance(score, float)
        self.assertEqual(result.content, content)
    
    def test_delete_entry(self):
        """Test deleting a reasoning entry."""
        # Add an entry
        content = "Test entry to delete"
        metadata = {"bug_id": "DELETE-001"}
        doc_id = self.rag_store.add_reasoning_entry(content, metadata)
        
        # Verify entry exists
        self.assertIn(doc_id, self.mock_vector_store.documents)
        
        # Delete the entry
        success = self.rag_store.delete_entry(doc_id)
        
        # Verify deletion
        self.assertTrue(success)
        self.assertNotIn(doc_id, self.mock_vector_store.documents)
    
    def test_get_collection_stats(self):
        """Test getting collection statistics."""
        # Add some entries
        for i in range(3):
            content = f"Test entry {i}"
            metadata = {"bug_id": f"TEST-{i:03d}"}
            self.rag_store.add_reasoning_entry(content, metadata)
        
        # Get stats
        stats = self.rag_store.get_collection_stats()
        
        # Verify stats
        self.assertIsInstance(stats, dict)
        self.assertEqual(stats["total_documents"], 3)
        self.assertIn("collection_name", stats)
        self.assertIn("database_name", stats)
    
    def test_invalid_metadata_handling(self):
        """Test handling of invalid metadata."""
        content = "Test content with invalid metadata"
        metadata = {
            "bug_id": "INVALID-001",
            "invalid_field": "this should be ignored",
            "line_number": "not_a_number"  # Invalid type
        }
        
        # This should not raise an exception
        doc_id = self.rag_store.add_reasoning_entry(content, metadata)
        self.assertIsNotNone(doc_id)
    
    def test_close(self):
        """Test closing the RAG store."""
        # This should not raise an exception
        self.rag_store.close()


class TestRAGStoreIntegration(unittest.TestCase):
    """Integration tests for RAG store components."""
    
    @patch('rag.embeddings.OpenAI')
    def test_openai_embedding_provider_integration(self, mock_openai):
        """Test integration with OpenAI embedding provider."""
        from rag.embeddings import OpenAIEmbeddingProvider
        
        # Mock OpenAI client response
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.data = [MagicMock(embedding=[0.1] * 1536)]
        mock_client.embeddings.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        # Create provider
        provider = OpenAIEmbeddingProvider(api_key="test-key")
        
        # Test embedding generation
        embedding = provider.embed_text("test text")
        self.assertEqual(len(embedding), 1536)
        self.assertEqual(embedding[0], 0.1)
    
    def test_end_to_end_workflow(self):
        """Test complete end-to-end workflow."""
        # Use mock components for end-to-end test
        embedding_provider = MockEmbeddingProvider()
        vector_store = MockVectorStore()
        rag_store = FixChainRAGStore(embedding_provider, vector_store)
        
        # Add multiple entries
        entries = [
            {
                "content": "Bug fix for email validation using regex",
                "metadata": {"bug_id": "E2E-001", "method_name": "validateEmail"}
            },
            {
                "content": "Null pointer exception fix in user authentication",
                "metadata": {"bug_id": "E2E-002", "method_name": "authenticateUser"}
            }
        ]
        
        doc_ids = []
        for entry in entries:
            doc_id = rag_store.add_reasoning_entry(entry["content"], entry["metadata"])
            doc_ids.append(doc_id)
        
        # Search for similar entries
        results = rag_store.retrieve_similar_entries("email validation bug", k=1)
        self.assertEqual(len(results), 1)
        
        # Get statistics
        stats = rag_store.get_collection_stats()
        self.assertEqual(stats["total_documents"], 2)
        
        # Delete an entry
        success = rag_store.delete_entry(doc_ids[0])
        self.assertTrue(success)
        
        # Verify deletion
        stats = rag_store.get_collection_stats()
        self.assertEqual(stats["total_documents"], 1)
        
        # Close the store
        rag_store.close()


if __name__ == '__main__':
    unittest.main()