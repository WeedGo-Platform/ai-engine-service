#!/usr/bin/env python3
"""
Cannabis Knowledge Graph Builder
Creates a sales-focused knowledge graph for intelligent budtender recommendations
"""

import json
import logging
import psycopg2
from psycopg2.extras import execute_values
from typing import Dict, List, Set, Tuple
from collections import defaultdict
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CannabisKnowledgeGraph:
    """Build cannabis knowledge graph for effect-based recommendations"""
    
    # Core terpenes and their primary effects (sales-focused)
    TERPENE_EFFECTS = {
        'Limonene': {
            'effects': ['energizing', 'uplifting', 'mood-enhancing', 'stress-relief'],
            'medical': ['anxiety', 'depression', 'stress'],
            'flavor': 'citrus',
            'sales_pitch': 'Great for daytime use and mood enhancement'
        },
        'Myrcene': {
            'effects': ['sedating', 'relaxing', 'couch-lock', 'body-high'],
            'medical': ['insomnia', 'pain', 'inflammation'],
            'flavor': 'earthy, musky',
            'sales_pitch': 'Perfect for evening relaxation and sleep'
        },
        'Pinene': {
            'effects': ['alertness', 'memory-retention', 'focus', 'anti-anxiety'],
            'medical': ['asthma', 'inflammation', 'anxiety'],
            'flavor': 'pine',
            'sales_pitch': 'Ideal for focus without the jitters'
        },
        'Linalool': {
            'effects': ['calming', 'sedating', 'anti-anxiety', 'relaxing'],
            'medical': ['anxiety', 'depression', 'insomnia', 'pain'],
            'flavor': 'floral, lavender',
            'sales_pitch': 'Natural anxiety relief and relaxation'
        },
        'Caryophyllene': {
            'effects': ['anti-inflammatory', 'pain-relief', 'relaxing'],
            'medical': ['pain', 'inflammation', 'anxiety'],
            'flavor': 'spicy, peppery',
            'sales_pitch': 'Excellent for pain management'
        },
        'Humulene': {
            'effects': ['appetite-suppressant', 'anti-inflammatory', 'pain-relief'],
            'medical': ['inflammation', 'pain', 'appetite-control'],
            'flavor': 'woody, earthy',
            'sales_pitch': 'Great for those avoiding munchies'
        },
        'Terpinolene': {
            'effects': ['uplifting', 'energizing', 'creative', 'focus'],
            'medical': ['fatigue', 'depression', 'anxiety'],
            'flavor': 'fruity, floral',
            'sales_pitch': 'Boosts creativity and energy'
        },
        'Ocimene': {
            'effects': ['energizing', 'uplifting', 'decongestant'],
            'medical': ['congestion', 'fatigue', 'depression'],
            'flavor': 'sweet, herbal',
            'sales_pitch': 'Natural energy boost'
        }
    }
    
    # Cannabinoid profiles and effects
    CANNABINOID_EFFECTS = {
        'THC': {
            'effects': ['euphoric', 'psychoactive', 'appetite-stimulant', 'pain-relief'],
            'medical': ['pain', 'nausea', 'appetite-loss', 'insomnia'],
            'sales_pitch': 'Classic cannabis experience'
        },
        'CBD': {
            'effects': ['non-psychoactive', 'anti-anxiety', 'anti-inflammatory', 'neuroprotective'],
            'medical': ['anxiety', 'inflammation', 'epilepsy', 'pain'],
            'sales_pitch': 'Relief without the high'
        },
        'CBG': {
            'effects': ['focus', 'energy', 'anti-bacterial', 'neuroprotective'],
            'medical': ['glaucoma', 'inflammation', 'bacterial-infections'],
            'sales_pitch': 'Clear-headed focus'
        },
        'CBN': {
            'effects': ['sedating', 'sleep-inducing', 'pain-relief'],
            'medical': ['insomnia', 'pain', 'inflammation'],
            'sales_pitch': 'Natural sleep aid'
        }
    }
    
    # Strain type characteristics
    STRAIN_PROFILES = {
        'Indica': {
            'typical_effects': ['relaxing', 'sedating', 'body-high', 'couch-lock'],
            'best_for': ['evening', 'sleep', 'relaxation', 'pain-relief'],
            'customer_profile': 'stress relief seekers, insomniacs, pain patients'
        },
        'Sativa': {
            'typical_effects': ['energizing', 'uplifting', 'cerebral', 'creative'],
            'best_for': ['daytime', 'social', 'creative-tasks', 'exercise'],
            'customer_profile': 'active users, creatives, social consumers'
        },
        'Hybrid': {
            'typical_effects': ['balanced', 'versatile', 'customizable'],
            'best_for': ['anytime', 'mixed-effects', 'specific-needs'],
            'customer_profile': 'experienced users, medical patients'
        }
    }
    
    # Customer intent mapping (for sales)
    CUSTOMER_INTENTS = {
        'sleep': {
            'terpenes': ['Myrcene', 'Linalool', 'Caryophyllene'],
            'cannabinoids': ['CBN', 'CBD'],
            'strain_type': 'Indica',
            'time_of_day': 'evening'
        },
        'energy': {
            'terpenes': ['Limonene', 'Pinene', 'Terpinolene'],
            'cannabinoids': ['THC', 'CBG'],
            'strain_type': 'Sativa',
            'time_of_day': 'morning'
        },
        'pain': {
            'terpenes': ['Caryophyllene', 'Myrcene', 'Humulene'],
            'cannabinoids': ['THC', 'CBD', 'CBG'],
            'strain_type': 'Hybrid',
            'time_of_day': 'anytime'
        },
        'anxiety': {
            'terpenes': ['Linalool', 'Limonene', 'Caryophyllene'],
            'cannabinoids': ['CBD', 'CBG'],
            'strain_type': 'Hybrid',
            'time_of_day': 'anytime'
        },
        'creativity': {
            'terpenes': ['Terpinolene', 'Limonene', 'Pinene'],
            'cannabinoids': ['THC'],
            'strain_type': 'Sativa',
            'time_of_day': 'daytime'
        },
        'social': {
            'terpenes': ['Limonene', 'Terpinolene', 'Ocimene'],
            'cannabinoids': ['THC'],
            'strain_type': 'Sativa',
            'time_of_day': 'evening'
        },
        'focus': {
            'terpenes': ['Pinene', 'Limonene', 'CBG'],
            'cannabinoids': ['CBG', 'THC'],
            'strain_type': 'Sativa',
            'time_of_day': 'daytime'
        },
        'appetite': {
            'terpenes': ['Myrcene', 'Limonene'],
            'cannabinoids': ['THC'],
            'strain_type': 'Hybrid',
            'time_of_day': 'anytime'
        }
    }
    
    def __init__(self, db_config):
        self.db_config = db_config
        self.conn = None
        self.graph = defaultdict(lambda: defaultdict(set))
        self.product_profiles = {}
        
    def connect_db(self):
        """Connect to PostgreSQL"""
        self.conn = psycopg2.connect(**self.db_config)
        logger.info("Connected to database")
        
    def build_graph(self):
        """Build the complete knowledge graph"""
        logger.info("Building cannabis knowledge graph...")
        
        # Create graph tables if needed
        self._create_graph_tables()
        
        # Build terpene-effect relationships
        self._build_terpene_graph()
        
        # Build cannabinoid-effect relationships  
        self._build_cannabinoid_graph()
        
        # Build strain-effect relationships
        self._build_strain_graph()
        
        # Build customer intent graph
        self._build_intent_graph()
        
        # Process products and create connections
        self._process_products()
        
        # Calculate product scores for different intents
        self._calculate_product_scores()
        
        logger.info("Knowledge graph built successfully")
        
    def _create_graph_tables(self):
        """Create tables for storing graph data"""
        cur = self.conn.cursor()
        
        # Drop existing tables to ensure correct schema
        cur.execute("DROP TABLE IF EXISTS product_terpenes CASCADE")
        cur.execute("DROP TABLE IF EXISTS product_effect_scores CASCADE")
        
        # Terpene effects table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS terpene_effects (
                terpene VARCHAR(100) PRIMARY KEY,
                effects TEXT[],
                medical_benefits TEXT[],
                flavor VARCHAR(255),
                sales_pitch TEXT
            )
        """)
        
        # Product terpene profiles
        cur.execute("""
            CREATE TABLE IF NOT EXISTS product_terpenes (
                product_id INTEGER,
                terpene VARCHAR(100),
                concentration FLOAT,
                PRIMARY KEY (product_id, terpene)
            )
        """)
        
        # Product effect scores
        cur.execute("""
            CREATE TABLE IF NOT EXISTS product_effect_scores (
                product_id INTEGER,
                intent VARCHAR(50),
                score FLOAT,
                reasoning TEXT,
                PRIMARY KEY (product_id, intent)
            )
        """)
        
        # Customer preference learning
        cur.execute("""
            CREATE TABLE IF NOT EXISTS customer_preferences (
                customer_id VARCHAR(255),
                preferred_terpenes TEXT[],
                preferred_effects TEXT[],
                avoided_effects TEXT[],
                purchase_history JSONB,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        self.conn.commit()
        logger.info("Graph tables created")
        
    def _build_terpene_graph(self):
        """Build terpene-effect relationships"""
        cur = self.conn.cursor()
        
        for terpene, data in self.TERPENE_EFFECTS.items():
            # Store in database
            cur.execute("""
                INSERT INTO terpene_effects (terpene, effects, medical_benefits, flavor, sales_pitch)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (terpene) DO UPDATE SET
                    effects = EXCLUDED.effects,
                    medical_benefits = EXCLUDED.medical_benefits,
                    flavor = EXCLUDED.flavor,
                    sales_pitch = EXCLUDED.sales_pitch
            """, (
                terpene,
                data['effects'],
                data['medical'],
                data['flavor'],
                data['sales_pitch']
            ))
            
            # Build in-memory graph
            for effect in data['effects']:
                self.graph['terpene'][terpene].add(effect)
                self.graph['effect'][effect].add(terpene)
            
            for medical in data['medical']:
                self.graph['medical'][medical].add(terpene)
                
        self.conn.commit()
        logger.info(f"Built terpene graph with {len(self.TERPENE_EFFECTS)} terpenes")
        
    def _build_cannabinoid_graph(self):
        """Build cannabinoid-effect relationships"""
        for cannabinoid, data in self.CANNABINOID_EFFECTS.items():
            for effect in data['effects']:
                self.graph['cannabinoid'][cannabinoid].add(effect)
                self.graph['effect'][effect].add(cannabinoid)
            
            for medical in data['medical']:
                self.graph['medical'][medical].add(cannabinoid)
                
        logger.info(f"Built cannabinoid graph with {len(self.CANNABINOID_EFFECTS)} cannabinoids")
        
    def _build_strain_graph(self):
        """Build strain type relationships"""
        for strain_type, data in self.STRAIN_PROFILES.items():
            for effect in data['typical_effects']:
                self.graph['strain'][strain_type].add(effect)
                self.graph['effect'][effect].add(strain_type)
                
        logger.info("Built strain type graph")
        
    def _build_intent_graph(self):
        """Build customer intent mappings"""
        for intent, data in self.CUSTOMER_INTENTS.items():
            self.graph['intent'][intent] = data
            
        logger.info(f"Built intent graph with {len(self.CUSTOMER_INTENTS)} intents")
        
    def _process_products(self):
        """Process products and extract profiles"""
        cur = self.conn.cursor()
        
        # Get all products
        cur.execute("""
            SELECT id, product_name, brand, category, sub_category, 
                   thc_min_percent, thc_max_percent, cbd_min_percent, cbd_max_percent,
                   terpenes, plant_type, short_description
            FROM products
            WHERE category IN ('Flower', 'Vapes', 'Extracts', 'Edibles')
        """)
        
        products = cur.fetchall()
        logger.info(f"Processing {len(products)} products")
        
        for product in products:
            product_id = product[0]
            name = product[1]
            terpenes = product[9] if product[9] else []
            strain_type = product[10]
            
            # Parse terpenes from product
            if isinstance(terpenes, str):
                terpenes = [t.strip() for t in terpenes.split(',')]
            
            # Store product terpene profile
            for terpene in terpenes:
                if terpene in self.TERPENE_EFFECTS:
                    cur.execute("""
                        INSERT INTO product_terpenes (product_id, terpene, concentration)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (product_id, terpene) DO NOTHING
                    """, (product_id, terpene, 1.0))  # Default concentration
                    
            # Map plant type to strain category
            if strain_type:
                if 'Indica' in strain_type:
                    strain_category = 'Indica'
                elif 'Sativa' in strain_type:
                    strain_category = 'Sativa'
                else:
                    strain_category = 'Hybrid'
            else:
                strain_category = 'Hybrid'
            
            # Build product profile
            self.product_profiles[product_id] = {
                'name': name,
                'terpenes': terpenes,
                'strain_type': strain_category,
                'thc_range': (product[5], product[6]),
                'cbd_range': (product[7], product[8])
            }
            
        self.conn.commit()
        logger.info("Product profiles processed")
        
    def _calculate_product_scores(self):
        """Calculate how well each product matches different intents"""
        cur = self.conn.cursor()
        
        for product_id, profile in self.product_profiles.items():
            for intent, intent_data in self.CUSTOMER_INTENTS.items():
                score = 0
                reasoning = []
                
                # Score based on terpene match
                product_terpenes = set(profile['terpenes'])
                intent_terpenes = set(intent_data['terpenes'])
                terpene_match = len(product_terpenes & intent_terpenes)
                
                if terpene_match > 0:
                    score += terpene_match * 30
                    reasoning.append(f"Contains {terpene_match} recommended terpenes")
                
                # Score based on strain type
                if profile['strain_type'] == intent_data['strain_type']:
                    score += 20
                    reasoning.append(f"Ideal strain type ({profile['strain_type']})")
                
                # Score based on THC/CBD ratio
                thc_avg = (profile['thc_range'][0] + profile['thc_range'][1]) / 2 if profile['thc_range'][0] else 0
                cbd_avg = (profile['cbd_range'][0] + profile['cbd_range'][1]) / 2 if profile['cbd_range'][0] else 0
                
                if intent in ['anxiety', 'pain'] and cbd_avg > 5:
                    score += 20
                    reasoning.append("High CBD content")
                elif intent in ['energy', 'creativity'] and thc_avg > 15:
                    score += 20
                    reasoning.append("Optimal THC level")
                    
                # Store score
                if score > 0:
                    cur.execute("""
                        INSERT INTO product_effect_scores (product_id, intent, score, reasoning)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (product_id, intent) DO UPDATE SET
                            score = EXCLUDED.score,
                            reasoning = EXCLUDED.reasoning
                    """, (product_id, intent, score, '; '.join(reasoning)))
                    
        self.conn.commit()
        logger.info("Product intent scores calculated")
        
    def get_recommendations(self, intent: str, limit: int = 5) -> List[Dict]:
        """Get product recommendations for a specific intent"""
        cur = self.conn.cursor()
        
        cur.execute("""
            SELECT p.id, p.product_name, p.brand, p.unit_price, 
                   pes.score, pes.reasoning
            FROM products p
            JOIN product_effect_scores pes ON p.id = pes.product_id
            WHERE pes.intent = %s
            ORDER BY pes.score DESC
            LIMIT %s
        """, (intent, limit))
        
        results = []
        for row in cur.fetchall():
            results.append({
                'product_id': str(row[0]),
                'name': row[1],
                'brand': row[2],
                'price': float(row[3]) if row[3] else 0,
                'score': row[4],
                'reasoning': row[5]
            })
            
        return results
        
    def generate_report(self):
        """Generate knowledge graph statistics"""
        cur = self.conn.cursor()
        
        stats = {}
        
        # Count relationships
        cur.execute("SELECT COUNT(DISTINCT terpene) FROM terpene_effects")
        stats['terpenes'] = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(DISTINCT product_id) FROM product_terpenes")
        stats['products_with_terpenes'] = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM product_effect_scores")
        stats['product_intent_scores'] = cur.fetchone()[0]
        
        cur.execute("""
            SELECT intent, COUNT(*) as products, AVG(score) as avg_score
            FROM product_effect_scores
            GROUP BY intent
            ORDER BY products DESC
        """)
        
        stats['intent_coverage'] = {}
        for row in cur.fetchall():
            stats['intent_coverage'][row[0]] = {
                'products': row[1],
                'avg_score': float(row[2])
            }
            
        return stats

def main():
    """Build the knowledge graph"""
    # Database configuration
    db_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', 5434)),
        'database': os.getenv('DB_NAME', 'ai_engine'),
        'user': os.getenv('DB_USER', 'weedgo'),
        'password': os.getenv('DB_PASSWORD', 'weedgo123')
    }
    
    # Build graph
    builder = CannabisKnowledgeGraph(db_config)
    builder.connect_db()
    builder.build_graph()
    
    # Generate report
    stats = builder.generate_report()
    print("\n=== Cannabis Knowledge Graph Built ===")
    print(f"Terpenes mapped: {stats['terpenes']}")
    print(f"Products with terpene data: {stats['products_with_terpenes']}")
    print(f"Product-intent scores: {stats['product_intent_scores']}")
    
    print("\nIntent Coverage:")
    for intent, data in stats['intent_coverage'].items():
        print(f"  {intent}: {data['products']} products (avg score: {data['avg_score']:.1f})")
    
    # Test recommendations
    print("\n=== Sample Recommendations ===")
    for intent in ['sleep', 'energy', 'anxiety']:
        print(f"\nTop products for '{intent}':")
        recommendations = builder.get_recommendations(intent, limit=3)
        for i, rec in enumerate(recommendations, 1):
            print(f"  {i}. {rec['name']} ({rec['brand']})")
            print(f"     Score: {rec['score']:.0f} - {rec['reasoning']}")
            print(f"     Price: ${rec['price']:.2f}")
    
    builder.conn.close()
    print("\nKnowledge graph building complete!")

if __name__ == "__main__":
    main()