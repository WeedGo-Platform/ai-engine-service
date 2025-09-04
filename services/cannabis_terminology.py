#!/usr/bin/env python3
"""
Multilingual Cannabis Terminology and Slang Handler
Maps common cannabis culture terms to searchable product attributes
Supports: English, Spanish, French, Portuguese, Chinese, Arabic
"""

import re
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class TerpeneProfile(Enum):
    """Common terpene profiles"""
    CITRUS = "citrus"  # Limonene dominant
    PINE = "pine"      # Pinene dominant
    FUEL = "fuel"      # Diesel/gas strains
    EARTH = "earth"    # Myrcene dominant
    SWEET = "sweet"    # Linalool/terpinolene
    BERRY = "berry"    # Berry terpenes
    MINT = "mint"      # Menthol/cooling
    SPICE = "spice"    # Caryophyllene dominant

@dataclass
class StrainCharacteristics:
    """Characteristics customers look for"""
    aroma: List[str]
    effects: List[str]
    structure: str  # dense, fluffy, sticky
    potency: str    # high, medium, low

class CannabisTerminologyMapper:
    """
    Maps cannabis slang and descriptors to searchable terms
    Multilingual support for 6 languages
    """
    
    def __init__(self):
        self.slang_mappings = self._load_slang_mappings()
        self.descriptor_mappings = self._load_descriptor_mappings()
        self.misspelling_corrections = self._load_common_misspellings()
        self.multilingual_terms = self._load_multilingual_terms()
    
    def _load_slang_mappings(self) -> Dict:
        """Load cannabis slang to formal term mappings"""
        return {
            # Aroma/Flavor descriptors
            "gas": ["diesel", "fuel", "OG", "chem"],
            "gassy": ["diesel", "fuel", "OG"],
            "loud": ["potent", "strong", "high THC", "premium"],
            "fire": ["premium", "top shelf", "high quality", "potent"],
            "loud fire": ["premium", "top shelf", "potent", "high THC", "fire"],
            "dank": ["potent", "sticky", "fresh"],
            "frosty": ["trichome", "crystal", "high THC"],
            "sticky": ["resinous", "fresh", "quality", "flower"],
            "icky": ["sticky", "potent", "dank"],
            "sticky icky": ["flower", "bud", "resinous", "premium", "sticky"],
            "funk": ["cheese", "skunk", "pungent"],
            "fruity": ["berry", "citrus", "tropical", "sweet"],
            "kushy": ["kush", "OG Kush", "indica"],
            
            # Structure descriptors
            "dense": ["tight", "compact", "heavy"],
            "fluffy": ["airy", "light", "sativa"],
            "nugs": ["buds", "flower"],
            "popcorn": ["small buds", "smalls"],
            
            # Basic flower terms (CRITICAL)
            "dried flower": ["flower", "cannabis", "bud"],
            "flowers": ["flower", "cannabis", "bud"],
            "good buds": ["flower", "premium", "quality"],
            "buds": ["flower", "cannabis"],
            
            # Quantity slang (corrected)
            "eighth": ["3.5g", "1/8", "half quarter"],
            "quarter": ["7g", "1/4", "quad"],
            "half": ["14g", "1/2", "half ounce", "half oz"],
            "ounce": ["28g", "oz", "zip", "whole"],
            "zip": ["28g", "ounce", "oz"],
            "qp": ["quarter pound", "4 ounces", "113g"],
            
            # Product types
            "dabs": ["concentrates", "extracts", "wax", "shatter"],
            "carts": ["cartridges", "vape cartridges", "vapes"],
            "j's": ["joints", "pre-rolls"],
            "blunts": ["pre-rolls", "large pre-rolls"],
            "eddies": ["edibles", "gummies", "chocolate"],
            "eddy": ["edibles", "edible"],
            "tinctures": ["drops", "sublingual"],
            
            # Effects
            "couch-lock": ["sedating", "indica", "relaxing"],
            "heady": ["cerebral", "sativa", "uplifting"],
            "munchies": ["appetite", "hungry"],
            "giggly": ["euphoric", "happy", "uplifting"],
            "sleepy": ["sedating", "nighttime", "indica"],
            "energetic": ["sativa", "daytime", "uplifting"],
        }
    
    def _load_descriptor_mappings(self) -> Dict:
        """Map descriptive terms to search strategies"""
        return {
            # Aroma combinations
            "gas and dense": {
                "strains": ["OG Kush", "Chemdawg", "Sour Diesel", "GG4"],
                "keywords": ["diesel", "fuel", "dense buds"],
                "category": "Flower"
            },
            "fruity and dense": {
                "strains": ["Purple Punch", "Zkittlez", "Gelato", "Wedding Cake"],
                "keywords": ["berry", "sweet", "fruit", "dense"],
                "category": "Flower"
            },
            "citrus and uplifting": {
                "strains": ["Tangie", "Lemon Haze", "Orange Cookies"],
                "keywords": ["citrus", "lemon", "orange", "sativa"],
                "category": "Flower"
            },
            "earthy and relaxing": {
                "strains": ["Northern Lights", "Afghan Kush", "Bubba Kush"],
                "keywords": ["earth", "pine", "indica", "relaxing"],
                "category": "Flower"
            },
            "sweet and potent": {
                "strains": ["Girl Scout Cookies", "Sunset Sherbet", "Birthday Cake"],
                "keywords": ["sweet", "dessert", "high THC"],
                "category": "Flower"
            },
        }
    
    def _load_common_misspellings(self) -> Dict:
        """Common misspellings in cannabis product names"""
        return {
            # Common strain misspellings
            "swettberry": "sweetberry",
            "sweatberry": "sweetberry",
            "sweetbery": "sweetberry",
            "purp": "purple",
            "cali": "california",
            "afgan": "afghan",
            "diesal": "diesel",
            "gorrila": "gorilla",
            "weding": "wedding",
            "cokies": "cookies",
            "kookies": "cookies",
            "hase": "haze",
            "og": "OG",
            "marijauna": "marijuana",
            "cannibus": "cannabis",
            "gellato": "gelato",
            "sherbert": "sherbet",
            "bannana": "banana",
            "straberry": "strawberry",
            "bluberry": "blueberry",
            
            # Product type misspellings
            "pre roll": "pre-roll",
            "preroll": "pre-roll",
            "vap": "vape",
            "catridge": "cartridge",
            "shattar": "shatter",
            "rosn": "rosin",
            "edable": "edible",
            "tinture": "tincture",
            "capule": "capsule",
        }
    
    def _load_multilingual_terms(self) -> Dict:
        """Load multilingual cannabis terminology"""
        return {
            # Product types
            "flower": {
                "en": "flower", "es": "flor", "fr": "fleur",
                "pt": "flor", "zh": "花", "ar": "زهرة"
            },
            "pre-roll": {
                "en": "pre-roll", "es": "pre-enrollado", "fr": "pré-roulé",
                "pt": "pré-enrolado", "zh": "预卷烟", "ar": "ملفوف مسبقا"
            },
            "edibles": {
                "en": "edibles", "es": "comestibles", "fr": "comestibles",
                "pt": "comestíveis", "zh": "食用品", "ar": "مأكولات"
            },
            "vape": {
                "en": "vape", "es": "vaporizador", "fr": "vaporisateur",
                "pt": "vaporizador", "zh": "电子烟", "ar": "بخار"
            },
            
            # Strain types
            "sativa": {
                "en": "sativa", "es": "sativa", "fr": "sativa",
                "pt": "sativa", "zh": "sativa", "ar": "ساتيفا"
            },
            "indica": {
                "en": "indica", "es": "indica", "fr": "indica",
                "pt": "indica", "zh": "indica", "ar": "إنديكا"
            },
            "hybrid": {
                "en": "hybrid", "es": "híbrido", "fr": "hybride",
                "pt": "híbrido", "zh": "混合", "ar": "هجين"
            },
            
            # Effects
            "relaxing": {
                "en": "relaxing", "es": "relajante", "fr": "relaxant",
                "pt": "relaxante", "zh": "放松", "ar": "مريح"
            },
            "energizing": {
                "en": "energizing", "es": "energizante", "fr": "énergisant",
                "pt": "energizante", "zh": "提神", "ar": "منشط"
            },
            "euphoric": {
                "en": "euphoric", "es": "eufórico", "fr": "euphorique",
                "pt": "eufórico", "zh": "欣快", "ar": "نشوة"
            },
            
            # Measurements
            "gram": {
                "en": "gram", "es": "gramo", "fr": "gramme",
                "pt": "grama", "zh": "克", "ar": "جرام"
            },
            "eighth": {
                "en": "eighth", "es": "octavo", "fr": "huitième",
                "pt": "oitavo", "zh": "八分之一", "ar": "ثمن"
            },
            "quarter": {
                "en": "quarter", "es": "cuarto", "fr": "quart",
                "pt": "quarto", "zh": "四分之一", "ar": "ربع"
            },
            "ounce": {
                "en": "ounce", "es": "onza", "fr": "once",
                "pt": "onça", "zh": "盎司", "ar": "أونصة"
            }
        }
    
    def translate_term(self, term: str, target_lang: str, source_lang: str = "en") -> str:
        """Translate a cannabis term to target language"""
        term_lower = term.lower()
        
        for key, translations in self.multilingual_terms.items():
            if translations.get(source_lang, "").lower() == term_lower:
                return translations.get(target_lang, term)
        
        return term
    
    def normalize_query(self, query: str, language: str = "en") -> Tuple[str, List[str]]:
        """
        Normalize and expand a user query
        Returns: (normalized_query, additional_search_terms)
        """
        query_lower = query.lower()
        additional_terms = []
        
        # Step 1: Fix common misspellings
        normalized = query_lower
        for misspelling, correct in self.misspelling_corrections.items():
            if misspelling in normalized:
                normalized = normalized.replace(misspelling, correct)
                logger.info(f"Corrected misspelling: {misspelling} → {correct}")
        
        # Step 2: Expand slang terms
        for slang, expansions in self.slang_mappings.items():
            if slang in normalized:
                additional_terms.extend(expansions)
                logger.info(f"Expanded slang: {slang} → {expansions}")
        
        # Step 3: Check for descriptor combinations
        for descriptor, mapping in self.descriptor_mappings.items():
            if descriptor in query_lower:
                additional_terms.extend(mapping["keywords"])
                additional_terms.extend(mapping["strains"])
                logger.info(f"Mapped descriptor: {descriptor} → {mapping['keywords']}")
        
        # Step 4: Handle quantity expressions (corrected)
        quantity_patterns = [
            (r"1/2\s*quarter", "3.5g eighth"),  # "1/2 quarter" = half of 7g = 3.5g (eighth)
            (r"1/4\s*quarter", "1.75g"),  # "1/4 quarter" = quarter of 7g = 1.75g
            (r"1/4", "7g quarter"),  # "1/4" alone means quarter ounce = 7g
            (r"1/8", "3.5g eighth"),  # "1/8" means eighth ounce = 3.5g
            (r"1/2", "14g half"),  # "1/2" means half ounce = 14g
            (r"quarter\s*pound", "qp"),
            (r"half\s*ounce", "14g"),
            (r"a quarter", "7g"),
            (r"an eighth", "3.5g"),
            (r"a half", "14g"),
        ]
        
        for pattern, replacement in quantity_patterns:
            if re.search(pattern, normalized):
                normalized = re.sub(pattern, replacement, normalized)
        
        return normalized, list(set(additional_terms))
    
    def identify_intent(self, query: str) -> Dict:
        """
        Identify the intent and characteristics from a query
        """
        query_lower = query.lower()
        intent = {
            "product_type": None,
            "characteristics": [],
            "effects": [],
            "quantity": None,
            "price_range": None,
            "strain_type": None,
        }
        
        # Extract price if mentioned
        import re
        price_pattern = r'\$?(\d+)\s*(?:dollar|bucks?)?'
        price_match = re.search(price_pattern, query_lower)
        if price_match:
            intent["price_range"] = float(price_match.group(1))
        
        # Identify strain type
        if "sativa" in query_lower:
            intent["strain_type"] = "sativa"
        elif "indica" in query_lower:
            intent["strain_type"] = "indica"
        elif "hybrid" in query_lower:
            intent["strain_type"] = "hybrid"
        
        # Identify product type
        product_types = {
            "flower": ["flower", "bud", "nug", "eighth", "quarter"],
            "pre-roll": ["pre-roll", "preroll", "joint", "j", "blunt"],
            "edible": ["edible", "eddy", "eddies", "gummy", "chocolate", "cookie", "brownie"],
            "vape": ["vape", "cart", "cartridge", "pen"],
            "concentrate": ["dab", "wax", "shatter", "rosin", "concentrate"],
            "tincture": ["tincture", "drops", "oil"],
        }
        
        for product_type, keywords in product_types.items():
            if any(keyword in query_lower for keyword in keywords):
                intent["product_type"] = product_type
                break
        
        # Identify characteristics
        characteristics = [
            "dense", "fluffy", "sticky", "frosty", "colorful",
            "purple", "orange", "crystally", "fresh", "cured"
        ]
        intent["characteristics"] = [c for c in characteristics if c in query_lower]
        
        # Identify effects
        effects = [
            "relaxing", "uplifting", "energetic", "creative", "focused",
            "sleepy", "hungry", "giggly", "euphoric", "calm"
        ]
        intent["effects"] = [e for e in effects if e in query_lower]
        
        # Identify quantity
        quantities = {
            "eighth": "3.5g",
            "quarter": "7g",
            "half": "14g",
            "ounce": "28g",
            "oz": "28g",
            "gram": "1g",
            "3.5": "3.5g",
            "7g": "7g",
            "14g": "14g",
            "28g": "28g",
        }
        
        for term, quantity in quantities.items():
            if term in query_lower:
                intent["quantity"] = quantity
                break
        
        return intent
    
    def generate_search_terms(self, query: str) -> List[str]:
        """
        Generate comprehensive search terms from a query
        """
        normalized, additional = self.normalize_query(query)
        intent = self.identify_intent(query)
        
        search_terms = [normalized]
        search_terms.extend(additional)
        
        # Add intent-based terms
        if intent["product_type"]:
            search_terms.append(intent["product_type"])
        
        search_terms.extend(intent["characteristics"])
        search_terms.extend(intent["effects"])
        
        # Remove duplicates and return
        return list(set(term for term in search_terms if term))


class StrainMatcher:
    """
    Matches user preferences to specific strains
    """
    
    def __init__(self):
        self.strain_database = self._load_strain_characteristics()
    
    def _load_strain_characteristics(self) -> Dict:
        """Load known strain characteristics"""
        return {
            # Classic strains
            "OG Kush": {
                "type": "hybrid",
                "effects": ["relaxing", "euphoric", "happy"],
                "flavors": ["earthy", "pine", "woody"],
                "characteristics": ["dense", "resinous"],
                "thc_range": (18, 25),
            },
            "Sour Diesel": {
                "type": "sativa",
                "effects": ["energetic", "uplifting", "creative"],
                "flavors": ["diesel", "fuel", "citrus"],
                "characteristics": ["pungent", "dense"],
                "thc_range": (20, 25),
            },
            "Purple Punch": {
                "type": "indica",
                "effects": ["relaxing", "sleepy", "euphoric"],
                "flavors": ["grape", "berry", "sweet"],
                "characteristics": ["purple", "dense", "frosty"],
                "thc_range": (18, 22),
            },
            "Girl Scout Cookies": {
                "type": "hybrid",
                "effects": ["euphoric", "relaxing", "creative"],
                "flavors": ["sweet", "earthy", "mint"],
                "characteristics": ["dense", "colorful", "crystally"],
                "thc_range": (20, 28),
            },
            "Blue Dream": {
                "type": "hybrid",
                "effects": ["creative", "uplifting", "focused"],
                "flavors": ["berry", "sweet", "herbal"],
                "characteristics": ["fluffy", "light", "blue-tinted"],
                "thc_range": (17, 24),
            },
            "Gorilla Glue #4": {
                "type": "hybrid",
                "effects": ["relaxing", "euphoric", "couch-lock"],
                "flavors": ["pine", "chocolate", "diesel"],
                "characteristics": ["sticky", "dense", "resinous"],
                "thc_range": (25, 32),
            },
            "Wedding Cake": {
                "type": "hybrid",
                "effects": ["relaxing", "euphoric", "aroused"],
                "flavors": ["vanilla", "sweet", "earthy"],
                "characteristics": ["dense", "colorful", "frosty"],
                "thc_range": (22, 27),
            },
            "Zkittlez": {
                "type": "indica",
                "effects": ["relaxing", "happy", "euphoric"],
                "flavors": ["tropical", "fruity", "sweet"],
                "characteristics": ["colorful", "dense", "aromatic"],
                "thc_range": (18, 23),
            },
        }
    
    def match_strains(self, preferences: Dict) -> List[str]:
        """
        Match user preferences to strains
        """
        matched_strains = []
        
        for strain_name, characteristics in self.strain_database.items():
            score = 0
            
            # Check effects match
            if preferences.get("effects"):
                matching_effects = set(preferences["effects"]) & set(characteristics["effects"])
                score += len(matching_effects) * 2
            
            # Check flavor match
            if preferences.get("flavors"):
                matching_flavors = set(preferences["flavors"]) & set(characteristics["flavors"])
                score += len(matching_flavors)
            
            # Check characteristics match
            if preferences.get("characteristics"):
                matching_chars = set(preferences["characteristics"]) & set(characteristics["characteristics"])
                score += len(matching_chars)
            
            # Check type preference
            if preferences.get("type") and preferences["type"] == characteristics["type"]:
                score += 3
            
            if score > 0:
                matched_strains.append((strain_name, score))
        
        # Sort by score and return top matches
        matched_strains.sort(key=lambda x: x[1], reverse=True)
        return [strain for strain, _ in matched_strains[:5]]


# Global instances
cannabis_terminology_mapper = CannabisTerminologyMapper()
strain_matcher = StrainMatcher()