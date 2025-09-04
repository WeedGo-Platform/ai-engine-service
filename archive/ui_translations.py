"""
UI Translations for Quick Actions and Quick Replies
"""

class UITranslations:
    """Handles translations for UI elements like quick actions and quick replies"""
    
    # Quick replies translations
    QUICK_REPLIES = {
        "en": [
            "Show popular products",
            "I need help choosing",
            "What's on sale?",
            "Tell me about strains"
        ],
        "es": [
            "Mostrar productos populares",
            "Necesito ayuda para elegir",
            "¿Qué hay en oferta?",
            "Cuéntame sobre las cepas"
        ],
        "zh": [
            "显示热门产品",
            "我需要帮助选择",
            "有什么特价？",
            "介绍一下品种"
        ],
        "fr": [
            "Afficher les produits populaires",
            "J'ai besoin d'aide pour choisir",
            "Qu'est-ce qui est en promotion?",
            "Parlez-moi des variétés"
        ]
    }
    
    # Quick action labels translations
    QUICK_ACTION_LABELS = {
        "en": {
            "tell_me_more": "Tell me more",
            "show_products": "Show products",
            "get_help": "Get help",
            "start_fresh": "Start fresh",
            "relaxation": "Relaxation",
            "pain_relief": "Pain relief",
            "energy_boost": "Energy boost",
            "browse_all": "Browse all",
            "add_to_cart": "Add to cart",
            "view_details": "View details",
            "similar_products": "Similar products",
            "checkout": "Checkout"
        },
        "es": {
            "tell_me_more": "Cuéntame más",
            "show_products": "Mostrar productos",
            "get_help": "Obtener ayuda",
            "start_fresh": "Empezar de nuevo",
            "relaxation": "Relajación",
            "pain_relief": "Alivio del dolor",
            "energy_boost": "Impulso de energía",
            "browse_all": "Ver todo",
            "add_to_cart": "Añadir al carrito",
            "view_details": "Ver detalles",
            "similar_products": "Productos similares",
            "checkout": "Pagar"
        },
        "zh": {
            "tell_me_more": "了解更多",
            "show_products": "显示产品",
            "get_help": "获取帮助",
            "start_fresh": "重新开始",
            "relaxation": "放松",
            "pain_relief": "缓解疼痛",
            "energy_boost": "提神",
            "browse_all": "浏览全部",
            "add_to_cart": "加入购物车",
            "view_details": "查看详情",
            "similar_products": "类似产品",
            "checkout": "结账"
        },
        "fr": {
            "tell_me_more": "Dis-moi plus",
            "show_products": "Afficher les produits",
            "get_help": "Obtenir de l'aide",
            "start_fresh": "Recommencer",
            "relaxation": "Relaxation",
            "pain_relief": "Soulagement de la douleur",
            "energy_boost": "Regain d'énergie",
            "browse_all": "Tout parcourir",
            "add_to_cart": "Ajouter au panier",
            "view_details": "Voir les détails",
            "similar_products": "Produits similaires",
            "checkout": "Commander"
        }
    }
    
    # Quick action values translations (what the user would say)
    QUICK_ACTION_VALUES = {
        "en": {
            "can_you_explain_more": "Can you explain more?",
            "what_do_you_have": "What do you have?",
            "i_need_help": "I need help",
            "lets_start_over": "Let's start over",
            "something_to_relax": "Something to relax",
            "for_pain_relief": "For pain relief",
            "something_energizing": "Something energizing",
            "show_me_options": "Just show me options"
        },
        "es": {
            "can_you_explain_more": "¿Puedes explicar más?",
            "what_do_you_have": "¿Qué tienes?",
            "i_need_help": "Necesito ayuda",
            "lets_start_over": "Empecemos de nuevo",
            "something_to_relax": "Algo para relajarme",
            "for_pain_relief": "Para aliviar el dolor",
            "something_energizing": "Algo energizante",
            "show_me_options": "Solo muéstrame opciones"
        },
        "zh": {
            "can_you_explain_more": "你能解释更多吗？",
            "what_do_you_have": "你有什么？",
            "i_need_help": "我需要帮助",
            "lets_start_over": "让我们重新开始",
            "something_to_relax": "放松的产品",
            "for_pain_relief": "缓解疼痛",
            "something_energizing": "提神的产品",
            "show_me_options": "显示选项"
        },
        "fr": {
            "can_you_explain_more": "Peux-tu expliquer plus?",
            "what_do_you_have": "Qu'est-ce que vous avez?",
            "i_need_help": "J'ai besoin d'aide",
            "lets_start_over": "Recommençons",
            "something_to_relax": "Quelque chose pour se détendre",
            "for_pain_relief": "Pour soulager la douleur",
            "something_energizing": "Quelque chose d'énergisant",
            "show_me_options": "Montrez-moi les options"
        }
    }
    
    @classmethod
    def translate_quick_replies(cls, language: str = "en") -> list:
        """Get quick replies in the specified language"""
        return cls.QUICK_REPLIES.get(language, cls.QUICK_REPLIES["en"])
    
    @classmethod
    def translate_quick_action(cls, action: dict, language: str = "en") -> dict:
        """Translate a quick action to the specified language"""
        if language == "en":
            return action  # No translation needed
        
        translated_action = action.copy()
        
        # Dynamic translation patterns for labels and values
        label_translations = {
            "es": {
                # Basic actions
                "Tell me more": "Cuéntame más",
                "Show products": "Mostrar productos",
                "Get help": "Obtener ayuda",
                "Start fresh": "Empezar de nuevo",
                "Browse products": "Ver productos",
                "Get recommendation": "Obtener recomendación",
                "New to cannabis": "Nuevo en cannabis",
                "Specific need": "Necesidad específica",
                # Effects
                "Relaxation": "Relajación",
                "Pain relief": "Alivio del dolor",
                "Energy boost": "Impulso de energía",
                "Browse all": "Ver todo",
                # Cart actions
                "Add to cart": "Añadir al carrito",
                "View details": "Ver detalles",
                "Similar products": "Productos similares",
                "Checkout": "Pagar",
                "Buy it": "Comprarlo",
                "View cart": "Ver carrito",
                "Keep shopping": "Seguir comprando",
                "Remove item": "Quitar artículo",
                # Categories
                "Flower": "Flor",
                "Edibles": "Comestibles",
                "Vapes": "Vaporizadores",
                "Surprise me": "Sorpréndeme",
                # Experience levels
                "First timer": "Primera vez",
                "Some experience": "Algo de experiencia",
                "Regular user": "Usuario regular",
                "Need guidance": "Necesito orientación",
                # Price
                "Cheaper options": "Opciones más baratas",
                "Compare prices": "Comparar precios",
                "Keep browsing": "Seguir viendo",
                "Check price": "Ver precio",
                # General
                "All products": "Todos los productos",
                "Categories": "Categorías",
                "Best sellers": "Más vendidos",
                "Help me choose": "Ayúdame a elegir",
                "Other categories": "Otras categorías",
                "Other effects": "Otros efectos",
                "Similar options": "Opciones similares",
                "Compare strains": "Comparar cepas",
                "1 gram": "1 gramo",
                "Eighth (3.5g)": "Octavo (3.5g)",
                "Quarter (7g)": "Cuarto (7g)",
                "Help me decide": "Ayúdame a decidir"
            },
            "zh": {
                "Tell me more": "了解更多",
                "Show products": "显示产品",
                "Get help": "获取帮助",
                "Start fresh": "重新开始",
                "Browse products": "浏览产品",
                "Get recommendation": "获取推荐",
                "Relaxation": "放松",
                "Pain relief": "缓解疼痛",
                "Energy boost": "提神",
                "Browse all": "浏览全部",
                "Add to cart": "加入购物车",
                "View details": "查看详情",
                "Similar products": "类似产品",
                "Checkout": "结账"
            },
            "fr": {
                "Tell me more": "Dis-moi plus",
                "Show products": "Afficher les produits",
                "Get help": "Obtenir de l'aide",
                "Start fresh": "Recommencer",
                "Browse products": "Parcourir les produits",
                "Get recommendation": "Obtenir une recommandation",
                "Relaxation": "Relaxation",
                "Pain relief": "Soulagement de la douleur",
                "Energy boost": "Regain d'énergie",
                "Browse all": "Tout parcourir",
                "Add to cart": "Ajouter au panier",
                "View details": "Voir les détails",
                "Similar products": "Produits similaires",
                "Checkout": "Commander"
            }
        }
        
        value_translations = {
            "es": {
                # Basic queries
                "Can you explain more?": "¿Puedes explicar más?",
                "What do you have?": "¿Qué tienes?",
                "I need help": "Necesito ayuda",
                "Let's start over": "Empecemos de nuevo",
                "Show me products": "Muéstrame productos",
                "Recommend something": "Recomienda algo",
                "I'm new to this": "Soy nuevo en esto",
                "I have a specific need": "Tengo una necesidad específica",
                # Effects
                "Something to relax": "Algo para relajarme",
                "For pain relief": "Para aliviar el dolor",
                "Something energizing": "Algo energizante",
                "Just show me options": "Solo muéstrame opciones",
                # Cart
                "I'll take it": "Lo tomaré",
                "Ready to checkout": "Listo para pagar",
                "Show more products": "Mostrar más productos",
                "Show my cart": "Mostrar mi carrito",
                "Remove from cart": "Quitar del carrito",
                # Categories
                "I prefer flower": "Prefiero flor",
                "I like edibles": "Me gustan los comestibles",
                "Vaping products": "Productos de vapeo",
                # Experience
                "This is my first time": "Esta es mi primera vez",
                "I have some experience": "Tengo algo de experiencia",
                "I use regularly": "Uso regularmente",
                "Help me understand": "Ayúdame a entender",
                # Price
                "Show cheaper options": "Mostrar opciones más baratas",
                "Compare similar products": "Comparar productos similares",
                "Show me more": "Muéstrame más",
                # General
                "Show all products": "Mostrar todos los productos",
                "Show categories": "Mostrar categorías",
                "What's popular?": "¿Qué es popular?",
                "Help me decide": "Ayúdame a decidir",
                "Just 1 gram": "Solo 1 gramo",
                "An eighth please": "Un octavo por favor",
                "A quarter ounce": "Un cuarto de onza",
                "What do you recommend?": "¿Qué recomiendas?",
                "Show other categories": "Mostrar otras categorías",
                "What about other effects?": "¿Qué hay de otros efectos?"
            },
            "zh": {
                "Can you explain more?": "你能解释更多吗？",
                "What do you have?": "你有什么？",
                "I need help": "我需要帮助",
                "Let's start over": "让我们重新开始",
                "Show me products": "给我看产品",
                "Recommend something": "推荐一些",
                "Something to relax": "放松的产品",
                "For pain relief": "缓解疼痛",
                "Something energizing": "提神的产品",
                "Just show me options": "显示选项"
            },
            "fr": {
                "Can you explain more?": "Peux-tu expliquer plus?",
                "What do you have?": "Qu'est-ce que vous avez?",
                "I need help": "J'ai besoin d'aide",
                "Let's start over": "Recommençons",
                "Show me products": "Montrez-moi les produits",
                "Recommend something": "Recommande quelque chose",
                "Something to relax": "Quelque chose pour se détendre",
                "For pain relief": "Pour soulager la douleur",
                "Something energizing": "Quelque chose d'énergisant",
                "Just show me options": "Montrez-moi les options"
            }
        }
        
        # Translate label
        label = action.get("label", "")
        if language in label_translations and label in label_translations[language]:
            translated_action["label"] = label_translations[language][label]
        # Also try to translate dynamic labels with product names
        elif label and language == "es":
            translated_action["label"] = cls._translate_dynamic_label_spanish(label)
        
        # Translate value
        value = action.get("value", "")
        if language in value_translations and value in value_translations[language]:
            translated_action["value"] = value_translations[language][value]
        # Also try to translate dynamic values with product names
        elif value and language == "es":
            translated_action["value"] = cls._translate_dynamic_value_spanish(value)
        
        return translated_action
    
    @classmethod
    def _translate_dynamic_label_spanish(cls, label: str) -> str:
        """Translate dynamic labels that include product names"""
        # Handle patterns like "More about Blue Dream"
        if label.startswith("More about"):
            product = label.replace("More about ", "")
            return f"Más sobre {product}"
        elif label.startswith("Best for"):
            effect = label.replace("Best for ", "")
            return f"Mejor para {effect}"
        elif label.startswith("All") and "products" in label:
            effect = label.replace("All ", "").replace(" products", "")
            return f"Todos para {effect}"
        elif label.startswith("Browse"):
            category = label.replace("Browse ", "")
            return f"Ver {category}"
        elif label.startswith("Best"):
            category = label.replace("Best ", "")
            return f"Mejores {category}"
        elif "price ranges" in label.lower():
            category = label.replace(" price ranges?", "")
            return f"Rangos de precio de {category}"
        return label
    
    @classmethod
    def _translate_dynamic_value_spanish(cls, value: str) -> str:
        """Translate dynamic values that include product names and actions"""
        # Common product/strain names to preserve
        products = ["Blue Dream", "OG Kush", "Purple Kush", "Northern Lights", 
                   "Sour Diesel", "Granddaddy Purple", "indica", "sativa", "hybrid"]
        
        # Translate common patterns
        if value.startswith("Tell me more about"):
            product = value.replace("Tell me more about ", "")
            return f"Cuéntame más sobre {product}"
        elif value.startswith("Add") and "to my cart" in value:
            product = value.replace("Add ", "").replace(" to my cart", "")
            return f"Añadir {product} a mi carrito"
        elif value.startswith("Show me similar to"):
            product = value.replace("Show me similar to ", "")
            return f"Muéstrame similar a {product}"
        elif value.startswith("What's the price of"):
            product = value.replace("What's the price of ", "").replace("?", "")
            return f"¿Cuál es el precio de {product}?"
        elif value.startswith("What's best for"):
            effect = value.replace("What's best for ", "").replace("?", "")
            return f"¿Qué es mejor para {effect}?"
        elif value.startswith("Show all for"):
            effect = value.replace("Show all for ", "")
            return f"Mostrar todo para {effect}"
        elif value.startswith("Compare strains for"):
            effect = value.replace("Compare strains for ", "")
            return f"Comparar cepas para {effect}"
        elif value.startswith("Show me all"):
            category = value.replace("Show me all ", "")
            return f"Muéstrame todos los {category}"
        elif value.startswith("What are your best"):
            category = value.replace("What are your best ", "").replace("?", "")
            return f"¿Cuáles son tus mejores {category}?"
        return value
    
    @classmethod
    def translate_quick_actions(cls, actions: list, language: str = "en") -> list:
        """Translate a list of quick actions to the specified language"""
        if language == "en":
            return actions  # No translation needed
        
        return [cls.translate_quick_action(action, language) for action in actions]