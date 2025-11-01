"""
Simple Barcode Lookup Service for quick testing
Direct database lookups only
"""

import psycopg2
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class SimpleBarcodeLookup:
    """Simple barcode lookup for testing"""
    
    def __init__(self):
        self.db_config = {
            'host': 'localhost',
            'port': 5434,
            'database': 'ai_engine',
            'user': 'weedgo',
            'password': 'weedgo123'
        }
    
    async def lookup_barcode(self, barcode: str, store_id: str = None) -> Dict[str, Any]:
        """Lookup barcode in database"""
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            
            # Check database
            cursor.execute("""
                SELECT 
                    ac.id, ac.barcode, ac.sku, ac.name, ac.brand,
                    ac.description, ac.image_url, ac.suggested_retail,
                    cat.name as category_name
                FROM accessories_catalog ac
                LEFT JOIN accessory_categories cat ON ac.category_id = cat.id
                WHERE ac.barcode = %s
                LIMIT 1
            """, (barcode,))
            
            row = cursor.fetchone()
            
            if row:
                data = {
                    'found': True,
                    'source': 'database',
                    'confidence': 1.0,
                    'data': {
                        'barcode': row[1],
                        'sku': row[2],
                        'name': row[3],
                        'brand': row[4],
                        'description': row[5],
                        'image_url': row[6],
                        'price': float(row[7]) if row[7] else None,
                        'category': row[8]
                    },
                    'requires_manual_entry': False
                }
            else:
                data = {
                    'found': False,
                    'source': 'none',
                    'confidence': 0,
                    'data': {
                        'barcode': barcode
                    },
                    'requires_manual_entry': True,
                    'message': 'Product not found. Please enter details manually.'
                }
            
            cursor.close()
            conn.close()
            return data
            
        except Exception as e:
            logger.error(f"Database lookup error: {e}")
            return {
                'found': False,
                'error': str(e),
                'requires_manual_entry': True
            }

# Singleton instance
_simple_lookup = None

def get_simple_lookup():
    global _simple_lookup
    if _simple_lookup is None:
        _simple_lookup = SimpleBarcodeLookup()
    return _simple_lookup