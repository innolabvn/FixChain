"""Unit tests for FixChainDB MongoDB implementation."""

import pytest
import asyncio
from datetime import datetime
from typing import Dict, Any
from unittest.mock import AsyncMock, MagicMock, patch

from db.mongo.fixchain_db import FixChainDB
from db.mongo.exceptions import DatabaseError, ConnectionError, ValidationError
from models.test_result import (
    TestExecutionResult, TestStatus, TestCategory, TestSeverity,
    TestIssue, TestAttemptResult
)


class TestFixChainDB:
    """Test cases for FixChainDB class."""
    
    @pytest.fixture
    def mock_motor_client(self):
        """Mock motor client for testing."""
        with patch('db.mongo.fixchain_db.AsyncIOMotorClient') as mock_client:
            mock_db = MagicMock()
            mock_client.return_value.__getitem__.return_value = mock_db
            yield mock_client, mock_db
    
    @pytest.fixture
    def mock_settings(self):
        """Mock settings for testing."""
        mock_settings = MagicMock()
        mock_settings.mongodb_uri = 'mongodb://localhost:27017'
        mock_settings.database_name = 'test_fixchain'
        return mock_settings
    
    @pytest.fixture
    def fixchain_db(self, mock_motor_client, mock_settings):
        """Create FixChainDB instance for testing."""
        mock_client, mock_db = mock_motor_client
        db = FixChainDB(settings=mock_settings)
        # Mock the database connection
        db._client = mock_client.return_value
        db._client.close = MagicMock()  # Add close method to mock client
        db._database = mock_db
        return db
    
    @pytest.fixture
    def sample_test_result(self):
        """Sample test execution result for testing."""
        return TestExecutionResult(
            test_name="SyntaxCheck",
            test_category=TestCategory.STATIC,
            description="Test syntax checking",
            attempts=[
                TestAttemptResult(
                    iteration=1,
                    status=TestStatus.FAILED,
                    start_time=datetime.now(),
                    end_time=datetime.now(),
                    result=False,
                    output="Test output",
                    message="Test failed",
                    issues=[
                        TestIssue(
                            file="test.py",
                            line=10,
                            message="Syntax error",
                            severity=TestSeverity.HIGH
                        )
                    ]
                )
            ],
            final_status=TestStatus.FAILED,
            final_result=False
        )
    
    @pytest.mark.asyncio
    async def test_connect_success(self, fixchain_db, mock_motor_client):
        """Test successful database connection."""
        mock_client, mock_db = mock_motor_client
        mock_client.return_value.admin.command = AsyncMock(return_value={"ok": 1})
        
        await fixchain_db.connect()
        
        assert fixchain_db.is_connected
        mock_client.return_value.admin.command.assert_called_once_with('ping')
    
    @pytest.mark.asyncio
    async def test_connect_failure(self, fixchain_db, mock_motor_client):
        """Test database connection failure."""
        mock_client, mock_db = mock_motor_client
        mock_client.return_value.admin.command = AsyncMock(side_effect=Exception("Connection failed"))
        
        with pytest.raises(ConnectionError):
            await fixchain_db.connect()
    
    @pytest.mark.asyncio
    async def test_save_test_result(self, fixchain_db, sample_test_result, mock_motor_client):
        """Test saving test result."""
        mock_client, mock_db = mock_motor_client
        mock_collection = AsyncMock()
        mock_db.__getitem__.return_value = mock_collection
        mock_collection.insert_one = AsyncMock(return_value=MagicMock(inserted_id="result-123"))
        
        result_id = await fixchain_db.save_test_result(sample_test_result)
        
        assert result_id == "result-123"
        mock_collection.insert_one.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_test_result(self, fixchain_db, sample_test_result, mock_motor_client):
        """Test retrieving test result."""
        mock_client, mock_db = mock_motor_client
        mock_collection = AsyncMock()
        mock_db.__getitem__.return_value = mock_collection
        
        # Mock the document data
        mock_doc = sample_test_result.dict()
        mock_doc["_id"] = "result-123"
        mock_collection.find_one = AsyncMock(return_value=mock_doc)
        
        result = await fixchain_db.get_test_result("result-123")
        
        assert result is not None
        assert result.test_name == sample_test_result.test_name
        mock_collection.find_one.assert_called_once_with({"_id": "result-123"})
    
    @pytest.mark.asyncio
    async def test_get_test_result_not_found(self, fixchain_db, mock_motor_client):
        """Test retrieving non-existent test result."""
        mock_client, mock_db = mock_motor_client
        mock_collection = AsyncMock()
        mock_db.__getitem__.return_value = mock_collection
        mock_collection.find_one = AsyncMock(return_value=None)
        
        result = await fixchain_db.get_test_result("nonexistent")
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_log_changelog(self, fixchain_db, mock_motor_client):
        """Test logging changelog."""
        mock_client, mock_db = mock_motor_client
        mock_collection = AsyncMock()
        mock_db.__getitem__.return_value = mock_collection
        mock_collection.insert_one = AsyncMock()
        
        changes = {"status": "fixed", "patch_applied": True}
        timestamp = datetime.utcnow()
        
        await fixchain_db.log_changelog("bug-123", changes, timestamp)
        
        mock_collection.insert_one.assert_called_once()
        call_args = mock_collection.insert_one.call_args[0][0]
        assert call_args["bug_id"] == "bug-123"
        assert call_args["changes"] == changes
        assert call_args["timestamp"] == timestamp
    
    @pytest.mark.asyncio
    async def test_save_fix_result(self, fixchain_db, mock_motor_client):
        """Test saving fix result."""
        mock_client, mock_db = mock_motor_client
        mock_collection = AsyncMock()
        mock_db.__getitem__.return_value = mock_collection
        mock_result = MagicMock()
        mock_result.upserted_id = "result-123"
        mock_collection.replace_one = AsyncMock(return_value=mock_result)
        
        result_id = await fixchain_db.save_fix_result("bug-123", "patch content", "applied")
        
        assert result_id == "result-123"
        mock_collection.replace_one.assert_called_once()
        call_args = mock_collection.replace_one.call_args[0]
        assert call_args[0] == {"bug_id": "bug-123"}
        assert call_args[1]["bug_id"] == "bug-123"
        assert call_args[1]["patch"] == "patch content"
        assert call_args[1]["status"] == "applied"
    
    @pytest.mark.asyncio
    async def test_get_bug_list(self, fixchain_db, mock_motor_client):
        """Test retrieving bug list."""
        mock_client, mock_db = mock_motor_client
        
        # Mock bug document
        mock_bug_doc = {
            "_id": "bug-123",
            "file": "test.py",
            "line": 10,
            "column": 0,
            "message": "Syntax error",
            "severity": "high",
            "rule_id": None,
            "tool": None,
            "error_code": None,
            "suggestion": None,
            "test_id": "test-123"
        }
        
        # Mock find_documents method
        with patch.object(fixchain_db, 'find_documents', new_callable=AsyncMock) as mock_find:
            mock_find.return_value = [mock_bug_doc]
            
            bugs = await fixchain_db.get_bug_list("test-123")
            
            assert len(bugs) == 1
            assert bugs[0].file == "test.py"
            assert bugs[0].message == "Syntax error"
            mock_find.assert_called_once_with(fixchain_db.BUGS_COLLECTION, {"test_id": "test-123"}, limit=None)
    
    @pytest.mark.asyncio
    async def test_close_connection(self, fixchain_db, mock_motor_client):
        """Test closing database connection."""
        mock_client, mock_db = mock_motor_client
        
        # Store reference to mock close method before calling close()
        mock_close = fixchain_db._client.close
        
        await fixchain_db.close()
        
        mock_close.assert_called_once()
        assert not fixchain_db.is_connected


if __name__ == "__main__":
    pytest.main([__file__])