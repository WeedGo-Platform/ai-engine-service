#!/usr/bin/env python3
"""
Milvus Vector Database Setup and Integration
Sets up Milvus collections for cannabis product embeddings and similarity search
"""

import os
import sys
import json
import logging
import psycopg2
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

# Milvus imports
from pymilvus import (
    connections, utility, Collection, CollectionSchema, FieldSchema, DataType,
    Index
)

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MilvusSetup:
    """Handles Milvus vector database setup and data loading"""
    
    def __init__(self, milvus_host: str = "localhost", milvus_port: str = "19530", 
                 db_config: Optional[Dict[str, str]] = None):
        self.milvus_host = milvus_host
        self.milvus_port = milvus_port
        self.db_config = db_config
        self.pg_conn = None
        
        # Collection configurations
        self.collections_config = {
            'cannabis_products_basic': {
                'dimension': 384,  # all-MiniLM-L6-v2 dimension
                'description': 'Basic product information embeddings'
            },
            'cannabis_products_detailed': {
                'dimension': 768,  # all-mpnet-base-v2 dimension
                'description': 'Detailed product embeddings with cannabis properties'
            },
            'cannabis_products_effects': {
                'dimension': 384,  # all-MiniLM-L12-v2 dimension
                'description': 'Effects and medical properties embeddings'
            },
            'cannabis_products_search': {
                'dimension': 384,  # all-MiniLM-L6-v2 dimension
                'description': 'Search-optimized embeddings'
            }
        }
    
    def connect_milvus(self):
        """Connect to Milvus database"""
        try:
            connections.connect(
                alias="default",
                host=self.milvus_host,
                port=self.milvus_port
            )
            logger.info(f"Connected to Milvus at {self.milvus_host}:{self.milvus_port}")
            
            # Check server status
            if utility.get_server_version():
                logger.info(f"Milvus server version: {utility.get_server_version()}")
            
        except Exception as e:
            logger.error(f"Failed to connect to Milvus: {e}")
            raise
    
    def connect_postgres(self):
        """Connect to PostgreSQL database"""
        if not self.db_config:
            return
        
        try:
            self.pg_conn = psycopg2.connect(**self.db_config)
            logger.info("Connected to PostgreSQL database")
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            raise
    
    def disconnect_postgres(self):
        """Disconnect from PostgreSQL"""
        if self.pg_conn:
            self.pg_conn.close()
            logger.info("Disconnected from PostgreSQL")
    
    def create_collection_schema(self, collection_name: str, dimension: int) -> CollectionSchema:
        """Create collection schema for product embeddings"""
        
        fields = [
            # Primary key
            FieldSchema(
                name="id",
                dtype=DataType.INT64,
                is_primary=True,
                auto_id=True
            ),
            
            # Product reference
            FieldSchema(
                name="product_id",
                dtype=DataType.VARCHAR,
                max_length=36  # UUID length
            ),
            
            # OCS item number for reference
            FieldSchema(
                name="ocs_item_number",
                dtype=DataType.VARCHAR,
                max_length=50
            ),
            
            # Product metadata
            FieldSchema(
                name="product_name",
                dtype=DataType.VARCHAR,
                max_length=500
            ),
            
            FieldSchema(
                name="brand",
                dtype=DataType.VARCHAR,
                max_length=200
            ),
            
            FieldSchema(
                name="category",
                dtype=DataType.VARCHAR,
                max_length=100
            ),
            
            FieldSchema(
                name="sub_category",
                dtype=DataType.VARCHAR,
                max_length=100
            ),
            
            # Cannabis properties for filtering
            FieldSchema(
                name="thc_min",
                dtype=DataType.FLOAT
            ),
            
            FieldSchema(
                name="thc_max",
                dtype=DataType.FLOAT
            ),
            
            FieldSchema(
                name="cbd_min",
                dtype=DataType.FLOAT
            ),
            
            FieldSchema(
                name="cbd_max",
                dtype=DataType.FLOAT
            ),
            
            # Embedding vector
            FieldSchema(
                name="embedding",
                dtype=DataType.FLOAT_VECTOR,
                dim=dimension
            ),
            
            # Metadata
            FieldSchema(
                name="created_at",
                dtype=DataType.INT64  # Unix timestamp
            )
        ]
        
        schema = CollectionSchema(
            fields=fields,
            description=f"Cannabis product embeddings for {collection_name}"
        )
        
        return schema
    
    def create_collections(self):
        """Create all required collections"""
        for collection_name, config in self.collections_config.items():
            try:
                # Drop existing collection if it exists
                if utility.has_collection(collection_name):
                    logger.info(f"Dropping existing collection: {collection_name}")
                    utility.drop_collection(collection_name)
                
                # Create new collection
                schema = self.create_collection_schema(collection_name, config['dimension'])
                collection = Collection(
                    name=collection_name,
                    schema=schema,
                    using='default'
                )
                
                logger.info(f"Created collection: {collection_name}")
                
                # Create indexes for better search performance
                self.create_indexes(collection, collection_name)
                
            except Exception as e:
                logger.error(f"Failed to create collection {collection_name}: {e}")
                raise
    
    def create_indexes(self, collection: Collection, collection_name: str):
        """Create indexes for efficient searching"""
        
        # Vector index for similarity search
        index_params = {
            "index_type": "IVF_FLAT",
            "metric_type": "IP",  # Inner Product (for normalized vectors)
            "params": {"nlist": 128}
        }
        
        collection.create_index(
            field_name="embedding",
            index_params=index_params
        )
        
        logger.info(f"Created vector index for {collection_name}")
        
        # Load collection to enable searching
        collection.load()
        logger.info(f"Loaded collection {collection_name} into memory")
    
    def get_embeddings_from_postgres(self, embedding_type: str) -> List[Dict[str, Any]]:
        """Get embeddings from PostgreSQL"""
        if not self.pg_conn:
            logger.warning("No PostgreSQL connection available")
            return []
        
        cursor = self.pg_conn.cursor()
        
        query = """
        SELECT 
            pe.product_id,
            p.ocs_item_number,
            p.name,
            p.brand,
            p.category,
            p.sub_category,
            p.thc_min_percent,
            p.thc_max_percent,
            p.cbd_min_percent,
            p.cbd_max_percent,
            pe.embedding_vector,
            EXTRACT(EPOCH FROM pe.created_at) as created_at
        FROM ai_engine.product_embeddings pe
        JOIN cannabis_data.products p ON pe.product_id = p.id
        WHERE pe.embedding_type = %s
        AND p.is_active = true
        ORDER BY pe.created_at DESC
        """
        
        cursor.execute(query, (embedding_type,))
        results = []
        
        for row in cursor.fetchall():
            results.append({
                'product_id': str(row[0]),
                'ocs_item_number': row[1],
                'product_name': row[2],
                'brand': row[3],
                'category': row[4],
                'sub_category': row[5] or '',
                'thc_min': float(row[6]) if row[6] is not None else 0.0,
                'thc_max': float(row[7]) if row[7] is not None else 0.0,
                'cbd_min': float(row[8]) if row[8] is not None else 0.0,
                'cbd_max': float(row[9]) if row[9] is not None else 0.0,
                'embedding': np.array(row[10], dtype=np.float32),
                'created_at': int(row[11])
            })
        
        cursor.close()
        logger.info(f"Retrieved {len(results)} embeddings of type '{embedding_type}' from PostgreSQL")
        return results
    
    def load_embeddings_to_milvus(self, collection_name: str, embedding_type: str):
        """Load embeddings from PostgreSQL to Milvus"""
        
        # Get embeddings from PostgreSQL
        embeddings_data = self.get_embeddings_from_postgres(embedding_type)
        
        if not embeddings_data:
            logger.warning(f"No embeddings found for type '{embedding_type}'")
            return
        
        # Get collection
        collection = Collection(collection_name)
        
        # Prepare data for insertion
        data = [
            [item['product_id'] for item in embeddings_data],           # product_id
            [item['ocs_item_number'] for item in embeddings_data],      # ocs_item_number
            [item['product_name'] for item in embeddings_data],         # product_name
            [item['brand'] for item in embeddings_data],                # brand
            [item['category'] for item in embeddings_data],             # category
            [item['sub_category'] for item in embeddings_data],         # sub_category
            [item['thc_min'] for item in embeddings_data],              # thc_min
            [item['thc_max'] for item in embeddings_data],              # thc_max
            [item['cbd_min'] for item in embeddings_data],              # cbd_min
            [item['cbd_max'] for item in embeddings_data],              # cbd_max
            [item['embedding'].tolist() for item in embeddings_data],   # embedding
            [item['created_at'] for item in embeddings_data]            # created_at
        ]
        
        # Insert data
        mr = collection.insert(data)
        collection.flush()
        
        logger.info(f"Inserted {len(embeddings_data)} embeddings into {collection_name}")
        logger.info(f"Insert result: {mr.insert_count} records, primary keys: {len(mr.primary_keys)}")
    
    def load_all_embeddings(self):
        """Load all embedding types to their respective collections"""
        embedding_mappings = {
            'cannabis_products_basic': 'basic',
            'cannabis_products_detailed': 'detailed',
            'cannabis_products_effects': 'effects',
            'cannabis_products_search': 'search'
        }
        
        for collection_name, embedding_type in embedding_mappings.items():
            logger.info(f"Loading {embedding_type} embeddings to {collection_name}")
            self.load_embeddings_to_milvus(collection_name, embedding_type)
    
    def test_similarity_search(self):
        """Test similarity search functionality"""
        logger.info("Testing similarity search...")
        
        try:
            # Test on basic embeddings collection
            collection = Collection('cannabis_products_basic')
            
            # Get a random embedding to test with
            search_params = {
                "metric_type": "IP",
                "params": {"nprobe": 10}
            }
            
            # Create a dummy query vector (in practice, this would come from encoding a query)
            query_vectors = [np.random.random(384).tolist()]
            
            results = collection.search(
                data=query_vectors,
                anns_field="embedding",
                param=search_params,
                limit=5,
                output_fields=["product_name", "brand", "category"]
            )
            
            logger.info("Similarity search test results:")
            for hits in results:
                for hit in hits:
                    logger.info(f"  Product: {hit.entity.get('product_name')} | "
                              f"Brand: {hit.entity.get('brand')} | "
                              f"Score: {hit.score:.4f}")
            
            return True
            
        except Exception as e:
            logger.error(f"Similarity search test failed: {e}")
            return False
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics for all collections"""
        stats = {}
        
        for collection_name in self.collections_config.keys():
            try:
                collection = Collection(collection_name)
                collection.load()
                
                stats[collection_name] = {
                    'count': collection.num_entities,
                    'dimension': self.collections_config[collection_name]['dimension'],
                    'description': self.collections_config[collection_name]['description']
                }
                
            except Exception as e:
                logger.error(f"Failed to get stats for {collection_name}: {e}")
                stats[collection_name] = {'error': str(e)}
        
        return stats

def main():
    """Main function"""
    # Configuration
    milvus_host = os.getenv('MILVUS_HOST', 'localhost')
    milvus_port = os.getenv('MILVUS_PORT', '19530')
    
    db_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': os.getenv('DB_PORT', '5432'),
        'database': os.getenv('DB_NAME', 'ai_engine'),
        'user': os.getenv('DB_USER', 'weedgo'),
        'password': os.getenv('DB_PASSWORD', 'your_password_here'),
    }
    
    # Initialize Milvus setup
    milvus_setup = MilvusSetup(milvus_host, milvus_port, db_config)
    
    try:
        # Connect to databases
        milvus_setup.connect_milvus()
        milvus_setup.connect_postgres()
        
        # Create collections
        logger.info("Creating Milvus collections...")
        milvus_setup.create_collections()
        
        # Load embeddings from PostgreSQL
        logger.info("Loading embeddings from PostgreSQL to Milvus...")
        milvus_setup.load_all_embeddings()
        
        # Test similarity search
        milvus_setup.test_similarity_search()
        
        # Get statistics
        stats = milvus_setup.get_collection_stats()
        
        # Save report
        output_dir = Path(__file__).parent.parent / "data" / "pipeline"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        report = {
            'milvus_host': milvus_host,
            'milvus_port': milvus_port,
            'collections': stats,
            'setup_completed_at': datetime.now().isoformat()
        }
        
        with open(output_dir / "milvus_setup_report.json", "w") as f:
            json.dump(report, f, indent=2, default=str)
        
        # Print summary
        print("\n=== Milvus Setup Summary ===")
        print(f"Host: {milvus_host}:{milvus_port}")
        for collection_name, collection_stats in stats.items():
            if 'error' not in collection_stats:
                print(f"{collection_name}: {collection_stats['count']} vectors "
                      f"(dim: {collection_stats['dimension']})")
            else:
                print(f"{collection_name}: ERROR - {collection_stats['error']}")
        
        logger.info("Milvus setup completed successfully!")
        
    except Exception as e:
        logger.error(f"Milvus setup failed: {e}")
        sys.exit(1)
    finally:
        milvus_setup.disconnect_postgres()

if __name__ == "__main__":
    main()