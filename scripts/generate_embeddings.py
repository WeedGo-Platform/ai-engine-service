#!/usr/bin/env python3
"""
Cannabis Product Embeddings Generator
Creates vector embeddings for cannabis products to enable semantic search and recommendations
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

# ML and embedding libraries
import torch
from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer, AutoModel
import torch.nn.functional as F

# Database
from psycopg2.extras import execute_values

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CannabisEmbeddingGenerator:
    """Generates embeddings for cannabis products using specialized models"""
    
    def __init__(self, db_config: Dict[str, str]):
        self.db_config = db_config
        self.conn = None
        
        # Initialize embedding models
        self.models = {}
        self.load_models()
    
    def load_models(self):
        """Load pre-trained embedding models"""
        logger.info("Loading embedding models...")
        
        try:
            # General purpose sentence transformer for product descriptions
            self.models['description'] = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("Loaded general description model")
            
            # Cannabis-specific model (we'll use a fine-tuned general model)
            # In production, this would be a model fine-tuned on cannabis data
            self.models['cannabis_specialized'] = SentenceTransformer('sentence-transformers/all-mpnet-base-v2')
            logger.info("Loaded cannabis specialized model")
            
            # Effects and medical properties model
            self.models['effects'] = SentenceTransformer('sentence-transformers/all-MiniLM-L12-v2')
            logger.info("Loaded effects model")
            
            # Multi-language support for budtender conversations
            self.models['multilingual'] = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
            logger.info("Loaded multilingual model")
            
        except Exception as e:
            logger.error(f"Failed to load models: {e}")
            raise
    
    def connect_db(self):
        """Connect to PostgreSQL database"""
        try:
            self.conn = psycopg2.connect(**self.db_config)
            self.conn.autocommit = False
            logger.info("Connected to PostgreSQL database")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    
    def disconnect_db(self):
        """Disconnect from database"""
        if self.conn:
            self.conn.close()
            logger.info("Disconnected from database")
    
    def get_products_for_embedding(self) -> List[Dict[str, Any]]:
        """Fetch products that need embeddings"""
        cursor = self.conn.cursor()
        
        query = """
        SELECT 
            p.id,
            p.ocs_item_number,
            p.name,
            p.brand,
            p.category,
            p.sub_category,
            p.short_description,
            p.long_description,
            p.terpenes,
            p.plant_type,
            p.thc_min_percent,
            p.thc_max_percent,
            p.cbd_min_percent,
            p.cbd_max_percent,
            p.effects_text
        FROM cannabis_data.products p
        LEFT JOIN ai_engine.product_embeddings pe ON p.id = pe.product_id
        WHERE p.is_active = true
        AND (pe.id IS NULL OR pe.model_name != 'cannabis_specialized_v1')
        ORDER BY p.created_at DESC
        """
        
        # Add effects_text as computed field for now
        enhanced_query = """
        SELECT 
            p.id,
            p.ocs_item_number,
            p.name,
            p.brand,
            p.category,
            p.sub_category,
            p.short_description,
            p.long_description,
            p.terpenes,
            p.plant_type,
            p.thc_min_percent,
            p.thc_max_percent,
            p.cbd_min_percent,
            p.cbd_max_percent,
            CASE 
                WHEN p.terpenes IS NOT NULL AND array_length(p.terpenes, 1) > 0 
                THEN 'Terpenes: ' || array_to_string(p.terpenes, ', ')
                ELSE ''
            END as effects_text
        FROM cannabis_data.products p
        WHERE p.is_active = true
        ORDER BY p.created_at DESC
        """
        
        cursor.execute(enhanced_query)
        products = []
        
        for row in cursor.fetchall():
            products.append({
                'id': row[0],
                'ocs_item_number': row[1],
                'name': row[2],
                'brand': row[3],
                'category': row[4],
                'sub_category': row[5],
                'short_description': row[6],
                'long_description': row[7],
                'terpenes': row[8] if row[8] else [],
                'plant_type': row[9],
                'thc_min_percent': row[10],
                'thc_max_percent': row[11],
                'cbd_min_percent': row[12],
                'cbd_max_percent': row[13],
                'effects_text': row[14]
            })
        
        cursor.close()
        logger.info(f"Found {len(products)} products for embedding generation")
        return products
    
    def create_product_text_representations(self, product: Dict[str, Any]) -> Dict[str, str]:
        """Create different text representations for embedding"""
        
        # Basic product description
        basic_text = f"{product['name']} by {product['brand']}"
        if product['short_description']:
            basic_text += f". {product['short_description']}"
        
        # Detailed description including cannabis properties
        detailed_text = basic_text
        if product['long_description']:
            detailed_text += f" {product['long_description']}"
        
        # Add cannabis-specific information
        cannabis_info = []
        if product['category']:
            cannabis_info.append(f"Category: {product['category']}")
        if product['plant_type']:
            cannabis_info.append(f"Type: {product['plant_type']}")
        if product['thc_min_percent'] and product['thc_max_percent']:
            cannabis_info.append(f"THC: {product['thc_min_percent']}-{product['thc_max_percent']}%")
        if product['cbd_min_percent'] and product['cbd_max_percent']:
            cannabis_info.append(f"CBD: {product['cbd_min_percent']}-{product['cbd_max_percent']}%")
        if product['terpenes']:
            cannabis_info.append(f"Terpenes: {', '.join(product['terpenes'])}")
        
        if cannabis_info:
            detailed_text += f" Cannabis properties: {'. '.join(cannabis_info)}"
        
        # Effects and medical text
        effects_text = ""
        if product['effects_text']:
            effects_text = product['effects_text']
        
        # Add inferred effects based on terpenes and strain type
        if product['terpenes']:
            terpene_effects = self.get_terpene_effects(product['terpenes'])
            if terpene_effects:
                effects_text += f" Potential effects: {', '.join(terpene_effects)}"
        
        # Search-optimized text (keywords and categories)
        search_text = f"{product['name']} {product['brand']} {product['category']} {product['sub_category'] or ''}"
        if product['terpenes']:
            search_text += f" {' '.join(product['terpenes'])}"
        
        return {
            'basic': basic_text,
            'detailed': detailed_text,
            'effects': effects_text if effects_text else basic_text,
            'search': search_text
        }
    
    def get_terpene_effects(self, terpenes: List[str]) -> List[str]:
        """Map terpenes to potential effects (simplified mapping)"""
        terpene_effects_map = {
            'myrcene': ['relaxing', 'sedating', 'calming'],
            'limonene': ['uplifting', 'mood-enhancing', 'energizing'],
            'pinene': ['alertness', 'memory-retention', 'focus'],
            'linalool': ['calming', 'anti-anxiety', 'relaxing'],
            'caryophyllene': ['anti-inflammatory', 'pain-relief'],
            'beta-caryophyllene': ['anti-inflammatory', 'pain-relief'],
            'humulene': ['appetite-suppressant', 'anti-inflammatory'],
            'terpinolene': ['uplifting', 'energizing'],
            'ocimene': ['uplifting', 'energizing'],
            'eucalyptol': ['mental-clarity', 'focus']
        }
        
        effects = []
        for terpene in terpenes:
            terpene_lower = terpene.lower()
            for key, terpene_effects in terpene_effects_map.items():
                if key in terpene_lower:
                    effects.extend(terpene_effects)
        
        # Remove duplicates and return
        return list(set(effects))
    
    def generate_embeddings(self, texts: List[str], model_name: str) -> np.ndarray:
        """Generate embeddings using specified model"""
        if model_name not in self.models:
            raise ValueError(f"Model {model_name} not loaded")
        
        model = self.models[model_name]
        
        # Generate embeddings
        embeddings = model.encode(texts, convert_to_tensor=True)
        
        # Convert to numpy and normalize
        embeddings_np = embeddings.cpu().numpy()
        embeddings_normalized = F.normalize(torch.tensor(embeddings_np), p=2, dim=1).numpy()
        
        return embeddings_normalized
    
    def save_embeddings(self, product_embeddings: List[Dict[str, Any]]):
        """Save embeddings to database"""
        if not product_embeddings:
            return
        
        # Prepare data for insertion
        values = []
        for embedding_data in product_embeddings:
            values.append((
                embedding_data['product_id'],
                embedding_data['embedding_type'],
                embedding_data['model_name'],
                embedding_data['model_version'],
                embedding_data['embedding_vector'].tolist(),  # Convert numpy array to list
                len(embedding_data['embedding_vector']),
                datetime.now()
            ))
        
        sql = """
        INSERT INTO ai_engine.product_embeddings 
        (product_id, embedding_type, model_name, model_version, embedding_vector, vector_dimension, created_at)
        VALUES %s
        ON CONFLICT (product_id, embedding_type, model_name, model_version)
        DO UPDATE SET
            embedding_vector = EXCLUDED.embedding_vector,
            vector_dimension = EXCLUDED.vector_dimension,
            created_at = EXCLUDED.created_at
        """
        
        try:
            cursor = self.conn.cursor()
            execute_values(cursor, sql, values, page_size=100)
            self.conn.commit()
            cursor.close()
            logger.info(f"Saved {len(product_embeddings)} embeddings to database")
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Failed to save embeddings: {e}")
            raise
    
    def process_products_batch(self, products: List[Dict[str, Any]], batch_size: int = 32):
        """Process products in batches to generate embeddings"""
        total_products = len(products)
        embeddings_to_save = []
        
        for i in range(0, total_products, batch_size):
            batch = products[i:i + batch_size]
            logger.info(f"Processing batch {i//batch_size + 1}/{(total_products + batch_size - 1)//batch_size}")
            
            # Prepare texts for each embedding type
            batch_texts = {
                'basic': [],
                'detailed': [],
                'effects': [],
                'search': []
            }
            
            for product in batch:
                text_representations = self.create_product_text_representations(product)
                for text_type, text in text_representations.items():
                    batch_texts[text_type].append(text)
            
            # Generate embeddings for each type
            for embedding_type, texts in batch_texts.items():
                if embedding_type == 'effects':
                    model_name = 'effects'
                elif embedding_type == 'search':
                    model_name = 'description'
                else:
                    model_name = 'cannabis_specialized'
                
                embeddings = self.generate_embeddings(texts, model_name)
                
                # Store embeddings
                for j, embedding in enumerate(embeddings):
                    embeddings_to_save.append({
                        'product_id': batch[j]['id'],
                        'embedding_type': embedding_type,
                        'model_name': f"{model_name}_v1",
                        'model_version': '1.0.0',
                        'embedding_vector': embedding
                    })
        
        # Save all embeddings
        if embeddings_to_save:
            self.save_embeddings(embeddings_to_save)
            logger.info(f"Generated and saved embeddings for {total_products} products")
    
    def update_embeddings_statistics(self):
        """Update database with embedding generation statistics"""
        cursor = self.conn.cursor()
        
        # Count embeddings by type
        cursor.execute("""
            SELECT embedding_type, model_name, COUNT(*) as count
            FROM ai_engine.product_embeddings
            GROUP BY embedding_type, model_name
            ORDER BY embedding_type, model_name
        """)
        
        stats = cursor.fetchall()
        cursor.close()
        
        logger.info("Embedding statistics:")
        for stat in stats:
            logger.info(f"  {stat[0]} ({stat[1]}): {stat[2]} products")
        
        return stats

def main():
    """Main function"""
    # Database configuration
    db_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': os.getenv('DB_PORT', '5432'),
        'database': os.getenv('DB_NAME', 'ai_engine'),
        'user': os.getenv('DB_USER', 'weedgo'),
        'password': os.getenv('DB_PASSWORD', 'your_password_here'),
    }
    
    # Check if GPU is available
    if torch.cuda.is_available():
        logger.info(f"CUDA available: {torch.cuda.get_device_name(0)}")
        device = 'cuda'
    else:
        logger.info("CUDA not available, using CPU")
        device = 'cpu'
    
    # Initialize embedding generator
    generator = CannabisEmbeddingGenerator(db_config)
    
    try:
        generator.connect_db()
        
        # Get products that need embeddings
        products = generator.get_products_for_embedding()
        
        if not products:
            logger.info("No products need embeddings. All products are up to date.")
            return
        
        logger.info(f"Generating embeddings for {len(products)} products...")
        
        # Process products in batches
        generator.process_products_batch(products, batch_size=32)
        
        # Update statistics
        stats = generator.update_embeddings_statistics()
        
        # Save summary report
        output_dir = Path(__file__).parent.parent / "data" / "pipeline"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        report = {
            'total_products_processed': len(products),
            'embedding_statistics': [
                {'type': stat[0], 'model': stat[1], 'count': stat[2]} 
                for stat in stats
            ],
            'generated_at': datetime.now().isoformat(),
            'device_used': device
        }
        
        with open(output_dir / "embeddings_report.json", "w") as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info("Embeddings generation completed successfully!")
        print(f"\n=== Embeddings Generation Summary ===")
        print(f"Products processed: {len(products)}")
        print(f"Device used: {device}")
        print(f"Report saved to: {output_dir / 'embeddings_report.json'}")
        
    except Exception as e:
        logger.error(f"Embeddings generation failed: {e}")
        sys.exit(1)
    finally:
        generator.disconnect_db()

if __name__ == "__main__":
    main()