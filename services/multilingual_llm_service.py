"""
Multilingual LLM Service for WeedGo
Handles multiple language models for different language families
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Dict, Optional, Tuple
from llama_cpp import Llama
import asyncpg
from .dynamic_model_selector import DynamicModelSelector

logger = logging.getLogger(__name__)

class MultilingualLLMService:
    """
    Service for handling multiple LLMs for different languages
    Uses Qwen for Chinese/Asian languages and Mistral for Western languages
    """
    
    def __init__(self, db_pool: asyncpg.Pool = None):
        self.db_pool = db_pool
        self.models = {}
        self.config = self._load_config()
        self.chinese_vocabulary = self._load_chinese_vocabulary()
        self.model_selector = DynamicModelSelector()
        
    def _load_config(self) -> Dict:
        """Load multilingual model configuration"""
        config_path = Path(__file__).parent.parent / "config" / "multilingual_models.json"
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # Default configuration
            return {
                "models": {
                    "qwen": {
                        "path": "models/multilingual/qwen2.5-7b-instruct-q4_k_m.gguf",
                        "languages": ["zh", "ar", "ja", "ko"],
                        "context_size": 4096,
                        "gpu_layers": 35,
                        "threads": 8
                    },
                    "mistral": {
                        "path": "models/base/mistral-7b-instruct-v0.2.Q4_K_M.gguf",
                        "languages": ["en", "es", "fr", "pt"],
                        "context_size": 4096,
                        "gpu_layers": 35,
                        "threads": 8
                    }
                },
                "language_routing": {
                    "zh": "qwen",
                    "zh-cn": "qwen",
                    "zh-tw": "qwen",
                    "ar": "qwen",
                    "ja": "qwen",
                    "ko": "qwen",
                    "en": "mistral",
                    "es": "mistral",
                    "fr": "mistral",
                    "pt": "mistral"
                }
            }
    
    def _load_chinese_vocabulary(self) -> Dict:
        """Load Chinese cannabis vocabulary"""
        vocab_path = Path(__file__).parent.parent / "data" / "chinese_cannabis_vocabulary.json"
        if vocab_path.exists():
            with open(vocab_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    @property
    def llm(self):
        """Expose default LLM for language detection"""
        # Return the first available model (preferably qwen for multilingual)
        if "qwen" in self.models:
            return self.models["qwen"]
        elif "mistral" in self.models:
            return self.models["mistral"]
        return None
    
    async def initialize(self):
        """Initialize language models with dynamic selection"""
        base_path = Path(__file__).parent.parent
        
        # Dynamically select and load models for Chinese/Arabic
        for language in ["zh", "ar"]:
            model_info = self.model_selector.select_model_for_language(language)
            if model_info:
                model_name, model_path = model_info
                if "qwen" in model_name.lower():
                    try:
                        logger.info(f"Loading {model_name} for {language} from {model_path}")
                        # Use consistent key for all Qwen models
                        self.models["qwen"] = Llama(
                            model_path=str(model_path),
                            n_ctx=self.config["models"].get("qwen", {}).get("context_size", 4096),
                            n_gpu_layers=self.config["models"].get("qwen", {}).get("gpu_layers", 35),
                            n_threads=self.config["models"].get("qwen", {}).get("threads", 8),
                            verbose=False
                        )
                        logger.info(f"✅ {model_name} loaded successfully for {language}")
                        break  # One Qwen model can handle multiple languages
                    except Exception as e:
                        logger.error(f"Failed to load {model_name}: {e}")
            else:
                logger.warning(f"No suitable model found for {language}")
        
        # Load Mistral for Western languages (already loaded by SmartAIEngineV3)
        # We'll reference it from the main engine
        logger.info("Multilingual LLM Service initialized")
    
    def get_model_for_language(self, language: str) -> Optional[str]:
        """Determine which model to use for a language"""
        return self.config["language_routing"].get(language, "mistral")
    
    async def generate_response(
        self,
        message: str,
        language: str,
        context: Dict = None,
        max_tokens: int = 512,
        temperature: float = 0.7
    ) -> Tuple[str, float]:
        """
        Generate response in the specified language
        Returns: (response_text, confidence_score)
        """
        
        model_name = self.get_model_for_language(language)
        
        # If Qwen is not available, return error
        if model_name == "qwen" and "qwen" not in self.models:
            logger.error(f"Qwen model not available for {language}")
            return self._get_fallback_response(language), 0.0
        
        if model_name == "qwen":
            return await self._generate_with_qwen(message, language, context, max_tokens, temperature)
        else:
            # For Mistral languages, return None to use the default engine
            return None, 0.0
    
    async def _generate_with_qwen(
        self,
        message: str,
        language: str,
        context: Dict,
        max_tokens: int,
        temperature: float
    ) -> Tuple[str, float]:
        """Generate response using Qwen model"""
        
        # Get language-specific prompt
        system_prompt = self._get_system_prompt(language)
        
        # Build conversation context
        conversation = ""
        if context and context.get("previous_messages"):
            for msg in context["previous_messages"][-3:]:  # Last 3 messages
                role = "user" if msg["role"] == "user" else "assistant"
                conversation += f"<|im_start|>{role}\n{msg['content']}<|im_end|>\n"
        
        # Format prompt for Qwen
        prompt = f"""<|im_start|>system
{system_prompt}
<|im_end|>
{conversation}<|im_start|>user
{message}
<|im_end|>
<|im_start|>assistant
"""
        
        try:
            # Generate response
            response = self.models["qwen"](
                prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                stop=["<|im_end|>", "<|im_start|>"],
                echo=False
            )
            
            text = response['choices'][0]['text'].strip()
            
            # Add product search if mentioned
            if any(keyword in message.lower() for keyword in ['产品', '推荐', '什么', 'thc', 'cbd']):
                products = await self._search_products_chinese(message)
                if products:
                    text += self._format_products_chinese(products)
            
            return text, 0.95  # High confidence for native model
            
        except Exception as e:
            logger.error(f"Qwen generation failed: {e}")
            return self._get_fallback_response(language), 0.0
    
    async def _search_products_chinese(self, query: str) -> list:
        """Search for products based on Chinese query"""
        if not self.db_pool:
            return []
        
        # Extract intent from Chinese query
        search_terms = []
        
        # Check for THC/CBD mentions
        if 'thc' in query.lower() or '含量' in query:
            search_terms.append("high_thc")
        if 'cbd' in query.lower():
            search_terms.append("high_cbd")
        
        # Check for strain types
        if '萨蒂瓦' in query or 'sativa' in query.lower():
            search_terms.append("sativa")
        elif '印度' in query or 'indica' in query.lower():
            search_terms.append("indica")
        elif '混合' in query or 'hybrid' in query.lower():
            search_terms.append("hybrid")
        
        # Check for product types
        if '花' in query:
            search_terms.append("flower")
        elif '食用' in query or '吃' in query:
            search_terms.append("edibles")
        elif '电子烟' in query or '烟' in query:
            search_terms.append("vape")
        
        # Build search query
        try:
            async with self.db_pool.acquire() as conn:
                conditions = []
                params = []
                param_count = 0
                
                if "high_thc" in search_terms:
                    conditions.append("thc_content > 20")
                if "high_cbd" in search_terms:
                    conditions.append("cbd_content > 10")
                
                for term in ["sativa", "indica", "hybrid"]:
                    if term in search_terms:
                        param_count += 1
                        conditions.append(f"plant_type ILIKE ${param_count}")
                        params.append(f"%{term}%")
                
                if "flower" in search_terms:
                    param_count += 1
                    conditions.append(f"category = ${param_count}")
                    params.append("Flower")
                elif "edibles" in search_terms:
                    param_count += 1
                    conditions.append(f"category = ${param_count}")
                    params.append("Edibles")
                elif "vape" in search_terms:
                    param_count += 1
                    conditions.append(f"category = ${param_count}")
                    params.append("Vapes")
                
                where_clause = " AND ".join(conditions) if conditions else "1=1"
                
                query = f"""
                    SELECT id, product_name, brand, category, 
                           thc_content, cbd_content, price, plant_type
                    FROM products
                    WHERE {where_clause}
                    ORDER BY thc_content DESC NULLS LAST
                    LIMIT 5
                """
                
                results = await conn.fetch(query, *params)
                return [dict(r) for r in results]
                
        except Exception as e:
            logger.error(f"Product search failed: {e}")
            return []
    
    def _format_products_chinese(self, products: list) -> str:
        """Format products for Chinese response"""
        if not products:
            return ""
        
        response = "\n\n为您推荐以下产品：\n"
        for i, product in enumerate(products, 1):
            response += f"\n{i}. {product['product_name']}"
            if product.get('brand'):
                response += f" - {product['brand']}"
            response += f"\n   类别: {self._translate_category(product.get('category', ''))}"
            if product.get('thc_content'):
                response += f"\n   THC含量: {product['thc_content']}%"
            if product.get('cbd_content'):
                response += f"\n   CBD含量: {product['cbd_content']}%"
            if product.get('price'):
                response += f"\n   价格: ${product['price']}"
            response += "\n"
        
        return response
    
    def _translate_category(self, category: str) -> str:
        """Translate category to Chinese"""
        translations = {
            "Flower": "花",
            "Edibles": "食用品",
            "Vapes": "电子烟",
            "Concentrates": "浓缩物",
            "Topicals": "外用品",
            "Accessories": "配件"
        }
        return translations.get(category, category)
    
    def _get_system_prompt(self, language: str) -> str:
        """Get system prompt for specific language"""
        prompts = {
            "zh": """你是一个专业友好的大麻产品顾问。你的职责是：
1. 用中文回答客户关于大麻产品的问题
2. 提供准确的产品信息，包括THC/CBD含量、效果和价格
3. 根据客户需求推荐合适的产品
4. 解释不同品种（Sativa萨蒂瓦、Indica印度大麻、Hybrid混合）的区别
5. 保持专业、友好和有帮助的态度
6. 如果客户是新手，建议从低THC含量的产品开始

重要：始终用中文回答，保持专业性。""",
            
            "ar": """أنت مستشار محترف وودود لمنتجات القنب. واجباتك:
1. الإجابة على أسئلة العملاء حول منتجات القنب بالعربية
2. تقديم معلومات دقيقة عن المنتجات
3. التوصية بالمنتجات المناسبة
4. الحفاظ على الاحترافية واللطف""",
            
            "ja": """あなたはプロフェッショナルで親切な大麻製品アドバイザーです。
お客様の質問に日本語で答え、適切な製品を推薦してください。""",
            
            "ko": """당신은 전문적이고 친절한 대마초 제품 상담원입니다.
한국어로 고객의 질문에 답하고 적절한 제품을 추천해주세요."""
        }
        
        return prompts.get(language, prompts["zh"])
    
    def _get_fallback_response(self, language: str) -> str:
        """Get fallback response when model is not available"""
        fallbacks = {
            "zh": "抱歉，我暂时无法处理您的请求。请稍后再试或用英语提问。",
            "ar": "عذرًا، لا أستطيع معالجة طلبك حاليًا. يرجى المحاولة لاحقًا أو السؤال بالإنجليزية.",
            "ja": "申し訳ございません。現在リクエストを処理できません。",
            "ko": "죄송합니다. 현재 요청을 처리할 수 없습니다."
        }
        return fallbacks.get(language, "Sorry, I cannot process your request in this language.")
    
    async def translate_products(self, products: list, target_language: str) -> list:
        """Translate product information to target language"""
        if target_language == "zh":
            # Add Chinese descriptions
            for product in products:
                if product.get('category'):
                    product['category_translated'] = self._translate_category(product['category'])
                
                # Translate strain type
                if product.get('plant_type'):
                    strain_map = {
                        'sativa': '萨蒂瓦',
                        'indica': '印度大麻',
                        'hybrid': '混合'
                    }
                    for eng, chi in strain_map.items():
                        if eng in product['plant_type'].lower():
                            product['plant_type_translated'] = chi
                            break
        
        return products