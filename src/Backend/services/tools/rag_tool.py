"""
RAG Tool for Agent System
Provides knowledge base search for AI agents
Portable version using SQLite + FAISS
"""

import logging
from typing import Dict, Any, List, Optional
from services.rag.portable_rag_service import get_portable_rag_service

logger = logging.getLogger(__name__)


class RAGTool:
    """
    RAG knowledge search tool for agents
    Retrieves factual information from knowledge base
    """
    
    def __init__(self):
        self.rag_service = None
        self.initialized = False
    
    async def initialize(self, data_dir: str = "data/rag"):
        """
        Initialize portable RAG service
        
        Args:
            data_dir: Directory for SQLite and FAISS data
        """
        if not self.initialized:
            self.rag_service = await get_portable_rag_service(data_dir=data_dir)
            self.initialized = True
            logger.info("✅ Portable RAG Tool initialized")
    
    async def search_knowledge(
        self,
        query: str,
        agent_id: str,
        tenant_id: Optional[str] = None,
        store_id: Optional[str] = None,
        top_k: int = 5,
        min_similarity: float = 0.3
    ) -> Dict[str, Any]:
        """
        Search knowledge base for relevant information
        
        Args:
            query: Search query (user question or context)
            agent_id: Agent identifier for access control
            tenant_id: Optional tenant ID for filtering
            store_id: Optional store ID for filtering
            top_k: Number of results to return
            min_similarity: Minimum similarity threshold (0-1)
            
        Returns:
            Dictionary with results and metadata
        """
        if not self.initialized:
            raise RuntimeError("RAG Tool not initialized. Call initialize() first.")
        
        try:
            # Retrieve from knowledge base
            results = await self.rag_service.retrieve(
                query=query,
                agent_id=agent_id,
                tenant_id=tenant_id,
                store_id=store_id,
                top_k=top_k
            )
            
            # Filter by minimum similarity
            filtered_results = [
                r for r in results 
                if r.get("similarity_score", r.get("similarity", 0)) >= min_similarity
            ]
            
            # Build response
            if not filtered_results:
                return {
                    "success": False,
                    "results": [],
                    "message": "No relevant information found",
                    "confidence": 0.0
                }
            
            # Format results for agent consumption
            formatted_results = []
            for result in filtered_results:
                formatted_results.append({
                    "text": result.get("content", result.get("text", "")),
                    "similarity": result.get("similarity_score", result.get("similarity", 0.0)),
                    "source": result.get("document_type", "unknown"),
                    "metadata": {
                        "category": result.get("metadata", {}).get("category"),
                        "question": result.get("metadata", {}).get("question"),
                        "product_name": result.get("metadata", {}).get("product_name"),
                        "chunk_type": result.get("metadata", {}).get("chunk_type")
                    }
                })
            
            # Calculate confidence
            avg_similarity = sum(
                r.get("similarity_score", r.get("similarity", 0)) for r in filtered_results
            ) / len(filtered_results)
            confidence = min(avg_similarity * 1.2, 1.0)  # Boost slightly, cap at 1.0
            
            return {
                "success": True,
                "results": formatted_results,
                "count": len(formatted_results),
                "confidence": confidence,
                "message": f"Found {len(filtered_results)} relevant results"
            }
            
        except Exception as e:
            logger.error(f"Error searching knowledge base: {e}", exc_info=True)
            return {
                "success": False,
                "results": [],
                "message": f"Error searching knowledge: {str(e)}",
                "confidence": 0.0
            }
    
    async def get_product_info(
        self,
        product_query: str,
        tenant_id: str,
        store_id: Optional[str] = None,
        top_k: int = 5
    ) -> Dict[str, Any]:
        """
        Specialized search for product information
        
        Args:
            product_query: Product search query
            tenant_id: Tenant ID
            store_id: Optional store ID
            top_k: Number of products to return
            
        Returns:
            Product information results
        """
        if not self.initialized:
            raise RuntimeError("RAG Tool not initialized")
        
        try:
            results = await self.rag_service.retrieve(
                query=product_query,
                agent_id="dispensary",  # Product access
                tenant_id=tenant_id,
                store_id=store_id,
                document_types=["ocs_product"],  # Only products
                top_k=top_k
            )
            
            return {
                "success": True,
                "products": results,
                "count": len(results)
            }
            
        except Exception as e:
            logger.error(f"Error getting product info: {e}")
            return {
                "success": False,
                "products": [],
                "error": str(e)
            }
    
    def get_tool_definition(self) -> Dict[str, Any]:
        """
        Get tool definition for agent system
        
        Returns:
            Tool definition dictionary
        """
        return {
            "name": "search_knowledge",
            "description": (
                "Search the knowledge base for factual information about cannabis products, "
                "compliance rules, platform features, and FAQs. Use this when you need "
                "accurate information about strains, effects, THC/CBD content, legal requirements, "
                "or any factual questions."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query or question to find information about"
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "Number of results to return (default: 5)",
                        "default": 5
                    }
                },
                "required": ["query"]
            }
        }


# Singleton instance
_rag_tool_instance = None


async def get_rag_tool(data_dir: str = "data/rag") -> RAGTool:
    """
    Get or create RAG tool singleton instance (portable version)
    
    Args:
        data_dir: Directory for SQLite and FAISS data (default: data/rag)
    
    Returns:
        RAGTool instance
    """
    global _rag_tool_instance
    
    if _rag_tool_instance is None:
        _rag_tool_instance = RAGTool()
        await _rag_tool_instance.initialize(data_dir=data_dir)
    
    return _rag_tool_instance
