"""Example usage of FixChain RAG system with rag_insights collection."""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any

# FixChain imports
from rag.stores import FixChainRAGStore, MongoVectorStore
from rag.embeddings import OpenAIEmbeddingProvider
from config.settings import get_settings

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FixChainRAGInsightsDemo:
    """Demonstration of FixChain RAG system with rag_insights collection."""
    
    def __init__(self):
        """Initialize demo with RAG components."""
        self.settings = get_settings()
        self.rag_store = None
    
    async def setup(self):
        """Setup RAG store connections."""
        try:
            # Initialize embedding provider
            embedding_provider = OpenAIEmbeddingProvider(
                api_key=self.settings.openai_api_key or "your-openai-api-key",
                model=self.settings.embedding_model
            )
            
            # Initialize vector store with rag_insights collection
            vector_store = MongoVectorStore(
                mongodb_uri=self.settings.mongodb_uri,
                database_name=self.settings.database_name,
                collection_name="rag_insights",  # Use rag_insights collection
                timeout=self.settings.timeout
            )
            
            # Initialize RAG store
            self.rag_store = FixChainRAGStore(
                embedding_provider=embedding_provider,
                vector_store=vector_store
            )
            
            logger.info("RAG store initialized successfully with rag_insights collection")
            
        except Exception as e:
            logger.error(f"Failed to setup RAG store: {e}")
            raise
    
    async def demo_store_reasoning(self):
        """Demonstrate storing reasoning with required metadata."""
        logger.info("=== Demo: Store Reasoning ===")
        
        # Sample reasoning content
        reasoning_content = """
        Analysis of SQL injection vulnerability in user authentication:
        
        1. Issue: Direct string concatenation in SQL query
        2. Risk: Allows malicious input to modify query structure
        3. Solution: Use parameterized queries with prepared statements
        4. Implementation: Replace string concatenation with placeholders
        5. Testing: Verify with both valid and malicious inputs
        """
        
        # Required metadata as per specification
        metadata = {
            "bug_id": "BUG-001",
            "test_name": "SyntaxCheck", 
            "iteration": 3,
            "category": "static",
            "tool": "bandit",
            "status": "fail",
            "tags": ["security", "logic"],
            "timestamp": "2025-07-31T10:00:00",
            "source_file": "src/main.py"
        }
        
        try:
            # Store reasoning
            document_id = await self.rag_store.store_reasoning(reasoning_content, metadata)
            logger.info(f"Stored reasoning with ID: {document_id}")
            
            # Store another reasoning entry
            reasoning_content_2 = """
            Cross-site scripting (XSS) vulnerability analysis:
            
            1. Issue: Unescaped user input in HTML output
            2. Risk: Malicious script execution in user browsers
            3. Solution: Implement proper input sanitization and output encoding
            4. Implementation: Use template engine with auto-escaping
            5. Testing: Test with various XSS payloads
            """
            
            metadata_2 = {
                "bug_id": "BUG-002",
                "test_name": "SecurityCheck",
                "iteration": 1,
                "category": "dynamic",
                "tool": "zap",
                "status": "fail",
                "tags": ["security", "xss"],
                "timestamp": "2025-07-31T11:00:00",
                "source_file": "src/templates/user_profile.html"
            }
            
            document_id_2 = await self.rag_store.store_reasoning(reasoning_content_2, metadata_2)
            logger.info(f"Stored second reasoning with ID: {document_id_2}")
            
        except Exception as e:
            logger.error(f"Failed to store reasoning: {e}")
            raise
    
    async def demo_search_reasoning(self):
        """Demonstrate searching for reasoning entries."""
        logger.info("=== Demo: Search Reasoning ===")
        
        try:
            # Search for SQL injection related reasoning
            query = "SQL injection vulnerability parameterized queries"
            results = self.rag_store.search_reasoning(query, limit=3)
            
            logger.info(f"Found {len(results)} reasoning entries for query: '{query}'")
            for i, result in enumerate(results, 1):
                logger.info(f"Result {i}:")
                logger.info(f"  Bug ID: {result.metadata.get('bug_id', 'N/A')}")
                logger.info(f"  Test: {result.metadata.get('test_name', 'N/A')}")
                logger.info(f"  Category: {result.metadata.get('category', 'N/A')}")
                logger.info(f"  Score: {result.score}")
                logger.info(f"  Content preview: {result.content[:100]}...")
                logger.info("---")
            
            # Search with filter
            filter_criteria = {"category": "static"}
            filtered_results = self.rag_store.search_reasoning(
                "security vulnerability", 
                limit=5, 
                filter=filter_criteria
            )
            
            logger.info(f"Found {len(filtered_results)} static analysis results")
            
        except Exception as e:
            logger.error(f"Failed to search reasoning: {e}")
            raise
    
    async def demo_delete_reasoning_by_bug_id(self):
        """Demonstrate deleting reasoning entries by bug ID."""
        logger.info("=== Demo: Delete Reasoning by Bug ID ===")
        
        try:
            # Delete all reasoning entries for a specific bug
            bug_id = "BUG-001"
            deleted_count = self.rag_store.delete_reasoning_by_bug_id(bug_id)
            
            logger.info(f"Deleted {deleted_count} reasoning entries for bug {bug_id}")
            
            # Verify deletion by searching
            remaining_results = self.rag_store.search_reasoning(
                "SQL injection", 
                filter={"bug_id": bug_id}
            )
            
            logger.info(f"Remaining entries for {bug_id}: {len(remaining_results)}")
            
        except Exception as e:
            logger.error(f"Failed to delete reasoning: {e}")
            raise
    
    async def demo_collection_stats(self):
        """Demonstrate getting collection statistics."""
        logger.info("=== Demo: Collection Statistics ===")
        
        try:
            stats = self.rag_store.get_collection_stats()
            
            logger.info("RAG Insights Collection Statistics:")
            logger.info(f"  Total documents: {stats.get('total_documents', 0)}")
            logger.info(f"  Collection name: {stats.get('collection_name', 'N/A')}")
            logger.info(f"  Database name: {stats.get('database_name', 'N/A')}")
            
            if 'indexes' in stats:
                logger.info(f"  Indexes: {len(stats['indexes'])}")
            
        except Exception as e:
            logger.error(f"Failed to get collection stats: {e}")
            raise
    
    async def cleanup(self):
        """Cleanup resources."""
        if self.rag_store:
            self.rag_store.close()
            logger.info("RAG store connections closed")


async def main():
    """Main demo function."""
    demo = FixChainRAGInsightsDemo()
    
    try:
        # Setup
        await demo.setup()
        
        # Run demonstrations
        await demo.demo_store_reasoning()
        await demo.demo_search_reasoning()
        await demo.demo_collection_stats()
        await demo.demo_delete_reasoning_by_bug_id()
        
        logger.info("Demo completed successfully!")
        
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        raise
    
    finally:
        # Cleanup
        await demo.cleanup()


if __name__ == "__main__":
    # Run the demo
    asyncio.run(main())