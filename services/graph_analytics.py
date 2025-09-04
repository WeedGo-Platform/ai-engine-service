"""
Graph Analytics Service for Cannabis Knowledge Graph
Implements PageRank, community detection, and recommendation algorithms
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Set, Tuple
from datetime import datetime
from enum import Enum
import numpy as np
import networkx as nx
from community import community_louvain
from scipy import sparse
from scipy.spatial.distance import cosine
from collections import defaultdict, Counter
import json

from services.knowledge_graph import KnowledgeGraphService, EntityType, RelationshipType

logger = logging.getLogger(__name__)

class AnalyticsMetric(Enum):
    """Analytics metric types"""
    PAGERANK = "pagerank"
    BETWEENNESS = "betweenness_centrality"
    CLOSENESS = "closeness_centrality"
    DEGREE = "degree_centrality"
    EIGENVECTOR = "eigenvector_centrality"
    CLUSTERING = "clustering_coefficient"

class RecommendationStrategy(Enum):
    """Recommendation algorithm strategies"""
    COLLABORATIVE = "collaborative"
    CONTENT_BASED = "content_based"
    HYBRID = "hybrid"
    GRAPH_BASED = "graph_based"
    KNOWLEDGE_BASED = "knowledge_based"

class GraphAnalyticsService:
    """Advanced graph analytics for cannabis products"""
    
    def __init__(self, graph_service: KnowledgeGraphService):
        """Initialize graph analytics service
        
        Args:
            graph_service: Knowledge graph service instance
        """
        self.graph_service = graph_service
        self._graph_cache = {}
        self._analytics_cache = {}
        self._community_cache = {}
        
    async def calculate_pagerank(
        self,
        entity_type: Optional[EntityType] = None,
        damping: float = 0.85,
        max_iter: int = 100
    ) -> Dict[str, float]:
        """Calculate PageRank scores for entities
        
        Args:
            entity_type: Optional filter by entity type
            damping: Damping factor
            max_iter: Maximum iterations
            
        Returns:
            PageRank scores by entity ID
        """
        try:
            # Build query based on entity type
            if entity_type:
                query = f"""
                MATCH (n:{entity_type.value})-[r]->(m:{entity_type.value})
                RETURN n.id as source, m.id as target, type(r) as rel_type
                """
            else:
                query = """
                MATCH (n)-[r]->(m)
                WHERE n.id IS NOT NULL AND m.id IS NOT NULL
                RETURN n.id as source, m.id as target, type(r) as rel_type
                """
            
            # Get graph data
            results = await self.graph_service.execute_cypher(query)
            
            # Build NetworkX graph
            G = nx.DiGraph()
            for record in results:
                G.add_edge(
                    record['source'],
                    record['target'],
                    type=record['rel_type']
                )
            
            # Calculate PageRank
            if G.number_of_nodes() > 0:
                pagerank = nx.pagerank(G, alpha=damping, max_iter=max_iter)
                
                # Cache results
                cache_key = f"pagerank_{entity_type}_{damping}"
                self._analytics_cache[cache_key] = {
                    'scores': pagerank,
                    'timestamp': datetime.utcnow()
                }
                
                return pagerank
            
            return {}
            
        except Exception as e:
            logger.error(f"Failed to calculate PageRank: {e}")
            return {}
    
    async def detect_communities(
        self,
        algorithm: str = "louvain",
        resolution: float = 1.0
    ) -> Dict[str, int]:
        """Detect communities in the graph
        
        Args:
            algorithm: Community detection algorithm
            resolution: Resolution parameter for modularity
            
        Returns:
            Community assignments by entity ID
        """
        try:
            # Get undirected graph
            query = """
            MATCH (n)-[r]-(m)
            WHERE n.id IS NOT NULL AND m.id IS NOT NULL
            RETURN DISTINCT n.id as source, m.id as target
            """
            
            results = await self.graph_service.execute_cypher(query)
            
            # Build NetworkX graph
            G = nx.Graph()
            for record in results:
                G.add_edge(record['source'], record['target'])
            
            if G.number_of_nodes() == 0:
                return {}
            
            # Detect communities
            if algorithm == "louvain":
                communities = community_louvain.best_partition(G, resolution=resolution)
            else:
                # Use label propagation as alternative
                communities_gen = nx.community.label_propagation_communities(G)
                communities = {}
                for i, comm in enumerate(communities_gen):
                    for node in comm:
                        communities[node] = i
            
            # Cache results
            self._community_cache = {
                'communities': communities,
                'algorithm': algorithm,
                'timestamp': datetime.utcnow()
            }
            
            return communities
            
        except Exception as e:
            logger.error(f"Failed to detect communities: {e}")
            return {}
    
    async def find_strain_families(self) -> Dict[str, List[str]]:
        """Identify strain families based on genetics and effects
        
        Returns:
            Strain families with member strains
        """
        try:
            # Get strain relationships
            query = """
            MATCH (s1:Strain)-[:PARENT_OF|SIMILAR_TO]-(s2:Strain)
            RETURN s1.id as strain1, s2.id as strain2
            UNION
            MATCH (s1:Strain)-[:HAS_EFFECT]->(e:Effect)<-[:HAS_EFFECT]-(s2:Strain)
            WHERE s1 <> s2
            WITH s1, s2, COUNT(e) as common_effects
            WHERE common_effects >= 3
            RETURN s1.id as strain1, s2.id as strain2
            """
            
            results = await self.graph_service.execute_cypher(query)
            
            # Build graph
            G = nx.Graph()
            for record in results:
                G.add_edge(record['strain1'], record['strain2'])
            
            # Find connected components as families
            families = {}
            for i, component in enumerate(nx.connected_components(G)):
                family_name = f"family_{i}"
                families[family_name] = list(component)
            
            # Get dominant strain for each family (highest degree)
            for family_name, members in families.items():
                if members:
                    subgraph = G.subgraph(members)
                    degrees = dict(subgraph.degree())
                    dominant = max(degrees, key=degrees.get)
                    
                    # Try to get actual strain name
                    name_query = """
                    MATCH (s:Strain {id: $strain_id})
                    RETURN s.name as name
                    """
                    result = await self.graph_service.execute_cypher(
                        name_query,
                        {'strain_id': dominant}
                    )
                    if result and result[0].get('name'):
                        families[f"{result[0]['name']}_family"] = families.pop(family_name)
            
            return families
            
        except Exception as e:
            logger.error(f"Failed to find strain families: {e}")
            return {}
    
    async def calculate_similarity_paths(
        self,
        source_id: str,
        target_id: str,
        max_length: int = 4
    ) -> List[List[str]]:
        """Find similarity paths between two products
        
        Args:
            source_id: Source product ID
            target_id: Target product ID
            max_length: Maximum path length
            
        Returns:
            List of paths between products
        """
        try:
            query = """
            MATCH path = shortestPath(
                (source {id: $source_id})-[*1..$max_length]-(target {id: $target_id})
            )
            RETURN [node in nodes(path) | node.id] as path
            LIMIT 10
            """
            
            results = await self.graph_service.execute_cypher(
                query,
                {
                    'source_id': source_id,
                    'target_id': target_id,
                    'max_length': max_length
                }
            )
            
            paths = [record['path'] for record in results]
            return paths
            
        except Exception as e:
            logger.error(f"Failed to find similarity paths: {e}")
            return []
    
    async def recommend_products(
        self,
        user_preferences: Dict[str, Any],
        strategy: RecommendationStrategy = RecommendationStrategy.HYBRID,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Generate product recommendations
        
        Args:
            user_preferences: User preference data
            strategy: Recommendation strategy
            limit: Number of recommendations
            
        Returns:
            List of recommended products with scores
        """
        try:
            if strategy == RecommendationStrategy.GRAPH_BASED:
                return await self._graph_based_recommendations(user_preferences, limit)
            elif strategy == RecommendationStrategy.CONTENT_BASED:
                return await self._content_based_recommendations(user_preferences, limit)
            elif strategy == RecommendationStrategy.COLLABORATIVE:
                return await self._collaborative_recommendations(user_preferences, limit)
            elif strategy == RecommendationStrategy.KNOWLEDGE_BASED:
                return await self._knowledge_based_recommendations(user_preferences, limit)
            else:  # HYBRID
                # Combine multiple strategies
                graph_recs = await self._graph_based_recommendations(user_preferences, limit * 2)
                content_recs = await self._content_based_recommendations(user_preferences, limit * 2)
                
                # Merge and score
                combined = self._merge_recommendations([graph_recs, content_recs])
                return combined[:limit]
                
        except Exception as e:
            logger.error(f"Failed to generate recommendations: {e}")
            return []
    
    async def _graph_based_recommendations(
        self,
        preferences: Dict[str, Any],
        limit: int
    ) -> List[Dict[str, Any]]:
        """Graph traversal based recommendations"""
        
        liked_products = preferences.get('liked_products', [])
        preferred_effects = preferences.get('effects', [])
        preferred_terpenes = preferences.get('terpenes', [])
        
        if not liked_products and not preferred_effects:
            return []
        
        # Build recommendation query
        query = """
        MATCH (p:Product)
        WHERE p.id IN $liked_products
        MATCH (p)-[:HAS_EFFECT|HAS_TERPENE|DERIVED_FROM]->(feature)
        MATCH (rec:Product)-[:HAS_EFFECT|HAS_TERPENE|DERIVED_FROM]->(feature)
        WHERE rec.id NOT IN $liked_products
        WITH rec, COUNT(DISTINCT feature) as shared_features
        """
        
        # Add effect preferences
        if preferred_effects:
            query += """
            OPTIONAL MATCH (rec)-[:HAS_EFFECT]->(e:Effect)
            WHERE e.name IN $preferred_effects
            WITH rec, shared_features, COUNT(e) as effect_matches
            """
        else:
            query += """
            WITH rec, shared_features, 0 as effect_matches
            """
        
        # Add terpene preferences
        if preferred_terpenes:
            query += """
            OPTIONAL MATCH (rec)-[:HAS_TERPENE]->(t:Terpene)
            WHERE t.name IN $preferred_terpenes
            WITH rec, shared_features, effect_matches, COUNT(t) as terpene_matches
            """
        else:
            query += """
            WITH rec, shared_features, effect_matches, 0 as terpene_matches
            """
        
        query += """
        WITH rec, 
             shared_features * 0.4 + effect_matches * 0.4 + terpene_matches * 0.2 as score
        ORDER BY score DESC
        LIMIT $limit
        RETURN rec.id as id, rec.name as name, rec.category as category,
               rec.thc_content as thc_content, rec.cbd_content as cbd_content,
               score
        """
        
        results = await self.graph_service.execute_cypher(
            query,
            {
                'liked_products': liked_products or [''],
                'preferred_effects': preferred_effects,
                'preferred_terpenes': preferred_terpenes,
                'limit': limit
            }
        )
        
        return [dict(record) for record in results]
    
    async def _content_based_recommendations(
        self,
        preferences: Dict[str, Any],
        limit: int
    ) -> List[Dict[str, Any]]:
        """Content similarity based recommendations"""
        
        # Build preference profile
        thc_preference = preferences.get('thc_range', [0, 100])
        cbd_preference = preferences.get('cbd_range', [0, 100])
        categories = preferences.get('categories', [])
        
        query = """
        MATCH (p:Product)
        WHERE p.thc_content >= $thc_min AND p.thc_content <= $thc_max
        AND p.cbd_content >= $cbd_min AND p.cbd_content <= $cbd_max
        """
        
        if categories:
            query += """
            AND p.category IN $categories
            """
        
        query += """
        OPTIONAL MATCH (p)-[:HAS_EFFECT]->(e:Effect)
        OPTIONAL MATCH (p)-[:HAS_TERPENE]->(t:Terpene)
        RETURN p.id as id, p.name as name, p.category as category,
               p.thc_content as thc_content, p.cbd_content as cbd_content,
               COLLECT(DISTINCT e.name) as effects,
               COLLECT(DISTINCT t.name) as terpenes
        LIMIT $limit
        """
        
        results = await self.graph_service.execute_cypher(
            query,
            {
                'thc_min': thc_preference[0],
                'thc_max': thc_preference[1],
                'cbd_min': cbd_preference[0],
                'cbd_max': cbd_preference[1],
                'categories': categories if categories else ['flower', 'edibles', 'vapes'],
                'limit': limit
            }
        )
        
        # Score based on preference match
        recommendations = []
        for record in results:
            score = 1.0
            
            # Adjust score based on cannabinoid preferences
            if 'high_thc' in preferences:
                score *= (record['thc_content'] / 30.0)
            elif 'high_cbd' in preferences:
                score *= (record['cbd_content'] / 20.0)
            
            recommendations.append({
                **dict(record),
                'score': score
            })
        
        recommendations.sort(key=lambda x: x['score'], reverse=True)
        return recommendations
    
    async def _collaborative_recommendations(
        self,
        preferences: Dict[str, Any],
        limit: int
    ) -> List[Dict[str, Any]]:
        """Collaborative filtering based recommendations"""
        
        # Find similar users based on purchase history
        user_id = preferences.get('user_id')
        if not user_id:
            return []
        
        query = """
        MATCH (u1:User {id: $user_id})-[:PURCHASED]->(p:Product)<-[:PURCHASED]-(u2:User)
        WHERE u1 <> u2
        WITH u2, COUNT(DISTINCT p) as common_purchases
        ORDER BY common_purchases DESC
        LIMIT 10
        MATCH (u2)-[:PURCHASED]->(rec:Product)
        WHERE NOT EXISTS((u1)-[:PURCHASED]->(rec))
        WITH rec, COUNT(u2) as recommenders
        ORDER BY recommenders DESC
        LIMIT $limit
        RETURN rec.id as id, rec.name as name, rec.category as category,
               rec.thc_content as thc_content, rec.cbd_content as cbd_content,
               recommenders as score
        """
        
        results = await self.graph_service.execute_cypher(
            query,
            {'user_id': user_id, 'limit': limit}
        )
        
        return [dict(record) for record in results]
    
    async def _knowledge_based_recommendations(
        self,
        preferences: Dict[str, Any],
        limit: int
    ) -> List[Dict[str, Any]]:
        """Knowledge-based recommendations using ontology"""
        
        conditions = preferences.get('medical_conditions', [])
        desired_effects = preferences.get('desired_effects', [])
        
        if not conditions and not desired_effects:
            return []
        
        recommendations = []
        
        # Load ontology
        with open('data/ontology/cannabis_ontology.json', 'r') as f:
            ontology = json.load(f)
        
        # Get recommended cannabinoids and terpenes for conditions
        recommended_cannabinoids = set()
        recommended_terpenes = set()
        
        for condition in conditions:
            if condition in ontology['categories']['medical_conditions']:
                condition_data = ontology['categories']['medical_conditions'][condition]
                recommended_cannabinoids.update(condition_data.get('recommended_cannabinoids', []))
                recommended_terpenes.update(condition_data.get('recommended_terpenes', []))
        
        # Query for products with recommended profiles
        if recommended_cannabinoids or recommended_terpenes:
            query = """
            MATCH (p:Product)
            """
            
            if recommended_terpenes:
                query += """
                MATCH (p)-[:HAS_TERPENE]->(t:Terpene)
                WHERE t.name IN $terpenes
                WITH p, COUNT(DISTINCT t) as terpene_matches
                """
            else:
                query += """
                WITH p, 0 as terpene_matches
                """
            
            if desired_effects:
                query += """
                OPTIONAL MATCH (p)-[:HAS_EFFECT]->(e:Effect)
                WHERE e.name IN $effects
                WITH p, terpene_matches, COUNT(e) as effect_matches
                """
            else:
                query += """
                WITH p, terpene_matches, 0 as effect_matches
                """
            
            query += """
            WITH p, terpene_matches * 0.5 + effect_matches * 0.5 as score
            WHERE score > 0
            ORDER BY score DESC
            LIMIT $limit
            RETURN p.id as id, p.name as name, p.category as category,
                   p.thc_content as thc_content, p.cbd_content as cbd_content,
                   score
            """
            
            results = await self.graph_service.execute_cypher(
                query,
                {
                    'terpenes': list(recommended_terpenes),
                    'effects': desired_effects,
                    'limit': limit
                }
            )
            
            recommendations = [dict(record) for record in results]
        
        return recommendations
    
    def _merge_recommendations(
        self,
        recommendation_lists: List[List[Dict[str, Any]]]
    ) -> List[Dict[str, Any]]:
        """Merge multiple recommendation lists"""
        
        merged = {}
        
        for recs in recommendation_lists:
            for rec in recs:
                product_id = rec['id']
                if product_id not in merged:
                    merged[product_id] = rec
                    merged[product_id]['scores'] = []
                
                merged[product_id]['scores'].append(rec.get('score', 0))
        
        # Calculate average score
        for product_id, data in merged.items():
            data['score'] = np.mean(data['scores'])
            del data['scores']
        
        # Sort by score
        result = list(merged.values())
        result.sort(key=lambda x: x['score'], reverse=True)
        
        return result
    
    async def analyze_market_trends(
        self,
        time_window: int = 30
    ) -> Dict[str, Any]:
        """Analyze market trends from graph data
        
        Args:
            time_window: Days to analyze
            
        Returns:
            Market trend analysis
        """
        try:
            trends = {
                'popular_strains': [],
                'trending_terpenes': [],
                'effect_correlations': {},
                'price_trends': {},
                'category_distribution': {}
            }
            
            # Get popular strains
            strain_query = """
            MATCH (s:Strain)<-[:DERIVED_FROM]-(p:Product)
            WITH s, COUNT(p) as product_count
            ORDER BY product_count DESC
            LIMIT 10
            RETURN s.name as strain, product_count
            """
            
            results = await self.graph_service.execute_cypher(strain_query)
            trends['popular_strains'] = [
                {'strain': r['strain'], 'count': r['product_count']}
                for r in results
            ]
            
            # Get trending terpenes
            terpene_query = """
            MATCH (t:Terpene)<-[:HAS_TERPENE]-(p:Product)
            WITH t, COUNT(p) as product_count
            ORDER BY product_count DESC
            LIMIT 10
            RETURN t.name as terpene, product_count
            """
            
            results = await self.graph_service.execute_cypher(terpene_query)
            trends['trending_terpenes'] = [
                {'terpene': r['terpene'], 'count': r['product_count']}
                for r in results
            ]
            
            # Analyze effect correlations
            correlation_query = """
            MATCH (e1:Effect)<-[:HAS_EFFECT]-(p:Product)-[:HAS_EFFECT]->(e2:Effect)
            WHERE e1.name < e2.name
            WITH e1.name as effect1, e2.name as effect2, COUNT(p) as co_occurrence
            ORDER BY co_occurrence DESC
            LIMIT 20
            RETURN effect1, effect2, co_occurrence
            """
            
            results = await self.graph_service.execute_cypher(correlation_query)
            for r in results:
                key = f"{r['effect1']}-{r['effect2']}"
                trends['effect_correlations'][key] = r['co_occurrence']
            
            # Get category distribution
            category_query = """
            MATCH (p:Product)
            RETURN p.category as category, COUNT(p) as count
            """
            
            results = await self.graph_service.execute_cypher(category_query)
            trends['category_distribution'] = {
                r['category']: r['count'] for r in results
            }
            
            return trends
            
        except Exception as e:
            logger.error(f"Failed to analyze market trends: {e}")
            return {}
    
    async def calculate_product_importance(
        self,
        metric: AnalyticsMetric = AnalyticsMetric.PAGERANK
    ) -> List[Dict[str, Any]]:
        """Calculate product importance scores
        
        Args:
            metric: Importance metric to use
            
        Returns:
            Products ranked by importance
        """
        try:
            # Get product graph
            query = """
            MATCH (p1:Product)-[r]-(p2:Product)
            RETURN p1.id as source, p2.id as target, type(r) as rel_type
            """
            
            results = await self.graph_service.execute_cypher(query)
            
            # Build graph
            G = nx.Graph()
            for record in results:
                G.add_edge(record['source'], record['target'])
            
            if G.number_of_nodes() == 0:
                return []
            
            # Calculate metric
            if metric == AnalyticsMetric.PAGERANK:
                scores = nx.pagerank(G)
            elif metric == AnalyticsMetric.BETWEENNESS:
                scores = nx.betweenness_centrality(G)
            elif metric == AnalyticsMetric.CLOSENESS:
                scores = nx.closeness_centrality(G)
            elif metric == AnalyticsMetric.DEGREE:
                scores = nx.degree_centrality(G)
            elif metric == AnalyticsMetric.EIGENVECTOR:
                scores = nx.eigenvector_centrality(G, max_iter=1000)
            elif metric == AnalyticsMetric.CLUSTERING:
                scores = nx.clustering(G)
            else:
                scores = {}
            
            # Get product details and combine with scores
            product_scores = []
            for product_id, score in scores.items():
                detail_query = """
                MATCH (p:Product {id: $product_id})
                RETURN p.name as name, p.category as category
                """
                
                details = await self.graph_service.execute_cypher(
                    detail_query,
                    {'product_id': product_id}
                )
                
                if details:
                    product_scores.append({
                        'id': product_id,
                        'name': details[0].get('name', 'Unknown'),
                        'category': details[0].get('category', 'Unknown'),
                        'importance_score': score,
                        'metric': metric.value
                    })
            
            # Sort by score
            product_scores.sort(key=lambda x: x['importance_score'], reverse=True)
            
            return product_scores
            
        except Exception as e:
            logger.error(f"Failed to calculate product importance: {e}")
            return []
    
    async def optimize_inventory(
        self,
        current_inventory: Dict[str, int],
        target_coverage: float = 0.8
    ) -> Dict[str, Any]:
        """Optimize inventory based on graph analysis
        
        Args:
            current_inventory: Current inventory levels by product ID
            target_coverage: Target market coverage percentage
            
        Returns:
            Inventory optimization recommendations
        """
        try:
            # Get product importance scores
            importance_scores = await self.calculate_product_importance()
            
            # Get demand patterns from graph
            demand_query = """
            MATCH (p:Product)<-[:PURCHASED]-(u:User)
            WITH p.id as product_id, COUNT(u) as demand
            RETURN product_id, demand
            ORDER BY demand DESC
            """
            
            demand_results = await self.graph_service.execute_cypher(demand_query)
            demand_map = {r['product_id']: r['demand'] for r in demand_results}
            
            # Calculate optimization
            recommendations = {
                'restock': [],
                'reduce': [],
                'optimal_levels': {},
                'coverage_analysis': {}
            }
            
            total_demand = sum(demand_map.values())
            covered_demand = 0
            
            for product in importance_scores:
                product_id = product['id']
                importance = product['importance_score']
                demand = demand_map.get(product_id, 0)
                current_stock = current_inventory.get(product_id, 0)
                
                # Calculate optimal stock level
                optimal_stock = int(demand * importance * 100)  # Simplified formula
                
                recommendations['optimal_levels'][product_id] = optimal_stock
                
                if current_stock < optimal_stock * 0.3:
                    recommendations['restock'].append({
                        'product_id': product_id,
                        'product_name': product['name'],
                        'current': current_stock,
                        'recommended': optimal_stock,
                        'priority': 'high' if importance > 0.01 else 'medium'
                    })
                elif current_stock > optimal_stock * 1.5:
                    recommendations['reduce'].append({
                        'product_id': product_id,
                        'product_name': product['name'],
                        'current': current_stock,
                        'recommended': optimal_stock
                    })
                
                if current_stock > 0:
                    covered_demand += demand
            
            recommendations['coverage_analysis'] = {
                'current_coverage': covered_demand / total_demand if total_demand > 0 else 0,
                'target_coverage': target_coverage,
                'gap': target_coverage - (covered_demand / total_demand if total_demand > 0 else 0)
            }
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Failed to optimize inventory: {e}")
            return {}