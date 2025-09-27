"""
RAG Tool for Knowledge Retrieval
Allows agents to search and retrieve information from the knowledge base
"""

import logging
from typing import Any, Dict, List, Optional

from agi.tools.base_tool import BaseTool
from agi.knowledge import get_rag_system

logger = logging.getLogger(__name__)


class KnowledgeSearchTool(BaseTool):
    """
    Tool for searching the knowledge base
    """

    def __init__(self):
        super().__init__(
            name="knowledge_search",
            description="Search the knowledge base for relevant information",
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results",
                        "default": 5
                    }
                },
                "required": ["query"]
            },
            examples=[
                "knowledge_search(query='What is machine learning?')",
                "knowledge_search(query='Python best practices', limit=3)"
            ]
        )
        self.rag_system = None

    async def _initialize(self):
        """Initialize RAG system if needed"""
        if not self.rag_system:
            self.rag_system = await get_rag_system()

    async def _execute_impl(self, query: str, limit: int = 5) -> Any:
        """Search the knowledge base"""
        await self._initialize()

        try:
            # Search for relevant chunks
            results = await self.rag_system.search(
                query=query,
                limit=limit,
                threshold=0.6
            )

            # Format results
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "content": result['content'][:500],  # Limit content length
                    "source": result['document_title'],
                    "similarity": round(result['similarity'], 3)
                })

            return {
                "query": query,
                "results": formatted_results,
                "count": len(formatted_results)
            }

        except Exception as e:
            logger.error(f"Knowledge search failed: {e}")
            raise


class DocumentIndexTool(BaseTool):
    """
    Tool for indexing documents into the knowledge base
    """

    def __init__(self):
        super().__init__(
            name="document_index",
            description="Index a document into the knowledge base",
            parameters={
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Document title"
                    },
                    "content": {
                        "type": "string",
                        "description": "Document content"
                    },
                    "source": {
                        "type": "string",
                        "description": "Document source/URL",
                        "default": "manual_input"
                    },
                    "metadata": {
                        "type": "object",
                        "description": "Additional metadata",
                        "default": {}
                    }
                },
                "required": ["title", "content"]
            },
            examples=[
                "document_index(title='Python Guide', content='Python is a programming language...')",
                "document_index(title='AI Research', content='Recent advances in AI...', source='research.pdf')"
            ]
        )
        self.rag_system = None

    async def _initialize(self):
        """Initialize RAG system if needed"""
        if not self.rag_system:
            self.rag_system = await get_rag_system()

    async def _execute_impl(
        self,
        title: str,
        content: str,
        source: str = "manual_input",
        metadata: Dict[str, Any] = None
    ) -> Any:
        """Index a document"""
        await self._initialize()

        try:
            # Index the document
            document = await self.rag_system.index_document(
                title=title,
                content=content,
                source=source,
                metadata=metadata or {}
            )

            return {
                "success": True,
                "document_id": document.id,
                "title": document.title,
                "chunks_created": len(document.chunk_ids) if document.chunk_ids else 0,
                "message": f"Document '{title}' indexed successfully"
            }

        except Exception as e:
            logger.error(f"Document indexing failed: {e}")
            raise


class RAGQueryTool(BaseTool):
    """
    Tool for retrieval-augmented generation
    Searches knowledge base and generates augmented response
    """

    def __init__(self):
        super().__init__(
            name="rag_query",
            description="Query the knowledge base with retrieval-augmented generation",
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Question or query"
                    },
                    "context_limit": {
                        "type": "integer",
                        "description": "Number of context chunks to retrieve",
                        "default": 3
                    }
                },
                "required": ["query"]
            },
            examples=[
                "rag_query(query='How does machine learning work?')",
                "rag_query(query='Explain Python decorators', context_limit=5)"
            ]
        )
        self.rag_system = None

    async def _initialize(self):
        """Initialize RAG system if needed"""
        if not self.rag_system:
            self.rag_system = await get_rag_system()

    async def _execute_impl(self, query: str, context_limit: int = 3) -> Any:
        """Execute RAG query"""
        await self._initialize()

        try:
            # Generate augmented response
            result = await self.rag_system.generate_augmented_response(
                query=query,
                context_limit=context_limit
            )

            # Format response
            return {
                "query": query,
                "context": result['context'][:2000] if result['context'] else None,
                "sources": result['sources'],
                "augmented_prompt": result['augmented_prompt'],
                "relevant_chunks": len(result['relevant_chunks']),
                "has_context": bool(result['context'])
            }

        except Exception as e:
            logger.error(f"RAG query failed: {e}")
            raise


class DocumentListTool(BaseTool):
    """
    Tool for listing documents in the knowledge base
    """

    def __init__(self):
        super().__init__(
            name="document_list",
            description="List documents in the knowledge base",
            parameters={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of documents to return",
                        "default": 10
                    }
                },
                "required": []
            },
            examples=[
                "document_list()",
                "document_list(limit=20)"
            ]
        )
        self.rag_system = None

    async def _initialize(self):
        """Initialize RAG system if needed"""
        if not self.rag_system:
            self.rag_system = await get_rag_system()

    async def _execute_impl(self, limit: int = 10) -> Any:
        """List documents"""
        await self._initialize()

        try:
            # Get documents
            documents = await self.rag_system.list_documents(limit=limit)

            return {
                "documents": documents,
                "count": len(documents),
                "limit": limit
            }

        except Exception as e:
            logger.error(f"Document listing failed: {e}")
            raise