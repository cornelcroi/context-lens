"""Integration tests for search enhancements.

Tests the complete search flow with metadata, timing measurement accuracy,
and model name propagation from config.
"""

import time

import pytest

from context_lens.config import (
    Config,
    DatabaseConfig,
    EmbeddingConfig,
    ProcessingConfig,
    ServerConfig,
)
from context_lens.services.document_service import DocumentService
from context_lens.server import reset_document_service


@pytest.mark.asyncio
async def test_complete_search_flow_with_metadata(temp_dir):
    """Test complete search flow with metadata from document addition to search."""
    # Reset service
    await reset_document_service()
    
    # Create test config
    test_config = Config(
        database=DatabaseConfig(
            path=str(temp_dir / "integration_test.db"),
            table_prefix="integration_"
        ),
        embedding=EmbeddingConfig(
            model="sentence-transformers/all-MiniLM-L6-v2",
            cache_dir=str(temp_dir / "models")
        ),
        processing=ProcessingConfig(
            max_file_size_mb=1,
            chunk_size=100,
            chunk_overlap=20
        ),
        server=ServerConfig(
            name="integration-test",
            log_level="DEBUG"
        ),
    )
    
    # Create test documents
    doc1 = temp_dir / "doc1.txt"
    doc1.write_text("Python is a high-level programming language known for its simplicity and readability.")
    
    doc2 = temp_dir / "doc2.txt"
    doc2.write_text("JavaScript is a versatile programming language used for web development.")
    
    doc3 = temp_dir / "doc3.txt"
    doc3.write_text("Machine learning algorithms can be implemented using various frameworks.")
    
    # Initialize service and add documents
    service = DocumentService(test_config)
    await service.initialize()
    
    add_result1 = await service.add_document(str(doc1))
    assert add_result1.get("success") is True
    
    add_result2 = await service.add_document(str(doc2))
    assert add_result2.get("success") is True
    
    add_result3 = await service.add_document(str(doc3))
    assert add_result3.get("success") is True
    
    # Perform search (simulating what the MCP tool does)
    query = "programming languages"
    
    # Capture start time for timing measurement
    start_time = time.perf_counter()
    
    # Call service method directly
    service_result = await service.search_documents(query=query, limit=10)
    
    # Capture end time and calculate elapsed time in milliseconds
    end_time = time.perf_counter()
    search_time_ms = int((end_time - start_time) * 1000)
    
    # Simulate the metadata enrichment that the MCP tool does
    if service_result.get("success"):
        search_stats = service_result.get("_search_stats", {})
        search_result = service_result.copy()
        search_result["search_metadata"] = {
            "query_processed": query,
            "embedding_model": search_stats.get("embedding_model", "unknown"),
            "search_time_ms": search_time_ms,
            "total_documents_searched": search_stats.get("total_documents", -1)
        }
        search_result.pop("_search_stats", None)
    else:
        search_result = service_result
    
    # Verify complete response structure
    assert search_result.get("success") is True
    assert "results" in search_result
    assert "query" in search_result
    assert "result_count" in search_result
    assert "search_metadata" in search_result
    
    # Verify search metadata structure
    metadata = search_result["search_metadata"]
    assert "query_processed" in metadata
    assert "embedding_model" in metadata
    assert "search_time_ms" in metadata
    assert "total_documents_searched" in metadata
    
    # Verify metadata accuracy
    assert metadata["query_processed"] == "programming languages"
    assert metadata["embedding_model"] == "sentence-transformers/all-MiniLM-L6-v2"
    assert metadata["search_time_ms"] > 0
    assert metadata["total_documents_searched"] == 3
    
    # Verify results are relevant
    assert search_result["result_count"] > 0
    
    # Verify no internal fields leaked
    assert "_search_stats" not in search_result
    
    # Clean up
    await reset_document_service()


@pytest.mark.asyncio
async def test_timing_measurement_accuracy(temp_dir):
    """Test that timing measurements are accurate and reasonable."""
    # Reset service
    await reset_document_service()
    
    # Create test config
    test_config = Config(
        database=DatabaseConfig(
            path=str(temp_dir / "timing_test.db"),
            table_prefix="timing_"
        ),
        embedding=EmbeddingConfig(
            model="sentence-transformers/all-MiniLM-L6-v2",
            cache_dir=str(temp_dir / "models")
        ),
        processing=ProcessingConfig(
            max_file_size_mb=1,
            chunk_size=100,
            chunk_overlap=20
        ),
        server=ServerConfig(
            name="timing-test",
            log_level="DEBUG"
        ),
    )
    
    # Create test documents with varying sizes
    for i in range(5):
        doc = temp_dir / f"doc{i}.txt"
        doc.write_text(f"Document {i}: " + "test content " * 50)
    
    # Initialize service and add documents
    service = DocumentService(test_config)
    await service.initialize()
    
    for i in range(5):
        await service.add_document(str(temp_dir / f"doc{i}.txt"))
    
    # Perform multiple searches and measure timing
    search_times = []
    
    for query_text in ["test content", "document information", "data analysis"]:
        start = time.perf_counter()
        
        # Call service method directly
        service_result = await service.search_documents(query=query_text, limit=5)
        
        # Simulate the metadata enrichment that the MCP tool does
        if service_result.get("success"):
            search_stats = service_result.get("_search_stats", {})
            result = service_result.copy()
            result["search_metadata"] = {
                "query_processed": query_text,
                "embedding_model": search_stats.get("embedding_model", "unknown"),
                "search_time_ms": int((time.perf_counter() - start) * 1000),
                "total_documents_searched": search_stats.get("total_documents", -1)
            }
            result.pop("_search_stats", None)
        else:
            result = service_result
        
        end = time.perf_counter()
        
        external_time_ms = int((end - start) * 1000)
        reported_time_ms = result["search_metadata"]["search_time_ms"]
        
        search_times.append(reported_time_ms)
        
        # Verify timing is reasonable (reported time should be close to external measurement)
        # Allow some variance due to overhead
        assert reported_time_ms > 0, "Search time should be positive"
        assert reported_time_ms <= external_time_ms + 100, \
            "Reported time should not exceed external measurement by more than 100ms"
        
        # Verify timing includes embedding generation (should be at least a few ms)
        assert reported_time_ms >= 1, "Search should take at least 1ms"
    
    # Verify timing consistency (all searches should be in similar range)
    avg_time = sum(search_times) / len(search_times)
    for t in search_times:
        # Each search should be within 5x of average (allowing for variance)
        assert t < avg_time * 5, "Search times should be relatively consistent"
    
    # Clean up
    await reset_document_service()


@pytest.mark.asyncio
async def test_model_name_propagation_from_config(temp_dir):
    """Test that embedding model name is correctly propagated from config to metadata."""
    # Reset service
    await reset_document_service()
    
    # Create test config with custom model name
    custom_model = "sentence-transformers/all-MiniLM-L6-v2"
    test_config = Config(
        database=DatabaseConfig(
            path=str(temp_dir / "model_test.db"),
            table_prefix="model_"
        ),
        embedding=EmbeddingConfig(
            model=custom_model,
            cache_dir=str(temp_dir / "models")
        ),
        processing=ProcessingConfig(
            max_file_size_mb=1,
            chunk_size=100,
            chunk_overlap=20
        ),
        server=ServerConfig(
            name="model-test",
            log_level="DEBUG"
        ),
    )
    
    # Create a test document
    doc = temp_dir / "test_doc.txt"
    doc.write_text("This is a test document for model name propagation testing.")
    
    # Initialize service with custom config
    service = DocumentService(test_config)
    await service.initialize()
    await service.add_document(str(doc))
    
    # Perform search (simulating what the MCP tool does)
    query = "test document"
    
    # Capture start time for timing measurement
    start_time = time.perf_counter()
    
    # Call service method directly
    service_result = await service.search_documents(query=query, limit=5)
    
    # Capture end time and calculate elapsed time in milliseconds
    end_time = time.perf_counter()
    search_time_ms = int((end_time - start_time) * 1000)
    
    # Simulate the metadata enrichment that the MCP tool does
    if service_result.get("success"):
        search_stats = service_result.get("_search_stats", {})
        result = service_result.copy()
        result["search_metadata"] = {
            "query_processed": query,
            "embedding_model": search_stats.get("embedding_model", "unknown"),
            "search_time_ms": search_time_ms,
            "total_documents_searched": search_stats.get("total_documents", -1)
        }
        result.pop("_search_stats", None)
    else:
        result = service_result
    
    # Verify model name in metadata matches config
    assert result.get("success") is True
    metadata = result["search_metadata"]
    
    assert metadata["embedding_model"] == custom_model, \
        f"Expected model '{custom_model}', got '{metadata['embedding_model']}'"
    
    # Verify model name is not "unknown" (the fallback value)
    assert metadata["embedding_model"] != "unknown", \
        "Model name should not be the fallback value"
    
    # Clean up
    await reset_document_service()


@pytest.mark.asyncio
async def test_search_with_large_corpus(temp_dir):
    """Test search metadata with a larger corpus to verify scalability."""
    # Reset service
    await reset_document_service()
    
    # Create test config
    test_config = Config(
        database=DatabaseConfig(
            path=str(temp_dir / "large_corpus_test.db"),
            table_prefix="large_"
        ),
        embedding=EmbeddingConfig(
            model="sentence-transformers/all-MiniLM-L6-v2",
            cache_dir=str(temp_dir / "models")
        ),
        processing=ProcessingConfig(
            max_file_size_mb=1,
            chunk_size=100,
            chunk_overlap=20
        ),
        server=ServerConfig(
            name="large-corpus-test",
            log_level="DEBUG"
        ),
    )
    
    # Create 20 test documents
    num_docs = 20
    for i in range(num_docs):
        doc = temp_dir / f"doc_{i}.txt"
        doc.write_text(f"Document {i}: This is test content about topic {i % 5}. " * 10)
    
    # Initialize service and add documents
    service = DocumentService(test_config)
    await service.initialize()
    
    for i in range(num_docs):
        await service.add_document(str(temp_dir / f"doc_{i}.txt"))
    
    # Perform search (simulating what the MCP tool does)
    query = "test content topic"
    
    # Capture start time for timing measurement
    start_time = time.perf_counter()
    
    # Call service method directly
    service_result = await service.search_documents(query=query, limit=10)
    
    # Capture end time and calculate elapsed time in milliseconds
    end_time = time.perf_counter()
    search_time_ms = int((end_time - start_time) * 1000)
    
    # Simulate the metadata enrichment that the MCP tool does
    if service_result.get("success"):
        search_stats = service_result.get("_search_stats", {})
        result = service_result.copy()
        result["search_metadata"] = {
            "query_processed": query,
            "embedding_model": search_stats.get("embedding_model", "unknown"),
            "search_time_ms": search_time_ms,
            "total_documents_searched": search_stats.get("total_documents", -1)
        }
        result.pop("_search_stats", None)
    else:
        result = service_result
    
    # Verify metadata reflects correct corpus size
    assert result.get("success") is True
    metadata = result["search_metadata"]
    
    assert metadata["total_documents_searched"] == num_docs, \
        f"Expected {num_docs} documents, got {metadata['total_documents_searched']}"
    
    # Verify search still performs well with larger corpus
    assert metadata["search_time_ms"] < 10000, \
        "Search should complete in reasonable time even with larger corpus"
    
    # Clean up
    await reset_document_service()
