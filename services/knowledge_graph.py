"""
Cannabis Knowledge Graph Service
Manages Neo4j graph database for cannabis domain knowledge
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Set, Tuple
from datetime import datetime
from enum import Enum
import json

from neo4j import AsyncGraphDatabase, AsyncDriver, AsyncSession
from neo4j.exceptions import Neo4jError
import networkx as nx
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

class EntityType(Enum):
    """Cannabis knowledge graph entity types"""
    STRAIN = "Strain"
    PRODUCT = "Product"
    BRAND = "Brand"
    TERPENE = "Terpene"
    CANNABINOID = "Cannabinoid"
    EFFECT = "Effect"
    CONDITION = "Condition"
    CATEGORY = "Category"
    CONSUMPTION_METHOD = "ConsumptionMethod"
    FLAVOR = "Flavor"
    AROMA = "Aroma"

class RelationshipType(Enum):
    """Knowledge graph relationship types"""
    CONTAINS = "CONTAINS"
    TREATS = "TREATS"
    CAUSES = "CAUSES"
    PARENT_OF = "PARENT_OF"
    SIMILAR_TO = "SIMILAR_TO"
    DERIVED_FROM = "DERIVED_FROM"
    BELONGS_TO = "BELONGS_TO"
    PRODUCED_BY = "PRODUCED_BY"
    HAS_TERPENE = "HAS_TERPENE"
    HAS_CANNABINOID = "HAS_CANNABINOID"
    HAS_EFFECT = "HAS_EFFECT"
    HAS_FLAVOR = "HAS_FLAVOR"
    HAS_AROMA = "HAS_AROMA"
    RECOMMENDED_FOR = "RECOMMENDED_FOR"
    CONSUMED_VIA = "CONSUMED_VIA"

@dataclass
class GraphEntity:
    """Graph entity representation"""
    id: str
    type: EntityType
    properties: Dict[str, Any]
    embeddings: Optional[List[float]] = None

@dataclass
class GraphRelationship:
    """Graph relationship representation"""
    source_id: str
    target_id: str
    type: RelationshipType
    properties: Dict[str, Any] = None

class KnowledgeGraphService:
    """Service for managing cannabis knowledge graph"""
    
    def __init__(self, uri: str, username: str, password: str):
        """Initialize knowledge graph service
        
        Args:
            uri: Neo4j connection URI
            username: Neo4j username
            password: Neo4j password
        """
        self.uri = uri
        self.username = username
        self.password = password
        self.driver: Optional[AsyncDriver] = None
        
    async def connect(self):
        """Connect to Neo4j database"""
        try:
            self.driver = AsyncGraphDatabase.driver(
                self.uri,
                auth=(self.username, self.password),
                max_connection_lifetime=3600
            )
            await self.driver.verify_connectivity()
            await self._create_constraints()
            logger.info("Connected to Neo4j knowledge graph")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise
    
    async def disconnect(self):
        """Disconnect from Neo4j"""
        if self.driver:
            await self.driver.close()
            logger.info("Disconnected from Neo4j")
    
    async def _create_constraints(self):
        """Create database constraints and indexes"""
        constraints = [
            "CREATE CONSTRAINT IF NOT EXISTS FOR (s:Strain) REQUIRE s.id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (p:Product) REQUIRE p.id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (b:Brand) REQUIRE b.id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (t:Terpene) REQUIRE t.name IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (c:Cannabinoid) REQUIRE c.name IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (e:Effect) REQUIRE e.name IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (co:Condition) REQUIRE co.name IS UNIQUE",
            "CREATE INDEX IF NOT EXISTS FOR (p:Product) ON (p.category)",
            "CREATE INDEX IF NOT EXISTS FOR (p:Product) ON (p.thc_content)",
            "CREATE INDEX IF NOT EXISTS FOR (p:Product) ON (p.cbd_content)",
            "CREATE INDEX IF NOT EXISTS FOR (s:Strain) ON (s.type)",
            "CREATE FULLTEXT INDEX product_search IF NOT EXISTS FOR (p:Product) ON EACH [p.name, p.description]",
            "CREATE FULLTEXT INDEX strain_search IF NOT EXISTS FOR (s:Strain) ON EACH [s.name, s.description]"
        ]
        
        async with self.driver.session() as session:
            for constraint in constraints:
                try:
                    await session.run(constraint)
                except Neo4jError as e:
                    if "already exists" not in str(e):
                        logger.warning(f"Constraint creation warning: {e}")
    
    async def add_entity(self, entity: GraphEntity) -> bool:
        """Add entity to knowledge graph
        
        Args:
            entity: Entity to add
            
        Returns:
            Success status
        """
        query = f"""
        MERGE (n:{entity.type.value} {{id: $id}})
        SET n += $properties
        RETURN n
        """
        
        async with self.driver.session() as session:
            try:
                result = await session.run(
                    query,
                    id=entity.id,
                    properties=entity.properties
                )
                record = await result.single()
                return record is not None
            except Exception as e:
                logger.error(f"Failed to add entity: {e}")
                return False
    
    async def add_relationship(self, relationship: GraphRelationship) -> bool:
        """Add relationship between entities
        
        Args:
            relationship: Relationship to add
            
        Returns:
            Success status
        """
        query = f"""
        MATCH (s {{id: $source_id}})
        MATCH (t {{id: $target_id}})
        MERGE (s)-[r:{relationship.type.value}]->(t)
        SET r += $properties
        RETURN r
        """
        
        async with self.driver.session() as session:
            try:
                result = await session.run(
                    query,
                    source_id=relationship.source_id,
                    target_id=relationship.target_id,
                    properties=relationship.properties or {}
                )
                record = await result.single()
                return record is not None
            except Exception as e:
                logger.error(f"Failed to add relationship: {e}")
                return False
    
    async def build_product_graph(self, product: Dict[str, Any]) -> bool:
        """Build graph structure for a product
        
        Args:
            product: Product data dictionary
            
        Returns:
            Success status
        """
        try:
            # Add product entity
            product_entity = GraphEntity(
                id=product['id'],
                type=EntityType.PRODUCT,
                properties={
                    'name': product.get('name'),
                    'description': product.get('description'),
                    'category': product.get('category'),
                    'thc_content': product.get('thc_content', 0),
                    'cbd_content': product.get('cbd_content', 0),
                    'price': product.get('price', 0),
                    'created_at': datetime.utcnow().isoformat()
                }
            )
            await self.add_entity(product_entity)
            
            # Add strain if exists
            if product.get('strain'):
                strain_entity = GraphEntity(
                    id=f"strain_{product['strain']}",
                    type=EntityType.STRAIN,
                    properties={
                        'name': product['strain'],
                        'type': product.get('strain_type', 'hybrid')
                    }
                )
                await self.add_entity(strain_entity)
                
                # Link product to strain
                await self.add_relationship(GraphRelationship(
                    source_id=product['id'],
                    target_id=strain_entity.id,
                    type=RelationshipType.DERIVED_FROM
                ))
            
            # Add brand
            if product.get('brand'):
                brand_entity = GraphEntity(
                    id=f"brand_{product['brand']}",
                    type=EntityType.BRAND,
                    properties={'name': product['brand']}
                )
                await self.add_entity(brand_entity)
                
                # Link product to brand
                await self.add_relationship(GraphRelationship(
                    source_id=product['id'],
                    target_id=brand_entity.id,
                    type=RelationshipType.PRODUCED_BY
                ))
            
            # Add terpenes
            for terpene in product.get('terpenes', []):
                terpene_entity = GraphEntity(
                    id=f"terpene_{terpene['name']}",
                    type=EntityType.TERPENE,
                    properties={
                        'name': terpene['name'],
                        'description': terpene.get('description')
                    }
                )
                await self.add_entity(terpene_entity)
                
                # Link product to terpene
                await self.add_relationship(GraphRelationship(
                    source_id=product['id'],
                    target_id=terpene_entity.id,
                    type=RelationshipType.HAS_TERPENE,
                    properties={'percentage': terpene.get('percentage', 0)}
                ))
            
            # Add effects
            for effect in product.get('effects', []):
                effect_entity = GraphEntity(
                    id=f"effect_{effect}",
                    type=EntityType.EFFECT,
                    properties={'name': effect}
                )
                await self.add_entity(effect_entity)
                
                # Link product to effect
                await self.add_relationship(GraphRelationship(
                    source_id=product['id'],
                    target_id=effect_entity.id,
                    type=RelationshipType.HAS_EFFECT
                ))
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to build product graph: {e}")
            return False
    
    async def find_similar_products(
        self,
        product_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Find similar products using graph structure
        
        Args:
            product_id: Product ID to find similar products for
            limit: Maximum number of results
            
        Returns:
            List of similar products
        """
        query = """
        MATCH (p1:Product {id: $product_id})
        MATCH (p1)-[:HAS_TERPENE|HAS_EFFECT|DERIVED_FROM]->(common)<-[:HAS_TERPENE|HAS_EFFECT|DERIVED_FROM]-(p2:Product)
        WHERE p1 <> p2
        WITH p2, COUNT(DISTINCT common) as commonality
        ORDER BY commonality DESC
        LIMIT $limit
        RETURN p2.id as id, p2.name as name, p2.category as category, 
               p2.thc_content as thc_content, p2.cbd_content as cbd_content,
               commonality
        """
        
        async with self.driver.session() as session:
            try:
                result = await session.run(query, product_id=product_id, limit=limit)
                products = []
                async for record in result:
                    products.append(dict(record))
                return products
            except Exception as e:
                logger.error(f"Failed to find similar products: {e}")
                return []
    
    async def recommend_products_for_condition(
        self,
        condition: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Recommend products for a medical condition
        
        Args:
            condition: Medical condition name
            limit: Maximum number of results
            
        Returns:
            List of recommended products
        """
        query = """
        MATCH (c:Condition {name: $condition})
        MATCH (c)<-[:TREATS]-(e:Effect)
        MATCH (p:Product)-[:HAS_EFFECT]->(e)
        WITH p, COUNT(DISTINCT e) as relevance
        ORDER BY relevance DESC
        LIMIT $limit
        RETURN p.id as id, p.name as name, p.category as category,
               p.thc_content as thc_content, p.cbd_content as cbd_content,
               relevance
        """
        
        async with self.driver.session() as session:
            try:
                result = await session.run(query, condition=condition, limit=limit)
                products = []
                async for record in result:
                    products.append(dict(record))
                return products
            except Exception as e:
                logger.error(f"Failed to recommend products: {e}")
                return []
    
    async def get_product_profile(self, product_id: str) -> Dict[str, Any]:
        """Get comprehensive product profile from graph
        
        Args:
            product_id: Product ID
            
        Returns:
            Product profile with all relationships
        """
        query = """
        MATCH (p:Product {id: $product_id})
        OPTIONAL MATCH (p)-[:HAS_TERPENE]->(t:Terpene)
        OPTIONAL MATCH (p)-[:HAS_EFFECT]->(e:Effect)
        OPTIONAL MATCH (p)-[:DERIVED_FROM]->(s:Strain)
        OPTIONAL MATCH (p)-[:PRODUCED_BY]->(b:Brand)
        OPTIONAL MATCH (p)-[:HAS_FLAVOR]->(f:Flavor)
        OPTIONAL MATCH (p)-[:HAS_AROMA]->(a:Aroma)
        RETURN p as product,
               COLLECT(DISTINCT t.name) as terpenes,
               COLLECT(DISTINCT e.name) as effects,
               s.name as strain,
               b.name as brand,
               COLLECT(DISTINCT f.name) as flavors,
               COLLECT(DISTINCT a.name) as aromas
        """
        
        async with self.driver.session() as session:
            try:
                result = await session.run(query, product_id=product_id)
                record = await result.single()
                if record:
                    return {
                        'product': dict(record['product']),
                        'terpenes': record['terpenes'],
                        'effects': record['effects'],
                        'strain': record['strain'],
                        'brand': record['brand'],
                        'flavors': record['flavors'],
                        'aromas': record['aromas']
                    }
                return {}
            except Exception as e:
                logger.error(f"Failed to get product profile: {e}")
                return {}
    
    async def calculate_strain_lineage(self, strain_name: str) -> Dict[str, Any]:
        """Calculate strain lineage tree
        
        Args:
            strain_name: Strain name
            
        Returns:
            Lineage tree structure
        """
        query = """
        MATCH path = (s:Strain {name: $strain_name})-[:PARENT_OF*0..5]->(:Strain)
        RETURN path
        """
        
        async with self.driver.session() as session:
            try:
                result = await session.run(query, strain_name=strain_name)
                lineage = {'strain': strain_name, 'parents': [], 'children': []}
                
                async for record in result:
                    path = record['path']
                    nodes = [node for node in path.nodes]
                    relationships = [rel for rel in path.relationships]
                    
                    # Build lineage tree
                    for i, rel in enumerate(relationships):
                        if rel.type == 'PARENT_OF':
                            parent = nodes[i]
                            child = nodes[i + 1]
                            if parent['name'] == strain_name:
                                lineage['children'].append(child['name'])
                            elif child['name'] == strain_name:
                                lineage['parents'].append(parent['name'])
                
                return lineage
            except Exception as e:
                logger.error(f"Failed to calculate lineage: {e}")
                return {}
    
    async def execute_cypher(self, query: str, parameters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Execute custom Cypher query
        
        Args:
            query: Cypher query string
            parameters: Query parameters
            
        Returns:
            Query results
        """
        async with self.driver.session() as session:
            try:
                result = await session.run(query, parameters or {})
                records = []
                async for record in result:
                    records.append(dict(record))
                return records
            except Exception as e:
                logger.error(f"Failed to execute query: {e}")
                return []
    
    async def export_subgraph(self, center_id: str, depth: int = 2) -> nx.Graph:
        """Export subgraph as NetworkX graph
        
        Args:
            center_id: Center node ID
            depth: Traversal depth
            
        Returns:
            NetworkX graph object
        """
        query = """
        MATCH path = (center {id: $center_id})-[*0..$depth]-()
        RETURN path
        """
        
        G = nx.Graph()
        
        async with self.driver.session() as session:
            try:
                result = await session.run(query, center_id=center_id, depth=depth)
                
                async for record in result:
                    path = record['path']
                    
                    # Add nodes
                    for node in path.nodes:
                        node_id = node.get('id', node.id)
                        G.add_node(node_id, **dict(node))
                    
                    # Add edges
                    for rel in path.relationships:
                        start_id = rel.start_node.get('id', rel.start_node.id)
                        end_id = rel.end_node.get('id', rel.end_node.id)
                        G.add_edge(start_id, end_id, type=rel.type, **dict(rel))
                
                return G
            except Exception as e:
                logger.error(f"Failed to export subgraph: {e}")
                return G
    
    async def get_graph_statistics(self) -> Dict[str, Any]:
        """Get graph database statistics
        
        Returns:
            Graph statistics
        """
        queries = {
            'total_nodes': "MATCH (n) RETURN COUNT(n) as count",
            'total_relationships': "MATCH ()-[r]->() RETURN COUNT(r) as count",
            'products': "MATCH (p:Product) RETURN COUNT(p) as count",
            'strains': "MATCH (s:Strain) RETURN COUNT(s) as count",
            'brands': "MATCH (b:Brand) RETURN COUNT(b) as count",
            'terpenes': "MATCH (t:Terpene) RETURN COUNT(t) as count",
            'effects': "MATCH (e:Effect) RETURN COUNT(e) as count"
        }
        
        stats = {}
        async with self.driver.session() as session:
            for key, query in queries.items():
                try:
                    result = await session.run(query)
                    record = await result.single()
                    stats[key] = record['count'] if record else 0
                except Exception as e:
                    logger.error(f"Failed to get {key}: {e}")
                    stats[key] = 0
        
        return stats