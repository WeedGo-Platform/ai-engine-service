#!/usr/bin/env python3
"""
Build Knowledge Graph Pipeline
ETL process to construct cannabis knowledge graph from various data sources
"""

import asyncio
import logging
import json
import pandas as pd
import re
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
import spacy
from tqdm import tqdm
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.knowledge_graph import (
    KnowledgeGraphService,
    GraphEntity,
    GraphRelationship,
    EntityType,
    RelationshipType
)
from services.semantic_search import SemanticSearchEngine
from services.graph_analytics import GraphAnalyticsService
from config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class KnowledgeGraphBuilder:
    """Build and populate cannabis knowledge graph"""
    
    def __init__(self):
        """Initialize builder"""
        self.graph_service = None
        self.search_engine = None
        self.analytics_service = None
        self.nlp = None
        self.ontology = None
        self.stats = {
            'entities_created': 0,
            'relationships_created': 0,
            'products_processed': 0,
            'errors': 0
        }
        
    async def initialize(self):
        """Initialize services and load resources"""
        try:
            # Initialize Neo4j
            self.graph_service = KnowledgeGraphService(
                uri=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
                username=os.getenv("NEO4J_USER", "neo4j"),
                password=os.getenv("NEO4J_PASSWORD", "password")
            )
            await self.graph_service.connect()
            
            # Initialize search engine
            self.search_engine = SemanticSearchEngine(
                es_host=os.getenv("ELASTICSEARCH_HOST", "localhost"),
                es_port=int(os.getenv("ELASTICSEARCH_PORT", "9200")),
                graph_service=self.graph_service
            )
            await self.search_engine.initialize()
            
            # Initialize analytics
            self.analytics_service = GraphAnalyticsService(self.graph_service)
            
            # Load spaCy
            try:
                self.nlp = spacy.load("en_core_web_sm")
            except:
                logger.info("Downloading spaCy model...")
                import subprocess
                subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"])
                self.nlp = spacy.load("en_core_web_sm")
            
            # Load ontology
            ontology_path = Path("data/ontology/cannabis_ontology.json")
            if ontology_path.exists():
                with open(ontology_path, 'r') as f:
                    self.ontology = json.load(f)
                logger.info("Loaded cannabis ontology")
            else:
                logger.warning("Ontology file not found")
                self.ontology = {}
            
            logger.info("Knowledge graph builder initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize builder: {e}")
            raise
    
    async def load_products_from_excel(self, file_path: str) -> List[Dict[str, Any]]:
        """Load products from Excel file
        
        Args:
            file_path: Path to Excel file
            
        Returns:
            List of product dictionaries
        """
        try:
            df = pd.read_excel(file_path)
            logger.info(f"Loaded {len(df)} products from {file_path}")
            
            # Convert to list of dictionaries
            products = []
            for _, row in df.iterrows():
                product = {
                    'id': str(row.get('SKU', row.get('Product ID', f"prod_{_}"))),
                    'name': str(row.get('Product Name', row.get('Name', 'Unknown'))),
                    'description': str(row.get('Description', '')),
                    'category': self._normalize_category(str(row.get('Category', 'flower'))),
                    'brand': str(row.get('Brand', row.get('Producer', 'Unknown'))),
                    'price': float(row.get('Price', row.get('Unit Price', 0))),
                    'thc_content': self._extract_percentage(row, 'THC'),
                    'cbd_content': self._extract_percentage(row, 'CBD'),
                    'strain': self._extract_strain(row),
                    'weight': self._extract_weight(row),
                    'available': bool(row.get('In Stock', True))
                }
                
                # Extract additional attributes
                product['terpenes'] = self._extract_terpenes(row)
                product['effects'] = self._extract_effects(row)
                product['flavors'] = self._extract_flavors(row)
                product['aromas'] = self._extract_aromas(row)
                
                products.append(product)
            
            return products
            
        except Exception as e:
            logger.error(f"Failed to load products: {e}")
            return []
    
    def _normalize_category(self, category: str) -> str:
        """Normalize product category"""
        category_lower = category.lower()
        
        category_map = {
            'flower': ['flower', 'bud', 'dried flower'],
            'pre-roll': ['pre-roll', 'preroll', 'joint'],
            'edible': ['edible', 'gummy', 'chocolate', 'beverage', 'drink'],
            'vape': ['vape', 'cartridge', 'pen', 'vapor'],
            'concentrate': ['concentrate', 'extract', 'shatter', 'wax', 'oil', 'rosin'],
            'topical': ['topical', 'cream', 'lotion', 'balm'],
            'capsule': ['capsule', 'pill', 'softgel'],
            'tincture': ['tincture', 'drops', 'spray']
        }
        
        for normalized, variants in category_map.items():
            if any(variant in category_lower for variant in variants):
                return normalized
        
        return 'other'
    
    def _extract_percentage(self, row: pd.Series, cannabinoid: str) -> float:
        """Extract cannabinoid percentage from row"""
        patterns = [
            f"{cannabinoid}",
            f"{cannabinoid}%",
            f"{cannabinoid} Content",
            f"Total {cannabinoid}",
            f"{cannabinoid} Percentage"
        ]
        
        for pattern in patterns:
            for col in row.index:
                if pattern.lower() in col.lower():
                    value = row[col]
                    if pd.notna(value):
                        # Extract number from string
                        if isinstance(value, str):
                            match = re.search(r'(\d+\.?\d*)', value)
                            if match:
                                return float(match.group(1))
                        else:
                            return float(value)
        
        return 0.0
    
    def _extract_strain(self, row: pd.Series) -> Optional[str]:
        """Extract strain name from row"""
        strain_cols = ['Strain', 'Strain Name', 'Genetics', 'Cultivar']
        
        for col in strain_cols:
            if col in row.index and pd.notna(row[col]):
                return str(row[col])
        
        # Try to extract from product name
        name = str(row.get('Product Name', row.get('Name', '')))
        
        # Check against known strains from ontology
        if self.ontology and 'categories' in self.ontology:
            popular_strains = self.ontology['categories'].get('strains', {}).get('popular_strains', {})
            for strain_key in popular_strains:
                strain_name = strain_key.replace('_', ' ').title()
                if strain_name.lower() in name.lower():
                    return strain_name
        
        return None
    
    def _extract_weight(self, row: pd.Series) -> Optional[float]:
        """Extract product weight in grams"""
        weight_cols = ['Weight', 'Size', 'Quantity', 'Net Weight']
        
        for col in weight_cols:
            if col in row.index and pd.notna(row[col]):
                value = str(row[col])
                # Extract number and unit
                match = re.search(r'(\d+\.?\d*)\s*(g|gram|mg|oz)', value.lower())
                if match:
                    number = float(match.group(1))
                    unit = match.group(2)
                    
                    # Convert to grams
                    if unit == 'mg':
                        return number / 1000
                    elif unit == 'oz':
                        return number * 28.35
                    else:
                        return number
        
        return None
    
    def _extract_terpenes(self, row: pd.Series) -> List[Dict[str, Any]]:
        """Extract terpene information"""
        terpenes = []
        
        # Check for terpene columns
        terpene_cols = [col for col in row.index if 'terpene' in col.lower()]
        
        for col in terpene_cols:
            if pd.notna(row[col]):
                value = str(row[col])
                # Parse terpene data (format may vary)
                if ':' in value:
                    parts = value.split(':')
                    terpenes.append({
                        'name': parts[0].strip(),
                        'percentage': float(parts[1].strip()) if len(parts) > 1 else 0
                    })
        
        # Check description for terpene mentions
        description = str(row.get('Description', ''))
        if description and self.ontology:
            terpene_list = self.ontology['categories'].get('terpenes', {}).get('primary', {})
            for terpene_name in terpene_list:
                if terpene_name.lower() in description.lower():
                    # Check if not already added
                    if not any(t['name'].lower() == terpene_name.lower() for t in terpenes):
                        terpenes.append({'name': terpene_name, 'percentage': 0})
        
        return terpenes
    
    def _extract_effects(self, row: pd.Series) -> List[str]:
        """Extract effects from product data"""
        effects = []
        
        # Check for effects column
        effects_cols = ['Effects', 'Expected Effects', 'Reported Effects']
        for col in effects_cols:
            if col in row.index and pd.notna(row[col]):
                value = str(row[col])
                # Split by common delimiters
                parts = re.split(r'[,;|]', value)
                effects.extend([e.strip() for e in parts])
        
        # Check description
        description = str(row.get('Description', ''))
        if description and self.ontology:
            effect_list = self.ontology['categories'].get('effects', {}).get('positive', {})
            for effect_name in effect_list:
                if effect_name.lower() in description.lower():
                    if effect_name not in effects:
                        effects.append(effect_name)
        
        return list(set(effects))  # Remove duplicates
    
    def _extract_flavors(self, row: pd.Series) -> List[str]:
        """Extract flavor profile"""
        flavors = []
        
        flavor_cols = ['Flavors', 'Flavor', 'Taste', 'Flavor Profile']
        for col in flavor_cols:
            if col in row.index and pd.notna(row[col]):
                value = str(row[col])
                parts = re.split(r'[,;|]', value)
                flavors.extend([f.strip() for f in parts])
        
        return list(set(flavors))
    
    def _extract_aromas(self, row: pd.Series) -> List[str]:
        """Extract aroma profile"""
        aromas = []
        
        aroma_cols = ['Aromas', 'Aroma', 'Smell', 'Scent']
        for col in aroma_cols:
            if col in row.index and pd.notna(row[col]):
                value = str(row[col])
                parts = re.split(r'[,;|]', value)
                aromas.extend([a.strip() for a in parts])
        
        return list(set(aromas))
    
    async def build_graph_from_products(self, products: List[Dict[str, Any]]):
        """Build knowledge graph from product list
        
        Args:
            products: List of product dictionaries
        """
        logger.info(f"Building graph from {len(products)} products")
        
        for product in tqdm(products, desc="Processing products"):
            try:
                # Build product graph
                success = await self.graph_service.build_product_graph(product)
                
                if success:
                    self.stats['products_processed'] += 1
                    
                    # Index in Elasticsearch
                    await self.search_engine.index_product(product)
                else:
                    self.stats['errors'] += 1
                    
            except Exception as e:
                logger.error(f"Failed to process product {product.get('id')}: {e}")
                self.stats['errors'] += 1
    
    async def enrich_graph_with_ontology(self):
        """Enrich graph with ontology relationships"""
        if not self.ontology:
            logger.warning("No ontology loaded")
            return
        
        logger.info("Enriching graph with ontology data")
        
        # Add terpene relationships
        terpenes = self.ontology['categories'].get('terpenes', {}).get('primary', {})
        for terpene_name, terpene_data in terpenes.items():
            # Create terpene entity
            entity = GraphEntity(
                id=f"terpene_{terpene_name}",
                type=EntityType.TERPENE,
                properties={
                    'name': terpene_name,
                    'aroma': terpene_data.get('aroma', []),
                    'effects': terpene_data.get('effects', []),
                    'boiling_point': terpene_data.get('boiling_point'),
                    'medical_benefits': terpene_data.get('medical_benefits', [])
                }
            )
            await self.graph_service.add_entity(entity)
            
            # Link terpene to effects
            for effect in terpene_data.get('effects', []):
                effect_entity = GraphEntity(
                    id=f"effect_{effect}",
                    type=EntityType.EFFECT,
                    properties={'name': effect}
                )
                await self.graph_service.add_entity(effect_entity)
                
                await self.graph_service.add_relationship(GraphRelationship(
                    source_id=entity.id,
                    target_id=effect_entity.id,
                    type=RelationshipType.CAUSES
                ))
        
        # Add medical condition relationships
        conditions = self.ontology['categories'].get('medical_conditions', {})
        for condition_name, condition_data in conditions.items():
            # Create condition entity
            entity = GraphEntity(
                id=f"condition_{condition_name}",
                type=EntityType.CONDITION,
                properties={
                    'name': condition_name,
                    'types': condition_data.get('types', [])
                }
            )
            await self.graph_service.add_entity(entity)
            
            # Link to recommended cannabinoids
            for cannabinoid in condition_data.get('recommended_cannabinoids', []):
                cannabinoid_entity = GraphEntity(
                    id=f"cannabinoid_{cannabinoid}",
                    type=EntityType.CANNABINOID,
                    properties={'name': cannabinoid}
                )
                await self.graph_service.add_entity(cannabinoid_entity)
                
                await self.graph_service.add_relationship(GraphRelationship(
                    source_id=cannabinoid_entity.id,
                    target_id=entity.id,
                    type=RelationshipType.TREATS
                ))
        
        logger.info("Ontology enrichment complete")
    
    async def infer_relationships(self):
        """Infer additional relationships using NLP and analytics"""
        logger.info("Inferring relationships")
        
        # Find similar products based on shared attributes
        similar_query = """
        MATCH (p1:Product)-[:HAS_TERPENE|HAS_EFFECT]->(shared)<-[:HAS_TERPENE|HAS_EFFECT]-(p2:Product)
        WHERE p1.id < p2.id
        WITH p1, p2, COUNT(shared) as similarity
        WHERE similarity >= 3
        MERGE (p1)-[r:SIMILAR_TO]-(p2)
        SET r.similarity = similarity
        RETURN COUNT(r) as relationships_created
        """
        
        result = await self.graph_service.execute_cypher(similar_query)
        if result:
            logger.info(f"Created {result[0].get('relationships_created', 0)} similarity relationships")
        
        # Infer strain relationships
        strain_query = """
        MATCH (s1:Strain)<-[:DERIVED_FROM]-(p1:Product)-[:SIMILAR_TO]-(p2:Product)-[:DERIVED_FROM]->(s2:Strain)
        WHERE s1 <> s2
        WITH s1, s2, COUNT(*) as connection_strength
        WHERE connection_strength >= 2
        MERGE (s1)-[r:SIMILAR_TO]-(s2)
        SET r.strength = connection_strength
        RETURN COUNT(r) as strain_relationships
        """
        
        result = await self.graph_service.execute_cypher(strain_query)
        if result:
            logger.info(f"Created {result[0].get('strain_relationships', 0)} strain relationships")
    
    async def validate_graph(self) -> Dict[str, Any]:
        """Validate graph integrity and completeness
        
        Returns:
            Validation report
        """
        logger.info("Validating knowledge graph")
        
        validation = {
            'stats': await self.graph_service.get_graph_statistics(),
            'orphan_nodes': [],
            'missing_relationships': [],
            'data_quality': {}
        }
        
        # Check for orphan nodes
        orphan_query = """
        MATCH (n)
        WHERE NOT (n)--()
        RETURN labels(n)[0] as type, COUNT(n) as count
        """
        
        orphans = await self.graph_service.execute_cypher(orphan_query)
        validation['orphan_nodes'] = orphans
        
        # Check data quality
        quality_checks = [
            {
                'name': 'products_without_effects',
                'query': """
                MATCH (p:Product)
                WHERE NOT (p)-[:HAS_EFFECT]->()
                RETURN COUNT(p) as count
                """
            },
            {
                'name': 'products_without_terpenes',
                'query': """
                MATCH (p:Product)
                WHERE NOT (p)-[:HAS_TERPENE]->()
                RETURN COUNT(p) as count
                """
            },
            {
                'name': 'products_without_brand',
                'query': """
                MATCH (p:Product)
                WHERE NOT (p)-[:PRODUCED_BY]->()
                RETURN COUNT(p) as count
                """
            }
        ]
        
        for check in quality_checks:
            result = await self.graph_service.execute_cypher(check['query'])
            if result:
                validation['data_quality'][check['name']] = result[0].get('count', 0)
        
        return validation
    
    async def run_pipeline(self, data_file: str):
        """Run complete pipeline
        
        Args:
            data_file: Path to data file
        """
        try:
            # Load products
            products = await self.load_products_from_excel(data_file)
            
            if not products:
                logger.error("No products loaded")
                return
            
            # Build graph
            await self.build_graph_from_products(products)
            
            # Enrich with ontology
            await self.enrich_graph_with_ontology()
            
            # Infer relationships
            await self.infer_relationships()
            
            # Validate
            validation = await self.validate_graph()
            
            # Calculate analytics
            logger.info("Calculating graph analytics")
            
            # PageRank
            pagerank = await self.analytics_service.calculate_pagerank(EntityType.PRODUCT)
            logger.info(f"Calculated PageRank for {len(pagerank)} products")
            
            # Community detection
            communities = await self.analytics_service.detect_communities()
            logger.info(f"Detected {len(set(communities.values()))} communities")
            
            # Strain families
            families = await self.analytics_service.find_strain_families()
            logger.info(f"Found {len(families)} strain families")
            
            # Market trends
            trends = await self.analytics_service.analyze_market_trends()
            
            # Print summary
            print("\n" + "="*50)
            print("KNOWLEDGE GRAPH BUILD COMPLETE")
            print("="*50)
            print(f"Products processed: {self.stats['products_processed']}")
            print(f"Errors: {self.stats['errors']}")
            print(f"\nGraph Statistics:")
            for key, value in validation['stats'].items():
                print(f"  {key}: {value}")
            print(f"\nData Quality:")
            for key, value in validation['data_quality'].items():
                print(f"  {key}: {value}")
            print(f"\nTop Strains:")
            for strain in trends.get('popular_strains', [])[:5]:
                print(f"  - {strain['strain']}: {strain['count']} products")
            print(f"\nTop Terpenes:")
            for terpene in trends.get('trending_terpenes', [])[:5]:
                print(f"  - {terpene['terpene']}: {terpene['count']} products")
            
            # Save report
            report = {
                'timestamp': datetime.utcnow().isoformat(),
                'stats': self.stats,
                'validation': validation,
                'trends': trends,
                'communities': len(set(communities.values())) if communities else 0,
                'strain_families': len(families)
            }
            
            report_path = Path("data/pipeline/knowledge_graph_report.json")
            report_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(report_path, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            
            logger.info(f"Report saved to {report_path}")
            
        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            raise
        finally:
            # Cleanup
            if self.graph_service:
                await self.graph_service.disconnect()

async def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Build Cannabis Knowledge Graph")
    parser.add_argument(
        "--data-file",
        default="data/datasets/OCS_Catalogue_31_Jul_2025_226PM.xlsx",
        help="Path to data file"
    )
    parser.add_argument(
        "--neo4j-uri",
        default="bolt://localhost:7687",
        help="Neo4j connection URI"
    )
    parser.add_argument(
        "--neo4j-user",
        default="neo4j",
        help="Neo4j username"
    )
    parser.add_argument(
        "--neo4j-password",
        default="password",
        help="Neo4j password"
    )
    
    args = parser.parse_args()
    
    # Set environment variables
    os.environ["NEO4J_URI"] = args.neo4j_uri
    os.environ["NEO4J_USER"] = args.neo4j_user
    os.environ["NEO4J_PASSWORD"] = args.neo4j_password
    
    # Run pipeline
    builder = KnowledgeGraphBuilder()
    await builder.initialize()
    await builder.run_pipeline(args.data_file)

if __name__ == "__main__":
    asyncio.run(main())