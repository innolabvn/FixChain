"""Example usage of FixChain DB and RAG components."""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any

# FixChain imports
from db import FixChainDB, DatabaseError
from rag.stores import FixChainRAGStore, MongoVectorStore
from rag.embedding import OpenAIEmbeddingProvider
from models.test_result import (
    TestExecutionResult, TestStatus, TestCategory, TestSeverity,
    TestIssue, TestAttemptResult
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FixChainDBRAGDemo:
    """Demonstration of FixChain DB and RAG integration."""
    
    def __init__(self):
        """Initialize demo with DB and RAG components."""
        # MongoDB connection settings
        self.mongo_uri = "mongodb://localhost:27017"
        self.db_name = "fixchain_demo"
        
        # Initialize components
        self.fixchain_db = None
        self.rag_store = None
    
    async def setup(self):
        """Setup database and RAG store connections."""
        try:
            # Initialize FixChain DB
            self.fixchain_db = FixChainDB(
                connection_string=self.mongo_uri,
                database_name=self.db_name
            )
            await self.fixchain_db.connect()
            logger.info("FixChain DB connected successfully")
            
            # Initialize RAG Store
            embedding_provider = OpenAIEmbeddingProvider(
                api_key="your-openai-api-key",  # Replace with actual key
                model="text-embedding-ada-002"
            )
            
            vector_store = MongoVectorStore(
                connection_string=self.mongo_uri,
                database_name=f"{self.db_name}_rag",
                collection_name="reasoning_vectors"
            )
            
            self.rag_store = FixChainRAGStore(embedding_provider, vector_store)
            logger.info("RAG Store initialized successfully")
            
        except Exception as e:
            logger.error(f"Setup failed: {e}")
            raise
    
    async def demo_test_result_storage(self):
        """Demonstrate storing and retrieving test results."""
        logger.info("=== Demo: Test Result Storage ===")
        
        # Create sample test result
        test_result = TestExecutionResult(
            test_id="demo-test-001",
            test_name="SecurityCheck",
            status=TestStatus.FAILED,
            category=TestCategory.STATIC,
            start_time=datetime.utcnow(),
            end_time=datetime.utcnow(),
            total_duration=2.5,
            attempts=[
                TestAttemptResult(
                    attempt_number=1,
                    status=TestStatus.FAILED,
                    start_time=datetime.utcnow(),
                    end_time=datetime.utcnow(),
                    duration=2.5,
                    issues=[
                        TestIssue(
                            issue_id="security-001",
                            description="SQL injection vulnerability detected",
                            severity=TestSeverity.CRITICAL,
                            category=TestCategory.STATIC,
                            file_path="app/models/user.py",
                            line_number=45,
                            details={
                                "rule": "B608",
                                "confidence": "HIGH",
                                "cwe": "CWE-89"
                            }
                        )
                    ]
                )
            ]
        )
        
        # Save test result
        result_id = await self.fixchain_db.save_test_result(test_result)
        logger.info(f"Saved test result with ID: {result_id}")
        
        # Retrieve test result
        retrieved_result = await self.fixchain_db.get_test_result(result_id)
        if retrieved_result:
            logger.info(f"Retrieved test result: {retrieved_result.test_name} - {retrieved_result.status}")
        
        # Get bug list from test
        bugs = await self.fixchain_db.get_bug_list("demo-test-001")
        logger.info(f"Found {len(bugs)} bugs in test")
        
        return result_id, test_result
    
    async def demo_reasoning_storage(self, bug_id: str):
        """Demonstrate storing reasoning in RAG."""
        logger.info("=== Demo: Reasoning Storage ===")
        
        # Sample reasoning content
        reasoning_text = """
        The SQL injection vulnerability in user.py line 45 occurs because user input 
        is directly concatenated into the SQL query without proper sanitization or 
        parameterization. This allows attackers to inject malicious SQL code.
        
        Recommended fix:
        1. Use parameterized queries or prepared statements
        2. Implement input validation and sanitization
        3. Apply principle of least privilege for database access
        
        Example fix:
        cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        """
        
        # Metadata for reasoning
        metadata = {
            "bug_id": bug_id,
            "test_name": "SecurityCheck",
            "iteration": 1,
            "category": "static",
            "tags": ["reasoning", "critical", "sql-injection"],
            "source": "bandit",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Store reasoning
        doc_id = await self.rag_store.store_reasoning(reasoning_text, metadata)
        logger.info(f"Stored reasoning with document ID: {doc_id}")
        
        return doc_id
    
    async def demo_context_search(self):
        """Demonstrate searching for relevant context."""
        logger.info("=== Demo: Context Search ===")
        
        # Search for SQL injection related reasoning
        query = "SQL injection vulnerability fix parameterized queries"
        
        context_results = await self.rag_store.search_context(
            query=query,
            limit=3,
            tags=["sql-injection", "critical"]
        )
        
        logger.info(f"Found {len(context_results)} relevant context entries")
        
        for i, result in enumerate(context_results, 1):
            logger.info(f"Context {i}:")
            logger.info(f"  Score: {result['score']:.3f}")
            logger.info(f"  Bug ID: {result['metadata'].get('bug_id')}")
            logger.info(f"  Content preview: {result['content'][:100]}...")
    
    async def demo_changelog_and_fixes(self, bug_id: str):
        """Demonstrate changelog and fix result storage."""
        logger.info("=== Demo: Changelog and Fix Results ===")
        
        # Log changelog entry
        changes = {
            "status": "in_progress",
            "assigned_to": "security_team",
            "priority": "high",
            "estimated_fix_time": "2 hours"
        }
        
        await self.fixchain_db.log_changelog(bug_id, changes, datetime.utcnow())
        logger.info("Logged changelog entry")
        
        # Save fix result
        patch_content = """
        --- a/app/models/user.py
        +++ b/app/models/user.py
        @@ -42,7 +42,7 @@ class UserModel:
             def get_user_by_id(self, user_id):
                 cursor = self.db.cursor()
        -        query = f"SELECT * FROM users WHERE id = {user_id}"
        +        query = "SELECT * FROM users WHERE id = %s"
        -        cursor.execute(query)
        +        cursor.execute(query, (user_id,))
                 return cursor.fetchone()
        """
        
        await self.fixchain_db.save_fix_result(bug_id, patch_content, "applied")
        logger.info("Saved fix result")
    
    async def demo_integration_workflow(self):
        """Demonstrate complete integration workflow."""
        logger.info("=== Demo: Complete Integration Workflow ===")
        
        # 1. Store test result and get bug
        result_id, test_result = await self.demo_test_result_storage()
        bug_id = test_result.attempts[0].issues[0].issue_id
        
        # 2. Store reasoning for the bug
        doc_id = await self.demo_reasoning_storage(bug_id)
        
        # 3. Search for relevant context
        await self.demo_context_search()
        
        # 4. Log changes and save fix
        await self.demo_changelog_and_fixes(bug_id)
        
        logger.info("Integration workflow completed successfully")
    
    async def cleanup(self):
        """Cleanup connections and resources."""
        try:
            if self.fixchain_db:
                await self.fixchain_db.close()
                logger.info("FixChain DB connection closed")
            
            if self.rag_store:
                self.rag_store.close()
                logger.info("RAG Store connection closed")
                
        except Exception as e:
            logger.error(f"Cleanup error: {e}")


async def main():
    """Main demo function."""
    demo = FixChainDBRAGDemo()
    
    try:
        # Setup connections
        await demo.setup()
        
        # Run demonstrations
        await demo.demo_integration_workflow()
        
    except DatabaseError as e:
        logger.error(f"Database error: {e}")
    except Exception as e:
        logger.error(f"Demo error: {e}")
    finally:
        # Cleanup
        await demo.cleanup()


if __name__ == "__main__":
    # Run the demo
    asyncio.run(main())