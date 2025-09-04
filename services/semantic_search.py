"""
Semantic Search Engine for Cannabis Products
Multi-modal embeddings with hybrid search capabilities
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from enum import Enum
import numpy as np
from dataclasses import dataclass, asdict
import json
import re

from sentence_transformers import SentenceTransformer, CrossEncoder
from elasticsearch import AsyncElasticsearch
from elasticsearch.helpers import async_bulk
import spacy
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import torch

from services.knowledge_graph import KnowledgeGraphService

logger = logging.getLogger(__name__)

class SearchIntent(Enum):
    """Search query intent types"""
    MEDICAL = "medical"
    RECREATIONAL = "recreational"
    STRAIN_LOOKUP = "strain_lookup"
    EFFECT_BASED = "effect_based"
    PRICE_INQUIRY = "price_inquiry"
    BRAND_SEARCH = "brand_search"
    POTENCY_BASED = "potency_based"
    TERPENE_PROFILE = "terpene_profile"
    GENERAL = "general"

@dataclass
class SearchQuery:
    """Structured search query"""
    text: str
    intent: SearchIntent
    entities: Dict[str, List[str]]
    filters: Dict[str, Any]
    expanded_terms: List[str]
    embeddings: Optional[np.ndarray] = None

@dataclass
class SearchResult:
    """Search result with relevance scoring"""
    id: str
    name: str
    category: str
    description: str
    score: float
    match_type: str  # 'semantic', 'keyword', 'graph', 'hybrid'
    highlights: Dict[str, List[str]]
    metadata: Dict[str, Any]

class SemanticSearchEngine:
    """Advanced semantic search for cannabis products"""
    
    def __init__(
        self,
        es_host: str = "localhost",
        es_port: int = 9200,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        reranker_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
        graph_service: Optional[KnowledgeGraphService] = None
    ):
        """Initialize semantic search engine
        
        Args:
            es_host: Elasticsearch host
            es_port: Elasticsearch port
            model_name: Sentence transformer model name
            reranker_model: Cross-encoder reranker model
            graph_service: Knowledge graph service instance
        """
        self.es_host = es_host
        self.es_port = es_port
        self.model_name = model_name
        self.reranker_model_name = reranker_model
        
        self.es_client: Optional[AsyncElasticsearch] = None
        self.encoder: Optional[SentenceTransformer] = None
        self.reranker: Optional[CrossEncoder] = None
        self.nlp: Optional[spacy.Language] = None
        self.graph_service = graph_service
        
        # Cannabis-specific term expansions
        self.term_expansions = {
            'weed': ['cannabis', 'marijuana', 'flower', 'bud'],
            'high': ['euphoric', 'uplifted', 'energetic', 'buzz'],
            'chill': ['relaxed', 'calm', 'mellow', 'peaceful'],
            'pain': ['pain relief', 'analgesic', 'ache', 'discomfort'],
            'sleep': ['insomnia', 'sedative', 'nighttime', 'rest'],
            'anxiety': ['stress', 'anxious', 'nervous', 'worried'],
            'focus': ['concentration', 'clarity', 'alert', 'productive'],
            'creative': ['creativity', 'artistic', 'inspired', 'imaginative'],
            'hungry': ['munchies', 'appetite', 'hunger'],
            'indica': ['body high', 'couch lock', 'sedating', 'relaxing'],
            'sativa': ['head high', 'energizing', 'uplifting', 'cerebral'],
            'hybrid': ['balanced', 'mixed effects', 'combination']
        }
        
        # Intent patterns
        self.intent_patterns = {
            SearchIntent.MEDICAL: r'\b(medical|medicine|treat|relief|pain|anxiety|insomnia|nausea)\b',
            SearchIntent.RECREATIONAL: r'\b(party|fun|social|recreational|weekend|friends)\b',
            SearchIntent.STRAIN_LOOKUP: r'\b(strain|genetics|lineage|parent)\b',
            SearchIntent.EFFECT_BASED: r'\b(effect|feeling|high|buzz|experience)\b',
            SearchIntent.PRICE_INQUIRY: r'\b(price|cost|cheap|expensive|budget|affordable)\b',
            SearchIntent.BRAND_SEARCH: r'\b(brand|company|producer|grower)\b',
            SearchIntent.POTENCY_BASED: r'\b(thc|cbd|potent|strong|mild|percentage)\b',
            SearchIntent.TERPENE_PROFILE: r'\b(terpene|flavor|taste|aroma|smell|profile)\b'
        }
        
    async def initialize(self):
        """Initialize search engine components"""
        try:
            # Initialize Elasticsearch
            self.es_client = AsyncElasticsearch(
                [f"http://{self.es_host}:{self.es_port}"],
                verify_certs=False
            )
            
            # Create index if not exists
            await self._create_index()
            
            # Load models
            self.encoder = SentenceTransformer(self.model_name)
            self.reranker = CrossEncoder(self.reranker_model_name)
            
            # Load spaCy
            try:
                self.nlp = spacy.load("en_core_web_sm")
            except:
                logger.warning("spaCy model not found, downloading...")
                import subprocess
                subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"])
                self.nlp = spacy.load("en_core_web_sm")
            
            logger.info("Semantic search engine initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize search engine: {e}")
            raise
    
    async def _create_index(self):
        """Create Elasticsearch index with mapping"""
        index_name = "cannabis_products"
        
        mapping = {
            "mappings": {
                "properties": {
                    "id": {"type": "keyword"},
                    "name": {"type": "text", "analyzer": "english"},
                    "description": {"type": "text", "analyzer": "english"},
                    "category": {"type": "keyword"},
                    "strain": {"type": "keyword"},
                    "brand": {"type": "keyword"},
                    "thc_content": {"type": "float"},
                    "cbd_content": {"type": "float"},
                    "price": {"type": "float"},
                    "terpenes": {
                        "type": "nested",
                        "properties": {
                            "name": {"type": "keyword"},
                            "percentage": {"type": "float"}
                        }
                    },
                    "effects": {"type": "keyword"},
                    "flavors": {"type": "keyword"},
                    "aromas": {"type": "keyword"},
                    "embeddings": {
                        "type": "dense_vector",
                        "dims": 384,
                        "index": True,
                        "similarity": "cosine"
                    },
                    "created_at": {"type": "date"},
                    "updated_at": {"type": "date"}
                }
            },
            "settings": {
                "number_of_shards": 2,
                "number_of_replicas": 1,
                "analysis": {
                    "analyzer": {
                        "cannabis_analyzer": {
                            "type": "custom",
                            "tokenizer": "standard",
                            "filter": ["lowercase", "cannabis_synonyms", "stop"]
                        }
                    },
                    "filter": {
                        "cannabis_synonyms": {
                            "type": "synonym",
                            "synonyms": [
                                "weed,cannabis,marijuana",
                                "thc,delta9,tetrahydrocannabinol",
                                "cbd,cannabidiol",
                                "high,euphoric,buzz",
                                "relax,calm,chill"
                            ]
                        }
                    }
                }
            }
        }
        
        try:
            exists = await self.es_client.indices.exists(index=index_name)
            if not exists:
                await self.es_client.indices.create(index=index_name, body=mapping)
                logger.info(f"Created index: {index_name}")
        except Exception as e:
            logger.error(f"Failed to create index: {e}")
    
    async def index_product(self, product: Dict[str, Any]) -> bool:
        """Index product in Elasticsearch
        
        Args:
            product: Product data
            
        Returns:
            Success status
        """
        try:
            # Generate embeddings
            text = f"{product.get('name', '')} {product.get('description', '')} {' '.join(product.get('effects', []))}"
            embeddings = self.encoder.encode(text).tolist()
            
            # Prepare document
            doc = {
                **product,
                "embeddings": embeddings,
                "updated_at": datetime.utcnow().isoformat()
            }
            
            # Index document
            await self.es_client.index(
                index="cannabis_products",
                id=product['id'],
                body=doc
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to index product: {e}")
            return False
    
    async def bulk_index_products(self, products: List[Dict[str, Any]]) -> int:
        """Bulk index products
        
        Args:
            products: List of products
            
        Returns:
            Number of indexed products
        """
        actions = []
        
        for product in products:
            # Generate embeddings
            text = f"{product.get('name', '')} {product.get('description', '')} {' '.join(product.get('effects', []))}"
            embeddings = self.encoder.encode(text).tolist()
            
            action = {
                "_index": "cannabis_products",
                "_id": product['id'],
                "_source": {
                    **product,
                    "embeddings": embeddings,
                    "updated_at": datetime.utcnow().isoformat()
                }
            }
            actions.append(action)
        
        try:
            success, failed = await async_bulk(self.es_client, actions)
            logger.info(f"Indexed {success} products, {len(failed)} failed")
            return success
        except Exception as e:
            logger.error(f"Bulk indexing failed: {e}")
            return 0
    
    async def parse_query(self, query_text: str) -> SearchQuery:
        """Parse and understand search query
        
        Args:
            query_text: Raw query text
            
        Returns:
            Structured search query
        """
        # Detect intent
        intent = self._detect_intent(query_text)
        
        # Extract entities
        entities = self._extract_entities(query_text)
        
        # Build filters
        filters = self._build_filters(entities)
        
        # Expand query terms
        expanded_terms = self._expand_query(query_text)
        
        # Generate embeddings
        embeddings = self.encoder.encode(query_text)
        
        return SearchQuery(
            text=query_text,
            intent=intent,
            entities=entities,
            filters=filters,
            expanded_terms=expanded_terms,
            embeddings=embeddings
        )
    
    def _detect_intent(self, text: str) -> SearchIntent:
        """Detect search intent from query text"""
        text_lower = text.lower()
        
        for intent, pattern in self.intent_patterns.items():
            if re.search(pattern, text_lower):
                return intent
        
        return SearchIntent.GENERAL
    
    def _extract_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract named entities from query"""
        doc = self.nlp(text)
        entities = {
            'strains': [],
            'brands': [],
            'effects': [],
            'conditions': [],
            'terpenes': [],
            'numbers': []
        }
        
        for ent in doc.ents:
            if ent.label_ in ['ORG', 'PRODUCT']:
                entities['brands'].append(ent.text)
            elif ent.label_ in ['CARDINAL', 'PERCENT']:
                entities['numbers'].append(ent.text)
        
        # Extract cannabis-specific entities
        cannabis_effects = ['relaxed', 'happy', 'euphoric', 'uplifted', 'creative', 'energetic', 'focused', 'sleepy']
        for effect in cannabis_effects:
            if effect in text.lower():
                entities['effects'].append(effect)
        
        return entities
    
    def _build_filters(self, entities: Dict[str, List[str]]) -> Dict[str, Any]:
        """Build Elasticsearch filters from entities"""
        filters = {}
        
        if entities['brands']:
            filters['brand'] = entities['brands']
        
        if entities['effects']:
            filters['effects'] = entities['effects']
        
        # Parse THC/CBD percentages from numbers
        for num in entities['numbers']:
            try:
                value = float(num.replace('%', ''))
                if 'thc' in entities.get('text', '').lower():
                    filters['thc_min'] = value
                elif 'cbd' in entities.get('text', '').lower():
                    filters['cbd_min'] = value
            except:
                pass
        
        return filters
    
    def _expand_query(self, text: str) -> List[str]:
        """Expand query with synonyms and related terms"""
        expanded = [text]
        text_lower = text.lower()
        
        for term, expansions in self.term_expansions.items():
            if term in text_lower:
                for expansion in expansions:
                    expanded.append(text_lower.replace(term, expansion))
        
        return list(set(expanded))
    
    async def search(
        self,
        query: str,
        limit: int = 20,
        filters: Optional[Dict[str, Any]] = None,
        use_graph: bool = True
    ) -> List[SearchResult]:
        """Execute hybrid search
        
        Args:
            query: Search query text
            limit: Maximum results
            filters: Additional filters
            use_graph: Whether to use graph traversal
            
        Returns:
            Ranked search results
        """
        # Parse query
        search_query = await self.parse_query(query)
        
        # Merge filters
        if filters:
            search_query.filters.update(filters)
        
        # Execute parallel searches
        results = await asyncio.gather(
            self._semantic_search(search_query, limit * 2),
            self._keyword_search(search_query, limit * 2),
            self._graph_search(search_query, limit) if use_graph and self.graph_service else asyncio.sleep(0)
        )
        
        # Combine results
        semantic_results, keyword_results, graph_results = results
        combined = self._combine_results(
            semantic_results or [],
            keyword_results or [],
            graph_results or [] if use_graph else []
        )
        
        # Rerank if we have results
        if combined:
            reranked = await self._rerank_results(query, combined[:limit * 2])
            return reranked[:limit]
        
        return []
    
    async def _semantic_search(
        self,
        query: SearchQuery,
        limit: int
    ) -> List[SearchResult]:
        """Execute semantic vector search"""
        try:
            # Build query
            es_query = {
                "knn": {
                    "field": "embeddings",
                    "query_vector": query.embeddings.tolist(),
                    "k": limit,
                    "num_candidates": limit * 2
                }
            }
            
            # Add filters
            if query.filters:
                filter_clauses = []
                for field, value in query.filters.items():
                    if isinstance(value, list):
                        filter_clauses.append({"terms": {field: value}})
                    else:
                        filter_clauses.append({"term": {field: value}})
                
                es_query["filter"] = {"bool": {"must": filter_clauses}}
            
            # Execute search
            response = await self.es_client.search(
                index="cannabis_products",
                body={"query": es_query, "size": limit}
            )
            
            # Parse results
            results = []
            for hit in response['hits']['hits']:
                source = hit['_source']
                results.append(SearchResult(
                    id=source['id'],
                    name=source['name'],
                    category=source.get('category', ''),
                    description=source.get('description', ''),
                    score=hit['_score'],
                    match_type='semantic',
                    highlights={},
                    metadata=source
                ))
            
            return results
            
        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            return []
    
    async def _keyword_search(
        self,
        query: SearchQuery,
        limit: int
    ) -> List[SearchResult]:
        """Execute keyword-based search"""
        try:
            # Build multi-match query
            should_clauses = []
            
            # Search in multiple fields with different boosts
            for term in query.expanded_terms:
                should_clauses.extend([
                    {"match": {"name": {"query": term, "boost": 3}}},
                    {"match": {"description": {"query": term, "boost": 1}}},
                    {"match": {"effects": {"query": term, "boost": 2}}},
                    {"match": {"strain": {"query": term, "boost": 2}}}
                ])
            
            es_query = {
                "bool": {
                    "should": should_clauses,
                    "minimum_should_match": 1
                }
            }
            
            # Add filters
            if query.filters:
                must_clauses = []
                for field, value in query.filters.items():
                    if isinstance(value, list):
                        must_clauses.append({"terms": {field: value}})
                    else:
                        must_clauses.append({"term": {field: value}})
                es_query["bool"]["must"] = must_clauses
            
            # Execute search
            response = await self.es_client.search(
                index="cannabis_products",
                body={
                    "query": es_query,
                    "size": limit,
                    "highlight": {
                        "fields": {
                            "name": {},
                            "description": {}
                        }
                    }
                }
            )
            
            # Parse results
            results = []
            for hit in response['hits']['hits']:
                source = hit['_source']
                highlights = hit.get('highlight', {})
                
                results.append(SearchResult(
                    id=source['id'],
                    name=source['name'],
                    category=source.get('category', ''),
                    description=source.get('description', ''),
                    score=hit['_score'],
                    match_type='keyword',
                    highlights=highlights,
                    metadata=source
                ))
            
            return results
            
        except Exception as e:
            logger.error(f"Keyword search failed: {e}")
            return []
    
    async def _graph_search(
        self,
        query: SearchQuery,
        limit: int
    ) -> List[SearchResult]:
        """Execute graph-based search"""
        if not self.graph_service:
            return []
        
        try:
            results = []
            
            # Search based on intent
            if query.intent == SearchIntent.MEDICAL and query.entities.get('conditions'):
                for condition in query.entities['conditions']:
                    products = await self.graph_service.recommend_products_for_condition(
                        condition, limit
                    )
                    for product in products:
                        results.append(SearchResult(
                            id=product['id'],
                            name=product['name'],
                            category=product.get('category', ''),
                            description='',
                            score=product.get('relevance', 1.0),
                            match_type='graph',
                            highlights={},
                            metadata=product
                        ))
            
            elif query.intent == SearchIntent.EFFECT_BASED and query.entities.get('effects'):
                # Find products with similar effects
                cypher = """
                MATCH (e:Effect)
                WHERE e.name IN $effects
                MATCH (p:Product)-[:HAS_EFFECT]->(e)
                RETURN p.id as id, p.name as name, p.category as category,
                       COUNT(e) as match_count
                ORDER BY match_count DESC
                LIMIT $limit
                """
                products = await self.graph_service.execute_cypher(
                    cypher,
                    {'effects': query.entities['effects'], 'limit': limit}
                )
                
                for product in products:
                    results.append(SearchResult(
                        id=product['id'],
                        name=product['name'],
                        category=product.get('category', ''),
                        description='',
                        score=product.get('match_count', 1.0),
                        match_type='graph',
                        highlights={},
                        metadata=product
                    ))
            
            return results[:limit]
            
        except Exception as e:
            logger.error(f"Graph search failed: {e}")
            return []
    
    def _combine_results(
        self,
        semantic: List[SearchResult],
        keyword: List[SearchResult],
        graph: List[SearchResult]
    ) -> List[SearchResult]:
        """Combine results from different search methods"""
        # Score normalization weights
        weights = {
            'semantic': 0.4,
            'keyword': 0.3,
            'graph': 0.3
        }
        
        # Collect all unique results
        results_map = {}
        
        for result in semantic:
            if result.id not in results_map:
                results_map[result.id] = result
                result.score *= weights['semantic']
            else:
                results_map[result.id].score += result.score * weights['semantic']
        
        for result in keyword:
            if result.id not in results_map:
                results_map[result.id] = result
                result.score *= weights['keyword']
            else:
                results_map[result.id].score += result.score * weights['keyword']
                # Merge highlights
                results_map[result.id].highlights.update(result.highlights)
        
        for result in graph:
            if result.id not in results_map:
                results_map[result.id] = result
                result.score *= weights['graph']
            else:
                results_map[result.id].score += result.score * weights['graph']
        
        # Sort by combined score
        combined = list(results_map.values())
        combined.sort(key=lambda x: x.score, reverse=True)
        
        return combined
    
    async def _rerank_results(
        self,
        query: str,
        results: List[SearchResult]
    ) -> List[SearchResult]:
        """Rerank results using cross-encoder"""
        if not results or not self.reranker:
            return results
        
        try:
            # Prepare pairs for reranking
            pairs = []
            for result in results:
                text = f"{result.name} {result.description}"
                pairs.append([query, text])
            
            # Get reranking scores
            scores = self.reranker.predict(pairs)
            
            # Update scores and resort
            for i, result in enumerate(results):
                result.score = float(scores[i])
            
            results.sort(key=lambda x: x.score, reverse=True)
            
            return results
            
        except Exception as e:
            logger.error(f"Reranking failed: {e}")
            return results
    
    async def get_facets(self, query: str = "") -> Dict[str, List[Dict[str, Any]]]:
        """Get search facets for filtering
        
        Args:
            query: Optional query to filter facets
            
        Returns:
            Facet counts by field
        """
        try:
            aggs = {
                "categories": {"terms": {"field": "category", "size": 20}},
                "brands": {"terms": {"field": "brand", "size": 50}},
                "effects": {"terms": {"field": "effects", "size": 30}},
                "price_ranges": {
                    "range": {
                        "field": "price",
                        "ranges": [
                            {"to": 20},
                            {"from": 20, "to": 50},
                            {"from": 50, "to": 100},
                            {"from": 100}
                        ]
                    }
                },
                "thc_ranges": {
                    "range": {
                        "field": "thc_content",
                        "ranges": [
                            {"to": 10},
                            {"from": 10, "to": 20},
                            {"from": 20, "to": 30},
                            {"from": 30}
                        ]
                    }
                }
            }
            
            # Add query if provided
            body = {"aggs": aggs, "size": 0}
            if query:
                body["query"] = {"match": {"_all": query}}
            
            response = await self.es_client.search(
                index="cannabis_products",
                body=body
            )
            
            # Parse aggregations
            facets = {}
            for key, agg in response['aggregations'].items():
                if 'buckets' in agg:
                    facets[key] = [
                        {"value": bucket.get('key'), "count": bucket.get('doc_count')}
                        for bucket in agg['buckets']
                    ]
            
            return facets
            
        except Exception as e:
            logger.error(f"Failed to get facets: {e}")
            return {}