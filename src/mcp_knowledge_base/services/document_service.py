"""Document service layer orchestrating document operations for the MCP Knowledge Base Server."""

import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

from ..models.data_models import (
    DocumentMetadata, 
    DocumentChunk, 
    SearchResult, 
    ClearResult, 
    ErrorResponse
)
from ..config import Config
from ..storage.lancedb_manager import LanceDBManager, VectorSearchResult
from ..services.embedding_service import EmbeddingService
from ..processors.content_extractor import ContentExtractor
from ..processors.file_readers import FileProcessingError


logger = logging.getLogger(__name__)


class DocumentService:
    """Service class orchestrating document operations for the knowledge base."""
    
    def __init__(self, config: Optional[Config] = None):
        """Initialize the document service with configuration.
        
        Args:
            config: Configuration object, defaults to environment-based config
        """
        self.config = config or Config.from_env()
        
        # Initialize components
        self.db_manager = LanceDBManager(self.config.database)
        self.embedding_service = EmbeddingService(
            self.config.embedding, 
            self.config.processing
        )
        self.content_extractor = ContentExtractor(
            chunk_size=self.config.processing.chunk_size,
            chunk_overlap=self.config.processing.chunk_overlap
        )
        
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize the document service and its components.
        
        Raises:
            Exception: If initialization fails
        """
        try:
            logger.info("Initializing document service...")
            
            # Initialize database
            await self.db_manager.initialize_database()
            
            # Load embedding model
            await self.embedding_service.load_model()
            
            self._initialized = True
            logger.info("Document service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize document service: {e}")
            raise Exception(f"Document service initialization failed: {str(e)}")
    
    def _ensure_initialized(self) -> None:
        """Ensure the service is initialized before operations."""
        if not self._initialized:
            raise RuntimeError("Document service not initialized. Call initialize() first.")
    
    async def add_document(self, file_path: str) -> Dict[str, Any]:
        """Add a document to the knowledge base.
        
        Args:
            file_path: Path to the document file (.py or .txt)
            
        Returns:
            Dictionary containing success status and document metadata or error details
        """
        self._ensure_initialized()
        
        try:
            logger.info(f"Adding document: {file_path}")
            
            # Validate and extract content
            try:
                metadata, chunks = self.content_extractor.extract_and_chunk(file_path)
            except FileProcessingError as e:
                logger.error(f"File processing failed for {file_path}: {e}")
                return {
                    "success": False,
                    "error_type": e.error_type,
                    "error_message": str(e),
                    "error_details": e.details
                }
            
            # Set ingestion timestamp
            metadata.ingestion_timestamp = datetime.utcnow()
            
            # Generate embeddings for chunks
            if chunks:
                chunk_texts = [chunk.content for chunk in chunks]
                embeddings = await self.embedding_service.generate_embeddings(chunk_texts)
                
                # Assign embeddings to chunks
                for chunk, embedding in zip(chunks, embeddings):
                    chunk.embedding = embedding
            
            # Store in vector database
            await self.db_manager.add_document_vectors(metadata, chunks)
            
            logger.info(f"Successfully added document {file_path} with {len(chunks)} chunks")
            
            return {
                "success": True,
                "document": {
                    "id": metadata.id,
                    "file_path": metadata.file_path,
                    "file_name": metadata.file_name,
                    "file_size": metadata.file_size,
                    "file_type": metadata.file_type,
                    "ingestion_timestamp": metadata.ingestion_timestamp.isoformat(),
                    "content_hash": metadata.content_hash,
                    "chunk_count": metadata.chunk_count
                },
                "message": f"Document '{metadata.file_name}' added successfully with {len(chunks)} chunks"
            }
            
        except Exception as e:
            logger.error(f"Failed to add document {file_path}: {e}")
            return {
                "success": False,
                "error_type": "document_ingestion_error",
                "error_message": f"Failed to add document: {str(e)}",
                "error_details": {"file_path": file_path, "error": str(e)}
            }
    
    async def list_documents(self, limit: Optional[int] = None, offset: int = 0) -> Dict[str, Any]:
        """List all documents in the knowledge base with pagination support.
        
        Args:
            limit: Maximum number of documents to return (None for no limit)
            offset: Number of documents to skip for pagination
            
        Returns:
            Dictionary containing success status and list of documents or error details
        """
        self._ensure_initialized()
        
        try:
            logger.info(f"Listing documents with limit={limit}, offset={offset}")
            
            # Get documents from database
            documents = await self.db_manager.list_all_documents(limit=limit, offset=offset)
            
            # Convert to serializable format
            document_list = []
            for doc in documents:
                document_list.append({
                    "id": doc.id,
                    "file_path": doc.file_path,
                    "file_name": doc.file_name,
                    "file_size": doc.file_size,
                    "file_type": doc.file_type,
                    "ingestion_timestamp": doc.ingestion_timestamp.isoformat() if doc.ingestion_timestamp else None,
                    "content_hash": doc.content_hash,
                    "chunk_count": doc.chunk_count
                })
            
            # Get total count for pagination info
            total_count = await self.db_manager.get_document_count()
            
            logger.info(f"Listed {len(document_list)} documents (total: {total_count})")
            
            return {
                "success": True,
                "documents": document_list,
                "pagination": {
                    "total_count": total_count,
                    "returned_count": len(document_list),
                    "offset": offset,
                    "limit": limit
                },
                "message": f"Found {len(document_list)} documents" + (
                    f" (showing {offset + 1}-{offset + len(document_list)} of {total_count})" 
                    if total_count > len(document_list) else ""
                )
            }
            
        except Exception as e:
            logger.error(f"Failed to list documents: {e}")
            return {
                "success": False,
                "error_type": "document_listing_error",
                "error_message": f"Failed to list documents: {str(e)}",
                "error_details": {"limit": limit, "offset": offset, "error": str(e)}
            }
    
    async def search_documents(self, query: str, limit: int = 10) -> Dict[str, Any]:
        """Search documents using vector similarity search.
        
        Args:
            query: Search query text
            limit: Maximum number of results to return
            
        Returns:
            Dictionary containing success status and search results or error details
        """
        self._ensure_initialized()
        
        try:
            logger.info(f"Searching documents with query: '{query}' (limit: {limit})")
            
            if not query.strip():
                return {
                    "success": False,
                    "error_type": "invalid_query",
                    "error_message": "Search query cannot be empty",
                    "error_details": {"query": query}
                }
            
            # Generate embedding for query
            query_embedding = await self.embedding_service.generate_embedding(query.strip())
            
            if not query_embedding:
                return {
                    "success": False,
                    "error_type": "embedding_generation_error",
                    "error_message": "Failed to generate embedding for query",
                    "error_details": {"query": query}
                }
            
            # Perform vector search
            vector_results = await self.db_manager.search_vectors(query_embedding, limit=limit)
            
            # Convert to SearchResult objects
            search_results = []
            for vector_result in vector_results:
                # Get document metadata
                doc_metadata = await self.db_manager.get_document_metadata(vector_result.document_id)
                
                if doc_metadata:
                    # Create content excerpt (limit to reasonable length)
                    excerpt = vector_result.content
                    if len(excerpt) > 200:
                        excerpt = excerpt[:200] + "..."
                    
                    search_result = SearchResult(
                        document_id=vector_result.document_id,
                        document_path=doc_metadata.file_path,
                        relevance_score=1.0 - vector_result.score,  # Convert distance to similarity score
                        content_excerpt=excerpt,
                        metadata=doc_metadata
                    )
                    search_results.append(search_result)
            
            # Convert to serializable format
            results_list = []
            for result in search_results:
                results_list.append({
                    "document_id": result.document_id,
                    "document_path": result.document_path,
                    "relevance_score": round(result.relevance_score, 4),
                    "content_excerpt": result.content_excerpt,
                    "metadata": {
                        "id": result.metadata.id,
                        "file_name": result.metadata.file_name,
                        "file_type": result.metadata.file_type,
                        "file_size": result.metadata.file_size,
                        "ingestion_timestamp": result.metadata.ingestion_timestamp.isoformat() if result.metadata.ingestion_timestamp else None,
                        "chunk_count": result.metadata.chunk_count
                    }
                })
            
            logger.info(f"Search returned {len(results_list)} results for query: '{query}'")
            
            return {
                "success": True,
                "results": results_list,
                "query": query,
                "result_count": len(results_list),
                "message": f"Found {len(results_list)} relevant documents" + (
                    f" (showing top {limit})" if len(results_list) == limit else ""
                )
            }
            
        except Exception as e:
            logger.error(f"Failed to search documents with query '{query}': {e}")
            return {
                "success": False,
                "error_type": "document_search_error",
                "error_message": f"Failed to search documents: {str(e)}",
                "error_details": {"query": query, "limit": limit, "error": str(e)}
            }
    
    async def clear_knowledge_base(self) -> Dict[str, Any]:
        """Clear all documents from the knowledge base.
        
        Returns:
            Dictionary containing success status and clear result or error details
        """
        self._ensure_initialized()
        
        try:
            logger.info("Clearing knowledge base...")
            
            # Clear all documents and chunks
            documents_removed = await self.db_manager.clear_all_documents()
            
            logger.info(f"Successfully cleared {documents_removed} documents from knowledge base")
            
            return {
                "success": True,
                "documents_removed": documents_removed,
                "message": f"Successfully cleared {documents_removed} documents from the knowledge base"
            }
            
        except Exception as e:
            logger.error(f"Failed to clear knowledge base: {e}")
            return {
                "success": False,
                "error_type": "knowledge_base_clear_error",
                "error_message": f"Failed to clear knowledge base: {str(e)}",
                "error_details": {"error": str(e)}
            }
    
    async def get_document_by_id(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific document by its ID.
        
        Args:
            document_id: ID of the document to retrieve
            
        Returns:
            Document metadata dictionary or None if not found
        """
        self._ensure_initialized()
        
        try:
            metadata = await self.db_manager.get_document_metadata(document_id)
            
            if metadata:
                return {
                    "id": metadata.id,
                    "file_path": metadata.file_path,
                    "file_name": metadata.file_name,
                    "file_size": metadata.file_size,
                    "file_type": metadata.file_type,
                    "ingestion_timestamp": metadata.ingestion_timestamp.isoformat() if metadata.ingestion_timestamp else None,
                    "content_hash": metadata.content_hash,
                    "chunk_count": metadata.chunk_count
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get document {document_id}: {e}")
            return None
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get knowledge base statistics.
        
        Returns:
            Dictionary containing knowledge base statistics
        """
        self._ensure_initialized()
        
        try:
            document_count = await self.db_manager.get_document_count()
            
            return {
                "document_count": document_count,
                "embedding_model": self.config.embedding.model,
                "chunk_size": self.config.processing.chunk_size,
                "supported_file_types": self.config.processing.supported_extensions
            }
            
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {
                "document_count": 0,
                "embedding_model": "unknown",
                "chunk_size": 0,
                "supported_file_types": []
            }
    
    async def cleanup(self) -> None:
        """Clean up resources used by the document service."""
        try:
            logger.info("Cleaning up document service...")
            
            # Cleanup embedding service
            await self.embedding_service.cleanup()
            
            # Cleanup database manager
            await self.db_manager.close()
            
            self._initialized = False
            logger.info("Document service cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during document service cleanup: {e}")