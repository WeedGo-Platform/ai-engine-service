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

# Import our data cleaning services
from services.product_data_cleaner import ProductDataCleaner
from services.llm_enhanced_product_cleaner import LLMEnhancedProductCleaner

# Import browser automation for JavaScript-heavy sites
from services.browser_automation import (
    BrowserAutomationService,
    BarcodeProductScraper
)

logger = logging.getLogger(__name__)

# Optional OCR imports
try:
    import pytesseract
    from PIL import Image
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    logger.warning("OCR not available. Install pytesseract and Pillow for OCR support.")

# Import advanced OCR extraction system
try:
    from services.ocr_extraction import accessory_extractor, ocr_service
    from services.ocr_extraction.domain.value_objects import ExtractionOptions
    ADVANCED_OCR_AVAILABLE = True
    logger.info("Advanced OCR extraction system available (MiniCPM-V, PaddleOCR-VL)")
except ImportError as e:
    ADVANCED_OCR_AVAILABLE = False
    logger.warning(f"Advanced OCR not available: {e}. Falling back to basic Tesseract if available.")


class BarcodeLookupService:
    """
    Intelligent barcode lookup with multiple fallback strategies
    Priority: Cache → Database → Web APIs → Web Scraping → OCR → Manual
    """
    
    def __init__(self, redis_client=None, db_connection=None, llm_router=None):
        self.redis = redis_client or redis.Redis(
            host='localhost',
            port=6379,
            db=0,
            decode_responses=True
        )
        self.db = db_connection
        self.session = None

        # Initialize data cleaners
        self.cleaner = ProductDataCleaner()  # Fallback for sync operations
        self.llm_cleaner = LLMEnhancedProductCleaner(
            llm_router=llm_router,
            confidence_threshold=0.6  # Use LLM if confidence < 60%
        )

        # Initialize browser automation for JavaScript-heavy sites
        self.browser_service = BrowserAutomationService()
        self.barcode_scraper = BarcodeProductScraper(self.browser_service)
        logger.info("Browser automation initialized for JavaScript-heavy sites")

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
                'name': 'ONE Wholesale',
                'search_url': 'https://www.onewholesale.ca/search?q={query}',
                'scraper': self._scrape_one_wholesale
            },
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
        if web_data and web_data.get('confidence', 0) >= 0.5:
            logger.info(f"Web lookup successful for barcode: {barcode}")

            # Validate and fix image URL if needed
            if 'image_candidates' in web_data:
                validated_image = await self._validate_image_urls(web_data['image_candidates'])
                if validated_image:
                    web_data['image_url'] = validated_image
                else:
                    # No valid image found, remove image_url
                    web_data.pop('image_url', None)
                # Remove candidates from final data
                web_data.pop('image_candidates', None)

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
                ON CONFLICT ON CONSTRAINT accessories_catalog_barcode_unique DO UPDATE SET
                    name = EXCLUDED.name,
                    brand = EXCLUDED.brand,
                    description = EXCLUDED.description,
                    image_url = EXCLUDED.image_url,
                    msrp = EXCLUDED.msrp,
                    confidence_score = EXCLUDED.confidence_score
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

    async def _validate_image_urls(self, image_urls: List[str]) -> Optional[str]:
        """
        Validate image URLs and return the first working one
        Checks each URL with HEAD request to avoid downloading full image
        """
        if not self.session:
            return image_urls[0] if image_urls else None

        for url in image_urls:
            try:
                async with self.session.head(url, timeout=5, allow_redirects=True) as response:
                    if response.status == 200:
                        logger.info(f"Valid image found: {url}")
                        return url
                    else:
                        logger.debug(f"Image URL returned {response.status}: {url}")
            except Exception as e:
                logger.debug(f"Image validation failed for {url}: {e}")
                continue

        logger.warning(f"No valid images found from {len(image_urls)} candidates")
        return None

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

                    # Scrape data (sync operation)
                    data = scraper_func(html, source_name)

                    # Apply LLM enhancement (async) - automatically uses rules first
                    if data:
                        data = await self.llm_cleaner.clean_product_data(data)

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
        
        # Look for brand and other metadata in HTML tables FIRST
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cols = row.find_all('td')
                if len(cols) >= 2:
                    label = cols[0].text.strip().lower()
                    value = cols[1].text.strip()

                    if 'brand' in label and value and 'brand' not in data:
                        data['brand'] = value
                    elif 'category' in label and value and 'category' not in data:
                        data['category'] = value
                    elif 'manufacturer' in label and value and 'manufacturer' not in data:
                        data['manufacturer'] = value

        # Only try to extract brand from product name if not found in tables
        if 'name' in data and 'brand' not in data:
            name_parts = data['name'].split()
            if name_parts:
                potential_brand = name_parts[0]
                # Check if it's actually a valid brand (not a number, uppercase, > 2 chars)
                if (potential_brand and
                    potential_brand[0].isupper() and
                    not potential_brand[0].isdigit() and
                    len(potential_brand) > 2):
                    data['brand'] = potential_brand

        # Look for product images - collect ALL available images for fallback
        image_candidates = []

        # Method 1: Look for <img class="product">
        product_img = soup.find('img', class_='product')
        if product_img:
            img_src = product_img.get('src')
            if img_src:
                # Normalize to absolute URL
                if img_src.startswith('http'):
                    image_candidates.append(img_src)
                elif img_src.startswith('//'):
                    image_candidates.append('https:' + img_src)
                elif img_src.startswith('/'):
                    image_candidates.append('https://www.upcitemdb.com' + img_src)

        # Method 2: Look in image list div for additional images
        imglist_div = soup.find('div', class_='imglist')
        if imglist_div:
            for img in imglist_div.find_all('img'):
                img_src = img.get('src')
                if img_src and img_src.startswith('http') and img_src not in image_candidates:
                    image_candidates.append(img_src)

        # Store all image candidates for later validation
        if image_candidates:
            data['image_candidates'] = image_candidates
            # Use first one for now (will be validated later)
            data['image_url'] = image_candidates[0]

        # Look for prices in the table
        price_matches = re.findall(r'\$(\d+\.?\d*)', html)
        if price_matches:
            try:
                data['price'] = float(price_matches[0])
            except:
                pass

        # Calculate confidence based on completeness
        # Note: LLM enhancement will boost this in _fetch_and_scrape
        fields_found = sum(1 for k in ['name', 'brand', 'image_url'] if k in data and data[k])
        data['confidence'] = min(fields_found / 3.0, 0.8)  # Cap at 0.8 for web scraping

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
        # Note: LLM enhancement will boost this in _fetch_and_scrape
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

        # Calculate confidence
        # Note: LLM enhancement will boost this in _fetch_and_scrape
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

        # Calculate confidence
        # Note: LLM enhancement will boost this in _fetch_and_scrape
        base_confidence = 0.7 if 'name' in data else 0.0
        if 'price' in data:
            base_confidence = 0.8
        data['confidence'] = base_confidence

        return data
    
    async def _search_smoke_shops(self, barcode: str) -> Optional[Dict[str, Any]]:
        """Search smoke shop sites for accessories"""

        # Special handling: Try ONE Wholesale with browser automation first
        # (JavaScript-heavy site that requires browser rendering)
        try:
            logger.info("Trying ONE Wholesale with browser automation...")
            one_wholesale_result = await self._scrape_one_wholesale_with_browser(barcode)

            # Check if we got usable results (need at least a product name)
            if (one_wholesale_result.get('confidence', 0) > 0.5 and
                one_wholesale_result.get('name')):
                logger.info(f"ONE Wholesale found product with confidence {one_wholesale_result['confidence']:.2f}")
                # Apply LLM enhancement if confidence is below threshold
                one_wholesale_result = await self.llm_cleaner.clean_product_data(one_wholesale_result)
                return one_wholesale_result
            elif one_wholesale_result.get('confidence', 0) > 0:
                logger.info(f"ONE Wholesale found partial data (no name), continuing to other sources...")
        except Exception as e:
            logger.warning(f"ONE Wholesale browser automation failed: {e}")

        # Fallback: Try other smoke shop sites with static scraping
        tasks = []
        for site in self.SMOKE_SHOP_SITES:
            # Skip ONE Wholesale (already tried with browser automation)
            if site['name'] == 'ONE Wholesale':
                continue

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

    def _scrape_one_wholesale(self, html: str, source: str) -> Dict[str, Any]:
        """Scrape product from ONE Wholesale (Shopify-based B2B site)"""
        soup = BeautifulSoup(html, 'html.parser')
        data = {'source': source}

        # Try multiple Shopify product selectors (themes vary)
        product = None
        selectors = [
            ('div', 'product-card'),
            ('div', 'grid-item'),
            ('div', 'product-item'),
            ('article', 'product'),
            ('li', 'product')
        ]

        for tag, class_name in selectors:
            product = soup.find(tag, class_=lambda x: x and class_name in x if x else False)
            if product:
                break

        # Also try looking for product data in script tags (common in Shopify)
        if not product:
            script_tags = soup.find_all('script', type='application/ld+json')
            for script in script_tags:
                try:
                    json_data = json.loads(script.string)
                    if isinstance(json_data, dict) and json_data.get('@type') == 'Product':
                        data['name'] = json_data.get('name', '')
                        data['brand'] = json_data.get('brand', {}).get('name', '')
                        if 'offers' in json_data:
                            offers = json_data['offers']
                            if isinstance(offers, dict):
                                price_str = offers.get('price', '')
                                if price_str:
                                    data['price'] = float(price_str)
                            elif isinstance(offers, list) and offers:
                                price_str = offers[0].get('price', '')
                                if price_str:
                                    data['price'] = float(price_str)
                        if 'image' in json_data:
                            img = json_data['image']
                            if isinstance(img, list):
                                data['image_url'] = img[0]
                            elif isinstance(img, str):
                                data['image_url'] = img
                        data['confidence'] = 0.75 if 'name' in data else 0.0
                        return data
                except (json.JSONDecodeError, AttributeError, ValueError):
                    continue

        # Parse from HTML if product found
        if product:
            # Product name - try multiple selectors
            name_selectors = [
                ('h2', None),
                ('h3', None),
                ('a', 'product-title'),
                ('a', 'product-link'),
                ('div', 'product-title'),
                ('span', 'product-title')
            ]
            for tag, class_name in name_selectors:
                if class_name:
                    name = product.find(tag, class_=lambda x: x and class_name in x if x else False)
                else:
                    name = product.find(tag)
                if name:
                    data['name'] = name.text.strip()
                    break

            # Brand (if available)
            brand = product.find('div', class_=lambda x: x and 'vendor' in x if x else False)
            if brand:
                data['brand'] = brand.text.strip()

            # Price - look for common Shopify price classes
            price_selectors = [
                ('span', 'price'),
                ('span', 'money'),
                ('div', 'price'),
                ('p', 'price')
            ]
            for tag, class_name in price_selectors:
                price = product.find(tag, class_=lambda x: x and class_name in x if x else False)
                if price:
                    price_text = re.findall(r'[\d.]+', price.text)
                    if price_text:
                        data['price'] = float(price_text[0])
                        break

            # Image
            img = product.find('img')
            if img:
                img_src = img.get('src') or img.get('data-src') or img.get('data-srcset', '').split(',')[0].split(' ')[0]
                if img_src:
                    if img_src.startswith('//'):
                        data['image_url'] = 'https:' + img_src
                    elif img_src.startswith('/'):
                        data['image_url'] = 'https://www.onewholesale.ca' + img_src
                    else:
                        data['image_url'] = img_src

            # Category hint for smoke shop products
            data['category'] = 'Smoking Accessories'

        # For B2B sites like ONE Wholesale, boost confidence slightly if found
        # because they typically have cleaner, more reliable data
        data['confidence'] = 0.75 if 'name' in data else 0.0
        return data

    async def _scrape_one_wholesale_with_browser(self, barcode: str) -> Dict[str, Any]:
        """
        Scrape ONE Wholesale using browser automation

        This replaces the static HTML scraper for ONE Wholesale because
        the site uses JavaScript to render product search results.

        Args:
            barcode: Barcode to search for

        Returns:
            Dictionary with product data in standard format
        """
        try:
            # Use browser automation scraper
            result = await self.barcode_scraper.scrape_one_wholesale(barcode)

            # Convert to format expected by lookup_barcode
            if result['found'] and result['data']:
                return {
                    'name': result['data'].get('name'),
                    'brand': result['data'].get('brand'),
                    'price': result['data'].get('price'),
                    'image_url': result['data'].get('image_url'),
                    'sku': result['data'].get('sku'),
                    'category': result['data'].get('category', 'Smoking Accessories'),
                    'confidence': result['confidence'],
                    'source': 'ONE Wholesale',
                    'strategy_used': result['strategy_used'],  # Track which strategy was used
                }
            else:
                return {
                    'source': 'ONE Wholesale',
                    'confidence': 0.0
                }

        except Exception as e:
            logger.error(f"Browser automation failed for ONE Wholesale: {e}")
            return {
                'source': 'ONE Wholesale',
                'confidence': 0.0,
                'error': str(e)
            }

    async def ocr_extract(self, image_data: str, store_id: str = None) -> Dict[str, Any]:
        """
        Extract product information from image using OCR
        Expects base64 encoded image data

        Uses advanced OCR system (MiniCPM-V, PaddleOCR-VL) if available,
        falls back to basic Tesseract if not.
        """
        # Try advanced OCR first
        if ADVANCED_OCR_AVAILABLE:
            try:
                logger.info("Using advanced OCR extraction system")

                # Initialize OCR service if not already done
                if not ocr_service.is_initialized:
                    await ocr_service.initialize()
                    logger.info("OCR service initialized")

                # Decode base64 image to create temporary file
                image_bytes = base64.b64decode(image_data)

                # Use hybrid strategy for best results (local first, cloud fallback if needed)
                options = ExtractionOptions(strategy='hybrid')

                # Extract using accessory template
                result = await accessory_extractor.extract_from_bytes(
                    image_bytes,
                    extraction_options=options
                )

                # Transform to expected format
                data = {
                    'product_name': result.extracted_data.get('product_name', ''),
                    'brand': result.extracted_data.get('brand', ''),
                    'barcode': result.extracted_data.get('barcode', ''),
                    'sku': result.extracted_data.get('sku', ''),
                    'price': result.extracted_data.get('price'),
                    'quantity': result.extracted_data.get('quantity'),
                    'description': result.extracted_data.get('description', ''),
                    'category': result.extracted_data.get('category', ''),
                    'confidence': result.get_overall_confidence(),
                    'provider': result.provider_name,
                    'extraction_time': result.extraction_time
                }

                # Save OCR history
                if self.db and store_id:
                    cursor = self.db.cursor()
                    try:
                        cursor.execute("""
                            INSERT INTO ocr_scan_history
                            (store_id, extracted_text, extracted_data, confidence_score, status, provider)
                            VALUES (%s, %s, %s, %s, %s, %s)
                        """, (
                            store_id,
                            json.dumps(result.extracted_data),  # Full extracted data as text
                            json.dumps(data),
                            data['confidence'],
                            'success' if data['confidence'] > 0.5 else 'low_confidence',
                            result.provider_name
                        ))
                        self.db.commit()
                    except Exception as db_err:
                        logger.warning(f"Failed to save OCR history: {db_err}")
                        self.db.rollback()
                    finally:
                        cursor.close()

                logger.info(f"Advanced OCR completed: confidence={data['confidence']:.2%}, provider={result.provider_name}")
                return data

            except Exception as e:
                logger.error(f"Advanced OCR extraction error: {e}", exc_info=True)
                # Fall through to basic OCR

        # Fallback to basic Tesseract OCR
        if not OCR_AVAILABLE:
            return {
                'error': 'OCR not available. Install pytesseract and Pillow, or configure advanced OCR models.',
                'confidence': 0,
                'requires_manual_entry': True
            }

        try:
            logger.info("Using basic Tesseract OCR (fallback)")

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
                try:
                    cursor.execute("""
                        INSERT INTO ocr_scan_history
                        (store_id, extracted_text, extracted_data, confidence_score, status, provider)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (
                        store_id,
                        extracted_text,
                        json.dumps(data),
                        data.get('confidence', 0),
                        'success' if data else 'failed',
                        'tesseract'
                    ))
                    self.db.commit()
                except Exception as db_err:
                    logger.warning(f"Failed to save OCR history: {db_err}")
                    self.db.rollback()
                finally:
                    cursor.close()

            logger.info(f"Basic OCR completed: confidence={data.get('confidence', 0):.2%}")
            return data

        except Exception as e:
            logger.error(f"Basic OCR extraction error: {e}")
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

def get_lookup_service(llm_router=None):
    """
    Get or create singleton lookup service

    Args:
        llm_router: Optional LLMRouter instance for enhanced data cleaning

    Returns:
        BarcodeLookupService instance
    """
    global _lookup_service
    if _lookup_service is None:
        # Get database connection
        from database.connection import get_db_connection
        db_conn = get_db_connection()

        # Create service with optional LLM router
        _lookup_service = BarcodeLookupService(
            db_connection=db_conn,
            llm_router=llm_router
        )

        if llm_router:
            logger.info("BarcodeLookupService initialized with LLM enhancement")
        else:
            logger.info("BarcodeLookupService initialized without LLM (rules-only mode)")

    return _lookup_service