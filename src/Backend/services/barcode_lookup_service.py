"""
Intelligent Barcode Lookup Service for Accessories
Multi-tier lookup system with caching and web scraping
"""

import asyncio
import aiohttp
import redis
import json
import logging
import hashlib
import re
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
import io
import base64

logger = logging.getLogger(__name__)

# Optional OCR imports
try:
    import pytesseract
    from PIL import Image
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    logger.warning("OCR not available. Install pytesseract and Pillow for OCR support.")


class BarcodeLookupService:
    """
    Intelligent barcode lookup with multiple fallback strategies
    Priority: Cache → Database → Web APIs → Web Scraping → OCR → Manual
    """
    
    def __init__(self, redis_client=None, db_connection=None):
        self.redis = redis_client or redis.Redis(
            host='localhost', 
            port=6379, 
            db=0,
            decode_responses=True
        )
        self.db = db_connection
        self.session = None
        
        # Cache settings
        self.CACHE_TTL = 86400 * 30  # 30 days
        self.CACHE_PREFIX = "barcode:"
        
        # Free UPC/Barcode lookup sources
        self.LOOKUP_SOURCES = [
            {
                'name': 'UPCItemDB',
                'url': 'https://www.upcitemdb.com/upc/{barcode}',
                'scraper': self._scrape_upcitemdb
            },
            {
                'name': 'Barcode Lookup',
                'url': 'https://www.barcodelookup.com/{barcode}',
                'scraper': self._scrape_barcodelookup
            },
            {
                'name': 'EAN Search',
                'url': 'https://www.ean-search.org/?q={barcode}',
                'scraper': self._scrape_ean_search
            },
            {
                'name': 'Google Search',
                'url': 'https://www.google.com/search?q={barcode}',
                'scraper': self._scrape_google_search
            }
        ]
        
        # Smoke shop specific sites for paraphernalia
        self.SMOKE_SHOP_SITES = [
            {
                'name': 'SmokeCartel',
                'search_url': 'https://www.smokecartel.com/search?q={query}',
                'scraper': self._scrape_smoke_cartel
            },
            {
                'name': 'DankStop',
                'search_url': 'https://dankstop.com/search?q={query}',
                'scraper': self._scrape_dankstop
            },
            {
                'name': 'Grasscity',
                'search_url': 'https://www.grasscity.com/catalogsearch/result/?q={query}',
                'scraper': self._scrape_grasscity
            }
        ]
    
    async def __aenter__(self):
        """Async context manager entry"""
        import ssl
        import certifi
        
        # Create SSL context with certifi certificates
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        
        self.session = aiohttp.ClientSession(
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            },
            connector=aiohttp.TCPConnector(ssl=ssl_context)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def lookup_barcode(self, barcode: str, store_id: str = None) -> Dict[str, Any]:
        """
        Main entry point for barcode lookup
        Returns product data with confidence score
        """
        barcode = self._normalize_barcode(barcode)
        
        # Level 1: Check memory cache (Redis)
        cached_data = await self._check_cache(barcode)
        if cached_data:
            logger.info(f"Cache hit for barcode: {barcode}")
            cached_data['source'] = 'cache'
            return cached_data
        
        # Level 2: Check database
        db_data = await self._check_database(barcode)
        if db_data:
            logger.info(f"Database hit for barcode: {barcode}")
            await self._save_to_cache(barcode, db_data)
            db_data['source'] = 'database'
            return db_data
        
        # Level 3: Web lookup (parallel requests)
        web_data = await self._web_lookup(barcode)
        if web_data and web_data.get('confidence', 0) > 0.5:
            logger.info(f"Web lookup successful for barcode: {barcode}")
            await self._save_to_database(barcode, web_data)
            await self._save_to_cache(barcode, web_data)
            web_data['source'] = 'web'
            return web_data
        
        # Level 4: Return partial data for manual completion
        return {
            'barcode': barcode,
            'source': 'not_found',
            'confidence': 0,
            'requires_manual_entry': True,
            'partial_data': web_data or {}
        }
    
    def _normalize_barcode(self, barcode: str) -> str:
        """Normalize barcode format"""
        # Remove spaces and special characters
        barcode = re.sub(r'[^0-9A-Za-z]', '', barcode)
        
        # Add check digit for UPC-A if needed
        if len(barcode) == 11 and barcode.isdigit():
            barcode = barcode + self._calculate_upc_check_digit(barcode)
        
        return barcode.upper()
    
    def _calculate_upc_check_digit(self, barcode: str) -> str:
        """Calculate UPC-A check digit"""
        odd_sum = sum(int(barcode[i]) for i in range(0, 11, 2))
        even_sum = sum(int(barcode[i]) for i in range(1, 10, 2))
        total = odd_sum * 3 + even_sum
        check_digit = (10 - (total % 10)) % 10
        return str(check_digit)
    
    async def _check_cache(self, barcode: str) -> Optional[Dict[str, Any]]:
        """Check Redis cache for barcode data"""
        try:
            key = f"{self.CACHE_PREFIX}{barcode}"
            data = self.redis.get(key)
            if data:
                return json.loads(data)
        except Exception as e:
            logger.error(f"Cache lookup error: {e}")
        return None
    
    async def _save_to_cache(self, barcode: str, data: Dict[str, Any]):
        """Save data to Redis cache"""
        try:
            key = f"{self.CACHE_PREFIX}{barcode}"
            self.redis.setex(
                key,
                self.CACHE_TTL,
                json.dumps(data, default=str)
            )
        except Exception as e:
            logger.error(f"Cache save error: {e}")
    
    async def _check_database(self, barcode: str) -> Optional[Dict[str, Any]]:
        """Check PostgreSQL database for barcode"""
        if not self.db:
            return None
        
        try:
            cursor = self.db.cursor()
            cursor.execute("""
                SELECT 
                    id, name, brand, description, 
                    image_url, msrp, category_id
                FROM accessories_catalog
                WHERE barcode = %s
                LIMIT 1
            """, (barcode,))
            
            row = cursor.fetchone()
            if row:
                return {
                    'id': row[0],
                    'name': row[1],
                    'brand': row[2],
                    'description': row[3],
                    'image_url': row[4],
                    'price': float(row[5]) if row[5] else None,
                    'category_id': row[6],
                    'confidence': 1.0
                }
        except Exception as e:
            logger.error(f"Database lookup error: {e}")
        return None
    
    async def _save_to_database(self, barcode: str, data: Dict[str, Any]):
        """Save discovered product to database"""
        if not self.db:
            return
        
        try:
            cursor = self.db.cursor()
            
            # Generate SKU if not present
            sku = data.get('sku') or f"ACC-{barcode[-8:]}"
            
            cursor.execute("""
                INSERT INTO accessories_catalog 
                (barcode, sku, name, brand, description, image_url, 
                 msrp, data_source, confidence_score)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (barcode) DO UPDATE SET
                    name = EXCLUDED.name,
                    brand = EXCLUDED.brand,
                    description = EXCLUDED.description,
                    image_url = EXCLUDED.image_url
                RETURNING id
            """, (
                barcode,
                sku,
                data.get('name', 'Unknown Product'),
                data.get('brand'),
                data.get('description'),
                data.get('image_url'),
                data.get('price'),
                data.get('source', 'web'),
                data.get('confidence', 0.5)
            ))
            
            self.db.commit()
            product_id = cursor.fetchone()[0]
            data['id'] = product_id
            
        except Exception as e:
            logger.error(f"Database save error: {e}")
            self.db.rollback()
    
    async def _web_lookup(self, barcode: str) -> Optional[Dict[str, Any]]:
        """
        Perform web lookup using multiple sources
        Returns best match with highest confidence
        """
        if not self.session:
            import ssl
            import certifi
            ssl_context = ssl.create_default_context(cafile=certifi.where())
            self.session = aiohttp.ClientSession(
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'},
                connector=aiohttp.TCPConnector(ssl=ssl_context)
            )
        
        tasks = []
        for source in self.LOOKUP_SOURCES:
            url = source['url'].format(barcode=barcode)
            tasks.append(self._fetch_and_scrape(url, source['scraper'], source['name']))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out errors and empty results
        valid_results = [
            r for r in results 
            if r and isinstance(r, dict) and r.get('confidence', 0) > 0
        ]
        
        # Return result with highest confidence
        if valid_results:
            return max(valid_results, key=lambda x: x.get('confidence', 0))
        
        # Try smoke shop sites as fallback
        return await self._search_smoke_shops(barcode)
    
    async def _fetch_and_scrape(self, url: str, scraper_func, source_name: str) -> Optional[Dict[str, Any]]:
        """Fetch URL and scrape product data"""
        try:
            async with self.session.get(url, timeout=10) as response:
                if response.status == 200:
                    html = await response.text()
                    data = scraper_func(html, source_name)
                    return data
        except Exception as e:
            logger.debug(f"Failed to fetch {url}: {e}")
        return None
    
    def _scrape_upcitemdb(self, html: str, source: str) -> Dict[str, Any]:
        """Scrape product data from UPCItemDB"""
        soup = BeautifulSoup(html, 'html.parser')
        data = {'source': source}
        
        # Try multiple methods to extract product name
        # Method 1: From title tag
        title_tag = soup.find('title')
        if title_tag:
            title_text = title_tag.text.strip()
            # Extract product name from title (format: "UPC 123456 - Product Name | upcitemdb.com")
            if ' - ' in title_text and '|' in title_text:
                product_part = title_text.split(' - ', 1)[1].split('|')[0].strip()
                if product_part:
                    data['name'] = product_part
        
        # Method 2: From detailtitle paragraph with <b> tag
        if 'name' not in data:
            detail_p = soup.find('p', class_='detailtitle')
            if detail_p:
                bold_tag = detail_p.find('b')
                if bold_tag:
                    data['name'] = bold_tag.text.strip()
        
        # Method 3: Look for product info in table rows
        if 'name' not in data:
            # Find first <b> tag in a table that's not a header
            tables = soup.find_all('table')
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    cols = row.find_all('td')
                    if len(cols) >= 2:
                        # Second column often has product name in <b> tag
                        product_b = cols[1].find('b')
                        if product_b and product_b.text.strip():
                            data['name'] = product_b.text.strip()
                            break
                if 'name' in data:
                    break
        
        # Try to extract brand from product name
        if 'name' in data:
            # Common brand patterns
            name_parts = data['name'].split()
            if name_parts:
                potential_brand = name_parts[0]
                # Check if first word looks like a brand
                if potential_brand and potential_brand[0].isupper():
                    data['brand'] = potential_brand
        
        # Look for prices in the table
        price_matches = re.findall(r'\$(\d+\.?\d*)', html)
        if price_matches:
            try:
                data['price'] = float(price_matches[0])
            except:
                pass
        
        # Calculate confidence based on completeness
        fields_found = sum(1 for k in ['name', 'brand'] if k in data)
        data['confidence'] = min(fields_found / 2.0, 0.8)  # Cap at 0.8 for web scraping
        
        return data
    
    def _scrape_barcodelookup(self, html: str, source: str) -> Dict[str, Any]:
        """Scrape product data from BarcodeLookup"""
        soup = BeautifulSoup(html, 'html.parser')
        data = {'source': source}
        
        # Product details
        product_div = soup.find('div', class_='product-details')
        if product_div:
            name = product_div.find('h4')
            if name:
                data['name'] = name.text.strip()
            
            # Extract other details from list items
            details = product_div.find_all('li')
            for detail in details:
                text = detail.text.lower()
                if 'brand' in text:
                    data['brand'] = detail.text.split(':')[-1].strip()
                elif 'category' in text:
                    data['category'] = detail.text.split(':')[-1].strip()
        
        # Image
        img = soup.find('img', {'id': 'product-image'})
        if img:
            data['image_url'] = img.get('src')
        
        # Calculate confidence
        fields_found = sum(1 for k in ['name', 'brand'] if k in data)
        data['confidence'] = fields_found / 2.0
        
        return data
    
    def _scrape_ean_search(self, html: str, source: str) -> Dict[str, Any]:
        """Scrape product data from EAN Search"""
        soup = BeautifulSoup(html, 'html.parser')
        data = {'source': source}
        
        # Find product row
        product_row = soup.find('div', class_='product')
        if product_row:
            # Product name
            name_elem = product_row.find('a', class_='product-name')
            if name_elem:
                data['name'] = name_elem.text.strip()
            
            # Category
            cat_elem = product_row.find('span', class_='category')
            if cat_elem:
                data['category'] = cat_elem.text.strip()
            
            # Image
            img = product_row.find('img')
            if img:
                img_src = img.get('src') or img.get('data-src')
                if img_src:
                    # Make sure it's an absolute URL
                    if img_src.startswith('//'):
                        data['image_url'] = 'https:' + img_src
                    elif img_src.startswith('/'):
                        data['image_url'] = 'https://www.ean-search.org' + img_src
                    else:
                        data['image_url'] = img_src
        
        data['confidence'] = 0.5 if 'name' in data else 0.0
        return data
    
    def _scrape_google_search(self, html: str, source: str) -> Dict[str, Any]:
        """Scrape product data from Google search results"""
        soup = BeautifulSoup(html, 'html.parser')
        data = {'source': source}
        
        # Look for product information in regular Google search results
        # Method 1: Check for shopping results in regular search
        shopping_results = soup.find_all('div', class_='g')
        
        for result in shopping_results[:3]:  # Check first 3 results
            # Look for product title in h3 tags
            title_elem = result.find('h3')
            if title_elem:
                title_text = title_elem.text.strip()
                # Check if it looks like a product name (contains brand names, ml, etc)
                if any(word in title_text.lower() for word in ['butane', 'lighter', 'fluid', 'refill', 'ml', 'oz', 'pack']):
                    data['name'] = title_text
                    
                    # Try to extract brand from title
                    words = title_text.split()
                    if words and words[0][0].isupper():
                        data['brand'] = words[0]
                    
                    # Look for price in snippet
                    snippet = result.find('span', class_='aCOpRe') or result.find('div', class_='VwiC3b')
                    if snippet:
                        price_matches = re.findall(r'\$([\d.]+)', snippet.text)
                        if price_matches:
                            try:
                                data['price'] = float(price_matches[0])
                            except:
                                pass
                    
                    # Try to find image from Google Images or shopping results
                    img = result.find('img')
                    if img:
                        img_src = img.get('src') or img.get('data-src')
                        if img_src and not img_src.startswith('data:'):
                            data['image_url'] = img_src
                    break
        
        # Method 2: Look for product panels or knowledge graph
        product_panel = soup.find('div', {'data-attrid': re.compile('.*product.*', re.I)})
        if product_panel and 'name' not in data:
            title = product_panel.find('h2') or product_panel.find('h3')
            if title:
                data['name'] = title.text.strip()
        
        # Method 3: Check meta description for product info
        if 'name' not in data:
            meta_desc = soup.find('meta', {'name': 'description'})
            if meta_desc:
                desc_content = meta_desc.get('content', '')
                # Check if description contains product-like information
                if 'butane' in desc_content.lower() or 'lighter' in desc_content.lower():
                    # Extract first sentence as potential product name
                    sentences = desc_content.split('.')
                    if sentences:
                        data['name'] = sentences[0].strip()
        
        # Extract barcode-specific results
        if 'name' not in data:
            # Look for any text containing the barcode and product info
            barcode_pattern = re.compile(r'\b\d{12,13}\b')
            for text_elem in soup.find_all(text=barcode_pattern):
                parent = text_elem.parent
                if parent:
                    # Check surrounding text for product info
                    parent_text = parent.text.strip()
                    if len(parent_text) > 20 and len(parent_text) < 200:
                        data['name'] = parent_text
                        break
        
        data['confidence'] = 0.7 if 'name' in data else 0.0
        if 'price' in data:
            data['confidence'] = 0.8
        
        return data
    
    async def _search_smoke_shops(self, barcode: str) -> Optional[Dict[str, Any]]:
        """Search smoke shop sites for accessories"""
        # First try searching by barcode
        tasks = []
        for site in self.SMOKE_SHOP_SITES:
            url = site['search_url'].format(query=barcode)
            tasks.append(self._fetch_and_scrape(url, site['scraper'], site['name']))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        valid_results = [
            r for r in results 
            if r and isinstance(r, dict) and r.get('confidence', 0) > 0
        ]
        
        if valid_results:
            return max(valid_results, key=lambda x: x.get('confidence', 0))
        
        return None
    
    def _scrape_smoke_cartel(self, html: str, source: str) -> Dict[str, Any]:
        """Scrape product from SmokeCartel"""
        soup = BeautifulSoup(html, 'html.parser')
        data = {'source': source}
        
        # Find first product
        product = soup.find('div', class_='product-item')
        if product:
            # Name
            name = product.find('a', class_='product-item-link')
            if name:
                data['name'] = name.text.strip()
            
            # Price
            price = product.find('span', class_='price')
            if price:
                price_text = re.findall(r'[\d.]+', price.text)
                if price_text:
                    data['price'] = float(price_text[0])
            
            # Image
            img = product.find('img', class_='product-image')
            if img:
                data['image_url'] = img.get('src')
            
            # Category (usually glass, vaporizer, etc.)
            data['category'] = 'Smoking Accessories'
        
        data['confidence'] = 0.7 if 'name' in data else 0.0
        return data
    
    def _scrape_dankstop(self, html: str, source: str) -> Dict[str, Any]:
        """Scrape product from DankStop"""
        soup = BeautifulSoup(html, 'html.parser')
        data = {'source': source}
        
        # Find product grid item
        product = soup.find('div', class_='grid-item')
        if product:
            # Product name
            title = product.find('p', class_='grid-item__title')
            if title:
                data['name'] = title.text.strip()
            
            # Brand
            vendor = product.find('p', class_='grid-item__vendor')
            if vendor:
                data['brand'] = vendor.text.strip()
            
            # Price
            price = product.find('span', class_='grid-item__price--current')
            if price:
                price_text = re.findall(r'[\d.]+', price.text)
                if price_text:
                    data['price'] = float(price_text[0])
            
            # Image
            img = product.find('img', class_='grid-item__image')
            if not img:
                img = product.find('img')
            if img:
                img_src = img.get('src') or img.get('data-src')
                if img_src:
                    if img_src.startswith('//'):
                        data['image_url'] = 'https:' + img_src
                    elif img_src.startswith('/'):
                        data['image_url'] = 'https://dankstop.com' + img_src
                    else:
                        data['image_url'] = img_src
        
        data['confidence'] = 0.7 if 'name' in data else 0.0
        return data
    
    def _scrape_grasscity(self, html: str, source: str) -> Dict[str, Any]:
        """Scrape product from Grasscity"""
        soup = BeautifulSoup(html, 'html.parser')
        data = {'source': source}
        
        # Find product item
        product = soup.find('li', class_='product-item')
        if product:
            # Name
            name = product.find('a', class_='product-item-link')
            if name:
                data['name'] = name.text.strip()
            
            # Price
            price = product.find('span', class_='price')
            if price:
                price_text = re.findall(r'[\d.]+', price.text)
                if price_text:
                    data['price'] = float(price_text[0])
            
            # Image
            img = product.find('img', class_='product-image-photo')
            if not img:
                img = product.find('img')
            if img:
                img_src = img.get('src') or img.get('data-src')
                if img_src:
                    if img_src.startswith('//'):
                        data['image_url'] = 'https:' + img_src
                    elif img_src.startswith('/'):
                        data['image_url'] = 'https://www.grasscity.com' + img_src
                    else:
                        data['image_url'] = img_src
        
        data['confidence'] = 0.6 if 'name' in data else 0.0
        return data
    
    async def ocr_extract(self, image_data: str, store_id: str = None) -> Dict[str, Any]:
        """
        Extract product information from image using OCR
        Expects base64 encoded image data
        """
        if not OCR_AVAILABLE:
            return {
                'error': 'OCR not available. Install pytesseract and Pillow.',
                'confidence': 0,
                'requires_manual_entry': True
            }
            
        try:
            # Decode base64 image
            image_bytes = base64.b64decode(image_data)
            image = Image.open(io.BytesIO(image_bytes))
            
            # Extract text using Tesseract
            extracted_text = pytesseract.image_to_string(image)
            
            # Parse extracted text for product info
            data = self._parse_ocr_text(extracted_text)
            
            # Save OCR history
            if self.db and store_id:
                cursor = self.db.cursor()
                cursor.execute("""
                    INSERT INTO ocr_scan_history 
                    (store_id, extracted_text, extracted_data, confidence_score, status)
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    store_id,
                    extracted_text,
                    json.dumps(data),
                    data.get('confidence', 0),
                    'success' if data else 'failed'
                ))
                self.db.commit()
            
            return data
            
        except Exception as e:
            logger.error(f"OCR extraction error: {e}")
            return {
                'error': str(e),
                'confidence': 0,
                'requires_manual_entry': True
            }
    
    def _parse_ocr_text(self, text: str) -> Dict[str, Any]:
        """Parse OCR text to extract product information"""
        data = {}
        lines = text.split('\n')
        
        # Look for patterns
        for line in lines:
            line = line.strip()
            
            # Barcode patterns
            barcode_match = re.search(r'\b\d{8,14}\b', line)
            if barcode_match and 'barcode' not in data:
                data['barcode'] = barcode_match.group()
            
            # Price patterns
            price_match = re.search(r'\$?([\d,]+\.?\d{0,2})', line)
            if price_match and 'price' not in data:
                data['price'] = float(price_match.group(1).replace(',', ''))
            
            # SKU patterns
            sku_match = re.search(r'SKU[:\s]*([A-Z0-9\-]+)', line, re.I)
            if sku_match:
                data['sku'] = sku_match.group(1)
            
            # Quantity patterns
            qty_match = re.search(r'QTY[:\s]*(\d+)', line, re.I)
            if qty_match:
                data['quantity'] = int(qty_match.group(1))
        
        # Try to identify product name (usually one of the first non-numeric lines)
        for line in lines[:5]:
            line = line.strip()
            if len(line) > 10 and not re.match(r'^[\d\s\-.$]+$', line):
                if 'name' not in data:
                    data['name'] = line
                    break
        
        # Calculate confidence
        fields_found = sum(1 for k in ['barcode', 'name', 'price'] if k in data)
        data['confidence'] = fields_found / 3.0
        
        return data


# Singleton instance
_lookup_service = None

def get_lookup_service():
    """Get or create singleton lookup service"""
    global _lookup_service
    if _lookup_service is None:
        # Get database connection
        from database.connection import get_db_connection
        db_conn = get_db_connection()
        _lookup_service = BarcodeLookupService(db_connection=db_conn)
    return _lookup_service