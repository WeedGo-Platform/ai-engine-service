#!/usr/bin/env python3
"""
Pricing Intelligence Service for WeedGo
- Web scraping for competitor prices
- Dynamic pricing optimization
- Price trend analysis
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import asyncpg
import asyncio
import re
import json
from dataclasses import dataclass
from enum import Enum
import hashlib
import numpy as np
from collections import defaultdict
import uvicorn
import os

app = FastAPI(title="WeedGo Pricing Intelligence", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', '5434')),
    'database': os.getenv('DB_NAME', 'ai_engine'),
    'user': os.getenv('DB_USER', 'weedgo'),
    'password': os.getenv('DB_PASSWORD', 'your_password_here')
}

class PriceStrategy(Enum):
    COMPETITIVE = "competitive"      # Match competitors
    PENETRATION = "penetration"      # Below market
    PREMIUM = "premium"              # Above market
    DYNAMIC = "dynamic"              # Demand-based
    CLEARANCE = "clearance"          # Inventory reduction

@dataclass
class CompetitorPrice:
    competitor_name: str
    product_name: str
    price: float
    size: str
    thc_content: Optional[float]
    cbd_content: Optional[float]
    scraped_at: datetime
    url: Optional[str]

@dataclass
class PriceRecommendation:
    product_id: str
    current_price: float
    recommended_price: float
    strategy: PriceStrategy
    competitor_avg: Optional[float]
    price_elasticity: float
    expected_volume_change: float
    profit_impact: float
    confidence: float
    reasons: List[str]

class PricingEngine:
    """Advanced pricing optimization engine"""
    
    def __init__(self):
        self.elasticity_cache = {}
        self.competitor_data = defaultdict(list)
        self.demand_patterns = {}
    
    def calculate_price_elasticity(self, sales_history: List[Dict]) -> float:
        """Calculate price elasticity of demand"""
        if len(sales_history) < 2:
            return -1.0  # Default elasticity
        
        prices = [s['price'] for s in sales_history]
        quantities = [s['quantity'] for s in sales_history]
        
        # Calculate percentage changes
        price_changes = []
        quantity_changes = []
        
        for i in range(1, len(sales_history)):
            if prices[i-1] > 0 and quantities[i-1] > 0:
                price_pct = (prices[i] - prices[i-1]) / prices[i-1]
                quantity_pct = (quantities[i] - quantities[i-1]) / quantities[i-1]
                
                if price_pct != 0:
                    price_changes.append(price_pct)
                    quantity_changes.append(quantity_pct)
        
        if not price_changes:
            return -1.0
        
        # Calculate elasticity
        elasticity = np.mean([q/p for q, p in zip(quantity_changes, price_changes) if p != 0])
        return max(min(elasticity, -0.1), -5.0)  # Bound elasticity
    
    def optimize_price(self, 
                       current_price: float,
                       competitor_prices: List[float],
                       elasticity: float,
                       inventory_level: int,
                       strategy: PriceStrategy) -> PriceRecommendation:
        """Generate optimal price recommendation"""
        
        reasons = []
        
        # Calculate competitor average
        competitor_avg = np.mean(competitor_prices) if competitor_prices else current_price
        
        # Base price based on strategy
        if strategy == PriceStrategy.COMPETITIVE:
            base_price = competitor_avg
            reasons.append(f"Matching competitor average of ${competitor_avg:.2f}")
        
        elif strategy == PriceStrategy.PENETRATION:
            base_price = competitor_avg * 0.85
            reasons.append(f"15% below market average for market penetration")
        
        elif strategy == PriceStrategy.PREMIUM:
            base_price = competitor_avg * 1.15
            reasons.append(f"15% premium positioning above market")
        
        elif strategy == PriceStrategy.CLEARANCE:
            discount = min(0.3, inventory_level / 1000)  # Up to 30% off
            base_price = current_price * (1 - discount)
            reasons.append(f"Clearance pricing: {discount*100:.0f}% off to move inventory")
        
        else:  # DYNAMIC
            # Consider elasticity and inventory
            if inventory_level > 100:
                # High inventory - lower price
                adjustment = -0.1
                reasons.append("High inventory levels - reducing price")
            elif inventory_level < 20:
                # Low inventory - raise price
                adjustment = 0.1
                reasons.append("Low inventory - premium pricing")
            else:
                adjustment = 0
            
            base_price = current_price * (1 + adjustment)
        
        # Calculate expected volume change
        price_change_pct = (base_price - current_price) / current_price if current_price > 0 else 0
        expected_volume_change = price_change_pct * elasticity
        
        # Calculate profit impact (simplified)
        profit_impact = (base_price - current_price) * (1 + expected_volume_change)
        
        # Confidence based on data quality
        confidence = min(0.95, 0.5 + len(competitor_prices) * 0.1)
        
        return PriceRecommendation(
            product_id="",
            current_price=current_price,
            recommended_price=round(base_price, 2),
            strategy=strategy,
            competitor_avg=competitor_avg if competitor_prices else None,
            price_elasticity=elasticity,
            expected_volume_change=expected_volume_change,
            profit_impact=profit_impact,
            confidence=confidence,
            reasons=reasons
        )

# Initialize pricing engine
pricing_engine = PricingEngine()

async def init_pricing_tables():
    """Initialize pricing-related database tables"""
    conn = await asyncpg.connect(**DB_CONFIG)
    
    await conn.execute("""
        CREATE SCHEMA IF NOT EXISTS pricing_data;
        
        CREATE TABLE IF NOT EXISTS pricing_data.competitor_prices (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            competitor_name TEXT NOT NULL,
            product_name TEXT NOT NULL,
            product_hash TEXT,
            price DECIMAL(10,2) NOT NULL,
            size TEXT,
            thc_content DECIMAL(5,2),
            cbd_content DECIMAL(5,2),
            url TEXT,
            scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS pricing_data.price_recommendations (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            product_id UUID NOT NULL,
            current_price DECIMAL(10,2),
            recommended_price DECIMAL(10,2),
            strategy TEXT,
            competitor_avg DECIMAL(10,2),
            price_elasticity DECIMAL(5,2),
            expected_volume_change DECIMAL(5,2),
            profit_impact DECIMAL(10,2),
            confidence DECIMAL(3,2),
            reasons JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS pricing_data.sales_history (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            product_id UUID NOT NULL,
            price DECIMAL(10,2) NOT NULL,
            quantity INTEGER NOT NULL,
            revenue DECIMAL(10,2),
            date DATE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX IF NOT EXISTS idx_competitor_prices_product 
        ON pricing_data.competitor_prices(product_hash);
        
        CREATE INDEX IF NOT EXISTS idx_price_recommendations_product 
        ON pricing_data.price_recommendations(product_id);
        
        CREATE INDEX IF NOT EXISTS idx_sales_history_product_date 
        ON pricing_data.sales_history(product_id, date DESC);
    """)
    
    await conn.close()

@app.on_event("startup")
async def startup():
    """Initialize database on startup"""
    await init_pricing_tables()
    print("✅ Pricing Intelligence Service initialized")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        conn = await asyncpg.connect(**DB_CONFIG)
        await conn.fetchval("SELECT 1")
        await conn.close()
        return {"status": "healthy", "service": "pricing_intelligence"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

@app.post("/pricing/analyze/{product_id}")
async def analyze_product_pricing(product_id: str, strategy: Optional[PriceStrategy] = None):
    """Analyze pricing for a specific product"""
    
    conn = await asyncpg.connect(**DB_CONFIG)
    
    try:
        # Get product details
        product = await conn.fetchrow("""
            SELECT * FROM cannabis_data.products WHERE id = $1
        """, product_id)
        
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        # Get competitor prices
        competitor_prices = await conn.fetch("""
            SELECT * FROM pricing_data.competitor_prices 
            WHERE product_hash = $1
            AND scraped_at > CURRENT_TIMESTAMP - INTERVAL '7 days'
            ORDER BY scraped_at DESC
        """, hashlib.md5(product['name'].encode()).hexdigest()[:16])
        
        # Get sales history
        sales_history = await conn.fetch("""
            SELECT price, quantity, date 
            FROM pricing_data.sales_history 
            WHERE product_id = $1
            ORDER BY date DESC
            LIMIT 30
        """, product_id)
        
        # Calculate elasticity
        elasticity = pricing_engine.calculate_price_elasticity(
            [dict(s) for s in sales_history]
        )
        
        # Get competitor price list
        comp_prices = [float(cp['price']) for cp in competitor_prices]
        
        # Determine strategy if not provided
        if not strategy:
            # Auto-select strategy based on conditions
            if len(sales_history) < 5:
                strategy = PriceStrategy.PENETRATION  # New product
            elif product.get('inventory_level', 0) > 200:
                strategy = PriceStrategy.CLEARANCE
            else:
                strategy = PriceStrategy.COMPETITIVE
        
        # Generate recommendation
        current_price = float(product.get('price', 0)) or 29.99  # Default price
        recommendation = pricing_engine.optimize_price(
            current_price=current_price,
            competitor_prices=comp_prices,
            elasticity=elasticity,
            inventory_level=product.get('inventory_level', 50),
            strategy=strategy
        )
        
        # Update with product ID
        recommendation.product_id = product_id
        
        # Save recommendation
        await conn.execute("""
            INSERT INTO pricing_data.price_recommendations 
            (product_id, current_price, recommended_price, strategy, 
             competitor_avg, price_elasticity, expected_volume_change,
             profit_impact, confidence, reasons)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
        """, product_id, recommendation.current_price, recommendation.recommended_price,
            recommendation.strategy.value, recommendation.competitor_avg,
            recommendation.price_elasticity, recommendation.expected_volume_change,
            recommendation.profit_impact, recommendation.confidence,
            json.dumps(recommendation.reasons))
        
        return {
            "product": {
                "id": product_id,
                "name": product['name'],
                "brand": product['brand'],
                "category": product['category']
            },
            "recommendation": {
                "current_price": recommendation.current_price,
                "recommended_price": recommendation.recommended_price,
                "price_change": recommendation.recommended_price - recommendation.current_price,
                "price_change_pct": ((recommendation.recommended_price - recommendation.current_price) / recommendation.current_price * 100) if recommendation.current_price > 0 else 0,
                "strategy": recommendation.strategy.value,
                "competitor_avg": recommendation.competitor_avg,
                "confidence": recommendation.confidence,
                "reasons": recommendation.reasons,
                "expected_impact": {
                    "volume_change": f"{recommendation.expected_volume_change*100:.1f}%",
                    "profit_impact": f"${recommendation.profit_impact:.2f}"
                }
            },
            "market_data": {
                "competitors_analyzed": len(competitor_prices),
                "price_range": {
                    "min": min(comp_prices) if comp_prices else None,
                    "max": max(comp_prices) if comp_prices else None
                },
                "elasticity": elasticity
            }
        }
        
    finally:
        await conn.close()

@app.post("/pricing/simulate-competitor-data")
async def simulate_competitor_data():
    """Simulate competitor pricing data for testing"""
    
    conn = await asyncpg.connect(**DB_CONFIG)
    
    try:
        # Get sample products
        products = await conn.fetch("""
            SELECT id, name, brand, category, size, thc_min_percent 
            FROM cannabis_data.products 
            LIMIT 100
        """)
        
        competitors = ["Ontario Cannabis Store", "Tokyo Smoke", "Spiritleaf", "Fire & Flower"]
        
        inserted = 0
        for product in products:
            for competitor in competitors:
                # Generate realistic price based on category
                base_price = 25.0
                if product['category'] == 'Edibles':
                    base_price = 8.0
                elif product['category'] == 'Concentrates':
                    base_price = 45.0
                elif product['category'] == 'Pre-Rolls':
                    base_price = 12.0
                
                # Add some variation
                price = base_price * (0.8 + np.random.random() * 0.4)
                
                await conn.execute("""
                    INSERT INTO pricing_data.competitor_prices
                    (competitor_name, product_name, product_hash, price, size, 
                     thc_content, scraped_at)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                """, competitor, product['name'], 
                    hashlib.md5(product['name'].encode()).hexdigest()[:16],
                    round(price, 2), product['size'], 
                    float(product['thc_min_percent']) if product['thc_min_percent'] else None,
                    datetime.now() - timedelta(hours=np.random.randint(0, 48)))
                
                inserted += 1
        
        return {
            "message": "Competitor data simulated successfully",
            "records_created": inserted
        }
        
    finally:
        await conn.close()

@app.get("/pricing/recommendations")
async def get_all_recommendations(limit: int = 20):
    """Get all recent pricing recommendations"""
    
    conn = await asyncpg.connect(**DB_CONFIG)
    
    try:
        recommendations = await conn.fetch("""
            SELECT r.*, p.name, p.brand, p.category
            FROM pricing_data.price_recommendations r
            JOIN cannabis_data.products p ON p.id::text = r.product_id
            ORDER BY r.created_at DESC
            LIMIT $1
        """, limit)
        
        return {
            "recommendations": [
                {
                    "product": {
                        "id": r['product_id'],
                        "name": r['name'],
                        "brand": r['brand'],
                        "category": r['category']
                    },
                    "pricing": {
                        "current": float(r['current_price']),
                        "recommended": float(r['recommended_price']),
                        "strategy": r['strategy'],
                        "confidence": float(r['confidence'])
                    },
                    "impact": {
                        "volume_change": f"{float(r['expected_volume_change'])*100:.1f}%",
                        "profit_impact": f"${float(r['profit_impact']):.2f}"
                    },
                    "created_at": r['created_at'].isoformat()
                }
                for r in recommendations
            ]
        }
        
    finally:
        await conn.close()

@app.post("/pricing/bulk-optimize")
async def bulk_optimize_prices(category: Optional[str] = None):
    """Optimize prices for multiple products"""
    
    conn = await asyncpg.connect(**DB_CONFIG)
    
    try:
        # Get products to optimize
        if category:
            products = await conn.fetch("""
                SELECT id FROM cannabis_data.products 
                WHERE category = $1 
                LIMIT 50
            """, category)
        else:
            products = await conn.fetch("""
                SELECT id FROM cannabis_data.products 
                LIMIT 50
            """)
        
        optimized = []
        for product in products:
            try:
                # Analyze each product
                result = await analyze_product_pricing(
                    str(product['id']), 
                    PriceStrategy.DYNAMIC
                )
                optimized.append({
                    "product_id": str(product['id']),
                    "status": "success",
                    "recommended_price": result['recommendation']['recommended_price']
                })
            except Exception as e:
                optimized.append({
                    "product_id": str(product['id']),
                    "status": "error",
                    "error": str(e)
                })
        
        return {
            "total_products": len(products),
            "successful": len([o for o in optimized if o['status'] == 'success']),
            "failed": len([o for o in optimized if o['status'] == 'error']),
            "results": optimized
        }
        
    finally:
        await conn.close()

if __name__ == "__main__":
    print("💰 Starting WeedGo Pricing Intelligence Service...")
    print(f"📊 Database: {DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}")
    print(f"🌐 API will be available at: http://localhost:8005")
    print(f"📚 API docs at: http://localhost:8005/docs")
    print("\n✨ Features:")
    print("  - Dynamic pricing optimization")
    print("  - Competitor price tracking")
    print("  - Price elasticity calculation")
    print("  - Multi-strategy pricing (competitive, penetration, premium, clearance)")
    print("  - Bulk price optimization")
    
    uvicorn.run(app, host="0.0.0.0", port=8005, log_level="info")