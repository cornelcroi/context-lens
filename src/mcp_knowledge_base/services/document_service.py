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
from ..utils.github_handler import (
    is_github_url,
    parse_github_url,
    clone_repository,
    get_repository_files,
    cleanup_repository,
    GitHubHandlerError,
)


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
        
        Supports:
        - Local file paths: "/path/to/file.py"
        - GitHub repository URLs: "https://github.com/user/repo"
        - GitHub file URLs: "https://github.com/user/repo/blob/main/file.py"
        - GitHub directory URLs: "https://github.com/user/repo/tree/main/src"
        
        Args:
            file_path: Path to document file or GitHub URL
            
        Returns:
            Dictionary containing success status and document metadata or error details
        """
        self._ensure_initialized()
        
        # Check if it's a GitHub URL
        if is_github_url(file_path):
            return await self._add_github_repository(file_path)
        
        # Handle local file
        return await self._add_local_file(file_path)
    
    async def _add_local_file(self, file_path: str) -> Dict[str, Any]:
        """Add a local file to the knowledge base.
        
        Args:
            file_path: Path to the document file
            
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
    
    async def _add_github_repository(self, github_url: str) -> Dict[str, Any]:
        """Add files from a GitHub repository to the knowledge base.
        
        Args:
            github_url: GitHub repository URL
            
        Returns:
            Dictionary containing success status and summary of added files
        """
        repo_path = None
        
        try:
            logger.info(f"Processing GitHub URL: {github_url}")
            
            # Parse GitHub URL
            try:
                repo_url, branch, subpath = parse_github_url(github_url)
            except GitHubHandlerError as e:
                return {
                    "success": False,
                    "error_type": "invalid_github_url",
                    "error_message": str(e),
                    "error_details": {"url": github_url}
                }
            
            # Clone repository
            try:
                repo_path = clone_repository(repo_url, branch)
            except GitHubHandlerError as e:
                return {
                    "success": False,
                    "error_type": "github_clone_error",
                    "error_message": str(e),
                    "error_details": {"url": repo_url, "branch": branch}
                }
            
            # Get files to process
            try:
                files = get_repository_files(
                    repo_path, 
                    subpath, 
                    self.config.processing.supported_extensions
                )
            except GitHubHandlerError as e:
                return {
                    "success": False,
                    "error_type": "github_file_error",
                    "error_message": str(e),
                    "error_details": {"subpath": subpath}
                }
            
            if not files:
                return {
                    "success": False,
                    "error_type": "no_files_found",
                    "error_message": "No supported files found in repository",
                    "error_details": {
                        "url": github_url,
                        "supported_extensions": self.config.processing.supported_extensions
                    }
                }
            
            logger.info(f"Found {len(files)} files to process from repository")
            
            # Process each file
            added_files = []
            failed_files = []
            
            for file_path in files:
                try:
                    result = await self._add_local_file(str(file_path))
                    if result.get("success"):
                        added_files.append({
                            "file_name": file_path.name,
                            "file_path": str(file_path.relative_to(repo_path)),
                            "chunks": result["document"]["chunk_count"]
                        })
                    else:
                        failed_files.append({
                            "file_name": file_path.name,
                            "error": result.get("error_message", "Unknown error")
                        })
                except Exception as e:
                    logger.warning(f"Failed to process {file_path}: {e}")
                    failed_files.append({
                        "file_name": file_path.name,
                        "error": str(e)
                    })
            
            # Build response
            total_chunks = sum(f["chunks"] for f in added_files)
            
            response = {
                "success": True,
                "repository": {
                    "url": repo_url,
                    "branch": branch or "default",
                    "subpath": subpath or "/"
                },
                "summary": {
                    "total_files_found": len(files),
                    "files_added": len(added_files),
                    "files_failed": len(failed_files),
                    "total_chunks": total_chunks
                },
                "added_files": added_files[:10],  # Limit to first 10 for response size
                "message": f"Successfully added {len(added_files)} files from repository with {total_chunks} chunks"
            }
            
            if failed_files:
                response["failed_files"] = failed_files[:5]  # Limit to first 5
                response["message"] += f" ({len(failed_files)} files failed)"
            
            if len(added_files) > 10:
                response["message"] += f" (showing first 10 of {len(added_files)} files)"
            
            logger.info(f"Repository processing complete: {len(added_files)} files added, {len(failed_files)} failed")
            
            return response
            
        except Exception as e:
            logger.error(f"Unexpected error processing GitHub repository: {e}")
            return {
                "success": False,
                "error_type": "github_processing_error",
                "error_message": f"Failed to process GitHub repository: {str(e)}",
                "error_details": {"url": github_url, "error": str(e)}
            }
        
        finally:
            # Cleanup cloned repository
            if repo_path:
                cleanup_repository(repo_path)
    
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