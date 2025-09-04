#!/usr/bin/env python3
"""
Multilingual Search Service
Handles product searches in any supported language using pre-translated data
"""

import logging
import json
from typing import Dict, List, Optional, Tuple
from enum import Enum
import asyncpg

logger = logging.getLogger(__name__)

class Language(Enum):
    """Supported languages"""
    ENGLISH = "en"
    SPANISH = "es"
    FRENCH = "fr"
    CHINESE = "zh"
    JAPANESE = "ja"
    KOREAN = "ko"
    PORTUGUESE = "pt"
    GERMAN = "de"
    ITALIAN = "it"
    RUSSIAN = "ru"


class MultilingualSearchService:
    """
    Handles multilingual product searches using pre-translated database columns
    
    Key Features:
    - Zero-latency translation (pre-computed)
    - Searches in user's language
    - Returns results in user's language
    - Falls back gracefully if translation missing
    """
    
    def __init__(self, db_connection):
        self.conn = db_connection
        self.search_term_mappings = self._load_search_mappings()
    
    def _load_search_mappings(self) -> Dict:
        """Load search term mappings for different languages"""
        return {
            Language.SPANISH: {
                "flor": "flower",
                "flores": "flower",
                "comestibles": "edibles",
                "vaporizadores": "vapes",
                "extractos": "extracts",
                "aceite": "oil",
                "cera": "wax",
                "fragmento": "shatter",
                "tintura": "tincture",
                "cápsulas": "capsules",
                "tópicos": "topicals",
                "sativa": "sativa",
                "índica": "indica",
                "híbrido": "hybrid"
            },
            Language.FRENCH: {
                "fleur": "flower",
                "fleurs": "flower",
                "comestibles": "edibles",
                "vaporisateurs": "vapes",
                "extraits": "extracts",
                "huile": "oil",
                "cire": "wax",
                "éclat": "shatter",
                "teinture": "tincture",
                "capsules": "capsules",
                "topiques": "topicals",
                "hybride": "hybrid"
            },
            Language.CHINESE: {
                "花": "flower",
                "大麻花": "flower",
                "食用品": "edibles",
                "电子烟": "vapes",
                "提取物": "extracts",
                "油": "oil",
                "蜡": "wax",
                "碎片": "shatter",
                "酊剂": "tincture",
                "胶囊": "capsules",
                "外用药": "topicals",
                "萨蒂瓦": "sativa",
                "印度大麻": "indica",
                "混合": "hybrid"
            },
            Language.JAPANESE: {
                "フラワー": "flower",
                "エディブル": "edibles",
                "ベイプ": "vapes",
                "エキストラクト": "extracts",
                "オイル": "oil",
                "ワックス": "wax",
                "シャッター": "shatter",
                "チンキ": "tincture",
                "カプセル": "capsules",
                "トピカル": "topicals",
                "サティバ": "sativa",
                "インディカ": "indica",
                "ハイブリッド": "hybrid"
            }
        }
    
    async def search_products(self, 
                             query: str, 
                             language: Language,
                             category: Optional[str] = None,
                             limit: int = 10) -> List[Dict]:
        """
        Search products in any language and return results in that language
        
        Args:
            query: Search query in user's language
            language: Target language for results
            category: Optional category filter
            limit: Maximum results to return
        
        Returns:
            List of products with translated fields
        """
        
        # Step 1: Normalize query to English for searching
        english_query = self._normalize_to_english(query, language)
        logger.info(f"Multilingual search: '{query}' ({language.value}) -> '{english_query}'")
        
        # Step 2: Build SQL query with language-specific fields
        sql = self._build_multilingual_query(language)
        
        # Step 3: Execute search
        params = []
        where_clauses = []
        
        if english_query:
            # Search in English fields (source of truth)
            where_clauses.append("""
                (product_name ILIKE $1 OR 
                 brand ILIKE $1 OR 
                 category ILIKE $1 OR 
                 sub_category ILIKE $1)
            """)
            params.append(f"%{english_query}%")
        
        if category:
            where_clauses.append(f"category = ${len(params) + 1}")
            params.append(category)
        
        where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"
        sql = sql.format(where_clause=where_clause)
        
        params.append(limit)
        sql += f" LIMIT ${len(params)}"
        
        # Execute query
        results = await self.conn.fetch(sql, *params)
        
        # Step 4: Format results with translations
        return self._format_multilingual_results(results, language)
    
    def _normalize_to_english(self, query: str, language: Language) -> str:
        """
        Normalize non-English query to English for searching
        """
        if language == Language.ENGLISH:
            return query
        
        query_lower = query.lower()
        
        # Check if we have mappings for this language
        if language in self.search_term_mappings:
            mappings = self.search_term_mappings[language]
            
            # Replace known terms
            for local_term, english_term in mappings.items():
                if local_term in query_lower:
                    query_lower = query_lower.replace(local_term, english_term)
        
        return query_lower
    
    def _build_multilingual_query(self, language: Language) -> str:
        """
        Build SQL query that includes translated fields
        """
        
        if language == Language.ENGLISH:
            # No translation needed
            return """
                SELECT 
                    product_id,
                    product_name,
                    brand,
                    category,
                    sub_category,
                    unit_price,
                    description,
                    thc_content,
                    cbd_content,
                    strain_type,
                    available_quantity
                FROM products
                WHERE {where_clause}
                ORDER BY product_name
            """
        
        # Include translated fields
        lang_code = language.value
        return f"""
            SELECT 
                product_id,
                product_name,
                COALESCE(
                    name_translations->>'{lang_code}',
                    product_name
                ) as translated_name,
                brand,
                category,
                COALESCE(
                    category_translations->>'{lang_code}',
                    category
                ) as translated_category,
                sub_category,
                COALESCE(
                    sub_category_translations->>'{lang_code}',
                    sub_category
                ) as translated_sub_category,
                unit_price,
                description,
                COALESCE(
                    description_translations->>'{lang_code}',
                    description
                ) as translated_description,
                thc_content,
                cbd_content,
                strain_type,
                available_quantity,
                name_translations,
                category_translations,
                description_translations
            FROM products
            WHERE {{where_clause}}
            ORDER BY product_name
        """
    
    def _format_multilingual_results(self, 
                                    results: List[asyncpg.Record], 
                                    language: Language) -> List[Dict]:
        """
        Format search results with appropriate translations
        """
        
        formatted_results = []
        
        for record in results:
            product = dict(record)
            
            if language != Language.ENGLISH:
                # Use translated fields
                if 'translated_name' in product:
                    product['product_name'] = product['translated_name']
                
                if 'translated_category' in product:
                    product['category'] = product['translated_category']
                
                if 'translated_sub_category' in product:
                    product['sub_category'] = product['translated_sub_category']
                
                if 'translated_description' in product:
                    product['description'] = product['translated_description']
                
                # Clean up translation fields
                for key in list(product.keys()):
                    if key.startswith('translated_') or key.endswith('_translations'):
                        del product[key]
            
            # Add language indicator
            product['display_language'] = language.value
            
            formatted_results.append(product)
        
        return formatted_results
    
    async def get_product_in_language(self, 
                                     product_id: str, 
                                     language: Language) -> Optional[Dict]:
        """
        Get a specific product with translations
        """
        
        if language == Language.ENGLISH:
            sql = """
                SELECT * FROM products WHERE product_id = $1
            """
        else:
            lang_code = language.value
            sql = f"""
                SELECT 
                    product_id,
                    product_name,
                    COALESCE(
                        name_translations->>'{lang_code}',
                        product_name
                    ) as product_name_translated,
                    brand,
                    category,
                    COALESCE(
                        category_translations->>'{lang_code}',
                        category
                    ) as category_translated,
                    sub_category,
                    COALESCE(
                        sub_category_translations->>'{lang_code}',
                        sub_category
                    ) as sub_category_translated,
                    unit_price,
                    description,
                    COALESCE(
                        description_translations->>'{lang_code}',
                        description
                    ) as description_translated,
                    thc_content,
                    cbd_content,
                    strain_type,
                    available_quantity
                FROM products
                WHERE product_id = $1
            """
        
        result = await self.conn.fetchrow(sql, product_id)
        
        if not result:
            return None
        
        product = dict(result)
        
        # Use translated fields if available
        if language != Language.ENGLISH:
            if 'product_name_translated' in product:
                product['product_name'] = product['product_name_translated']
                del product['product_name_translated']
            
            if 'category_translated' in product:
                product['category'] = product['category_translated']
                del product['category_translated']
            
            if 'sub_category_translated' in product:
                product['sub_category'] = product['sub_category_translated']
                del product['sub_category_translated']
            
            if 'description_translated' in product:
                product['description'] = product['description_translated']
                del product['description_translated']
        
        product['display_language'] = language.value
        
        return product


class MultilingualResponseFormatter:
    """
    Formats AI responses with language-appropriate product information
    """
    
    @staticmethod
    def format_product_list(products: List[Dict], 
                           language: Language,
                           message_template: str) -> str:
        """
        Format product list for display in target language
        """
        
        if not products:
            return ""
        
        # Language-specific formatting
        currency_symbols = {
            Language.ENGLISH: "$",
            Language.SPANISH: "$",
            Language.FRENCH: "$",
            Language.CHINESE: "¥",
            Language.JAPANESE: "¥",
            Language.KOREAN: "₩",
            Language.PORTUGUESE: "R$",
            Language.GERMAN: "€",
            Language.ITALIAN: "€",
            Language.RUSSIAN: "₽"
        }
        
        currency = currency_symbols.get(language, "$")
        
        # Format product details
        product_lines = []
        for i, product in enumerate(products, 1):
            name = product.get('product_name', 'Unknown')
            price = product.get('unit_price', 0)
            category = product.get('category', '')
            thc = product.get('thc_content', 0)
            cbd = product.get('cbd_content', 0)
            
            # Format based on language
            if language in [Language.CHINESE, Language.JAPANESE, Language.KOREAN]:
                # Asian languages format
                line = f"{i}. {name} ({category})\n   {currency}{price:.2f} | THC: {thc}% | CBD: {cbd}%"
            else:
                # Western languages format
                line = f"{i}. {name} - {currency}{price:.2f}\n   {category} | THC: {thc}% | CBD: {cbd}%"
            
            product_lines.append(line)
        
        # Combine with message
        product_text = "\n\n".join(product_lines)
        return f"{message_template}\n\n{product_text}"
    
    @staticmethod
    def get_quick_replies(language: Language) -> List[str]:
        """
        Get language-appropriate quick reply options
        """
        
        quick_replies = {
            Language.ENGLISH: [
                "Show more options",
                "Add to cart",
                "Different category",
                "Tell me more"
            ],
            Language.SPANISH: [
                "Mostrar más opciones",
                "Añadir al carrito",
                "Categoría diferente",
                "Cuéntame más"
            ],
            Language.FRENCH: [
                "Plus d'options",
                "Ajouter au panier",
                "Catégorie différente",
                "En savoir plus"
            ],
            Language.CHINESE: [
                "显示更多选项",
                "加入购物车",
                "不同类别",
                "了解更多"
            ],
            Language.JAPANESE: [
                "もっとオプションを表示",
                "カートに追加",
                "別のカテゴリー",
                "詳細を教えて"
            ],
            Language.KOREAN: [
                "더 많은 옵션 표시",
                "장바구니에 추가",
                "다른 카테고리",
                "자세히 알려주세요"
            ],
            Language.PORTUGUESE: [
                "Mostrar mais opções",
                "Adicionar ao carrinho",
                "Categoria diferente",
                "Conte-me mais"
            ],
            Language.GERMAN: [
                "Mehr Optionen anzeigen",
                "In den Warenkorb",
                "Andere Kategorie",
                "Mehr erfahren"
            ],
            Language.ITALIAN: [
                "Mostra più opzioni",
                "Aggiungi al carrello",
                "Categoria diversa",
                "Dimmi di più"
            ],
            Language.RUSSIAN: [
                "Показать больше",
                "Добавить в корзину",
                "Другая категория",
                "Расскажи больше"
            ]
        }
        
        return quick_replies.get(language, quick_replies[Language.ENGLISH])