#!/usr/bin/env python3
"""Main CLI application for FixChain RAG system."""

import logging
import sys
import argparse
from datetime import datetime
from typing import Optional

from config import get_settings
from rag import create_rag_store
from rag.interfaces import RAGStore
from models.schemas import ReasoningEntry

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/fixchain.log', mode='a')
    ]
)

logger = logging.getLogger(__name__)


def setup_logging(debug: bool = False):
    """Setup logging configuration.
    
    Args:
        debug: Enable debug logging
    """
    level = logging.DEBUG if debug else logging.INFO
    logging.getLogger().setLevel(level)
    
    # Reduce noise from external libraries
    logging.getLogger('pymongo').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)


def demonstrate_rag_workflow(rag_store: RAGStore) -> None:
    """Demonstrate the complete RAG workflow.
    
    Args:
        rag_store: Initialized RAG store instance
    """
    logger.info("Starting FixChain RAG demonstration...")
    
    # Sample reasoning entries for demonstration
    sample_entries = [
        {
            "content": "Fixing bug_X in method `sendEmail` caused bug_Y before. "
                      "Best approach is refactoring with null check to prevent "
                      "NullPointerException when email address is empty.",
            "metadata": {
                "bug_id": "BUG-001",
                "method_name": "sendEmail",
                "fix_type": "null_check_refactor",
                "severity": "medium",
                "file_path": "src/email/EmailService.java",
                "line_number": 45,
                "tags": ["email", "null-check", "refactor"]
            }
        },
        {
            "content": "Database connection timeout in getUserProfile method. "
                      "Solution: implement connection pooling and retry logic "
                      "with exponential backoff. Avoid blocking the main thread.",
            "metadata": {
                "bug_id": "BUG-002",
                "method_name": "getUserProfile",
                "fix_type": "connection_pooling",
                "severity": "high",
                "file_path": "src/user/UserService.java",
                "line_number": 123,
                "tags": ["database", "timeout", "connection-pool"]
            }
        },
        {
            "content": "Memory leak in image processing pipeline. "
                      "Root cause: not disposing of BufferedImage objects. "
                      "Fix: explicit disposal in finally blocks and use try-with-resources.",
            "metadata": {
                "bug_id": "BUG-003",
                "method_name": "processImage",
                "fix_type": "memory_management",
                "severity": "critical",
                "file_path": "src/image/ImageProcessor.java",
                "line_number": 78,
                "tags": ["memory-leak", "image-processing", "resource-management"]
            }
        }
    ]
    
    # Add reasoning entries
    logger.info("Adding reasoning entries...")
    doc_ids = []
    for i, entry in enumerate(sample_entries, 1):
        try:
            # Add timestamp
            entry["metadata"]["timestamp"] = datetime.now().isoformat()
            
            doc_id = rag_store.add_reasoning_entry(entry["content"], entry["metadata"])
            doc_ids.append(doc_id)
            logger.info(f"Added entry {i}/3: {doc_id}")
            
        except Exception as e:
            logger.error(f"Failed to add entry {i}: {e}")
    
    # Demonstrate retrieval
    logger.info("\nDemonstrating similarity search...")
    
    test_queries = [
        "email method null pointer exception",
        "database connection timeout fix",
        "memory leak in image processing",
        "java method refactoring best practices"
    ]
    
    for query in test_queries:
        logger.info(f"\nQuery: '{query}'")
        try:
            results = rag_store.retrieve_similar_entries(query, k=2)
            
            if results:
                for i, result in enumerate(results, 1):
                    logger.info(f"  Result {i}:")
                    logger.info(f"    Content: {result.content[:100]}...")
                    logger.info(f"    Bug ID: {result.metadata.get('bug_id', 'N/A')}")
                    logger.info(f"    Method: {result.metadata.get('method_name', 'N/A')}")
                    logger.info(f"    Score: {result.score:.3f}")
            else:
                logger.info("  No results found")
                
        except Exception as e:
            logger.error(f"Search failed for query '{query}': {e}")
    
    # Demonstrate filtering
    logger.info("\nDemonstrating filtered search...")
    try:
        filter_criteria = {"severity": "high"}
        results = rag_store.retrieve_similar_entries(
            "database issues", 
            k=5, 
            filter_criteria=filter_criteria
        )
        logger.info(f"Found {len(results)} high-severity entries related to database issues")
        
    except Exception as e:
        logger.error(f"Filtered search failed: {e}")
    
    # Get collection statistics
    logger.info("\nCollection statistics:")
    try:
        stats = rag_store.get_collection_stats()
        logger.info(f"  Total documents: {stats.get('total_documents', 'N/A')}")
        logger.info(f"  Database: {stats.get('database_name', 'N/A')}")
        logger.info(f"  Collection: {stats.get('collection_name', 'N/A')}")
        
    except Exception as e:
        logger.error(f"Failed to get statistics: {e}")
    
    # Cleanup demonstration (optional)
    if doc_ids and len(doc_ids) > 0:
        logger.info("\nCleaning up demonstration data...")
        try:
            # Delete the first entry as demonstration
            success = rag_store.delete_entry(doc_ids[0])
            if success:
                logger.info(f"Successfully deleted entry: {doc_ids[0]}")
            else:
                logger.warning(f"Failed to delete entry: {doc_ids[0]}")
                
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
    
    logger.info("\nRAG demonstration completed!")


def interactive_mode(rag_store: RAGStore) -> None:
    """Run interactive mode for testing RAG functionality.
    
    Args:
        rag_store: Initialized RAG store instance
    """
    logger.info("Entering interactive mode. Type 'help' for commands or 'quit' to exit.")
    
    while True:
        try:
            command = input("\nFixChain> ").strip().lower()
            
            if command == 'quit' or command == 'exit':
                break
            elif command == 'help':
                print("Available commands:")
                print("  add <content> - Add reasoning entry (will prompt for metadata)")
                print("  search <query> - Search for similar entries")
                print("  stats - Show collection statistics")
                print("  help - Show this help message")
                print("  quit/exit - Exit interactive mode")
            elif command.startswith('add '):
                content = command[4:].strip()
                if content:
                    # Simple metadata collection
                    bug_id = input("Bug ID: ").strip() or "INTERACTIVE-001"
                    method_name = input("Method name: ").strip() or "unknown"
                    
                    metadata = {
                        "bug_id": bug_id,
                        "method_name": method_name,
                        "fix_type": "interactive",
                        "severity": "medium",
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    doc_id = rag_store.add_reasoning_entry(content, metadata)
                    print(f"Added entry: {doc_id}")
                else:
                    print("Please provide content after 'add'")
            elif command.startswith('search '):
                query = command[7:].strip()
                if query:
                    results = rag_store.retrieve_similar_entries(query, k=3)
                    if results:
                        print(f"Found {len(results)} similar entries:")
                        for i, result in enumerate(results, 1):
                            print(f"\n{i}. {result.content[:150]}...")
                            print(f"   Bug ID: {result.metadata.get('bug_id', 'N/A')}")
                            print(f"   Score: {result.score:.3f}")
                    else:
                        print("No similar entries found")
                else:
                    print("Please provide a search query")
            elif command == 'stats':
                stats = rag_store.get_collection_stats()
                print(f"Total documents: {stats.get('total_documents', 'N/A')}")
                print(f"Database: {stats.get('database_name', 'N/A')}")
                print(f"Collection: {stats.get('collection_name', 'N/A')}")
            else:
                print("Unknown command. Type 'help' for available commands.")
                
        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            logger.error(f"Command failed: {e}")
            print(f"Error: {e}")


def main():
    """Main application entry point."""
    parser = argparse.ArgumentParser(description="FixChain RAG System")
    parser.add_argument(
        "--mode", 
        choices=["demo", "interactive", "test"], 
        default="demo",
        help="Run mode: demo (default), interactive, or test"
    )
    parser.add_argument(
        "--debug", 
        action="store_true", 
        help="Enable debug logging"
    )
    parser.add_argument(
        "--config-check", 
        action="store_true", 
        help="Check configuration and exit"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.debug)
    
    try:
        # Load settings
        settings = get_settings()
        
        if args.config_check:
            logger.info("Configuration check:")
            logger.info(f"  MongoDB URI: {settings.mongodb_uri[:20]}...")
            logger.info(f"  Database: {settings.database_name}")
            logger.info(f"  Collection: {settings.collection_name}")
            logger.info(f"  OpenAI API Key: {'Set' if settings.openai_api_key else 'Not set'}")
            logger.info(f"  Embedding Model: {settings.embedding_model}")
            return
        
        # Create RAG store
        logger.info("Initializing FixChain RAG system...")
        rag_store = create_rag_store(settings)
        
        try:
            if args.mode == "demo":
                demonstrate_rag_workflow(rag_store)
            elif args.mode == "interactive":
                interactive_mode(rag_store)
            elif args.mode == "test":
                logger.info("Running basic connectivity test...")
                stats = rag_store.get_collection_stats()
                logger.info(f"Successfully connected. Total documents: {stats.get('total_documents', 0)}")
            
        finally:
            # Cleanup
            logger.info("Closing RAG store...")
            rag_store.close()
            
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
    except Exception as e:
        logger.error(f"Application failed: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)
    
    logger.info("FixChain RAG system shutdown complete")


if __name__ == "__main__":
    main()