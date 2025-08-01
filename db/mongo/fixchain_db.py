"""MongoDB implementation of FixChain database operations.

This module provides the concrete implementation of database
interfaces using MongoDB with motor async driver.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection
from pymongo.errors import DuplicateKeyError as PyMongoDuplicateKeyError, PyMongoError

from ..interfaces.document_store import DocumentStore
from ..interfaces.bug_store import BugStore
from .exceptions import (
    DatabaseError,
    ConnectionError,
    ValidationError,
    DocumentNotFoundError,
    DuplicateKeyError,
    QueryError
)
from models.test_result import TestExecutionResult, TestIssue
from config.settings import Settings


class FixChainDB(DocumentStore, BugStore):
    """MongoDB implementation of FixChain database operations.
    
    This class implements both DocumentStore and BugStore interfaces
    to provide comprehensive database functionality for the FixChain system.
    """
    
    def __init__(self, settings: Settings):
        """Initialize FixChain database connection.
        
        Args:
            settings: Application settings containing database configuration
        """
        self.settings = settings
        self.logger = logging.getLogger(__name__)
        self._client: Optional[AsyncIOMotorClient] = None
        self._database: Optional[AsyncIOMotorDatabase] = None
        
        # Collection names
        self.TEST_RESULTS_COLLECTION = "test_results"
        self.BUGS_COLLECTION = "bugs"
        self.CHANGELOGS_COLLECTION = "changelogs"
        self.FIX_RESULTS_COLLECTION = "fix_results"
    
    async def connect(self) -> None:
        """Establish connection to MongoDB.
        
        Raises:
            ConnectionError: If connection fails
        """
        try:
            self._client = AsyncIOMotorClient(self.settings.mongodb_uri)
            self._database = self._client[self.settings.database_name]
            
            # Test connection
            await self._client.admin.command('ping')
            
            # Create indexes
            await self._create_indexes()
            
            self.logger.info(f"Connected to MongoDB: {self.settings.database_name}")
            
        except Exception as e:
            self.logger.error(f"Failed to connect to MongoDB: {str(e)}")
            raise ConnectionError(f"Failed to connect to MongoDB: {str(e)}", {"uri": self.settings.mongodb_uri})
    
    async def _create_indexes(self) -> None:
        """Create necessary indexes for optimal performance."""
        try:
            # Test results indexes
            test_results = self._database[self.TEST_RESULTS_COLLECTION]
            await test_results.create_index("test_name")
            await test_results.create_index("timestamp")
            await test_results.create_index("status")
            await test_results.create_index("bug_ids")
            
            # Bugs indexes
            bugs = self._database[self.BUGS_COLLECTION]
            await bugs.create_index("bug_id", unique=True)
            await bugs.create_index("severity")
            await bugs.create_index("status")
            await bugs.create_index("test_id")
            
            # Changelogs indexes
            changelogs = self._database[self.CHANGELOGS_COLLECTION]
            await changelogs.create_index("bug_id")
            await changelogs.create_index("timestamp")
            
            # Fix results indexes
            fix_results = self._database[self.FIX_RESULTS_COLLECTION]
            await fix_results.create_index("bug_id", unique=True)
            await fix_results.create_index("status")
            await fix_results.create_index("timestamp")
            
            self.logger.info("Database indexes created successfully")
            
        except Exception as e:
            self.logger.warning(f"Failed to create some indexes: {str(e)}")
    
    def _get_collection(self, collection_name: str) -> AsyncIOMotorCollection:
        """Get a collection from the database.
        
        Args:
            collection_name: Name of the collection
            
        Returns:
            MongoDB collection object
            
        Raises:
            ConnectionError: If not connected to database
        """
        if not self._database:
            raise ConnectionError("Not connected to database")
        return self._database[collection_name]
    
    def _serialize_for_mongo(self, data: Any) -> Any:
        """Serialize data for MongoDB storage.
        
        Args:
            data: Data to serialize
            
        Returns:
            Serialized data
        """
        if hasattr(data, 'model_dump'):
            # Pydantic model
            return data.model_dump()
        elif isinstance(data, dict):
            return {k: self._serialize_for_mongo(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._serialize_for_mongo(item) for item in data]
        elif isinstance(data, datetime):
            return data
        else:
            return data
    
    # DocumentStore implementation
    
    async def save_document(self, collection: str, document: Dict[str, Any]) -> str:
        """Save a document to the specified collection."""
        try:
            coll = self._get_collection(collection)
            serialized_doc = self._serialize_for_mongo(document)
            
            # Add timestamp if not present
            if 'created_at' not in serialized_doc:
                serialized_doc['created_at'] = datetime.utcnow()
            
            result = await coll.insert_one(serialized_doc)
            doc_id = str(result.inserted_id)
            
            self.logger.debug(f"Saved document to {collection}: {doc_id}")
            return doc_id
            
        except PyMongoDuplicateKeyError as e:
            raise DuplicateKeyError("unknown", "unknown", collection) from e
        except PyMongoError as e:
            raise DatabaseError(f"Failed to save document to {collection}", {"error": str(e)}) from e
    
    async def get_document(self, collection: str, doc_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a document by ID."""
        try:
            coll = self._get_collection(collection)
            
            # Try ObjectId first, then string
            try:
                object_id = ObjectId(doc_id)
                document = await coll.find_one({"_id": object_id})
            except:
                document = await coll.find_one({"_id": doc_id})
            
            if document:
                # Convert ObjectId to string for JSON serialization
                document["_id"] = str(document["_id"])
                return document
            
            return None
            
        except PyMongoError as e:
            raise DatabaseError(f"Failed to get document from {collection}", {"doc_id": doc_id, "error": str(e)}) from e
    
    async def update_document(self, collection: str, doc_id: str, updates: Dict[str, Any]) -> bool:
        """Update a document by ID."""
        try:
            coll = self._get_collection(collection)
            serialized_updates = self._serialize_for_mongo(updates)
            
            # Add update timestamp
            serialized_updates['updated_at'] = datetime.utcnow()
            
            # Try ObjectId first, then string
            try:
                object_id = ObjectId(doc_id)
                result = await coll.update_one({"_id": object_id}, {"$set": serialized_updates})
            except:
                result = await coll.update_one({"_id": doc_id}, {"$set": serialized_updates})
            
            return result.modified_count > 0
            
        except PyMongoError as e:
            raise DatabaseError(f"Failed to update document in {collection}", {"doc_id": doc_id, "error": str(e)}) from e
    
    async def delete_document(self, collection: str, doc_id: str) -> bool:
        """Delete a document by ID."""
        try:
            coll = self._get_collection(collection)
            
            # Try ObjectId first, then string
            try:
                object_id = ObjectId(doc_id)
                result = await coll.delete_one({"_id": object_id})
            except:
                result = await coll.delete_one({"_id": doc_id})
            
            return result.deleted_count > 0
            
        except PyMongoError as e:
            raise DatabaseError(f"Failed to delete document from {collection}", {"doc_id": doc_id, "error": str(e)}) from e
    
    async def find_documents(
        self, 
        collection: str, 
        query: Dict[str, Any], 
        limit: Optional[int] = None,
        sort: Optional[List[tuple]] = None
    ) -> List[Dict[str, Any]]:
        """Find documents matching a query."""
        try:
            coll = self._get_collection(collection)
            cursor = coll.find(query)
            
            if sort:
                cursor = cursor.sort(sort)
            
            if limit:
                cursor = cursor.limit(limit)
            
            documents = await cursor.to_list(length=limit)
            
            # Convert ObjectIds to strings
            for doc in documents:
                if "_id" in doc:
                    doc["_id"] = str(doc["_id"])
            
            return documents
            
        except PyMongoError as e:
            raise QueryError(query, collection, e) from e
    
    async def count_documents(self, collection: str, query: Dict[str, Any]) -> int:
        """Count documents matching a query."""
        try:
            coll = self._get_collection(collection)
            return await coll.count_documents(query)
            
        except PyMongoError as e:
            raise QueryError(query, collection, e) from e
    
    async def create_index(self, collection: str, index_spec: Dict[str, Any]) -> str:
        """Create an index on the collection."""
        try:
            coll = self._get_collection(collection)
            return await coll.create_index(list(index_spec.items()))
            
        except PyMongoError as e:
            raise DatabaseError(f"Failed to create index on {collection}", {"index_spec": index_spec, "error": str(e)}) from e
    
    async def get_collection_stats(self, collection: str) -> Dict[str, Any]:
        """Get statistics for a collection."""
        try:
            stats = await self._database.command("collStats", collection)
            return {
                "count": stats.get("count", 0),
                "size": stats.get("size", 0),
                "avgObjSize": stats.get("avgObjSize", 0),
                "storageSize": stats.get("storageSize", 0),
                "indexes": stats.get("nindexes", 0)
            }
            
        except PyMongoError as e:
            raise DatabaseError(f"Failed to get stats for {collection}", {"error": str(e)}) from e
    
    # BugStore implementation
    
    async def save_test_result(self, result: TestExecutionResult) -> str:
        """Save a test execution result."""
        try:
            document = self._serialize_for_mongo(result)
            return await self.save_document(self.TEST_RESULTS_COLLECTION, document)
            
        except Exception as e:
            raise DatabaseError(f"Failed to save test result", {"test_name": result.test_name, "error": str(e)}) from e
    
    async def get_test_result(self, test_id: str) -> Optional[TestExecutionResult]:
        """Retrieve a test result by ID."""
        try:
            document = await self.get_document(self.TEST_RESULTS_COLLECTION, test_id)
            if document:
                # Remove MongoDB-specific fields
                document.pop("_id", None)
                document.pop("created_at", None)
                document.pop("updated_at", None)
                return TestExecutionResult(**document)
            return None
            
        except Exception as e:
            raise DatabaseError(f"Failed to get test result", {"test_id": test_id, "error": str(e)}) from e
    
    async def get_test_results_by_bug(self, bug_id: str) -> List[TestExecutionResult]:
        """Get all test results related to a specific bug."""
        try:
            query = {"bug_ids": bug_id}
            documents = await self.find_documents(self.TEST_RESULTS_COLLECTION, query)
            
            results = []
            for doc in documents:
                # Remove MongoDB-specific fields
                doc.pop("_id", None)
                doc.pop("created_at", None)
                doc.pop("updated_at", None)
                results.append(TestExecutionResult(**doc))
            
            return results
            
        except Exception as e:
            raise DatabaseError(f"Failed to get test results for bug", {"bug_id": bug_id, "error": str(e)}) from e
    
    async def log_changelog(
        self, 
        bug_id: str, 
        changes: Dict[str, Any], 
        timestamp: Optional[datetime] = None
    ) -> str:
        """Log changes made to fix a bug."""
        try:
            changelog_entry = {
                "bug_id": bug_id,
                "changes": changes,
                "timestamp": timestamp or datetime.utcnow()
            }
            
            return await self.save_document(self.CHANGELOGS_COLLECTION, changelog_entry)
            
        except Exception as e:
            raise DatabaseError(f"Failed to log changelog", {"bug_id": bug_id, "error": str(e)}) from e
    
    async def get_changelog(self, bug_id: str) -> List[Dict[str, Any]]:
        """Get changelog entries for a bug."""
        try:
            query = {"bug_id": bug_id}
            sort = [("timestamp", -1)]  # Most recent first
            return await self.find_documents(self.CHANGELOGS_COLLECTION, query, sort=sort)
            
        except Exception as e:
            raise DatabaseError(f"Failed to get changelog", {"bug_id": bug_id, "error": str(e)}) from e
    
    async def save_fix_result(
        self, 
        bug_id: str, 
        patch: str, 
        status: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Save the result of applying a fix."""
        try:
            fix_result = {
                "bug_id": bug_id,
                "patch": patch,
                "status": status,
                "metadata": metadata or {},
                "timestamp": datetime.utcnow()
            }
            
            # Use upsert to replace existing fix result for the same bug
            coll = self._get_collection(self.FIX_RESULTS_COLLECTION)
            result = await coll.replace_one(
                {"bug_id": bug_id},
                fix_result,
                upsert=True
            )
            
            if result.upserted_id:
                return str(result.upserted_id)
            else:
                # Find the existing document
                existing = await coll.find_one({"bug_id": bug_id})
                return str(existing["_id"]) if existing else ""
            
        except Exception as e:
            raise DatabaseError(f"Failed to save fix result", {"bug_id": bug_id, "error": str(e)}) from e
    
    async def get_fix_result(self, bug_id: str) -> Optional[Dict[str, Any]]:
        """Get the latest fix result for a bug."""
        try:
            query = {"bug_id": bug_id}
            documents = await self.find_documents(self.FIX_RESULTS_COLLECTION, query, limit=1)
            return documents[0] if documents else None
            
        except Exception as e:
            raise DatabaseError(f"Failed to get fix result", {"bug_id": bug_id, "error": str(e)}) from e
    
    async def get_bug_list(
        self, 
        test_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[TestIssue]:
        """Get list of bugs/issues."""
        try:
            query = {}
            if test_id:
                query["test_id"] = test_id
            if status:
                query["status"] = status
            
            documents = await self.find_documents(self.BUGS_COLLECTION, query, limit=limit)
            
            bugs = []
            for doc in documents:
                # Remove MongoDB-specific fields
                doc.pop("_id", None)
                doc.pop("created_at", None)
                doc.pop("updated_at", None)
                bugs.append(TestIssue(**doc))
            
            return bugs
            
        except Exception as e:
            raise DatabaseError(f"Failed to get bug list", {"test_id": test_id, "status": status, "error": str(e)}) from e
    
    async def get_bug_by_id(self, bug_id: str) -> Optional[TestIssue]:
        """Get a specific bug by ID."""
        try:
            query = {"bug_id": bug_id}
            documents = await self.find_documents(self.BUGS_COLLECTION, query, limit=1)
            
            if documents:
                doc = documents[0]
                # Remove MongoDB-specific fields
                doc.pop("_id", None)
                doc.pop("created_at", None)
                doc.pop("updated_at", None)
                return TestIssue(**doc)
            
            return None
            
        except Exception as e:
            raise DatabaseError(f"Failed to get bug by ID", {"bug_id": bug_id, "error": str(e)}) from e
    
    async def update_bug_status(self, bug_id: str, status: str) -> bool:
        """Update the status of a bug."""
        try:
            query = {"bug_id": bug_id}
            documents = await self.find_documents(self.BUGS_COLLECTION, query, limit=1)
            
            if documents:
                doc_id = documents[0]["_id"]
                return await self.update_document(self.BUGS_COLLECTION, doc_id, {"status": status})
            
            return False
            
        except Exception as e:
            raise DatabaseError(f"Failed to update bug status", {"bug_id": bug_id, "status": status, "error": str(e)}) from e
    
    async def get_bug_statistics(self) -> Dict[str, Any]:
        """Get statistics about bugs in the system."""
        try:
            # Get total count
            total_bugs = await self.count_documents(self.BUGS_COLLECTION, {})
            
            # Get count by severity
            severity_stats = {}
            for severity in ["low", "medium", "high", "critical"]:
                count = await self.count_documents(self.BUGS_COLLECTION, {"severity": severity})
                severity_stats[severity] = count
            
            # Get count by status
            status_stats = {}
            for status in ["open", "in_progress", "fixed", "closed"]:
                count = await self.count_documents(self.BUGS_COLLECTION, {"status": status})
                status_stats[status] = count
            
            return {
                "total_bugs": total_bugs,
                "by_severity": severity_stats,
                "by_status": status_stats,
                "last_updated": datetime.utcnow()
            }
            
        except Exception as e:
            raise DatabaseError(f"Failed to get bug statistics", {"error": str(e)}) from e
    
    @property
    def is_connected(self) -> bool:
        """Check if database is connected."""
        return self._client is not None and self._database is not None
    
    async def close(self) -> None:
        """Close the database connection."""
        if self._client:
            self._client.close()
            self._client = None
            self._database = None
            self.logger.info("Database connection closed")