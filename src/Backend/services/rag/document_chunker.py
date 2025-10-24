"""
Document Chunking Pipeline
Semantic chunking with overlap and context preservation
"""

import re
import logging
from typing import List, Dict, Any, Optional
import nltk
from nltk.tokenize import sent_tokenize

logger = logging.getLogger(__name__)

# Download NLTK data on first import
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)


class DocumentChunker:
    """
    Smart document chunking with semantic awareness
    Preserves context boundaries and maintains coherence
    """
    
    def __init__(
        self,
        chunk_size: int = 512,
        chunk_overlap: int = 100,
        min_chunk_size: int = 50
    ):
        """
        Initialize document chunker
        
        Args:
            chunk_size: Target chunk size in tokens (approximate)
            chunk_overlap: Overlap between chunks for context
            min_chunk_size: Minimum chunk size to keep
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size
    
    def chunk_document(
        self,
        text: str,
        metadata: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """
        Chunk document into semantically coherent pieces
        
        Args:
            text: Document text to chunk
            metadata: Optional metadata to attach to chunks
            
        Returns:
            List of chunk dictionaries
        """
        if not text or len(text.strip()) == 0:
            return []
        
        # Clean text
        text = self._clean_text(text)
        
        # Split into sentences
        sentences = sent_tokenize(text)
        
        # Build chunks
        chunks = []
        current_chunk = []
        current_length = 0
        
        for sentence in sentences:
            sentence_length = len(sentence.split())
            
            # If adding this sentence exceeds chunk size
            if current_length + sentence_length > self.chunk_size and current_chunk:
                # Save current chunk
                chunk_text = " ".join(current_chunk)
                if len(chunk_text.split()) >= self.min_chunk_size:
                    chunks.append({
                        "text": chunk_text,
                        "metadata": metadata or {}
                    })
                
                # Start new chunk with overlap
                overlap_sentences = self._get_overlap_sentences(
                    current_chunk,
                    self.chunk_overlap
                )
                current_chunk = overlap_sentences
                current_length = sum(len(s.split()) for s in current_chunk)
            
            # Add sentence to current chunk
            current_chunk.append(sentence)
            current_length += sentence_length
        
        # Add final chunk
        if current_chunk:
            chunk_text = " ".join(current_chunk)
            if len(chunk_text.split()) >= self.min_chunk_size:
                chunks.append({
                    "text": chunk_text,
                    "metadata": metadata or {}
                })
        
        logger.info(f"Chunked document into {len(chunks)} chunks")
        return chunks
    
    def chunk_structured_data(
        self,
        data: Dict[str, Any],
        title: str,
        important_fields: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Chunk structured data (like OCS product catalog)
        Creates focused chunks around important fields
        
        Args:
            data: Structured data dictionary (e.g., product row)
            title: Title for the chunks (e.g., product name)
            important_fields: Fields to emphasize in chunking
            
        Returns:
            List of chunk dictionaries
        """
        chunks = []
        
        # Create main overview chunk
        overview_parts = [f"**{title}**"]
        
        # Add important fields first
        if important_fields:
            for field in important_fields:
                if field in data and data[field]:
                    value = data[field]
                    field_name = field.replace('_', ' ').title()
                    overview_parts.append(f"{field_name}: {value}")
        
        overview_text = "\n".join(overview_parts)
        chunks.append({
            "text": overview_text,
            "metadata": {
                "chunk_type": "overview",
                "source_fields": important_fields or []
            }
        })
        
        # Create detailed chunks for specific categories
        # Group related fields together
        field_groups = {
            "effects": ["effects", "medical_effects", "side_effects"],
            "potency": ["thc_min", "thc_max", "cbd_min", "cbd_max", "terpenes"],
            "details": ["strain_type", "genetics", "flavour_profile", "aroma"],
            "info": ["description", "producer", "brand", "category"]
        }
        
        for group_name, fields in field_groups.items():
            group_parts = [f"**{title} - {group_name.title()}**"]
            has_content = False
            
            for field in fields:
                if field in data and data[field]:
                    value = data[field]
                    field_name = field.replace('_', ' ').title()
                    group_parts.append(f"{field_name}: {value}")
                    has_content = True
            
            if has_content:
                group_text = "\n".join(group_parts)
                chunks.append({
                    "text": group_text,
                    "metadata": {
                        "chunk_type": group_name,
                        "source_fields": fields
                    }
                })
        
        return chunks
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        # Remove multiple spaces
        text = re.sub(r'\s+', ' ', text)
        
        # Remove multiple newlines (keep paragraph breaks)
        text = re.sub(r'\n\s*\n+', '\n\n', text)
        
        # Strip leading/trailing whitespace
        text = text.strip()
        
        return text
    
    def _get_overlap_sentences(
        self,
        sentences: List[str],
        overlap_tokens: int
    ) -> List[str]:
        """
        Get last N tokens worth of sentences for overlap
        
        Args:
            sentences: List of sentences
            overlap_tokens: Target overlap in tokens
            
        Returns:
            List of sentences for overlap
        """
        overlap_sents = []
        token_count = 0
        
        # Work backwards from end
        for sent in reversed(sentences):
            sent_tokens = len(sent.split())
            if token_count + sent_tokens > overlap_tokens:
                break
            overlap_sents.insert(0, sent)
            token_count += sent_tokens
        
        return overlap_sents


# Singleton instance
_document_chunker = None

def get_document_chunker() -> DocumentChunker:
    """Get or create document chunker singleton"""
    global _document_chunker
    if _document_chunker is None:
        _document_chunker = DocumentChunker()
    return _document_chunker

