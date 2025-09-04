#!/usr/bin/env python3
"""
Product Knowledge Base for WeedGo AI
Maps customer requests to actual product categories and search terms
"""

class ProductKnowledge:
    """
    Cannabis product knowledge for better search and recommendations
    """
    
    # Map common requests to categories and search terms
    PRODUCT_MAPPINGS = {
        # Concentrates/Extracts
        "shatter": {
            "category": "Extracts",
            "sub_category": "Shatter",
            "search_terms": ["shatter"],
            "description": "Glass-like cannabis concentrate"
        },
        "dab": {
            "category": "Extracts", 
            "search_terms": ["dab", "concentrate", "wax", "shatter", "rosin", "resin"],
            "description": "Concentrated cannabis for dabbing"
        },
        "concentrate": {
            "category": "Extracts",
            "search_terms": ["concentrate", "extract", "dab", "wax"],
            "description": "High-potency cannabis extracts"
        },
        "wax": {
            "category": "Extracts",
            "search_terms": ["wax"],
            "description": "Waxy cannabis concentrate"
        },
        "rosin": {
            "category": "Extracts",
            "sub_category": "Rosin",
            "search_terms": ["rosin", "live rosin"],
            "description": "Solventless cannabis extract"
        },
        "resin": {
            "category": "Extracts",
            "sub_category": "Resin",
            "search_terms": ["resin", "live resin"],
            "description": "Terpene-rich cannabis extract"
        },
        "hash": {
            "category": "Extracts",
            "sub_category": "Hash and Kief",
            "search_terms": ["hash", "kief"],
            "description": "Traditional cannabis concentrate"
        },
        "distillate": {
            "category": "Extracts",
            "sub_category": "Distillates",
            "search_terms": ["distillate"],
            "description": "Pure cannabis distillate"
        },
        
        # Consumption methods for non-smokers
        "odorless": {
            "category": ["Edibles", "Extracts", "Topicals"],
            "search_terms": ["capsule", "tablet", "softgel", "tincture"],
            "description": "Discrete, odor-free consumption methods"
        },
        "don't smoke": {
            "category": ["Edibles", "Vapes", "Extracts", "Topicals"],
            "search_terms": ["edible", "vape", "tincture", "capsule", "topical"],
            "description": "Non-smoking alternatives"
        },
        
        # Vaping
        "vape": {
            "category": "Vapes",
            "search_terms": ["vape", "cartridge", "pen"],
            "description": "Vaporizer products"
        },
        "cart": {
            "category": "Vapes",
            "search_terms": ["cartridge", "cart"],
            "description": "Vape cartridges"
        },
        
        # Traditional flower
        "joint": {
            "category": "Flower",
            "search_terms": ["pre-roll", "joint"],
            "description": "Pre-rolled cannabis joints"
        },
        "pre-roll": {
            "category": "Flower",
            "search_terms": ["pre-roll", "pre roll"],
            "description": "Pre-rolled cannabis"
        },
        "flower": {
            "category": "Flower",
            "search_terms": ["flower", "bud"],
            "description": "Cannabis flower/buds"
        },
        
        # Edibles
        "gummy": {
            "category": "Edibles",
            "search_terms": ["gummy", "gummies"],
            "description": "Cannabis-infused gummies"
        },
        "chocolate": {
            "category": "Edibles",
            "search_terms": ["chocolate"],
            "description": "Cannabis-infused chocolate"
        },
        "drink": {
            "category": "Edibles",
            "search_terms": ["beverage", "drink", "soda"],
            "description": "Cannabis beverages"
        },
        
        # Topicals
        "cream": {
            "category": "Topicals",
            "search_terms": ["cream", "lotion", "balm"],
            "description": "Topical cannabis creams"
        },
        "topical": {
            "category": "Topicals",
            "search_terms": ["topical", "cream", "balm", "salve"],
            "description": "Cannabis topicals for skin application"
        }
    }
    
    # Categories with descriptions
    CATEGORIES = {
        "Flower": "Traditional cannabis buds and pre-rolls",
        "Edibles": "Cannabis-infused food and drinks",
        "Vapes": "Vaporizers and cartridges",
        "Extracts": "Concentrates like shatter, wax, rosin for dabbing",
        "Topicals": "Creams and lotions for skin application",
        "Accessories": "Pipes, grinders, papers, and other tools"
    }
    
    @classmethod
    def identify_product_type(cls, user_message: str) -> dict:
        """
        Identify what type of product the customer is asking for
        """
        message_lower = user_message.lower()
        
        for keyword, mapping in cls.PRODUCT_MAPPINGS.items():
            if keyword in message_lower:
                return {
                    "identified_type": keyword,
                    "category": mapping["category"],
                    "search_terms": mapping["search_terms"],
                    "description": mapping["description"]
                }
        
        return {
            "identified_type": None,
            "category": None,
            "search_terms": [],
            "description": "General cannabis products"
        }
    
    @classmethod
    def get_category_description(cls, category: str) -> str:
        """Get description for a category"""
        return cls.CATEGORIES.get(category, "Cannabis products")
    
    @classmethod
    def suggest_alternatives(cls, unavailable_type: str) -> list:
        """Suggest alternatives when a product type is unavailable"""
        
        alternatives = {
            "shatter": ["wax", "rosin", "live resin", "other concentrates"],
            "edibles": ["tinctures", "capsules", "beverages"],
            "flower": ["pre-rolls", "vapes", "edibles"],
            "vapes": ["flower", "edibles", "tinctures"]
        }
        
        return alternatives.get(unavailable_type, ["other cannabis products"])
    
    @classmethod
    def handle_non_smoking_request(cls, preferences: dict) -> dict:
        """
        Handle requests from customers who don't want to smoke
        Returns appropriate product categories and search terms
        """
        
        options = []
        
        if not preferences.get("no_edibles"):
            options.append({
                "category": "Edibles",
                "types": ["gummies", "chocolates", "beverages", "capsules"],
                "description": "Discrete, smoke-free consumption"
            })
        
        if preferences.get("odorless"):
            options.append({
                "category": "Extracts",
                "types": ["capsules", "tablets", "tinctures"],
                "description": "Odorless consumption methods"
            })
        
        if not preferences.get("no_vapes"):
            options.append({
                "category": "Vapes",
                "types": ["vape pens", "cartridges"],
                "description": "Vapor with minimal odor"
            })
        
        options.append({
            "category": "Topicals",
            "types": ["creams", "balms", "lotions"],
            "description": "Non-psychoactive, applied to skin"
        })
        
        return {
            "recommended_options": options,
            "avoid_categories": ["Flower"] if preferences.get("no_smoking") else []
        }
    
    @classmethod
    def validate_request(cls, user_message: str) -> dict:
        """
        Validate if request is appropriate and legal
        """
        
        # Check for problematic requests
        if "illegal" in user_message.lower():
            return {
                "valid": True,  # It's NOT illegal at a dispensary
                "message": "All our products are legal for adult use in this dispensary"
            }
        
        return {
            "valid": True,
            "message": None
        }