"""
FAQ Ingestion Service
Loads FAQ documents into RAG knowledge base
"""

import os
import logging
from typing import List, Dict, Any, Optional
import re
import asyncpg
from services.rag.rag_service import get_rag_service
from services.rag.document_chunker import DocumentChunker

logger = logging.getLogger(__name__)


class FAQIngestionService:
    """
    Ingests FAQ markdown documents into RAG knowledge base
    """
    
    def __init__(self, db_pool: asyncpg.Pool):
        """
        Initialize FAQ ingestion service
        
        Args:
            db_pool: PostgreSQL connection pool
        """
        self.db_pool = db_pool
        self.rag_service = None
        self.chunker = DocumentChunker(
            chunk_size=512,
            chunk_overlap=50  # Less overlap for FAQs
        )
    
    async def initialize(self):
        """Initialize RAG service"""
        self.rag_service = await get_rag_service()
        await self.rag_service.initialize()
        logger.info("FAQ Ingestion Service initialized")
    
    async def ingest_faq_file(
        self,
        file_path: str,
        access_level: str = "public",
        tenant_id: Optional[str] = None,
        store_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Ingest FAQ markdown file into knowledge base
        
        Args:
            file_path: Path to FAQ markdown file
            access_level: Access level (public, customer, platform, internal)
            tenant_id: Optional tenant ID for tenant-specific FAQs
            store_id: Optional store ID for store-specific FAQs
            
        Returns:
            Ingestion results
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"FAQ file not found: {file_path}")
        
        # Read file
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse FAQ sections
        sections = self._parse_faq_sections(content)
        
        logger.info(f"Parsed {len(sections)} sections from {file_path}")
        
        # Ingest each section
        ingested_count = 0
        for section in sections:
            try:
                await self._ingest_faq_section(
                    section,
                    access_level,
                    tenant_id,
                    store_id,
                    file_path
                )
                ingested_count += 1
            except Exception as e:
                logger.error(f"Error ingesting FAQ section '{section.get('title')}': {e}")
        
        return {
            "file": file_path,
            "total_sections": len(sections),
            "ingested": ingested_count,
            "status": "success" if ingested_count == len(sections) else "partial"
        }
    
    async def ingest_all_faqs(
        self,
        faq_directory: str,
        access_level: str = "public"
    ) -> List[Dict[str, Any]]:
        """
        Ingest all FAQ files from directory
        
        Args:
            faq_directory: Directory containing FAQ markdown files
            access_level: Access level for FAQs
            
        Returns:
            List of ingestion results
        """
        if not os.path.isdir(faq_directory):
            raise NotADirectoryError(f"FAQ directory not found: {faq_directory}")
        
        results = []
        
        for filename in os.listdir(faq_directory):
            if filename.endswith('.md'):
                file_path = os.path.join(faq_directory, filename)
                try:
                    result = await self.ingest_faq_file(
                        file_path,
                        access_level
                    )
                    results.append(result)
                except Exception as e:
                    logger.error(f"Error ingesting FAQ file {filename}: {e}")
                    results.append({
                        "file": file_path,
                        "status": "error",
                        "error": str(e)
                    })
        
        return results
    
    def _parse_faq_sections(self, content: str) -> List[Dict[str, Any]]:
        """
        Parse FAQ markdown into sections
        
        Args:
            content: Markdown content
            
        Returns:
            List of FAQ sections
        """
        sections = []
        current_category = None
        current_qa = None
        
        lines = content.split('\n')
        
        for line in lines:
            # H2 headers are categories
            if line.startswith('## '):
                current_category = line[3:].strip()
                continue
            
            # H3 headers are questions
            if line.startswith('### '):
                # Save previous Q&A if exists
                if current_qa and current_qa.get('answer'):
                    sections.append(current_qa)
                
                # Start new Q&A
                question = line[4:].strip()
                current_qa = {
                    "category": current_category or "General",
                    "question": question,
                    "answer": "",
                    "title": f"{current_category}: {question}" if current_category else question
                }
            
            # Content lines are answers
            elif line.strip() and current_qa is not None:
                if current_qa.get('answer'):
                    current_qa['answer'] += '\n' + line
                else:
                    current_qa['answer'] = line
        
        # Don't forget last Q&A
        if current_qa and current_qa.get('answer'):
            sections.append(current_qa)
        
        return sections
    
    async def _ingest_faq_section(
        self,
        section: Dict[str, Any],
        access_level: str,
        tenant_id: Optional[str],
        store_id: Optional[str],
        source_file: str
    ):
        """
        Ingest single FAQ section
        
        Args:
            section: FAQ section dictionary
            access_level: Access level
            tenant_id: Optional tenant ID
            store_id: Optional store ID
            source_file: Source file path
        """
        # Build full text
        text = f"**{section['question']}**\n\n{section['answer']}"
        
        # Build metadata
        metadata = {
            "category": section.get("category", "General"),
            "question": section["question"],
            "source": "faq",
            "source_file": os.path.basename(source_file)
        }
        
        # Add to RAG
        await self.rag_service.add_document(
            text=text,
            metadata=metadata,
            document_type="faq",
            tenant_id=tenant_id,
            store_id=store_id,
            source_table="faq_knowledge_base",
            source_id=f"{section['category']}_{section['question'][:50]}",
            access_level=access_level
        )


async def get_faq_ingestion_service(
    db_pool: Optional[asyncpg.Pool] = None
) -> FAQIngestionService:
    """
    Get FAQ ingestion service instance
    
    Args:
        db_pool: PostgreSQL connection pool
        
    Returns:
        FAQIngestionService instance
    """
    service = FAQIngestionService(db_pool)
    await service.initialize()
    return service
