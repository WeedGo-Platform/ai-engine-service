"""
Multilingual Intent Detector
Shows how intent detection works across different languages
"""
import json
import logging
from typing import Dict, Optional, List, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class MultilingualIntent:
    """Intent detected from any language"""
    intent_type: str
    confidence: float
    entities: Dict
    original_language: str
    original_text: str
    understood_meaning: str

class MultilingualIntentDetector:
    """
    Detects intent from messages in any language
    Uses model's multilingual understanding
    """
    
    def __init__(self, llm_instance=None):
        self.llm = llm_instance
        self.intent_mappings = self._load_universal_intents()
        
    def _load_universal_intents(self) -> Dict:
        """
        Universal intent patterns that work across languages
        These are SEMANTIC patterns, not word patterns
        """
        return {
            "greeting": {
                "semantic_markers": ["polite opening", "hello equivalent", "time-based greeting"],
                "examples": {
                    "en": ["hello", "hi", "hey", "good morning"],
                    "es": ["hola", "buenos días", "buenas tardes", "qué tal"],
                    "zh": ["你好", "您好", "早上好", "晚上好"],
                    "ar": ["مرحبا", "السلام عليكم", "صباح الخير", "مساء الخير"],
                    "hi": ["नमस्ते", "नमस्कार", "सुप्रभात", "शुभ संध्या"],
                    "fr": ["bonjour", "bonsoir", "salut", "coucou"],
                    "de": ["hallo", "guten tag", "guten morgen", "grüß gott"],
                    "ja": ["こんにちは", "おはよう", "こんばんは", "やあ"],
                    "ko": ["안녕하세요", "안녕", "좋은 아침", "좋은 저녁"],
                    "pt": ["olá", "oi", "bom dia", "boa tarde"],
                    "ru": ["привет", "здравствуйте", "добрый день", "доброе утро"],
                    "sw": ["jambo", "habari", "salama", "hujambo"],
                    "th": ["สวัสดี", "หวัดดี", "อรุณสวัสดิ์", "สายัณสวัสดิ์"]
                }
            },
            "product_search": {
                "semantic_markers": ["looking for", "show items", "what do you have", "browse"],
                "examples": {
                    "en": ["show me", "what do you have", "I'm looking for", "do you carry"],
                    "es": ["muéstrame", "qué tienes", "estoy buscando", "tienen"],
                    "zh": ["给我看", "你有什么", "我在找", "有没有"],
                    "ar": ["أرني", "ماذا لديك", "أبحث عن", "هل عندك"],
                    "hi": ["मुझे दिखाओ", "क्या है", "मैं ढूंढ रहा हूं", "क्या आपके पास है"],
                    "fr": ["montrez-moi", "qu'avez-vous", "je cherche", "avez-vous"],
                    "de": ["zeig mir", "was haben sie", "ich suche", "haben sie"],
                    "ja": ["見せて", "何がありますか", "探しています", "ありますか"],
                    "ko": ["보여주세요", "뭐 있어요", "찾고 있어요", "있나요"],
                    "pt": ["mostre-me", "o que você tem", "estou procurando", "vocês têm"]
                }
            },
            "recommendation": {
                "semantic_markers": ["need help", "suggest", "recommend", "what's good for"],
                "examples": {
                    "en": ["I need something for", "recommend", "what's good for", "suggest"],
                    "es": ["necesito algo para", "recomienda", "qué es bueno para", "sugiere"],
                    "zh": ["我需要", "推荐", "什么好", "建议"],
                    "ar": ["أحتاج شيئا لـ", "أوصي", "ما هو جيد لـ", "اقترح"],
                    "hi": ["मुझे चाहिए", "सिफारिश करें", "क्या अच्छा है", "सुझाव दें"],
                    "fr": ["j'ai besoin de", "recommandez", "qu'est-ce qui est bon pour", "suggérez"],
                    "de": ["ich brauche etwas für", "empfehlen", "was ist gut für", "vorschlagen"],
                    "ja": ["必要です", "おすすめ", "何がいい", "提案して"],
                    "ko": ["필요해요", "추천", "뭐가 좋아요", "제안해주세요"],
                    "pt": ["preciso de algo para", "recomende", "o que é bom para", "sugira"]
                }
            },
            "pain_relief": {
                "semantic_markers": ["pain", "hurt", "ache", "sore", "relief"],
                "examples": {
                    "en": ["pain", "hurt", "ache", "sore", "relief"],
                    "es": ["dolor", "duele", "adolorido", "alivio", "dolencia"],
                    "zh": ["疼", "痛", "酸痛", "缓解", "止痛"],
                    "ar": ["ألم", "وجع", "يؤلم", "تخفيف", "مسكن"],
                    "hi": ["दर्द", "पीड़ा", "राहत", "दुखना", "कष्ट"],
                    "fr": ["douleur", "mal", "soulagement", "souffrance", "analgésique"],
                    "de": ["schmerz", "weh", "linderung", "schmerzlinderung", "leiden"],
                    "ja": ["痛み", "痛い", "緩和", "鎮痛", "苦痛"],
                    "ko": ["통증", "아프다", "완화", "진통", "고통"],
                    "pt": ["dor", "doer", "alívio", "sofrimento", "analgésico"],
                    "ru": ["боль", "болит", "облегчение", "обезболивающее", "страдание"],
                    "it": ["dolore", "male", "sollievo", "sofferenza", "antidolorifico"]
                }
            },
            "sleep": {
                "semantic_markers": ["sleep", "insomnia", "rest", "night", "bed"],
                "examples": {
                    "en": ["sleep", "insomnia", "can't sleep", "rest", "bedtime"],
                    "es": ["dormir", "insomnio", "no puedo dormir", "descansar", "sueño"],
                    "zh": ["睡觉", "失眠", "睡不着", "休息", "安眠"],
                    "ar": ["نوم", "أرق", "لا أستطيع النوم", "راحة", "نعاس"],
                    "hi": ["नींद", "अनिद्रा", "सो नहीं सकता", "आराम", "सोना"],
                    "fr": ["dormir", "insomnie", "ne peux pas dormir", "repos", "sommeil"],
                    "de": ["schlafen", "schlaflosigkeit", "kann nicht schlafen", "ruhe", "schlaf"],
                    "ja": ["睡眠", "不眠症", "眠れない", "休息", "寝る"],
                    "ko": ["수면", "불면증", "잠 못 자", "휴식", "잠"],
                    "pt": ["dormir", "insônia", "não consigo dormir", "descanso", "sono"]
                }
            },
            "anxiety": {
                "semantic_markers": ["anxious", "nervous", "stress", "worry", "calm"],
                "examples": {
                    "en": ["anxiety", "anxious", "nervous", "stressed", "worry"],
                    "es": ["ansiedad", "ansioso", "nervioso", "estresado", "preocupación"],
                    "zh": ["焦虑", "紧张", "压力", "担心", "烦躁"],
                    "ar": ["قلق", "متوتر", "عصبي", "ضغط", "هم"],
                    "hi": ["चिंता", "घबराहट", "तनाव", "परेशान", "बेचैन"],
                    "fr": ["anxiété", "anxieux", "nerveux", "stressé", "inquiétude"],
                    "de": ["angst", "ängstlich", "nervös", "gestresst", "sorge"],
                    "ja": ["不安", "心配", "ストレス", "緊張", "悩み"],
                    "ko": ["불안", "긴장", "스트레스", "걱정", "초조"],
                    "pt": ["ansiedade", "ansioso", "nervoso", "estressado", "preocupação"]
                }
            }
        }
    
    async def detect_intent_multilingual(
        self,
        text: str,
        detected_language: str,
        language_confidence: float
    ) -> MultilingualIntent:
        """
        Detect intent from text in any language
        
        The key insight: Modern multilingual models understand MEANING across languages
        They don't translate - they directly understand
        """
        
        # Step 1: Create a multilingual-aware prompt
        prompt = self._create_multilingual_prompt(text, detected_language)
        
        # Step 2: Get model's understanding
        response = await self._get_model_understanding(prompt)
        
        # Step 3: Parse multilingual response
        intent = self._parse_multilingual_response(response, text, detected_language)
        
        return intent
    
    def _create_multilingual_prompt(self, text: str, language: str) -> str:
        """
        Create a prompt that works for any language
        Key: We DON'T translate - we let the model understand directly
        """
        
        # The prompt is in English but the model understands the non-English input
        prompt = f"""Analyze this message in {language} and detect the intent.
The message is in {language}, but you should understand it directly without translation.

Message: {text}

Identify:
1. What does the user want? (intent)
2. What specific things are mentioned? (entities)
3. What effects/symptoms/needs are expressed?

Respond in JSON format:
{{
    "intent": "greeting|search|recommendation|purchase|info|help",
    "confidence": 0.0-1.0,
    "entities": {{
        "products": [],
        "effects": [],
        "symptoms": [],
        "preferences": []
    }},
    "understood_meaning": "what the user is asking for in English"
}}

JSON Response:"""
        
        return prompt
    
    async def _get_model_understanding(self, prompt: str) -> Dict:
        """
        Get the model's understanding of the multilingual input
        
        Key insight: Models like Qwen, Mistral, Llama-3 have seen millions of 
        multilingual examples during training. They understand meaning across languages.
        """
        
        if not self.llm:
            return {"error": "No model available"}
        
        try:
            # The model processes the prompt with multilingual text
            response = self.llm(
                prompt,
                max_tokens=200,
                temperature=0.3,  # Low for consistency
                echo=False
            )
            
            return response
        except Exception as e:
            logger.error(f"Model understanding failed: {e}")
            return {"error": str(e)}
    
    def _parse_multilingual_response(
        self,
        response: Dict,
        original_text: str,
        language: str
    ) -> MultilingualIntent:
        """
        Parse the model's understanding into structured intent
        """
        
        try:
            response_text = response.get('choices', [{}])[0].get('text', '')
            
            # Extract JSON
            if '{' in response_text:
                json_start = response_text.find('{')
                json_end = response_text.rfind('}') + 1
                json_str = response_text[json_start:json_end]
                intent_data = json.loads(json_str)
            else:
                intent_data = {
                    "intent": "general",
                    "confidence": 0.5,
                    "entities": {},
                    "understood_meaning": "unclear"
                }
            
            return MultilingualIntent(
                intent_type=intent_data.get("intent", "general"),
                confidence=intent_data.get("confidence", 0.5),
                entities=intent_data.get("entities", {}),
                original_language=language,
                original_text=original_text,
                understood_meaning=intent_data.get("understood_meaning", "")
            )
            
        except Exception as e:
            logger.error(f"Failed to parse response: {e}")
            return MultilingualIntent(
                intent_type="general",
                confidence=0.3,
                entities={},
                original_language=language,
                original_text=original_text,
                understood_meaning="parse_error"
            )
    
    def demonstrate_multilingual_understanding(self) -> Dict:
        """
        Show how the same intent is understood across languages
        """
        
        examples = {
            "pain_relief_requests": {
                "en": "I need something strong for back pain",
                "es": "Necesito algo fuerte para el dolor de espalda",
                "zh": "我需要一些强效的东西来缓解背痛",
                "ar": "أحتاج شيئا قويا لألم الظهر",
                "hi": "मुझे पीठ दर्द के लिए कुछ मजबूत चाहिए",
                "fr": "J'ai besoin de quelque chose de fort pour le mal de dos",
                "de": "Ich brauche etwas Starkes gegen Rückenschmerzen",
                "ja": "腰痛に効く強いものが必要です",
                "ko": "허리 통증에 강한 것이 필요해요",
                "pt": "Preciso de algo forte para dor nas costas",
                "ru": "Мне нужно что-то сильное от боли в спине",
                "it": "Ho bisogno di qualcosa di forte per il mal di schiena"
            },
            "sleep_requests": {
                "en": "What do you have for insomnia?",
                "es": "¿Qué tienes para el insomnio?",
                "zh": "你有什么治疗失眠的吗？",
                "ar": "ماذا لديك للأرق؟",
                "hi": "अनिद्रा के लिए क्या है?",
                "fr": "Qu'avez-vous pour l'insomnie?",
                "de": "Was haben Sie gegen Schlaflosigkeit?",
                "ja": "不眠症に何かありますか？",
                "ko": "불면증에 뭐 있어요?",
                "pt": "O que você tem para insônia?",
                "th": "มีอะไรสำหรับนอนไม่หลับไหม",
                "vi": "Bạn có gì cho chứng mất ngủ?"
            }
        }
        
        # All of these would be understood as the SAME intent
        # despite being in different languages
        
        return {
            "explanation": "The model understands the SEMANTIC MEANING, not just words",
            "examples": examples,
            "key_insight": "Modern LLMs are trained on multilingual data and understand concepts across languages"
        }
    
    def explain_how_it_works(self) -> str:
        """
        Explain the technical details of multilingual intent detection
        """
        
        explanation = """
        HOW MULTILINGUAL INTENT DETECTION WORKS:
        
        1. **Multilingual Embeddings**
           - Models convert text to vector representations
           - Similar meanings have similar vectors regardless of language
           - "pain" (English) ≈ "dolor" (Spanish) ≈ "痛" (Chinese) in vector space
        
        2. **Cross-Lingual Training**
           - Models like Qwen, Mistral, Llama-3 trained on many languages
           - They learn that "I need" = "Necesito" = "我需要" = "J'ai besoin"
           - Concepts map across languages in the model's weights
        
        3. **Semantic Understanding**
           - The model doesn't translate word-by-word
           - It understands the MEANING directly
           - "Necesito algo para dormir" → [NEED] + [SOMETHING] + [PURPOSE: SLEEP]
        
        4. **Intent Recognition Process**
           
           Spanish: "Necesito algo fuerte para el dolor"
                            ↓
           Model Internal: [NEED] [SOMETHING] [STRONG] [FOR] [PAIN]
                            ↓
           Intent: RECOMMENDATION (pain relief, strong preference)
        
        5. **Why This Works**
           - Transformer architecture processes sequences regardless of language
           - Attention mechanism finds relationships between concepts
           - Multi-head attention captures different linguistic patterns
           - The model has seen millions of examples in each language
        
        6. **Entity Extraction Across Languages**
           
           Input: "我需要一些強效的CBD產品" (Chinese)
           
           Model understands:
           - 我需要 = "I need" (intent marker)
           - 強效的 = "strong/potent" (preference)
           - CBD = "CBD" (product type - same in all languages)
           - 產品 = "products" (category)
           
           Extracted: {
               "intent": "product_search",
               "entities": {
                   "product_type": "CBD",
                   "preference": "strong",
                   "category": "products"
               }
           }
        
        7. **Challenges Handled**
           - Idioms: "Me duele la cabeza" (head hurts) → headache
           - Cultural expressions: Different ways to express needs
           - Script differences: Arabic RTL, Chinese characters, etc.
           - Formality levels: Polite forms in Japanese, formal Spanish
        
        The key is that the model learned these patterns during training,
        not through explicit programming!
        """
        
        return explanation