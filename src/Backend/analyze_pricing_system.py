#!/usr/bin/env python3
import asyncio
import asyncpg
import os
import json

async def analyze_pricing_system():
    db_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', 5434)),
        'database': os.getenv('DB_NAME', 'ai_engine'),
        'user': os.getenv('DB_USER', 'weedgo'),
        'password': os.getenv('DB_PASSWORD', 'weedgo123')
    }
    
    try:
        conn = await asyncpg.connect(**db_config)
        
        print("=" * 80)
        print("PRICING AND PROMOTIONS ANALYSIS")
        print("=" * 80)
        
        # 1. Check for promotion/discount related tables
        print("\n1. CHECKING FOR PROMOTION/DISCOUNT TABLES:")
        print("-" * 40)
        tables = await conn.fetch("""
            SELECT tablename 
            FROM pg_tables 
            WHERE schemaname = 'public' 
            AND (
                tablename ILIKE '%promo%' OR 
                tablename ILIKE '%discount%' OR 
                tablename ILIKE '%price%' OR 
                tablename ILIKE '%recommend%' OR 
                tablename ILIKE '%deal%' OR 
                tablename ILIKE '%offer%' OR 
                tablename ILIKE '%coupon%' OR
                tablename ILIKE '%special%' OR
                tablename ILIKE '%sale%'
            )
            ORDER BY tablename
        """)
        
        if tables:
            for table in tables:
                print(f"  • {table['tablename']}")
        else:
            print("  No promotion/discount specific tables found")
        
        # 2. Check pricing fields in product_catalog
        print("\n2. PRICING STRUCTURE IN PRODUCT_CATALOG:")
        print("-" * 40)
        pricing_fields = await conn.fetch("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'product_catalog' 
            AND (
                column_name ILIKE '%price%' OR 
                column_name ILIKE '%cost%' OR 
                column_name ILIKE '%discount%' OR
                column_name ILIKE '%margin%'
            )
            ORDER BY ordinal_position
        """)
        
        if pricing_fields:
            for field in pricing_fields:
                print(f"  • {field['column_name']}: {field['data_type']}")
        
        # 3. Check for inventory pricing
        print("\n3. PRICING IN INVENTORY TABLES:")
        print("-" * 40)
        inv_pricing = await conn.fetch("""
            SELECT column_name, data_type, table_name
            FROM information_schema.columns 
            WHERE table_name IN ('inventory', 'batch_tracking', 'inventory_movements')
            AND (
                column_name ILIKE '%price%' OR 
                column_name ILIKE '%cost%'
            )
            ORDER BY table_name, ordinal_position
        """)
        
        if inv_pricing:
            current_table = None
            for field in inv_pricing:
                if current_table != field['table_name']:
                    current_table = field['table_name']
                    print(f"\n  Table: {current_table}")
                print(f"    • {field['column_name']}: {field['data_type']}")
        
        # 4. Check for customer/tenant specific pricing
        print("\n4. TENANT/CUSTOMER SPECIFIC PRICING:")
        print("-" * 40)
        tenant_pricing = await conn.fetch("""
            SELECT column_name, data_type, table_name
            FROM information_schema.columns 
            WHERE table_name IN ('tenants', 'tenant_settings', 'customer_profiles')
            AND (
                column_name ILIKE '%price%' OR 
                column_name ILIKE '%discount%' OR
                column_name ILIKE '%tier%' OR
                column_name ILIKE '%markup%'
            )
            ORDER BY table_name, ordinal_position
        """)
        
        if tenant_pricing:
            for field in tenant_pricing:
                print(f"  • {field['table_name']}.{field['column_name']}: {field['data_type']}")
        else:
            print("  No tenant-specific pricing fields found")
        
        # 5. Check purchase order pricing
        print("\n5. PURCHASE ORDER PRICING:")
        print("-" * 40)
        po_pricing = await conn.fetch("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'purchase_orders'
            AND (
                column_name ILIKE '%price%' OR 
                column_name ILIKE '%cost%' OR
                column_name ILIKE '%amount%' OR
                column_name ILIKE '%fee%'
            )
            ORDER BY ordinal_position
        """)
        
        if po_pricing:
            for field in po_pricing:
                print(f"  • {field['column_name']}: {field['data_type']}")
        
        # 6. Sample pricing data
        print("\n6. SAMPLE PRICING DATA:")
        print("-" * 40)
        samples = await conn.fetch("""
            SELECT 
                ocs_variant_number,
                product_name,
                unit_price,
                CASE 
                    WHEN unit_price > 0 THEN 
                        ROUND((unit_price * 0.3)::numeric, 2)  -- Assuming 30% markup
                    ELSE 0 
                END as potential_markup,
                category,
                brand
            FROM product_catalog
            WHERE unit_price IS NOT NULL AND unit_price > 0
            ORDER BY RANDOM()
            LIMIT 5
        """)
        
        for sample in samples:
            print(f"\n  Product: {sample['product_name']}")
            print(f"    SKU: {sample['ocs_variant_number']}")
            print(f"    Unit Price: ${sample['unit_price']}")
            print(f"    Potential Markup (30%): ${sample['potential_markup']}")
            print(f"    Category: {sample['category']}")
            print(f"    Brand: {sample['brand']}")
        
        # 7. Check for any recommendation or analytics tables
        print("\n7. RECOMMENDATION/ANALYTICS TABLES:")
        print("-" * 40)
        analytics_tables = await conn.fetch("""
            SELECT tablename 
            FROM pg_tables 
            WHERE schemaname = 'public' 
            AND (
                tablename ILIKE '%analytic%' OR 
                tablename ILIKE '%recommend%' OR 
                tablename ILIKE '%suggest%' OR 
                tablename ILIKE '%trend%' OR
                tablename ILIKE '%popular%' OR
                tablename ILIKE '%bestsell%'
            )
            ORDER BY tablename
        """)
        
        if analytics_tables:
            for table in analytics_tables:
                print(f"  • {table['tablename']}")
        else:
            print("  No recommendation/analytics tables found")
        
        # 8. Check for order/sales history for recommendation basis
        print("\n8. SALES/ORDER HISTORY TABLES:")
        print("-" * 40)
        sales_tables = await conn.fetch("""
            SELECT tablename 
            FROM pg_tables 
            WHERE schemaname = 'public' 
            AND (
                tablename ILIKE '%order%' OR 
                tablename ILIKE '%sale%' OR 
                tablename ILIKE '%transaction%' OR 
                tablename ILIKE '%invoice%'
            )
            ORDER BY tablename
        """)
        
        if sales_tables:
            for table in sales_tables:
                print(f"  • {table['tablename']}")
                # Get row count
                count = await conn.fetchval(f"SELECT COUNT(*) FROM {table['tablename']}")
                print(f"    Records: {count}")
        
        print("\n" + "=" * 80)
        print("RECOMMENDATIONS FOR PRICING & PROMOTIONS SYSTEM")
        print("=" * 80)
        
        print("""
1. PRICING STRATEGY COMPONENTS NEEDED:
   • Tiered pricing by customer type (dispensary size, volume)
   • Dynamic pricing based on inventory levels
   • Bulk discount schedules
   • Time-based promotions (happy hour, daily deals)
   • Bundle pricing for product combinations
   
2. SUGGESTED DATABASE TABLES TO CREATE:
   
   a) price_tiers
      - id, name, discount_percentage, min_order_value, customer_type
   
   b) promotions
      - id, name, type, discount_type (%, $), discount_value
      - start_date, end_date, active, conditions_json
   
   c) bundle_deals
      - id, name, products_json, bundle_price, savings_amount
   
   d) customer_pricing_rules
      - id, tenant_id, price_tier_id, custom_markup, volume_discounts_json
   
   e) product_recommendations
      - id, product_id, related_products_json, recommendation_type
      - score, reason
   
3. RECOMMENDATION ENGINE APPROACH:
   • Collaborative filtering (customers who bought X also bought Y)
   • Content-based (similar products by category, THC/CBD content)
   • Trending products (velocity of sales)
   • Inventory optimization (push slow-moving stock)
   • Complementary products (papers with flower, batteries with carts)
   
4. PROMOTION TYPES TO IMPLEMENT:
   • BOGO (Buy One Get One)
   • Volume discounts (10% off 10+ units)
   • Category sales (20% off all edibles)
   • Flash sales (limited time)
   • Loyalty points/rewards
   • First-time customer discounts
   • Bundle deals
   
5. PRICING RULES ENGINE:
   • Base price from product_catalog
   • Apply customer tier discount
   • Apply active promotions (stackable or exclusive)
   • Apply volume discounts
   • Calculate final price with taxes
        """)
        
        await conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(analyze_pricing_system())