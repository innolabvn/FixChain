"""Unit tests for FixChainRAGStore with new methods."""

import pytest
import asyncio
from datetime import datetime
from typing import Dict, Any, List
from unittest.mock import MagicMock, patch, AsyncMock

from rag.stores import FixChainRAGStore
from models.schemas import SearchResult


class TestFixChainRAGStore:
    """Test cases for FixChainRAGStore class."""
    
    @pytest.fixture
    def mock_embedding_provider(self):
        """Mock embedding provider for testing."""
        mock_provider = MagicMock()
        mock_provider.embed_text.return_value = [0.1, 0.2, 0.3]  # Mock embedding
        return mock_provider
    
    @pytest.fixture
    def mock_vector_store(self):
        """Mock vector store for testing."""
        mock_store = MagicMock()
        mock_store.add_document.return_value = "doc-123"
        mock_store.search_similar.return_value = [
            SearchResult(
                content="Test reasoning content",
                metadata={
                    "bug_id": "bug-123",
                    "test_name": "SyntaxCheck",
                    "iteration": 1,
                    "category": "static",
                    "tags": ["reasoning", "critical"],
                    "source": "bandit"
                },
                score=0.95,
                document_id="doc-123"
            )
        ]
        return mock_store
    
    @pytest.fixture
    def rag_store(self, mock_embedding_provider, mock_vector_store):
        """Create FixChainRAGStore instance for testing."""
        return FixChainRAGStore(mock_embedding_provider, mock_vector_store)
    
    @pytest.fixture
    def sample_metadata(self):
        """Sample metadata for testing."""
        return {
            "bug_id": "bug-xyz123",
            "test_name": "SecurityCheck",
            "iteration": 2,
            "category": "static",
            "tags": ["reasoning", "critical"],
            "source": "bandit"
        }
    
    @pytest.mark.asyncio
    async def test_store_reasoning_success(self, rag_store, sample_metadata, mock_vector_store):
        """Test successful reasoning storage."""
        reasoning_text = "The vulnerability lies in unsafe string concatenation..."
        
        with patch.object(rag_store, 'add_reasoning_entry', return_value="doc-123") as mock_add:
            result = await rag_store.store_reasoning(reasoning_text, sample_metadata)
            
            assert result == "doc-123"
            mock_add.assert_called_once()
            call_args = mock_add.call_args[0]
            assert call_args[0] == reasoning_text
            assert call_args[1]['bug_id'] == "bug-xyz123"
            assert 'timestamp' in call_args[1]
    
    @pytest.mark.asyncio
    async def test_store_reasoning_missing_required_field(self, rag_store):
        """Test storing reasoning with missing required metadata field."""
        reasoning_text = "Test reasoning"
        incomplete_metadata = {
            "bug_id": "bug-123",
            "test_name": "SyntaxCheck"
            # Missing: iteration, category, source
        }
        
        with pytest.raises(ValueError, match="Required metadata field 'iteration' is missing"):
            await rag_store.store_reasoning(reasoning_text, incomplete_metadata)
    
    @pytest.mark.asyncio
    async def test_store_reasoning_auto_timestamp(self, rag_store, sample_metadata):
        """Test automatic timestamp addition."""
        reasoning_text = "Test reasoning"
        metadata_without_timestamp = sample_metadata.copy()
        metadata_without_timestamp.pop('timestamp', None)
        
        with patch.object(rag_store, 'add_reasoning_entry', return_value="doc-123") as mock_add:
            await rag_store.store_reasoning(reasoning_text, metadata_without_timestamp)
            
            call_args = mock_add.call_args[0][1]
            assert 'timestamp' in call_args
            assert isinstance(call_args['timestamp'], str)
    
    @pytest.mark.asyncio
    async def test_store_reasoning_auto_tags(self, rag_store, sample_metadata):
        """Test automatic tags addition."""
        reasoning_text = "Test reasoning"
        metadata_without_tags = sample_metadata.copy()
        metadata_without_tags.pop('tags', None)
        
        with patch.object(rag_store, 'add_reasoning_entry', return_value="doc-123") as mock_add:
            await rag_store.store_reasoning(reasoning_text, metadata_without_tags)
            
            call_args = mock_add.call_args[0][1]
            assert 'tags' in call_args
            assert call_args['tags'] == ['reasoning']
    
    @pytest.mark.asyncio
    async def test_search_context_success(self, rag_store, mock_vector_store):
        """Test successful context search."""
        query = "syntax error vulnerability"
        
        with patch.object(rag_store, 'retrieve_similar_entries', return_value=mock_vector_store.search_similar.return_value) as mock_retrieve:
            results = await rag_store.search_context(query, limit=3)
            
            assert len(results) == 1
            assert results[0]['content'] == "Test reasoning content"
            assert results[0]['metadata']['bug_id'] == "bug-123"
            assert results[0]['score'] == 0.95
            assert results[0]['document_id'] == "doc-123"
            
            mock_retrieve.assert_called_once_with(query, 3, {})
    
    @pytest.mark.asyncio
    async def test_search_context_with_tags(self, rag_store):
        """Test context search with tag filtering."""
        query = "security issue"
        tags = ["critical", "security"]
        
        with patch.object(rag_store, 'retrieve_similar_entries', return_value=[]) as mock_retrieve:
            await rag_store.search_context(query, limit=5, tags=tags)
            
            expected_filter = {'tags': {'$in': tags}}
            mock_retrieve.assert_called_once_with(query, 5, expected_filter)
    
    @pytest.mark.asyncio
    async def test_search_context_empty_results(self, rag_store):
        """Test context search with no results."""
        query = "nonexistent issue"
        
        with patch.object(rag_store, 'retrieve_similar_entries', return_value=[]):
            results = await rag_store.search_context(query)
            
            assert results == []
    
    @pytest.mark.asyncio
    async def test_search_context_error_handling(self, rag_store):
        """Test error handling in context search."""
        query = "test query"
        
        with patch.object(rag_store, 'retrieve_similar_entries', side_effect=Exception("Search failed")):
            with pytest.raises(Exception, match="Search failed"):
                await rag_store.search_context(query)
    
    def test_add_reasoning_entry_validation(self, rag_store, mock_embedding_provider, mock_vector_store):
        """Test reasoning entry validation."""
        content = "Test reasoning content"
        metadata = {
            "bug_id": "bug-123",
            "test_name": "SyntaxCheck",
            "iteration": 1,
            "category": "static",
            "source": "pylint"
        }
        
        result = rag_store.add_reasoning_entry(content, metadata)
        
        assert result == "doc-123"
        mock_embedding_provider.embed_text.assert_called_once_with(content)
        mock_vector_store.add_document.assert_called_once()
        
        # Verify the call arguments to add_document
        call_args = mock_vector_store.add_document.call_args
        assert call_args[0][0] == content  # content
        assert call_args[0][1] == [0.1, 0.2, 0.3]  # embedding
        assert call_args[0][2]['bug_id'] == "bug-123"  # metadata
    
    def test_retrieve_similar_entries(self, rag_store, mock_embedding_provider, mock_vector_store):
        """Test retrieving similar entries."""
        query = "test query"
        k = 3
        filter_criteria = {"category": "static"}
        
        results = rag_store.retrieve_similar_entries(query, k, filter_criteria)
        
        mock_embedding_provider.embed_text.assert_called_once_with(query)
        mock_vector_store.search_similar.assert_called_once_with([0.1, 0.2, 0.3], k, filter_criteria)
        assert len(results) == 1
        assert results[0].content == "Test reasoning content"
    
    def test_search_reasoning_success(self, rag_store, mock_vector_store):
        """Test successful reasoning search."""
        query = "SQL injection vulnerability"
        limit = 5
        filter_criteria = {"category": "security"}
        
        with patch.object(rag_store, 'retrieve_similar_entries', return_value=mock_vector_store.search_similar.return_value) as mock_retrieve:
            results = rag_store.search_reasoning(query, limit, filter_criteria)
            
            assert len(results) == 1
            assert results[0].content == "Test reasoning content"
            assert results[0].metadata['bug_id'] == "bug-123"
            mock_retrieve.assert_called_once_with(query, limit, filter_criteria)
    
    def test_search_reasoning_no_filter(self, rag_store, mock_vector_store):
        """Test reasoning search without filter."""
        query = "test query"
        
        with patch.object(rag_store, 'retrieve_similar_entries', return_value=[]) as mock_retrieve:
            results = rag_store.search_reasoning(query)
            
            assert results == []
            mock_retrieve.assert_called_once_with(query, 5, None)
    
    def test_delete_reasoning_by_bug_id_success(self, rag_store, mock_vector_store):
        """Test successful deletion of reasoning entries by bug ID."""
        bug_id = "bug-123"
        
        # Mock the collection with delete_many method
        mock_collection = MagicMock()
        mock_result = MagicMock()
        mock_result.deleted_count = 3
        mock_collection.delete_many.return_value = mock_result
        mock_vector_store.collection = mock_collection
        
        deleted_count = rag_store.delete_reasoning_by_bug_id(bug_id)
        
        assert deleted_count == 3
        mock_collection.delete_many.assert_called_once_with({"metadata.bug_id": bug_id})
    
    def test_delete_reasoning_by_bug_id_no_collection(self, rag_store, mock_vector_store):
        """Test deletion when vector store doesn't support bulk deletion."""
        bug_id = "bug-123"
        
        # Remove collection attribute to simulate unsupported store
        if hasattr(mock_vector_store, 'collection'):
            delattr(mock_vector_store, 'collection')
        
        deleted_count = rag_store.delete_reasoning_by_bug_id(bug_id)
        
        assert deleted_count == 0
    
    def test_delete_reasoning_by_bug_id_error(self, rag_store, mock_vector_store):
        """Test error handling in delete reasoning by bug ID."""
        bug_id = "bug-123"
        
        # Mock the collection to raise an exception
        mock_collection = MagicMock()
        mock_collection.delete_many.side_effect = Exception("Database error")
        mock_vector_store.collection = mock_collection
        
        with pytest.raises(Exception, match="Database error"):
            rag_store.delete_reasoning_by_bug_id(bug_id)
    
    def test_retrieve_similar_entries_with_scores(self, rag_store, mock_vector_store):
        """Test retrieving similar entries with scores."""
        query = "test query"
        
        with patch.object(rag_store, 'retrieve_similar_entries', return_value=mock_vector_store.search_similar.return_value):
            results = rag_store.retrieve_similar_entries_with_scores(query)
            
            assert len(results) == 1
            result, score = results[0]
            assert isinstance(result, SearchResult)
            assert score == 0.95
    
    def test_delete_entry(self, rag_store, mock_vector_store):
        """Test deleting an entry."""
        document_id = "doc-123"
        mock_vector_store.delete_document.return_value = True
        
        result = rag_store.delete_entry(document_id)
        
        assert result is True
        mock_vector_store.delete_document.assert_called_once_with(document_id)
    
    def test_get_collection_stats(self, rag_store, mock_vector_store):
        """Test getting collection statistics."""
        mock_stats = {"total_documents": 100, "collection_name": "test_collection"}
        mock_vector_store.get_stats.return_value = mock_stats
        
        stats = rag_store.get_collection_stats()
        
        assert stats == mock_stats
        mock_vector_store.get_stats.assert_called_once()
    
    def test_close(self, rag_store, mock_vector_store):
        """Test closing the RAG store."""
        rag_store.close()
        
        mock_vector_store.close.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__])