#!/usr/bin/env python3
"""Main CLI application for FixChain Test Suite and RAG system."""

import asyncio
import logging
import sys
import argparse
from datetime import datetime
from typing import Optional, List
from pathlib import Path

from config import get_settings
from rag import create_rag_store
from rag.interfaces import RAGStore
from models.schemas import ReasoningEntry
from core.test_executor import TestExecutor
from testsuite.static_tests.syntax_check import SyntaxCheckTest
from testsuite.static_tests.type_check import TypeCheckTest
from testsuite.static_tests.security_check import SecurityCheckTest

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


async def store_test_reasoning(rag_store: RAGStore, test_name: str, attempt_id: str, result, source_file: str) -> None:
    """Store test reasoning in RAG store.
    
    Args:
        rag_store: RAG store instance
        test_name: Name of the test
        attempt_id: Unique attempt identifier
        result: Test result object
        source_file: Path to source file
    """
    try:
        content = f"Test {test_name} on {source_file}: {result.summary}"
        if hasattr(result, 'output') and result.output:
            content += f" Output: {result.output}"
        
        metadata = {
            "test_name": test_name,
            "attempt_id": attempt_id,
            "source_file": source_file,
            "status": result.status,
            "timestamp": datetime.now().isoformat(),
            "test_type": "static_analysis"
        }
        
        if hasattr(result, 'metadata') and result.metadata:
            metadata.update(result.metadata)
        
        doc_id = rag_store.add_reasoning_entry(content, metadata)
        logger.info(f"Stored test reasoning: {doc_id}")
        
    except Exception as e:
        logger.warning(f"Failed to store test reasoning: {e}")


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


async def run_test_suite(file_path: str, tests: List[str], max_iterations: int = 5, enable_rag: bool = False) -> None:
    """Run the FixChain test suite on a source file.
    
    Args:
        file_path: Path to the source file to test
        tests: List of test types to run (syntax, type, security, all)
        max_iterations: Maximum number of fix iterations
        enable_rag: Whether to enable RAG storage for test reasoning
    """
    logger.info(f"Running FixChain Test Suite on: {file_path}")
    logger.info(f"Test types: {', '.join(tests)}")
    logger.info(f"Max iterations: {max_iterations}")
    logger.info(f"RAG storage: {'Enabled' if enable_rag else 'Disabled'}")
    
    # Check if file exists
    if not Path(file_path).exists():
        logger.error(f"File not found: {file_path}")
        return
    
    # Initialize RAG store if enabled
    rag_store = None
    if enable_rag:
        try:
            settings = get_settings()
            rag_store = create_rag_store(settings)
            logger.info("RAG store initialized successfully")
        except Exception as e:
            logger.warning(f"Failed to initialize RAG store: {e}")
            logger.info("Continuing without RAG storage...")
    
    # Create a simple test executor without database dependencies
    # We'll directly instantiate and run tests without the full TestExecutor
    from testsuite.static_tests.syntax_check import SyntaxCheckTest
    from testsuite.static_tests.type_check import TypeCheckTest  
    from testsuite.static_tests.security_check import SecurityCheckTest
    
    # Define available test cases
    available_tests = {
        'syntax': SyntaxCheckTest,
        'type': TypeCheckTest,
        'security': SecurityCheckTest
    }
    
    # Determine which tests to run
    if 'all' in tests:
        test_names = list(available_tests.keys())
    else:
        test_names = [test for test in tests if test in available_tests]
    
    if not test_names:
        logger.error("No valid test cases specified")
        return
    
    # Run each test case
    results = []
    for test_name in test_names:
        logger.info(f"\n{'='*50}")
        logger.info(f"Running {test_name.upper()} test...")
        logger.info(f"{'='*50}")
        
        try:
            # Create test instance
            test_class = available_tests[test_name]
            test_instance = test_class(max_iterations=max_iterations)
            
            # Run test directly
            attempt_id = f"{test_name}_1"
            result = await test_instance.run(
                source_file=file_path,
                attempt_id=attempt_id
            )
            
            results.append((test_name, result))
            
            # Store reasoning in RAG if enabled
            if rag_store and result:
                await store_test_reasoning(
                    rag_store=rag_store,
                    test_name=test_name,
                    attempt_id=attempt_id,
                    result=result,
                    source_file=file_path
                )
            
            # Log results
            logger.info(f"\n{test_name.upper()} Test Results:")
            logger.info(f"  Status: {result.status}")
            logger.info(f"  Summary: {result.summary}")
            
            if hasattr(result, 'output') and result.output:
                logger.info(f"  Output: {result.output[:200]}...")  # Show first 200 chars
            
            if hasattr(result, 'metadata') and result.metadata:
                logger.info(f"  Metadata: {result.metadata}")
            
        except Exception as e:
            logger.error(f"Failed to run {test_name} test: {e}")
            if logger.isEnabledFor(logging.DEBUG):
                import traceback
                traceback.print_exc()
            results.append((test_name, None))
    
    # Cleanup RAG store
    if rag_store:
        try:
            rag_store.close()
            logger.info("RAG store closed successfully")
        except Exception as e:
            logger.warning(f"Error closing RAG store: {e}")
    
    # Summary
    logger.info(f"\n{'='*60}")
    logger.info("TEST SUITE SUMMARY")
    logger.info(f"{'='*60}")
    
    passed = 0
    total = 0
    
    for test_name, result in results:
        if result is not None:
            total += 1
            status_symbol = "[PASS]" if result.status == "pass" else "[FAIL]"
            status_text = "PASSED" if result.status == "pass" else "FAILED"
            logger.info(f"{status_symbol} {test_name.upper()}: {status_text}")
            if result.status == "pass":
                passed += 1
        else:
            total += 1
            logger.info(f"[ERROR] {test_name.upper()}: ERROR")
    
    logger.info(f"\nOverall: {passed}/{total} tests passed")
    logger.info(f"Test suite completed for: {file_path}")


def main():
    """Main application entry point."""
    parser = argparse.ArgumentParser(description="FixChain Test Suite and RAG System")
    parser.add_argument(
        "--mode", 
        choices=["demo", "interactive", "test", "testsuite"], 
        default="demo",
        help="Run mode: demo (default), interactive, test, or testsuite"
    )
    parser.add_argument(
        "--file",
        type=str,
        help="Source file to test (required for testsuite mode)"
    )
    parser.add_argument(
        "--tests",
        type=str,
        default="all",
        help="Comma-separated list of tests to run: syntax,type,security,all (default: all)"
    )
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=5,
        help="Maximum number of fix iterations (default: 5)"
    )
    parser.add_argument(
        "--debug", 
        action="store_true", 
        help="Enable debug logging"
    )
    parser.add_argument(
        "--enable-rag",
        action="store_true",
        help="Enable RAG storage for test reasoning"
    )
    parser.add_argument(
        "--config-check", 
        action="store_true", 
        help="Check configuration and exit"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.debug)
    
    # Handle testsuite mode separately (doesn't need RAG store)
    if args.mode == "testsuite":
        if not args.file:
            logger.error("--file argument is required for testsuite mode")
            parser.print_help()
            sys.exit(1)
        
        # Parse test types
        test_types = [t.strip().lower() for t in args.tests.split(',')]
        
        # Validate test types
        valid_tests = {'syntax', 'type', 'security', 'all'}
        invalid_tests = [t for t in test_types if t not in valid_tests]
        if invalid_tests:
            logger.error(f"Invalid test types: {', '.join(invalid_tests)}")
            logger.error(f"Valid options: {', '.join(valid_tests)}")
            sys.exit(1)
        
        try:
            # Run test suite
            asyncio.run(run_test_suite(args.file, test_types, args.max_iterations, enable_rag=args.enable_rag))
        except KeyboardInterrupt:
            logger.info("Test suite interrupted by user")
        except Exception as e:
            logger.error(f"Test suite failed: {e}")
            if args.debug:
                import traceback
                traceback.print_exc()
            sys.exit(1)
        return
    
    # Handle RAG-related modes
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
    
    logger.info("FixChain application shutdown complete")


if __name__ == "__main__":
    main()