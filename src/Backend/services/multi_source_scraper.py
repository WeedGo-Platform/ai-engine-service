"""
Multi-Source Product Data Scraper
Improves accuracy by aggregating data from multiple sources
"""

import asyncio
import aiohttp
from typing import Dict, Any, Optional, List
from bs4 import BeautifulSoup
import logging
import re
from collections import Counter

logger = logging.getLogger(__name__)


class MultiSourceScraper:
    """
    Scrapes product data from multiple sources and aggregates results
    Uses voting and confidence scoring to determine best data
    """

    def __init__(self, session: aiohttp.ClientSession = None):
        self.session = session

        # Data sources with different strengths
        self.sources = [
            {
                'name': 'UPCItemDB',
                'url': 'https://www.upcitemdb.com/upc/{barcode}',
                'weight': 1.0,  # Primary source
                'scraper': self._scrape_upcitemdb
            },
            {
                'name': 'BarcodeSpider',
                'url': 'https://www.barcodespider.com/{barcode}',
                'weight': 0.8,
                'scraper': self._scrape_barcodespider
            },
            {
                'name': 'EAN-Search',
                'url': 'https://www.ean-search.org/?q={barcode}',
                'weight': 0.7,
                'scraper': self._scrape_ean_search
            },
        ]

    async def aggregate_product_data(self, barcode: str) -> Dict[str, Any]:
        """
        Scrape from multiple sources and aggregate results

        Strategy:
        1. Scrape all sources in parallel
        2. Use voting for conflicting data
        3. Weight sources by reliability
        4. Return aggregated result with confidence score
        """
        if not self.session:
            raise ValueError("Session required for scraping")

        # Scrape all sources in parallel
        tasks = []
        for source in self.sources:
            url = source['url'].format(barcode=barcode)
            tasks.append(self._fetch_and_scrape(url, source))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter valid results
        valid_results = [
            r for r in results
            if r and isinstance(r, dict) and r.get('name')
        ]

        if not valid_results:
            return {'error': 'No valid data from any source'}

        # Aggregate data using voting
        aggregated = self._aggregate_results(valid_results)

        return aggregated

    async def _fetch_and_scrape(self, url: str, source: Dict) -> Optional[Dict[str, Any]]:
        """Fetch and scrape a single source"""
        try:
            async with self.session.get(url, timeout=10) as response:
                if response.status == 200:
                    html = await response.text()
                    data = source['scraper'](html)
                    data['_source'] = source['name']
                    data['_weight'] = source['weight']
                    return data
        except Exception as e:
            logger.debug(f"Failed to scrape {source['name']}: {e}")
        return None

    def _aggregate_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Aggregate data from multiple sources using weighted voting

        For conflicting data:
        - Name: Use most common (weighted by source reliability)
        - Brand: Use most common
        - Price: Use median
        - Image: Use first valid from highest weight source
        """
        aggregated = {}

        # Aggregate names (weighted voting)
        names = [(r['name'], r.get('_weight', 1.0)) for r in results if r.get('name')]
        if names:
            aggregated['name'] = self._weighted_vote([n[0] for n in names], [n[1] for n in names])

        # Aggregate brands
        brands = [r['brand'] for r in results if r.get('brand')]
        if brands:
            aggregated['brand'] = max(set(brands), key=brands.count)

        # Aggregate prices (median of all found prices)
        prices = [r['price'] for r in results if r.get('price')]
        if prices:
            prices.sort()
            aggregated['price'] = prices[len(prices) // 2]  # Median

        # Image from highest confidence source
        for result in sorted(results, key=lambda x: x.get('_weight', 0), reverse=True):
            if result.get('image_url'):
                aggregated['image_url'] = result['image_url']
                break

        # Calculate confidence based on source agreement
        aggregated['confidence'] = self._calculate_confidence(results, aggregated)

        # Add metadata
        aggregated['sources_checked'] = len(results)
        aggregated['sources_agreed'] = self._count_agreement(results, aggregated)

        return aggregated

    def _weighted_vote(self, items: List[str], weights: List[float]) -> str:
        """Vote for best item using weights"""
        vote_scores = {}
        for item, weight in zip(items, weights):
            vote_scores[item] = vote_scores.get(item, 0) + weight

        return max(vote_scores.items(), key=lambda x: x[1])[0]

    def _calculate_confidence(self, results: List[Dict], aggregated: Dict) -> float:
        """
        Calculate confidence based on:
        - Number of sources that agree
        - Quality of sources (weight)
        - Completeness of data
        """
        if not results:
            return 0.0

        # Base confidence from number of sources
        source_confidence = min(len(results) / 3.0, 1.0)  # Cap at 3 sources

        # Agreement boost
        agreement_count = self._count_agreement(results, aggregated)
        agreement_confidence = agreement_count / len(results)

        # Data completeness
        completeness = sum(1 for k in ['name', 'brand', 'price', 'image_url'] if aggregated.get(k))
        completeness_confidence = completeness / 4.0

        # Weighted average
        confidence = (
            source_confidence * 0.3 +
            agreement_confidence * 0.4 +
            completeness_confidence * 0.3
        )

        return min(confidence, 0.95)  # Cap at 0.95 (web data never 1.0)

    def _count_agreement(self, results: List[Dict], aggregated: Dict) -> int:
        """Count how many sources agree with aggregated result"""
        agreement = 0
        for result in results:
            agrees = True

            # Check name similarity (allowing for minor differences)
            if result.get('name') and aggregated.get('name'):
                if not self._strings_similar(result['name'], aggregated['name']):
                    agrees = False

            # Check brand match
            if result.get('brand') and aggregated.get('brand'):
                if result['brand'].lower() != aggregated['brand'].lower():
                    agrees = False

            if agrees:
                agreement += 1

        return agreement

    def _strings_similar(self, s1: str, s2: str, threshold: float = 0.8) -> bool:
        """Check if two strings are similar (simple word overlap)"""
        words1 = set(s1.lower().split())
        words2 = set(s2.lower().split())

        if not words1 or not words2:
            return False

        overlap = len(words1 & words2)
        union = len(words1 | words2)

        return overlap / union >= threshold

    def _scrape_upcitemdb(self, html: str) -> Dict[str, Any]:
        """Scrape UPCItemDB (already implemented)"""
        # Reuse existing implementation
        return {}

    def _scrape_barcodespider(self, html: str) -> Dict[str, Any]:
        """Scrape BarcodeSpider"""
        soup = BeautifulSoup(html, 'html.parser')
        data = {}

        # Extract product name
        title = soup.find('h1', class_='product-title')
        if title:
            data['name'] = title.text.strip()

        # Extract brand
        brand_elem = soup.find('span', class_='brand-name')
        if brand_elem:
            data['brand'] = brand_elem.text.strip()

        # Extract price
        price_elem = soup.find('span', class_='price')
        if price_elem:
            price_match = re.search(r'\$?([\d.]+)', price_elem.text)
            if price_match:
                data['price'] = float(price_match.group(1))

        return data

    def _scrape_ean_search(self, html: str) -> Dict[str, Any]:
        """Scrape EAN-Search"""
        soup = BeautifulSoup(html, 'html.parser')
        data = {}

        # Extract from product listing
        product = soup.find('div', class_='product')
        if product:
            name = product.find('a', class_='product-name')
            if name:
                data['name'] = name.text.strip()

            # Try to find brand in description
            description = product.find('div', class_='description')
            if description:
                # Brand often first word
                words = description.text.strip().split()
                if words:
                    data['brand'] = words[0]

        return data


class EnhancedProductValidator:
    """
    Validates and scores product data quality
    Helps identify which data sources are most reliable
    """

    @staticmethod
    def validate_product_name(name: str) -> tuple[bool, float, str]:
        """
        Validate product name quality

        Returns: (is_valid, confidence, reason)
        """
        if not name or len(name) < 5:
            return False, 0.0, "Name too short"

        if len(name) > 200:
            return False, 0.0, "Name too long (likely includes description)"

        # Check for spam/junk patterns
        junk_patterns = [
            r'click here',
            r'buy now',
            r'limited time',
            r'order today',
            r'\d{10,}',  # Long numbers (likely spam)
        ]

        for pattern in junk_patterns:
            if re.search(pattern, name, re.IGNORECASE):
                return False, 0.0, f"Contains spam pattern: {pattern}"

        # Calculate confidence
        confidence = 1.0

        # Reduce confidence for very long names
        if len(name) > 100:
            confidence -= 0.2

        # Boost confidence if name has proper structure
        if re.search(r'[A-Z][a-z]+', name):  # Has capitalized words
            confidence += 0.1

        return True, min(confidence, 1.0), "Valid"

    @staticmethod
    def validate_price(price: float, expected_range: tuple = (0.5, 500.0)) -> tuple[bool, str]:
        """
        Validate price is reasonable

        Returns: (is_valid, reason)
        """
        if not price or price <= 0:
            return False, "Price is zero or negative"

        min_price, max_price = expected_range

        if price < min_price:
            return False, f"Price ${price} below minimum ${min_price}"

        if price > max_price:
            return False, f"Price ${price} above maximum ${max_price}"

        return True, "Valid"

    @staticmethod
    def detect_data_conflicts(results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Detect conflicts between data sources

        Returns dict with conflict analysis
        """
        conflicts = {
            'has_conflicts': False,
            'name_variants': [],
            'brand_variants': [],
            'price_range': None,
        }

        # Collect unique names
        names = [r['name'] for r in results if r.get('name')]
        if len(set(names)) > 1:
            conflicts['has_conflicts'] = True
            conflicts['name_variants'] = list(set(names))

        # Collect unique brands
        brands = [r['brand'] for r in results if r.get('brand')]
        if len(set(brands)) > 1:
            conflicts['has_conflicts'] = True
            conflicts['brand_variants'] = list(set(brands))

        # Check price range
        prices = [r['price'] for r in results if r.get('price')]
        if prices:
            min_price = min(prices)
            max_price = max(prices)
            if max_price > min_price * 1.5:  # More than 50% difference
                conflicts['has_conflicts'] = True
                conflicts['price_range'] = (min_price, max_price)

        return conflicts
