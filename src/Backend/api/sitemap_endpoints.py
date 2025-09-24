"""
Sitemap Generation API Endpoints
Generates dynamic XML sitemaps for SEO optimization
"""

from fastapi import APIRouter, Response, HTTPException, Query, Depends
from typing import Optional, List, Dict, Any
import logging
import asyncpg
import os
from datetime import datetime
import xml.etree.ElementTree as ET
from xml.dom import minidom

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/seo", tags=["seo"])

# Import robots endpoint
try:
    from api.robots_endpoints import router as robots_router
    router.include_router(robots_router)
except ImportError:
    pass

# Database connection pool
db_pool = None

async def get_db_pool():
    """Get or create database connection pool"""
    global db_pool
    if db_pool is None:
        db_pool = await asyncpg.create_pool(
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', 5434)),
            database=os.getenv('DB_NAME', 'ai_engine'),
            user=os.getenv('DB_USER', 'weedgo'),
            password=os.getenv('DB_PASSWORD', 'your_password_here'),
            min_size=1,
            max_size=10
        )
    return db_pool


async def get_db_connection():
    """Get database connection from pool"""
    pool = await get_db_pool()
    async with pool.acquire() as connection:
        yield connection


def create_xml_sitemap(urls: List[Dict[str, Any]]) -> str:
    """Create XML sitemap from URL list"""

    # Create root element
    urlset = ET.Element('urlset')
    urlset.set('xmlns', 'http://www.sitemaps.org/schemas/sitemap/0.9')
    urlset.set('xmlns:image', 'http://www.google.com/schemas/sitemap-image/1.1')

    for url_data in urls:
        url_elem = ET.SubElement(urlset, 'url')

        # Required: URL location
        loc = ET.SubElement(url_elem, 'loc')
        loc.text = url_data['loc']

        # Optional: Last modification date
        if 'lastmod' in url_data:
            lastmod = ET.SubElement(url_elem, 'lastmod')
            lastmod.text = url_data['lastmod']

        # Optional: Change frequency
        if 'changefreq' in url_data:
            changefreq = ET.SubElement(url_elem, 'changefreq')
            changefreq.text = url_data['changefreq']

        # Optional: Priority
        if 'priority' in url_data:
            priority = ET.SubElement(url_elem, 'priority')
            priority.text = str(url_data['priority'])

        # Optional: Image
        if 'image' in url_data and url_data['image']:
            image_elem = ET.SubElement(url_elem, 'image:image')
            image_loc = ET.SubElement(image_elem, 'image:loc')
            image_loc.text = url_data['image']

            if 'image_title' in url_data:
                image_title = ET.SubElement(image_elem, 'image:title')
                image_title.text = url_data['image_title']

    # Convert to string with pretty formatting
    rough_string = ET.tostring(urlset, encoding='unicode')
    reparsed = minidom.parseString(rough_string)

    return reparsed.toprettyxml(indent="  ", encoding='UTF-8').decode('utf-8')


@router.get("/sitemap.xml")
async def generate_sitemap(
    store_id: Optional[str] = Query(None, description="Store ID for store-specific sitemap"),
    base_url: str = Query("https://weedgo.com", description="Base URL for the sitemap"),
    conn = Depends(get_db_connection)
):
    """
    Generate dynamic XML sitemap for SEO
    """
    try:
        urls = []

        # Add static pages
        static_pages = [
            {'loc': base_url, 'changefreq': 'daily', 'priority': 1.0},
            {'loc': f"{base_url}/products", 'changefreq': 'daily', 'priority': 0.9},
            {'loc': f"{base_url}/about", 'changefreq': 'weekly', 'priority': 0.5},
            {'loc': f"{base_url}/contact", 'changefreq': 'monthly', 'priority': 0.5},
            {'loc': f"{base_url}/login", 'changefreq': 'monthly', 'priority': 0.3},
            {'loc': f"{base_url}/register", 'changefreq': 'monthly', 'priority': 0.3},
        ]
        urls.extend(static_pages)

        # Get all active categories
        category_query = """
            SELECT DISTINCT
                LOWER(REPLACE(category, ' ', '-')) as slug,
                category as name,
                COUNT(*) as product_count
            FROM ocs_product_catalog
            WHERE category IS NOT NULL
            GROUP BY category
            ORDER BY product_count DESC
        """
        categories = await conn.fetch(category_query)

        for cat in categories:
            urls.append({
                'loc': f"{base_url}/cannabis/{cat['slug']}",
                'changefreq': 'weekly',
                'priority': 0.8
            })

        # Get all products with their slugs
        product_query = """
            SELECT
                slug,
                product_name,
                ocs_variant_number,
                updated_at,
                image_url
            FROM ocs_product_catalog
            WHERE slug IS NOT NULL
            ORDER BY updated_at DESC
            LIMIT 5000
        """

        if store_id:
            product_query = """
                SELECT
                    p.slug,
                    p.product_name,
                    p.ocs_variant_number,
                    p.updated_at,
                    p.image_url
                FROM ocs_product_catalog p
                JOIN ocs_inventory i ON p.ocs_variant_number = i.ocs_variant_number
                WHERE p.slug IS NOT NULL
                    AND i.store_id = $1
                    AND i.quantity_on_hand > 0
                ORDER BY p.updated_at DESC
                LIMIT 5000
            """
            products = await conn.fetch(product_query, store_id)
        else:
            products = await conn.fetch(product_query)

        # Add product URLs
        for product in products:
            # Default city for SEO URLs
            city = 'toronto'

            url_data = {
                'loc': f"{base_url}/dispensary-near-me/{city}/{product['slug']}",
                'changefreq': 'weekly',
                'priority': 0.7
            }

            if product['updated_at']:
                url_data['lastmod'] = product['updated_at'].strftime('%Y-%m-%d')

            if product['image_url']:
                url_data['image'] = product['image_url']
                url_data['image_title'] = product['product_name']

            urls.append(url_data)

        # Get all brands
        brand_query = """
            SELECT DISTINCT
                LOWER(REPLACE(brand, ' ', '-')) as slug,
                brand as name,
                COUNT(*) as product_count
            FROM ocs_product_catalog
            WHERE brand IS NOT NULL
            GROUP BY brand
            ORDER BY product_count DESC
            LIMIT 100
        """
        brands = await conn.fetch(brand_query)

        for brand in brands:
            urls.append({
                'loc': f"{base_url}/brands/{brand['slug']}",
                'changefreq': 'weekly',
                'priority': 0.6
            })

        # Get store locations if applicable
        if not store_id:
            stores_query = """
                SELECT
                    store_code,
                    name,
                    address->>'city' as city,
                    updated_at
                FROM stores
                WHERE status = 'active'
            """
            stores = await conn.fetch(stores_query)

            for store in stores:
                city_slug = store['city'].lower().replace(' ', '-') if store['city'] else 'location'
                urls.append({
                    'loc': f"{base_url}/{city_slug}-dispensary",
                    'changefreq': 'weekly',
                    'priority': 0.8,
                    'lastmod': store['updated_at'].strftime('%Y-%m-%d') if store['updated_at'] else None
                })

        # Generate XML sitemap
        xml_content = create_xml_sitemap(urls)

        return Response(
            content=xml_content,
            media_type="application/xml",
            headers={
                "Cache-Control": "public, max-age=3600"  # Cache for 1 hour
            }
        )

    except Exception as e:
        logger.error(f"Error generating sitemap: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate sitemap")


@router.get("/sitemap-index.xml")
async def generate_sitemap_index(
    base_url: str = Query("https://weedgo.com", description="Base URL for the sitemap"),
    conn = Depends(get_db_connection)
):
    """
    Generate sitemap index for multiple sitemaps
    """
    try:
        # Create root element for sitemap index
        sitemapindex = ET.Element('sitemapindex')
        sitemapindex.set('xmlns', 'http://www.sitemaps.org/schemas/sitemap/0.9')

        # Main sitemap
        main_sitemap = ET.SubElement(sitemapindex, 'sitemap')
        loc = ET.SubElement(main_sitemap, 'loc')
        loc.text = f"{base_url}/api/seo/sitemap.xml"
        lastmod = ET.SubElement(main_sitemap, 'lastmod')
        lastmod.text = datetime.now().strftime('%Y-%m-%d')

        # Get all active stores for store-specific sitemaps
        stores_query = """
            SELECT store_code, name, updated_at
            FROM stores
            WHERE status = 'active'
        """
        stores = await conn.fetch(stores_query)

        for store in stores:
            store_sitemap = ET.SubElement(sitemapindex, 'sitemap')
            loc = ET.SubElement(store_sitemap, 'loc')
            loc.text = f"{base_url}/api/seo/sitemap.xml?store_id={store['store_code']}"
            lastmod = ET.SubElement(store_sitemap, 'lastmod')
            lastmod.text = store['updated_at'].strftime('%Y-%m-%d') if store['updated_at'] else datetime.now().strftime('%Y-%m-%d')

        # Convert to string with pretty formatting
        rough_string = ET.tostring(sitemapindex, encoding='unicode')
        reparsed = minidom.parseString(rough_string)

        xml_content = reparsed.toprettyxml(indent="  ", encoding='UTF-8').decode('utf-8')

        return Response(
            content=xml_content,
            media_type="application/xml",
            headers={
                "Cache-Control": "public, max-age=3600"  # Cache for 1 hour
            }
        )

    except Exception as e:
        logger.error(f"Error generating sitemap index: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate sitemap index")