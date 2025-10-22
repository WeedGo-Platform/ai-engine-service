"""
Product Data Cleaning and Normalization Service
Improves accuracy of scraped product data through cleaning and standardization
"""

import re
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)


class ProductDataCleaner:
    """
    Cleans and normalizes product data from web scraping
    Handles brand normalization, name cleaning, and structured data extraction
    """

    # Known brand mappings (distributor → manufacturer)
    BRAND_NORMALIZATION = {
        'raw sports': 'RAW',
        'raw': 'RAW',
        'rizla': 'Rizla',
        'zig zag': 'Zig-Zag',
        'zig-zag': 'Zig-Zag',
        'clipper': 'Clipper',
        'ocb': 'OCB',
        'elements': 'Elements',
        'smoking': 'Smoking',
        'gizeh': 'Gizeh',
        'vibes': 'Vibes',
    }

    # Words to remove from product names (marketing fluff)
    JUNK_WORDS = [
        'new', 'brand new', 'sealed', 'authentic', 'genuine', 'official',
        'fast shipping', 'free shipping', 'ships fast', 'usa seller',
        'full box', 'full sealed box', 'wholesale', 'bulk',
        'best price', 'lowest price', 'sale', 'deal',
        '100% authentic', 'original', 'factory sealed'
    ]

    # Common typos and corrections
    TYPO_CORRECTIONS = {
        'tobbaco': 'tobacco',
        'cigarrete': 'cigarette',
        'cigarrette': 'cigarette',
        'accesories': 'accessories',
        'acccessories': 'accessories',
    }

    # Category keywords for auto-categorization
    CATEGORY_KEYWORDS = {
        'Rolling Papers': ['paper', 'papers', 'rolling', 'booklet'],
        'Grinders': ['grinder', 'crusher', 'shredder'],
        'Pipes & Bongs': ['pipe', 'bong', 'water pipe', 'glass pipe'],
        'Vaporizers': ['vaporizer', 'vape', 'pen'],
        'Filter Tips': ['filter', 'tip', 'tips', 'roach'],
        'Lighters': ['lighter', 'torch', 'butane'],
        'Storage': ['jar', 'container', 'storage', 'stash'],
        'Cones': ['cone', 'cones', 'pre-rolled', 'prerolled'],
        'Trays': ['tray', 'rolling tray'],
    }

    def clean_product_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main entry point - cleans all fields in product data

        Args:
            data: Raw product data from web scraping

        Returns:
            Cleaned and normalized product data
        """
        cleaned = data.copy()

        # Clean product name
        if 'name' in cleaned:
            cleaned['name'] = self.clean_product_name(cleaned['name'])

        # Normalize brand
        if 'brand' in cleaned:
            cleaned['brand'] = self.normalize_brand(cleaned['brand'])

        # Extract structured attributes
        if 'name' in cleaned:
            attributes = self.extract_attributes(cleaned['name'])
            cleaned['attributes'] = attributes

            # Infer category if not present
            if 'category' not in cleaned or not cleaned['category']:
                cleaned['category'] = self.infer_category(cleaned['name'])

        # Validate and clean price
        if 'price' in cleaned and cleaned['price']:
            cleaned['price'] = self.validate_price(cleaned['price'])

        return cleaned

    def clean_product_name(self, name: str) -> str:
        """
        Clean product name by removing junk words and normalizing format

        Example:
            Input:  "5 Packs RAW Wide Perforated Natural Unrefined Hemp & Cotton Tips (250 Total) new"
            Output: "RAW Wide Perforated Hemp & Cotton Filter Tips - 5 Packs (250 Total)"
        """
        if not name:
            return name

        original = name

        # Fix common typos
        name_lower = name.lower()
        for typo, correction in self.TYPO_CORRECTIONS.items():
            name_lower = name_lower.replace(typo, correction)

        # Preserve original capitalization but apply corrections
        for typo, correction in self.TYPO_CORRECTIONS.items():
            # Case-insensitive replace
            pattern = re.compile(re.escape(typo), re.IGNORECASE)
            name = pattern.sub(correction, name)

        # Remove junk words (case-insensitive)
        for junk in self.JUNK_WORDS:
            pattern = re.compile(r'\b' + re.escape(junk) + r'\b', re.IGNORECASE)
            name = pattern.sub('', name)

        # Fix common grammar issues
        name = re.sub(r'\bPack\s+Off\s+(\d+)\b', r'Pack of \1', name, flags=re.IGNORECASE)
        name = re.sub(r'\bBox\s+Off\s+(\d+)\b', r'Box of \1', name, flags=re.IGNORECASE)

        # Remove redundant words
        name = re.sub(r'\b(Natural\s+)?Unrefined\s+Natural\b', 'Natural Unrefined', name, flags=re.IGNORECASE)
        name = re.sub(r'\b(Rolling\s+)?Papers?\s+Rolling\b', 'Rolling Papers', name, flags=re.IGNORECASE)

        # Clean up whitespace and punctuation
        name = re.sub(r'\s+', ' ', name)  # Multiple spaces → single space
        name = re.sub(r'\s*-\s*', ' - ', name)  # Normalize dashes
        name = re.sub(r'\s+([,.])', r'\1', name)  # Remove space before punctuation
        name = name.strip(' -')

        # Capitalize properly
        name = self._capitalize_product_name(name)

        logger.info(f"Name cleaned: '{original}' → '{name}'")
        return name

    def _capitalize_product_name(self, name: str) -> str:
        """Smart capitalization for product names"""
        # Keep certain words in specific case
        keep_uppercase = ['RAW', 'OCB', 'USA', 'UK']
        keep_lowercase = ['and', 'or', 'of', 'the', 'with', 'for']

        words = name.split()
        result = []

        for i, word in enumerate(words):
            # Check if it should stay uppercase
            if word.upper() in keep_uppercase:
                result.append(word.upper())
            # Check if it should be lowercase (not first word)
            elif i > 0 and word.lower() in keep_lowercase:
                result.append(word.lower())
            # Title case for others
            else:
                result.append(word.capitalize())

        return ' '.join(result)

    def normalize_brand(self, brand: str) -> str:
        """
        Normalize brand name to canonical form

        Example:
            "Raw Sports" → "RAW"
            "zig zag" → "Zig-Zag"
        """
        if not brand:
            return brand

        brand_lower = brand.lower().strip()

        # Check normalization mapping
        if brand_lower in self.BRAND_NORMALIZATION:
            normalized = self.BRAND_NORMALIZATION[brand_lower]
            logger.info(f"Brand normalized: '{brand}' → '{normalized}'")
            return normalized

        # Default: Title case
        return brand.strip().title()

    def extract_attributes(self, name: str) -> Dict[str, Any]:
        """
        Extract structured attributes from product name

        Returns dict with:
            - quantity: Number of items (e.g., 50, 32)
            - pack_size: How items are packaged (e.g., "5 Packs", "Per Box")
            - size: Product size (e.g., "King Size", "1 1/4")
            - color: Product color (e.g., "Blue")
            - material: Material (e.g., "Hemp", "Paper")
        """
        attributes = {}

        # Extract quantity
        qty_patterns = [
            r'(\d+)\s*(?:Count|Ct|Pieces?|Pcs?)',
            r'(\d+)\s*Per\s+(?:Pack|Box)',
            r'Pack\s+of\s+(\d+)',
            r'\((\d+)\s+Total\)',
        ]
        for pattern in qty_patterns:
            match = re.search(pattern, name, re.IGNORECASE)
            if match:
                attributes['quantity'] = int(match.group(1))
                break

        # Extract pack size
        pack_match = re.search(r'(\d+)\s*Packs?', name, re.IGNORECASE)
        if pack_match:
            attributes['pack_size'] = f"{pack_match.group(1)} Packs"

        # Extract size descriptors
        size_patterns = [
            (r'\b(King\s+Size)\b', 'size'),
            (r'\b(1\s*1/4)\b', 'size'),
            (r'\b(Slim)\b', 'style'),
            (r'\b(Wide)\b', 'style'),
        ]
        for pattern, attr_name in size_patterns:
            match = re.search(pattern, name, re.IGNORECASE)
            if match:
                attributes[attr_name] = match.group(1)

        # Extract color
        colors = ['Blue', 'Red', 'Green', 'Yellow', 'Black', 'White', 'Silver', 'Gold']
        for color in colors:
            if re.search(r'\b' + color + r'\b', name, re.IGNORECASE):
                attributes['color'] = color
                break

        # Extract material
        materials = ['Hemp', 'Cotton', 'Paper', 'Wood', 'Metal', 'Glass', 'Plastic']
        found_materials = []
        for material in materials:
            if re.search(r'\b' + material + r'\b', name, re.IGNORECASE):
                found_materials.append(material)
        if found_materials:
            attributes['materials'] = found_materials

        return attributes

    def infer_category(self, name: str) -> Optional[str]:
        """
        Infer product category from name

        Example:
            "RAW Rolling Papers" → "Rolling Papers"
            "Metal Herb Grinder" → "Grinders"
        """
        name_lower = name.lower()

        # Check each category's keywords
        for category, keywords in self.CATEGORY_KEYWORDS.items():
            for keyword in keywords:
                if keyword in name_lower:
                    logger.info(f"Category inferred: '{category}' from keyword '{keyword}'")
                    return category

        return None

    def validate_price(self, price: float) -> Optional[float]:
        """
        Validate and clean price data

        Returns None for invalid prices (too low, too high, or nonsensical)
        """
        if not price or price <= 0:
            return None

        # Sanity checks for accessories
        if price < 0.50:  # Too cheap (likely error)
            logger.warning(f"Price too low: ${price} - setting to None")
            return None

        if price > 999.99:  # Too expensive for typical accessories
            logger.warning(f"Price too high: ${price} - setting to None")
            return None

        # Round to 2 decimal places
        return round(price, 2)

    def calculate_confidence_boost(self, original: Dict[str, Any], cleaned: Dict[str, Any]) -> float:
        """
        Calculate confidence boost based on cleaning improvements

        Returns: Confidence adjustment (0.0 to 0.2)
        """
        boost = 0.0

        # Boost if brand was normalized
        if original.get('brand') != cleaned.get('brand'):
            boost += 0.05

        # Boost if attributes were extracted
        if cleaned.get('attributes'):
            boost += 0.05

        # Boost if category was inferred
        if cleaned.get('category') and not original.get('category'):
            boost += 0.05

        # Boost if name was significantly cleaned
        if original.get('name') and cleaned.get('name'):
            if len(cleaned['name']) < len(original['name']) * 0.8:
                boost += 0.05

        return min(boost, 0.2)  # Cap at 0.2


# Helper function for easy import
def clean_product_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Convenience function to clean product data"""
    cleaner = ProductDataCleaner()
    return cleaner.clean_product_data(data)
